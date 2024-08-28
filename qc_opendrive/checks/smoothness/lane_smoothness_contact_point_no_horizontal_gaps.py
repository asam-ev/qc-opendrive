import logging

from typing import Union, List, Dict
from lxml import etree
from scipy.spatial import distance

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import utils, models
from qc_opendrive.checks.smoothness import smoothness_constants


RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
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
    rule_uid: str,
    previous_geometry: etree._Element,
    geometry: etree._Element,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        description=f"The transition between geometry elements should be defined with no gaps.",
        level=IssueSeverity.ERROR,
        rule_uid=rule_uid,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(previous_geometry),
        description=f"First geometry element",
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(geometry),
        description=f"Second geometry element",
    )


def _raise_lane_linkage_gap_issue(
    checker_data: models.CheckerData,
    rule_uid: str,
    previous_lane: etree._Element,
    current_lane: etree._Element,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        description=f"The transition between lane elements should be defined with no gaps.",
        level=IssueSeverity.ERROR,
        rule_uid=rule_uid,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(previous_lane),
        description=f"First lane element",
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(current_lane),
        description=f"Next lane element",
    )


def _check_geometries_gap(
    previous_geometry: etree._Element,
    current_geometry: etree._Element,
    checker_data: models.CheckerData,
    rule_uid: str,
) -> None:
    x0 = utils.get_x_from_geometry(current_geometry)
    y0 = utils.get_y_from_geometry(current_geometry)

    if x0 is None or y0 is None:
        return

    previous_s0 = utils.get_s_from_geometry(previous_geometry)
    previous_length = utils.get_length_from_geometry(previous_geometry)
    previous_end_point = utils.get_point_xy_from_geometry(
        previous_geometry, previous_s0 + previous_length
    )

    if previous_end_point is not None:
        gap_size = distance.euclidean(
            (previous_end_point.x, previous_end_point.y),
            (x0, y0),
        )
        if gap_size > TOLERANCE_THRESHOLD:
            _raise_geometry_gap_issue(
                checker_data, rule_uid, previous_geometry, current_geometry
            )


def _check_plan_view_gaps(
    geometries: etree._ElementTree,
    checker_data: models.CheckerData,
    rule_uid: str,
) -> None:
    # we are assuming geometries is a sorted list on s position
    previous_geometry: Union[etree._Element, None] = None
    for geometry in geometries:
        if previous_geometry is not None:
            _check_geometries_gap(
                previous_geometry=previous_geometry,
                current_geometry=geometry,
                checker_data=checker_data,
                rule_uid=rule_uid,
            )

        previous_geometry = geometry


def _compute_inner_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> Union[None, models.Point3D]:
    sign = -1 if lane_id < 0 else 1
    current_lane_t = current_lane_t = lanes_outer_points.get(lane_id - 1 * sign)
    if current_lane_t is None:
        return None
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


def _compute_outer_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> Union[None, models.Point3D]:
    current_lane_t = lanes_outer_points.get(lane_id)
    if current_lane_t is None:
        return None
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


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
    rule_uid: str,
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    lane,
                    next_lane[0],
                )

    elif len(successors) == 2:
        successors = sorted(successors)
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    lane,
                    next_lane[0],
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    lane,
                    next_lane[0],
                )

    else:
        for extra_lane_id in successors[1:-1]:
            next_lane = [
                next_lane
                for next_lane in successor_lanes
                if utils.get_lane_id(next_lane) == extra_lane_id
            ]
            if len(next_lane) == 1:
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    lane,
                    next_lane[0],
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
    rule_uid: str,
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    prev_lane[0],
                    lane,
                )

    elif len(predecessors) == 2:
        predecessors = sorted(predecessors)
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    prev_lane[0],
                    lane,
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
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    prev_lane[0],
                    lane,
                )

    else:
        for extra_lane_id in predecessors[1:-1]:
            prev_lane = [
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == extra_lane_id
            ]
            if len(prev_lane) == 1:
                _raise_lane_linkage_gap_issue(
                    checker_data,
                    rule_uid,
                    prev_lane[0],
                    lane,
                )


def _check_road_lane_sections_gaps(
    road: etree._ElementTree,
    checker_data: models.CheckerData,
    rule_uid: str,
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
                rule_uid,
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
                rule_uid,
            )


def _check_roads_internal_smoothness(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in road_id_map.values():
        geometries = utils.get_road_plan_view_geometry_list(road)

        # we can only calculate gaps with 2 or more geometries
        if len(geometries) > 2:
            _check_plan_view_gaps(geometries, checker_data, rule_uid)

        _check_road_lane_sections_gaps(road, checker_data, rule_uid)


def _validate_inter_road_smoothness(
    road: etree._ElementTree,
    linkage: models.RoadLinkage,
    road_relation: models.LinkageTag,
    road_lane_section: models.LaneSectionWithLength,
    road_s: float,
    road_id_map: Dict[int, etree._ElementTree],
    checker_data: models.CheckerData,
    rule_uid: str,
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
                    _raise_lane_linkage_gap_issue(
                        checker_data,
                        rule_uid,
                        target_lane,
                        lane,
                    )
                elif road_relation == models.LinkageTag.SUCCESSOR:
                    _raise_lane_linkage_gap_issue(
                        checker_data,
                        rule_uid,
                        lane,
                        target_lane,
                    )


def _check_inter_roads_smoothness(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in road_id_map.values():
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
                rule_uid=rule_uid,
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
                rule_uid=rule_uid,
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

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="lane_smoothness.contact_point_no_horizontal_gaps",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_roads_internal_smoothness(checker_data=checker_data, rule_uid=rule_uid)
    _check_inter_roads_smoothness(checker_data=checker_data, rule_uid=rule_uid)
