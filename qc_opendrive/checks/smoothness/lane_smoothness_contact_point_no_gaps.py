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


def _get_cumulative_width(lane_id, lane_section, s) -> float:
    lane_width = 0.0
    sign = -1 if lane_id < 0 else 1

    for i in range(1, abs(lane_id) + 1):
        lane = utils.get_lane_from_lane_section(lane_section, i * sign)
        lane_width += utils.evaluate_lane_width(lane, s)

    return lane_width


def _compare_outer_border_points(
    road,
    current_lane_section,
    current_lane_id,
    next_lane_section,
    next_lane_id,
):
    current_lane_section_s0 = utils.get_s_coordinate_from_lane_section(
        current_lane_section.lane_section
    )
    next_lane_section_s0 = utils.get_s_coordinate_from_lane_section(
        next_lane_section.lane_section
    )
    # current lane c1
    current_lane_s = current_lane_section_s0 + current_lane_section.length
    current_lane_t = _get_cumulative_width(
        current_lane_id,
        current_lane_section.lane_section,
        current_lane_section.length,
    )
    current_xy = utils.get_point_xyz_from_road(
        road=road, s=current_lane_s, t=current_lane_t, h=0
    )

    # next lane c1
    next_lane_s = next_lane_section_s0
    next_lane_t = _get_cumulative_width(
        next_lane_id, next_lane_section.lane_section, 0.0
    )
    next_xy = utils.get_point_xyz_from_road(
        road=road, s=next_lane_s, t=next_lane_t, h=0
    )

    if DEBUG:
        print(f"lane id = {current_lane_id} next lane id = {next_lane_id}")
        print("-" * 10)
        print(f"c1 current width = {current_lane_t}")
        print(f"c1 next width    = {next_lane_t}")
        print("-" * 10)
        print(f"c1 current xy = {current_xy}")
        print(f"c1 next xy    = {next_xy}")
        print("-" * 10)

    gap_size = distance.euclidean(
        (next_xy.x, next_xy.y),
        (current_xy.x, current_xy.y),
    )
    if gap_size > TOLERANCE_THRESHOLD:
        print(
            f"ISSUE gap_size   = {gap_size} / clane_id = {current_lane_id} / nlane_id = {next_lane_id}"
        )
        print(f"lane id = {current_lane_id} next lane id = {next_lane_id}")
        print("-" * 10)
        print(f"c1 current t = {current_lane_t}")
        print(f"c1 next t    = {next_lane_t}")
        print(f"c1 current s = {current_lane_s}")
        print(f"c1 next s    = {next_lane_s}")
        print("-" * 10)
        print(f"c1 current xy = {current_xy}")
        print(f"c1 next xy    = {next_xy}")
        print("-" * 10)
        # _raise_gap_issue(
        #     checker_data, rule_uid, previous_geometry, current_geometry
        # )


