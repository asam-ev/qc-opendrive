# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from typing import List, Dict, Optional, Set
from lxml import etree
from scipy.spatial import distance

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import utils, models
from qc_opendrive import basic_preconditions


CHECKER_ID = "check_asam_xodr_lane_smoothness_contact_point_no_horizontal_gaps"
CHECKER_DESCRIPTION = "Two connected drivable lanes shall have no horizontal gaps."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps"

# This parameter needs to be configurable later
TOLERANCE_THRESHOLD = 0.01  # meters

DRIVABLE_LANE_TYPES = {
    "driving",
    "entry",
    "exit",
    "onRamp",
    "offRamp",
    "connectingRamp",
    "slipLane",
    "parking",
    "biking",
    "border",
    "stop",
    "restricted",
}


def _raise_geometry_gap_issue(
    checker_data: models.CheckerData,
    previous_geometry: etree._Element,
    geometry: etree._Element,
    distance: float,
    inertial_point: Optional[models.Point3D],
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"The transition between geometry elements should be defined with no gaps. A gap of {distance} meters has been found.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(previous_geometry),
        description=f"First geometry element",
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(geometry),
        description=f"Second geometry element",
    )

    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description=f"Point where the transition between geometry elements has a gap of {distance} meters.",
        )


def _raise_lane_linkage_gap_issue(
    checker_data: models.CheckerData,
    previous_lane: etree._Element,
    current_lane: etree._Element,
    raised_issue_xpaths: Set[str],
    inertial_point: Optional[models.Point3D],
) -> None:
    issue_xpaths = [
        checker_data.input_file_xml_root.getpath(previous_lane),
        checker_data.input_file_xml_root.getpath(current_lane),
    ]
    sorted_issue_xpaths = sorted(issue_xpaths)

    issue_xpaths_key = "-".join(sorted_issue_xpaths)

    if issue_xpaths_key in raised_issue_xpaths:
        logging.debug(
            f"Issue already raised for xpaths: {issue_xpaths} // inertial_point = {inertial_point}"
        )
        return

    raised_issue_xpaths.add(issue_xpaths_key)

    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"The transition between lane elements should be defined with no gaps.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=issue_xpaths[0],
        description=f"First lane element",
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=issue_xpaths[1],
        description=f"Next lane element",
    )

    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description="Next lane middle reference point",
        )


def _check_geometries_gap(
    road: etree._ElementTree,
    previous_geometry: etree._Element,
    current_geometry: etree._Element,
    checker_data: models.CheckerData,
) -> None:
    x0 = utils.get_x_from_geometry(current_geometry)
    y0 = utils.get_y_from_geometry(current_geometry)

    if x0 is None or y0 is None:
        return

    previous_s0 = utils.get_s_from_geometry(previous_geometry)
    previous_length = utils.get_length_from_geometry(previous_geometry)
    if previous_s0 is None or previous_length is None:
        return

    previous_end_point = utils.get_point_xy_from_geometry(
        previous_geometry, previous_s0 + previous_length
    )

    if previous_end_point is not None:
        gap_size = distance.euclidean(
            (previous_end_point.x, previous_end_point.y),
            (x0, y0),
        )
        if gap_size > TOLERANCE_THRESHOLD:
            inertial_point = None

            current_s = utils.get_s_from_geometry(current_geometry)
            if current_s is not None:
                elevation = utils.get_elevation_from_road_by_s(road, current_s)

                if elevation is not None:
                    z0 = utils.calculate_elevation_value(elevation, current_s)
                    inertial_point = models.Point3D(x=x0, y=y0, z=z0)

            _raise_geometry_gap_issue(
                checker_data,
                previous_geometry,
                current_geometry,
                gap_size,
                inertial_point,
            )


def _check_plan_view_gaps(
    road: etree._ElementTree,
    geometries: etree._ElementTree,
    checker_data: models.CheckerData,
) -> None:
    # we are assuming geometries is a sorted list on s position
    previous_geometry: Optional[etree._Element] = None
    for geometry in geometries:
        if previous_geometry is not None:
            _check_geometries_gap(
                road=road,
                previous_geometry=previous_geometry,
                current_geometry=geometry,
                checker_data=checker_data,
            )

        previous_geometry = geometry


