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

DEBUG = False


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
) -> models.Point3D:
    sign = -1 if lane_id < 0 else 1
    current_lane_t = current_lane_t = lanes_outer_points[lane_id - 1 * sign]
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


def _compute_outer_point(
    lanes_outer_points: Dict[int, float],
    lane_id: int,
    road: etree._Element,
    road_s: float,
) -> models.Point3D:
    current_lane_t = lanes_outer_points[lane_id]
    return utils.get_point_xyz_from_road(road=road, s=road_s, t=current_lane_t, h=0)


def _equal_outer_border_points(
    road: etree._Element,
    lane_id: int,
    current_outer_points: Dict[int, float],
    current_s: float,
    next_lane_id: int,
    successor_outer_points: Dict[int, float],
    successor_s: float,
):
    current_xy = _compute_outer_point(current_outer_points, lane_id, road, current_s)

    next_xy = _compute_outer_point(
        successor_outer_points, next_lane_id, road, successor_s
    )

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
):
    current_xy = _compute_inner_point(current_outer_points, lane_id, road, current_s)

    next_xy = _compute_inner_point(
        successor_outer_points, next_lane_id, road, successor_s
    )

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
            next_lane = next(
                prev_lane
                for prev_lane in successor_lanes
                if utils.get_lane_id(prev_lane) == next_lane_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                lane,
                next_lane,
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
            next_lane = next(
                prev_lane
                for prev_lane in successor_lanes
                if utils.get_lane_id(prev_lane) == bottom_successor_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                lane,
                next_lane,
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
            next_lane = next(
                prev_lane
                for prev_lane in successor_lanes
                if utils.get_lane_id(prev_lane) == upper_successor_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                lane,
                next_lane,
            )

    else:
        for extra_lane_id in successors[1:-1]:
            next_lane = next(
                prev_lane
                for prev_lane in successor_lanes
                if utils.get_lane_id(prev_lane) == extra_lane_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                lane,
                next_lane,
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
            prev_lane = next(
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == prev_lane_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                prev_lane,
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
            prev_lane = next(
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == upper_prev_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                prev_lane,
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
            prev_lane = next(
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == bottom_prev_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                prev_lane,
                lane,
            )

    else:
        for extra_lane_id in predecessors[1:-1]:
            prev_lane = next(
                prev_lane
                for prev_lane in prev_lanes
                if utils.get_lane_id(prev_lane) == extra_lane_id
            )
            _raise_lane_linkage_gap_issue(
                checker_data,
                rule_uid,
                prev_lane,
                lane,
            )


def _check_road_lane_sections_gaps(
    road: etree._ElementTree,
    geometries: etree._ElementTree,
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

    for road_id, road in road_id_map.items():
        geometries = utils.get_road_plan_view_geometry_list(road)

        # we can only calculate gaps with 2 or more geometries
        if len(geometries) > 2:
            _check_plan_view_gaps(geometries, checker_data, rule_uid)

        _check_road_lane_sections_gaps(road, geometries, checker_data, rule_uid)


def _check_inter_roads_smoothness(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        successor = utils.get_road_linkage(road, models.LinkageTag.SUCCESSOR)
        predecessor = utils.get_road_linkage(road, models.LinkageTag.PREDECESSOR)

        road_lane_sections = utils.get_sorted_lane_sections_with_length_from_road(road)
        road_length = utils.get_road_length(road)

        if successor is not None:
            # current_lane_section
            last_lane_section = road_lane_sections[-1]

            # next_lane_section
            successor_road = road_id_map[successor.id]
            successor_road_length = utils.get_road_length(successor_road)
            successor_lane_sections = (
                utils.get_sorted_lane_sections_with_length_from_road(successor_road)
            )

            successor_lane_section = None
            successor_s = 0.0
            if successor.contact_point == models.ContactPoint.END:
                successor_lane_section = successor_lane_sections[-1]
                successor_s = successor_road_length
            elif successor.contact_point == models.ContactPoint.START:
                successor_lane_section = successor_lane_sections[0]
                successor_s = 0.0

            lanes = utils.get_left_and_right_lanes_from_lane_section(
                last_lane_section.lane_section
            )
            successor_lanes = utils.get_left_and_right_lanes_from_lane_section(
                successor_lane_section.lane_section
            )

            lane_offset = utils.get_lane_offset_value_from_road_by_s(road, road_length)
            successor_lane_offset = utils.get_lane_offset_value_from_road_by_s(
                successor_road, successor_s
            )

            lanes_outer_points = utils.get_outer_border_points_from_lane_group_by_s(
                lanes,
                lane_offset,
                utils.get_s_from_lane_section(last_lane_section.lane_section),
                road_length,
            )
            lanes_outer_points[0] = lane_offset
            successor_lanes_outer_points = (
                utils.get_outer_border_points_from_lane_group_by_s(
                    successor_lanes,
                    successor_lane_offset,
                    utils.get_s_from_lane_section(successor_lane_section.lane_section),
                    successor_s,
                )
            )
            successor_lanes_outer_points[0] = successor_lane_offset

            for lane in lanes:
                successors = utils.get_successor_lane_ids(lane)
                lane_id = utils.get_lane_id(lane)

                current_c0 = _compute_inner_point(
                    lanes_outer_points,
                    lane_id,
                    road,
                    road_length,
                )
                current_c1 = _compute_outer_point(
                    lanes_outer_points,
                    lane_id,
                    road,
                    road_length,
                )

                if len(successors) > 1:
                    matches_threshold = 1
                else:
                    matches_threshold = 2

                for next_lane_id in successors:
                    next_c0 = _compute_inner_point(
                        successor_lanes_outer_points,
                        next_lane_id,
                        successor_road,
                        successor_s,
                    )
                    next_c1 = _compute_outer_point(
                        successor_lanes_outer_points,
                        next_lane_id,
                        successor_road,
                        successor_s,
                    )

                    matches = 0

                    if (
                        distance.euclidean(
                            (current_c0.x, current_c0.y), (next_c0.x, next_c0.y)
                        )
                        < TOLERANCE_THRESHOLD
                    ):
                        matches += 1
                    if (
                        distance.euclidean(
                            (current_c0.x, current_c0.y), (next_c1.x, next_c1.y)
                        )
                        < TOLERANCE_THRESHOLD
                    ):
                        matches += 1
                    if (
                        distance.euclidean(
                            (current_c1.x, current_c1.y), (next_c0.x, next_c0.y)
                        )
                        < TOLERANCE_THRESHOLD
                    ):
                        matches += 1
                    if (
                        distance.euclidean(
                            (current_c1.x, current_c1.y), (next_c1.x, next_c1.y)
                        )
                        < TOLERANCE_THRESHOLD
                    ):
                        matches += 1

                    if matches < matches_threshold:
                        print("ISSUE")
                        print(f"road id      - {road_id}      --  lane ={lane_id}")
                        print(
                            f"successor id - {successor.id}      --  lane ={next_lane_id}"
                        )
                        print(f"matches = {matches} < {matches_threshold}")
                        print(current_c0, current_c1)
                        print(next_c0, next_c1)

        # if predecessor is not None:
        #     # current_lane_section
        #     first_lane_section = road_lane_sections[0]

        #     # next_lane_section
        #     predecessor_road = road_id_map[predecessor.id]
        #     predecessor_lane_sections = (
        #         utils.get_sorted_lane_sections_with_length_from_road(predecessor_road)
        #     )
        #     predecessor_lane_section = None
        #     if predecessor.contact_point == models.ContactPoint.END:
        #         predecessor_lane_section = predecessor_lane_sections[-1]
        #     elif predecessor.contact_point == models.ContactPoint.START:
        #         predecessor_lane_section = predecessor_lane_sections[0]

        #     lanes = utils.get_left_and_right_lanes_from_lane_section(
        #         first_lane_section.lane_section
        #     )
        #     for lane in lanes:
        #         print(lane)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID:

    Description:

    Severity:

    Version range: []

    Remark:

    More info at
        -
    """
    logging.info("Executing lane_smoothness.contact_point_no_gaps check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="lane_smoothness.contact_point_no_gaps",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_roads_internal_smoothness(checker_data=checker_data, rule_uid=rule_uid)
    _check_inter_roads_smoothness(checker_data=checker_data, rule_uid=rule_uid)