def _compare_inner_border_points(
    road,
    current_lane_section,
    current_lane_id,
    next_lane_section,
    next_lane_id,
):
    current_lane_section_s0 = utils.get_s_coordinate_from_lane_section(
        current_lane_section.lane_section
    )
    next_lane_section_s0 = utils.get_s_coordinate_from_lane_section(
        next_lane_section.lane_section
    )
    # current lane c1
    current_lane_s = current_lane_section_s0 + current_lane_section.length
    sign = -1 if current_lane_id < 0 else 1
    current_lane_t = _get_cumulative_width(
        current_lane_id - 1 * sign,
        current_lane_section.lane_section,
        current_lane_section.length,
    )
    current_xy = utils.get_point_xyz_from_road(
        road=road, s=current_lane_s, t=current_lane_t, h=0
    )

    # next lane c1
    next_lane_s = next_lane_section_s0
    sign = -1 if next_lane_id < 0 else 1
    next_lane_t = _get_cumulative_width(
        next_lane_id - 1 * sign, next_lane_section.lane_section, 0.0
    )
    next_xy = utils.get_point_xyz_from_road(
        road=road, s=next_lane_s, t=next_lane_t, h=0
    )

    if DEBUG:
        print(f"lane id = {current_lane_id} next lane id = {next_lane_id}")
        print("-" * 10)
        print(f"c0 current width = {current_lane_t}")
        print(f"c0 next width    = {next_lane_t}")
        print("-" * 10)
        print(f"c0 current xy = {current_xy}")
        print(f"c0 next xy    = {next_xy}")
        print("-" * 10)

    gap_size = distance.euclidean(
        (next_xy.x, next_xy.y),
        (current_xy.x, current_xy.y),
    )
    if gap_size > TOLERANCE_THRESHOLD:
        print(
            f"ISSUE gap_size   = {gap_size} / clane_id = {current_lane_id} / nlane_id = {next_lane_id}"
        )
        print(f"lane id = {current_lane_id} next lane id = {next_lane_id}")
        print("-" * 10)
        print(f"c0 current width = {current_lane_t}")
        print(f"c0 next width    = {next_lane_t}")
        print("-" * 10)
        print(f"c0 current xy = {current_xy}")
        print(f"c0 next xy    = {next_xy}")
        print("-" * 10)
        # _raise_gap_issue(
        #     checker_data, rule_uid, previous_geometry, current_geometry
        # )


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

        print(f"i = {index}, j = {index + 1}")

        current_lanes = utils.get_left_and_right_lanes_from_lane_section(
            current_lane_section.lane_section
        )
        next_lanes = utils.get_left_and_right_lanes_from_lane_section(
            next_lane_section.lane_section
        )

        for lane in current_lanes:
            successors = utils.get_successor_lane_ids(lane)
            lane_id = utils.get_lane_id(lane)

            if len(successors) == 1:
                next_lane_id = successors[0]

                _compare_outer_border_points(
                    road, current_lane_section, lane_id, next_lane_section, next_lane_id
                )
                _compare_inner_border_points(
                    road, current_lane_section, lane_id, next_lane_section, next_lane_id
                )
            elif len(successors) > 1:
                print("multiple successors")
                successors = sorted(successors)
                upper_successor_id = successors[0]
                bottom_successor_id = successors[-1]

                _compare_outer_border_points(
                    road,
                    current_lane_section,
                    lane_id,
                    next_lane_section,
                    bottom_successor_id,
                )
                _compare_inner_border_points(
                    road,
                    current_lane_section,
                    lane_id,
                    next_lane_section,
                    upper_successor_id,
                )

                if len(successors) > 2:
                    for extra_lane_id in successors[1:-1]:
                        print(f"succ - raise issue for {extra_lane_id}")

        for lane in next_lanes:
            lane_id = utils.get_lane_id(lane)
            predecessors = utils.get_predecessor_lane_ids(lane)

            if len(predecessors) == 1:
                prev_lane_id = predecessors[0]
                _compare_outer_border_points(
                    road,
                    current_lane_section,
                    prev_lane_id,
                    next_lane_section,
                    lane_id,
                )
                _compare_inner_border_points(
                    road,
                    current_lane_section,
                    prev_lane_id,
                    next_lane_section,
                    lane_id,
                )
            elif len(predecessors) > 1:
                print("multiple predecessors")
                predecessors = sorted(predecessors)
                upper_prev_id = predecessors[0]
                bottom_prev_id = predecessors[-1]

                _compare_outer_border_points(
                    road,
                    current_lane_section,
                    upper_prev_id,
                    next_lane_section,
                    lane_id,
                )
                _compare_inner_border_points(
                    road,
                    current_lane_section,
                    bottom_prev_id,
                    next_lane_section,
                    lane_id,
                )

                if len(predecessors) > 2:
                    for extra_lane_id in predecessors[1:-1]:
                        print(f"pred - raise issue for {extra_lane_id}")


def _check_roads_internal_smoothness(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        geometries = utils.get_road_plan_view_geometry_list(road)

        # we can only calculate gaps with 2 or more geometries
        if len(geometries) > 2:
            _check_plan_view_gaps(geometries, checker_data, rule_uid)

        print(f"road id = {road_id}")
        _check_road_lane_sections_gaps(road, geometries, checker_data, rule_uid)


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
    # _check_inter_roads_smoothness(checker_data=checker_data, rule_uid=rule_uid)
    # implement the check in between roads
    # implement the "virtual contact point", need to base the rule in the lanes
    # connection as well
    # add lanes types check as well - list of possible lane types