def _compute_inner_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> Optional[models.Point3D]:
    sign = -1 if lane_id < 0 else 1
    current_lane_t = lanes_outer_points.get(lane_id - 1 * sign)
    if current_lane_t is None:
        return None
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


def _compute_outer_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> Optional[models.Point3D]:
    current_lane_t = lanes_outer_points.get(lane_id)
    if current_lane_t is None:
        return None
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


def _compute_middle_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> Optional[models.Point3D]:
    outer_point = _compute_outer_point(lanes_outer_points, lane_id, road, road_s)

    inner_point = _compute_inner_point(lanes_outer_points, lane_id, road, road_s)

    if inner_point is not None and outer_point is not None:
        return models.Point3D(
            x=(inner_point.x + outer_point.x) / 2,
            y=(inner_point.y + outer_point.y) / 2,
            z=(inner_point.z + outer_point.z) / 2,
        )
    else:
        return None


def _equal_outer_border_points(
    road: etree._Element,
    lane_id: int,
    current_outer_points: Dict[int, float],
    current_s: float,
    next_lane_id: int,
    successor_outer_points: Dict[int, float],
    successor_s: float,
) -> bool:
    current_xy = _compute_outer_point(current_outer_points, lane_id, road, current_s)

    next_xy = _compute_outer_point(
        successor_outer_points, next_lane_id, road, successor_s
    )

    if current_xy is None or next_xy is None:
        return False

    gap_size = distance.euclidean(
        (next_xy.x, next_xy.y),
        (current_xy.x, current_xy.y),
    )
    if gap_size > TOLERANCE_THRESHOLD:
        return False
    return True


def _equal_inner_border_points(
    road: etree._Element,
    lane_id: int,
    current_outer_points: Dict[int, float],
    current_s: float,
    next_lane_id: int,
    successor_outer_points: Dict[int, float],
    successor_s: float,
) -> bool:
    current_xy = _compute_inner_point(current_outer_points, lane_id, road, current_s)

    next_xy = _compute_inner_point(
        successor_outer_points, next_lane_id, road, successor_s
    )

    if current_xy is None or next_xy is None:
        return False

    gap_size = distance.euclidean(
        (next_xy.x, next_xy.y),
        (current_xy.x, current_xy.y),
    )
    if gap_size > TOLERANCE_THRESHOLD:
        return False
    return True


def _validate_same_road_lane_successors(
    road: etree._ElementTree,
    lane: etree._ElementTree,
    current_outer_points: Dict[int, float],
    current_road_s: float,
    successor_outer_points: Dict[int, float],
    successor_road_s: float,
    successor_lanes: List[etree._Element],
    checker_data: models.CheckerData,
    raised_issue_xpaths: Set[str],
) -> None:
    successors = utils.get_successor_lane_ids(lane)
    lane_id = utils.get_lane_id(lane)

    if len(successors) == 1:
        next_lane_id = successors[0]

        if not _equal_outer_border_points(
            road,
            lane_id,
            current_outer_points,
            current_road_s,
            next_lane_id,
            successor_outer_points,
            successor_road_s,
        ) or not _equal_inner_border_points(
            road,
            lane_id,
            current_outer_points,
            current_road_s,
            next_lane_id,
            successor_outer_points,
            successor_road_s,
        ):
            next_lane = [
                next_lane
                for next_lane in successor_lanes
                if utils.get_lane_id(next_lane) == next_lane_id
            ]
            if len(next_lane) == 1:
                inertial_point = _compute_middle_point(
                    successor_outer_points,
                    next_lane_id,
                    road,
                    successor_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    lane,
                    next_lane[0],
                    raised_issue_xpaths,
                    inertial_point,
                )

    elif len(successors) == 2:
        reverse = True if lane_id < 0 else False
        successors = sorted(successors, reverse=reverse)
        upper_successor_id = successors[0]
        bottom_successor_id = successors[-1]

        if not _equal_outer_border_points(
            road,
            lane_id,
            current_outer_points,
            current_road_s,
            bottom_successor_id,
            successor_outer_points,
            successor_road_s,
        ):
            next_lane = [
                next_lane
                for next_lane in successor_lanes
                if utils.get_lane_id(next_lane) == bottom_successor_id
            ]
            if len(next_lane) == 1:
                inertial_point = _compute_middle_point(
                    successor_outer_points,
                    bottom_successor_id,
                    road,
                    successor_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    lane,
                    next_lane[0],
                    raised_issue_xpaths,
                    inertial_point,
                )

        if not _equal_inner_border_points(
            road,
            lane_id,
            current_outer_points,
            current_road_s,
            upper_successor_id,
            successor_outer_points,
            successor_road_s,
        ):
            next_lane = [
                next_lane
                for next_lane in successor_lanes
                if utils.get_lane_id(next_lane) == upper_successor_id
            ]
            if len(next_lane) == 1:
                inertial_point = _compute_middle_point(
                    successor_outer_points,
                    upper_successor_id,
                    road,
                    successor_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    lane,
                    next_lane[0],
                    raised_issue_xpaths,
                    inertial_point,
                )

    else:
        for extra_lane_id in successors[1:-1]:
            next_lane = [
                next_lane
                for next_lane in successor_lanes
                if utils.get_lane_id(next_lane) == extra_lane_id
            ]
            if len(next_lane) == 1:
                inertial_point = _compute_middle_point(
                    successor_outer_points,
                    extra_lane_id,
                    road,
                    successor_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    lane,
                    next_lane[0],
                    raised_issue_xpaths,
                    inertial_point,
                )


def _validate_same_road_lane_predecessors(
    road: etree._ElementTree,
    lane: etree._ElementTree,
    prev_outer_points: Dict[int, float],
    prev_road_s: float,
    current_outer_points: Dict[int, float],
    current_road_s: float,
    prev_lanes: List[etree._Element],
    checker_data: models.CheckerData,
    raised_issue_xpaths: Set[str],
) -> None:
    lane_id = utils.get_lane_id(lane)
    predecessors = utils.get_predecessor_lane_ids(lane)

    if len(predecessors) == 1:
        prev_lane_id = predecessors[0]

        if not _equal_outer_border_points(
            road,
            prev_lane_id,
            prev_outer_points,
            prev_road_s,
            lane_id,
            current_outer_points,
            current_road_s,
        ) or not _equal_inner_border_points(
            road,
            prev_lane_id,
            prev_outer_points,
            prev_road_s,
            lane_id,
            current_outer_points,
            current_road_s,
        ):
            prev_lane = [
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == prev_lane_id
            ]
            if len(prev_lane) == 1:
                inertial_point = _compute_middle_point(
                    current_outer_points,
                    lane_id,
                    road,
                    current_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    prev_lane[0],
                    lane,
                    raised_issue_xpaths,
                    inertial_point,
                )

    elif len(predecessors) == 2:
        reverse = True if lane_id < 0 else False
        predecessors = sorted(predecessors, reverse=reverse)
        upper_prev_id = predecessors[0]
        bottom_prev_id = predecessors[-1]

        if not _equal_outer_border_points(
            road,
            upper_prev_id,
            prev_outer_points,
            prev_road_s,
            lane_id,
            current_outer_points,
            current_road_s,
        ):
            prev_lane = [
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == upper_prev_id
            ]
            if len(prev_lane) == 1:
                inertial_point = _compute_middle_point(
                    current_outer_points,
                    lane_id,
                    road,
                    current_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    prev_lane[0],
                    lane,
                    raised_issue_xpaths,
                    inertial_point,
                )

        if not _equal_inner_border_points(
            road,
            bottom_prev_id,
            prev_outer_points,
            prev_road_s,
            lane_id,
            current_outer_points,
            current_road_s,
        ):
            prev_lane = [
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == bottom_prev_id
            ]
            if len(prev_lane) == 1:
                inertial_point = _compute_middle_point(
                    current_outer_points,
                    lane_id,
                    road,
                    current_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    prev_lane[0],
                    lane,
                    raised_issue_xpaths,
                    inertial_point,
                )

    else:
        for extra_lane_id in predecessors[1:-1]:
            prev_lane = [
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == extra_lane_id
            ]
            if len(prev_lane) == 1:
                inertial_point = _compute_middle_point(
                    current_outer_points,
                    lane_id,
                    road,
                    current_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    prev_lane[0],
                    lane,
                    raised_issue_xpaths,
                    inertial_point,
                )


def _check_road_lane_sections_gaps(
    road: etree._ElementTree,
    checker_data: models.CheckerData,
    raised_issue_xpaths: Set[str],
) -> None:
    lane_sections = utils.get_sorted_lane_sections_with_length_from_road(road)

    if len(lane_sections) == 1:
        return

    for index in range(0, len(lane_sections) - 1):
        current_lane_section = lane_sections[index]
        next_lane_section = lane_sections[index + 1]

        current_lanes = utils.get_left_and_right_lanes_from_lane_section(
            current_lane_section.lane_section
        )
        next_lanes = utils.get_left_and_right_lanes_from_lane_section(
            next_lane_section.lane_section
        )

        current_lane_section_s = utils.get_s_from_lane_section(
            current_lane_section.lane_section
        )
        next_lane_section_s = utils.get_s_from_lane_section(
            next_lane_section.lane_section
        )

        lane_offset = utils.get_lane_offset_value_from_road_by_s(
            road, current_lane_section_s + current_lane_section.length
        )
        successor_lane_offset = utils.get_lane_offset_value_from_road_by_s(
            road, next_lane_section_s
        )

        current_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
            current_lanes,
            lane_offset,
            current_lane_section_s,
            current_lane_section_s + current_lane_section.length,
        )
        current_outer_points[0] = lane_offset
        successor_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
            next_lanes,
            successor_lane_offset,
            next_lane_section_s,
            next_lane_section_s,
        )
        successor_outer_points[0] = successor_lane_offset

        for lane in current_lanes:
            if utils.get_type_from_lane(lane) not in DRIVABLE_LANE_TYPES:
                continue
            _validate_same_road_lane_successors(
                road,
                lane,
                current_outer_points,
                current_lane_section_s + current_lane_section.length,
                successor_outer_points,
                next_lane_section_s,
                next_lanes,
                checker_data,
                raised_issue_xpaths,
            )

        for lane in next_lanes:
            if utils.get_type_from_lane(lane) not in DRIVABLE_LANE_TYPES:
                continue
            _validate_same_road_lane_predecessors(
                road,
                lane,
                current_outer_points,
                current_lane_section_s + current_lane_section.length,
                successor_outer_points,
                next_lane_section_s,
                current_lanes,
                checker_data,
                raised_issue_xpaths,
            )


def _check_roads_internal_smoothness(checker_data: models.CheckerData) -> None:
    raised_issue_xpaths = set()

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in road_id_map.values():
        geometries = utils.get_road_plan_view_geometry_list(road)

        # we can only calculate gaps with 2 or more geometries
        if len(geometries) > 2:
            _check_plan_view_gaps(road, geometries, checker_data)

        _check_road_lane_sections_gaps(road, checker_data, raised_issue_xpaths)


def _validate_inter_road_smoothness(
    road: etree._ElementTree,
    linkage: models.RoadLinkage,
    road_relation: models.LinkageTag,
    road_lane_section: models.LaneSectionWithLength,
    road_s: float,
    road_id_map: Dict[int, etree._ElementTree],
    checker_data: models.CheckerData,
    raised_issue_xpaths: Set[str],
):
    lane_section = road_lane_section

    target_road = road_id_map.get(linkage.id)
    if target_road is None:
        return
    target_road_length = utils.get_road_length(target_road)
    target_lane_sections = utils.get_sorted_lane_sections_with_length_from_road(
        target_road
    )

    target_lane_section = None
    target_s = 0.0
    if linkage.contact_point == models.ContactPoint.END:
        target_lane_section = target_lane_sections[-1]
        target_s = target_road_length
    elif linkage.contact_point == models.ContactPoint.START:
        target_lane_section = target_lane_sections[0]
        target_s = 0.0

    lanes = utils.get_left_and_right_lanes_from_lane_section(lane_section.lane_section)
    target_lanes = utils.get_left_and_right_lanes_from_lane_section(
        target_lane_section.lane_section
    )

    lane_offset = utils.get_lane_offset_value_from_road_by_s(road, road_s)
    target_lane_offset = utils.get_lane_offset_value_from_road_by_s(
        target_road, target_s
    )

    lanes_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
        lanes,
        lane_offset,
        utils.get_s_from_lane_section(lane_section.lane_section),
        road_s,
    )
    lanes_outer_points[0] = lane_offset
    target_lanes_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
        target_lanes,
        target_lane_offset,
        utils.get_s_from_lane_section(target_lane_section.lane_section),
        target_s,
    )
    target_lanes_outer_points[0] = target_lane_offset

    for lane in lanes:
        if utils.get_type_from_lane(lane) not in DRIVABLE_LANE_TYPES:
            continue
        connections = []
        if road_relation == models.LinkageTag.PREDECESSOR:
            connections = utils.get_predecessor_lane_ids(lane)
        elif road_relation == models.LinkageTag.SUCCESSOR:
            connections = utils.get_successor_lane_ids(lane)

        lane_id = utils.get_lane_id(lane)

        current_c0 = _compute_inner_point(
            lanes_outer_points,
            lane_id,
            road,
            road_s,
        )
        current_c1 = _compute_outer_point(
            lanes_outer_points,
            lane_id,
            road,
            road_s,
        )
        if current_c0 is None or current_c1 is None:
            continue

        # For connected drivable lanes:
        #  - lanes with single successor/predecessor should match on both contact
        #    points.
        #  - lanes with multiple successor/predecessor can match only on one
        #    contact point.
        if len(connections) > 1:
            matches_threshold = 1
        else:
            matches_threshold = 2

        for conn_lane_id in connections:
            target_c0 = _compute_inner_point(
                target_lanes_outer_points,
                conn_lane_id,
                target_road,
                target_s,
            )
            target_c1 = _compute_outer_point(
                target_lanes_outer_points,
                conn_lane_id,
                target_road,
                target_s,
            )

            if target_c0 is None or target_c1 is None:
                continue

            matches = 0
            # The method will evaluate all pairs to check if we can get the
            # desired number of points matched for the horizontal gap.
            if (
                distance.euclidean(
                    (current_c0.x, current_c0.y), (target_c0.x, target_c0.y)
                )
                < TOLERANCE_THRESHOLD
            ):
                matches += 1
            if (
                distance.euclidean(
                    (current_c0.x, current_c0.y), (target_c1.x, target_c1.y)
                )
                < TOLERANCE_THRESHOLD
            ):
                matches += 1
            if (
                distance.euclidean(
                    (current_c1.x, current_c1.y), (target_c0.x, target_c0.y)
                )
                < TOLERANCE_THRESHOLD
            ):
                matches += 1
            if (
                distance.euclidean(
                    (current_c1.x, current_c1.y), (target_c1.x, target_c1.y)
                )
                < TOLERANCE_THRESHOLD
            ):
                matches += 1

            if matches < matches_threshold:
                target_lane = next(
                    target_lane
                    for target_lane in target_lanes
                    if utils.get_lane_id(target_lane) == conn_lane_id
                )

                if road_relation == models.LinkageTag.PREDECESSOR:
                    inertial_point = _compute_middle_point(
                        lanes_outer_points,
                        lane_id,
                        road,
                        road_s,
                    )
                    _raise_lane_linkage_gap_issue(
                        checker_data,
                        target_lane,
                        lane,
                        raised_issue_xpaths,
                        inertial_point,
                    )

                elif road_relation == models.LinkageTag.SUCCESSOR:
                    inertial_point = _compute_middle_point(
                        target_lanes_outer_points,
                        conn_lane_id,
                        target_road,
                        target_s,
                    )
                    _raise_lane_linkage_gap_issue(
                        checker_data,
                        lane,
                        target_lane,
                        raised_issue_xpaths,
                        inertial_point,
                    )


def _validate_junction_connection_gaps(
    incoming_road: etree._ElementTree,
    incoming_lane_section: models.LaneSectionWithLength,
    incoming_road_s: float,
    connection: etree._ElementTree,
    road_relation: models.ContactPoint,
    road_id_map: Dict[int, etree._ElementTree],
    checker_data: models.CheckerData,
    raised_issue_xpaths: Set[str],
):
    connection_contact_point = utils.get_contact_point_from_connection(connection)
    connection_road_id = utils.get_connecting_road_id_from_connection(connection)
    if connection_contact_point is None or connection_road_id is None:
        return

    connection_road = road_id_map.get(connection_road_id)
    if connection_road is None:
        return

    contact_lane_sections = (
        utils.get_contact_lane_section_from_junction_connection_road(
            connection_road, connection_contact_point
        )
    )
    if contact_lane_sections is None:
        return

    lane_links = utils.get_lane_links_from_connection(connection)

    if len(lane_links) == 0:
        return

    target_road = connection_road
    target_road_length = utils.get_road_length(target_road)
    target_lane_sections = utils.get_sorted_lane_sections_with_length_from_road(
        target_road
    )

    target_lane_section = None
    target_s = 0.0
    if connection_contact_point == models.ContactPoint.END:
        target_lane_section = target_lane_sections[-1]
        target_s = target_road_length
    elif connection_contact_point == models.ContactPoint.START:
        target_lane_section = target_lane_sections[0]
        target_s = 0.0

    lanes = utils.get_left_and_right_lanes_from_lane_section(
        incoming_lane_section.lane_section
    )
    target_lanes = utils.get_left_and_right_lanes_from_lane_section(
        target_lane_section.lane_section
    )

    lane_offset = utils.get_lane_offset_value_from_road_by_s(
        incoming_road, incoming_road_s
    )
    target_lane_offset = utils.get_lane_offset_value_from_road_by_s(
        target_road, target_s
    )

    lanes_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
        lanes,
        lane_offset,
        utils.get_s_from_lane_section(incoming_lane_section.lane_section),
        incoming_road_s,
    )
    lanes_outer_points[0] = lane_offset
    target_lanes_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
        target_lanes,
        target_lane_offset,
        utils.get_s_from_lane_section(target_lane_section.lane_section),
        target_s,
    )
    target_lanes_outer_points[0] = target_lane_offset

    for link in lane_links:
        # incoming road lane id
        from_id = utils.get_from_attribute_from_lane_link(link)
        # connection road lane id
        to_id = utils.get_to_attribute_from_lane_link(link)

        if from_id is None or to_id is None:
            continue

        from_lane = utils.get_lane_from_lane_section(
            incoming_lane_section.lane_section, from_id
        )

        if utils.get_type_from_lane(from_lane) not in DRIVABLE_LANE_TYPES:
            continue

        current_c0 = _compute_inner_point(
            lanes_outer_points,
            from_id,
            incoming_road,
            incoming_road_s,
        )
        current_c1 = _compute_outer_point(
            lanes_outer_points,
            from_id,
            incoming_road,
            incoming_road_s,
        )
        if current_c0 is None or current_c1 is None:
            continue

        target_c0 = _compute_inner_point(
            target_lanes_outer_points,
            to_id,
            target_road,
            target_s,
        )
        target_c1 = _compute_outer_point(
            target_lanes_outer_points,
            to_id,
            target_road,
            target_s,
        )

        if target_c0 is None or target_c1 is None:
            continue

        matches = 0
        # The method will evaluate all pairs to check if we can get the
        # desired number of points matched for the horizontal gap.
        if (
            distance.euclidean((current_c0.x, current_c0.y), (target_c0.x, target_c0.y))
            < TOLERANCE_THRESHOLD
        ):
            matches += 1
        if (
            distance.euclidean((current_c0.x, current_c0.y), (target_c1.x, target_c1.y))
            < TOLERANCE_THRESHOLD
        ):
            matches += 1
        if (
            distance.euclidean((current_c1.x, current_c1.y), (target_c0.x, target_c0.y))
            < TOLERANCE_THRESHOLD
        ):
            matches += 1
        if (
            distance.euclidean((current_c1.x, current_c1.y), (target_c1.x, target_c1.y))
            < TOLERANCE_THRESHOLD
        ):
            matches += 1

        if matches < 2:
            target_lane = next(
                target_lane
                for target_lane in target_lanes
                if utils.get_lane_id(target_lane) == to_id
            )

            if road_relation == models.LinkageTag.PREDECESSOR:
                inertial_point = _compute_middle_point(
                    lanes_outer_points,
                    from_id,
                    incoming_road,
                    incoming_road_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    from_lane,
                    target_lane,
                    raised_issue_xpaths,
                    inertial_point,
                )
            elif road_relation == models.LinkageTag.SUCCESSOR:
                inertial_point = _compute_middle_point(
                    target_lanes_outer_points,
                    to_id,
                    target_road,
                    target_s,
                )
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    from_lane,
                    target_lane,
                    raised_issue_xpaths,
                    inertial_point,
                )


def _check_inter_roads_smoothness(checker_data: models.CheckerData) -> None:
    raised_issue_xpaths = set()

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        successor = utils.get_road_linkage(road, models.LinkageTag.SUCCESSOR)
        predecessor = utils.get_road_linkage(road, models.LinkageTag.PREDECESSOR)

        road_lane_sections = utils.get_sorted_lane_sections_with_length_from_road(road)
        road_length = utils.get_road_length(road)

        if successor is not None:
            _validate_inter_road_smoothness(
                road=road,
                linkage=successor,
                road_relation=models.LinkageTag.SUCCESSOR,
                road_lane_section=road_lane_sections[-1],
                road_s=road_length,
                road_id_map=road_id_map,
                checker_data=checker_data,
                raised_issue_xpaths=raised_issue_xpaths,
            )

        if predecessor is not None:
            _validate_inter_road_smoothness(
                road=road,
                linkage=predecessor,
                road_relation=models.LinkageTag.PREDECESSOR,
                road_lane_section=road_lane_sections[0],
                road_s=0.0,
                road_id_map=road_id_map,
                checker_data=checker_data,
                raised_issue_xpaths=raised_issue_xpaths,
            )

        successor_junction_id = utils.get_linked_junction_id(
            road, models.LinkageTag.SUCCESSOR
        )
        predecessor_junction_id = utils.get_linked_junction_id(
            road, models.LinkageTag.PREDECESSOR
        )

        if successor_junction_id is not None:
            connections = utils.get_connections_between_road_and_junction(
                road_id,
                successor_junction_id,
                road_id_map,
                junction_id_map,
                models.ContactPoint.END,
            )

            incoming_road_lane_section = road_lane_sections[-1]

            for connection in connections:
                _validate_junction_connection_gaps(
                    incoming_road=road,
                    incoming_lane_section=incoming_road_lane_section,
                    incoming_road_s=road_length,
                    connection=connection,
                    road_relation=models.LinkageTag.SUCCESSOR,
                    road_id_map=road_id_map,
                    checker_data=checker_data,
                    raised_issue_xpaths=raised_issue_xpaths,
                )

        if predecessor_junction_id is not None:
            connections = utils.get_connections_between_road_and_junction(
                road_id,
                predecessor_junction_id,
                road_id_map,
                junction_id_map,
                models.ContactPoint.START,
            )

            incoming_road_lane_section = road_lane_sections[0]

            for connection in connections:
                _validate_junction_connection_gaps(
                    incoming_road=road,
                    incoming_lane_section=incoming_road_lane_section,
                    incoming_road_s=0.0,
                    connection=connection,
                    road_relation=models.LinkageTag.PREDECESSOR,
                    road_id_map=road_id_map,
                    checker_data=checker_data,
                    raised_issue_xpaths=raised_issue_xpaths,
                )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps

    Description: Two connected drivable lanes shall have no horizontal gaps.
    There is no gap between two connected lanes in s-direction if the x,y values
    of the contact points of the two connected lanes match. There shall be no
    plan view gaps in its reference line geometry definition

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        - Only lanes of drivable types would be checked.
        - The rule will trigger one issue for each logical link. If lanes are
        connected as successor and predecessor, the rule will trigger 2 issues
        for the given connection.

    More info at
        - Not available yet.
    """
    logging.info("Executing lane_smoothness.contact_point_no_horizontal_gaps check.")

    _check_roads_internal_smoothness(checker_data=checker_data)
    _check_inter_roads_smoothness(checker_data=checker_data)
