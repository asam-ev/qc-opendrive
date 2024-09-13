from dataclasses import dataclass
import logging

from typing import Union, List, Dict, Set
from enum import Enum

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"


def _check_true_level_on_side(
    root: etree._ElementTree,
    side_lanes: List[etree._Element],
    road: etree._ElementTree,
    lane_section_with_length: models.LaneSectionWithLength,
    result: Result,
    rule_uid: str,
) -> None:
    """
    Check on a sorted list of lanes if any false level occurs after a true.
    The side_lanes must be sorted in the order from the center to the border of the road.
    The side_lanes must contain lanes from only one side, that is, all the lane ids must be positive, or all the lane ids must be negative.
    If the lane ids are positive, the lane should be in the ascending order.
    If the lane ids are negative, the lane should be in the descending order.
    """
    found_true_level = False

    for index, lane in enumerate(side_lanes):
        lane_level = utils.get_lane_level_from_lane(lane)

        if lane_level == True:
            found_true_level = True

        elif lane_level == False and found_true_level == True:
            # lane_level is False when previous lane_level was True before
            issue_id = result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                description="Lane level False encountered on same side after True set.",
                level=IssueSeverity.ERROR,
                rule_uid=rule_uid,
            )

            path = root.getpath(lane)

            result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=path,
                description=f"Lane id {index} @level=False where previous lane id @level=True.",
            )

            s_section = utils.get_s_from_lane_section(
                lane_section_with_length.lane_section
            )
            if s_section is None:
                continue

            s = s_section + lane_section_with_length.length / 2.0

            inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
                road, lane_section_with_length.lane_section, lane, s
            )
            if inertial_point is not None:
                result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Lane level false when previous lane level is True.",
                )


def _get_linkage_level_warnings(
    root: etree._ElementTree,
    current_lane_section: etree._ElementTree,
    target_lane_section: etree._ElementTree,
    linkage_tag: models.LinkageTag,
):
    warnings: Set[str] = set()

    for lane in utils.get_left_and_right_lanes_from_lane_section(current_lane_section):
        lane_level = utils.get_lane_level_from_lane(lane)

        for link in lane.findall("link"):
            for linkage in link.findall(linkage_tag):
                linkage_id = utils.to_int(linkage.get("id"))
                if linkage_id is None:
                    continue
                linkage_lane = utils.get_lane_from_lane_section(
                    target_lane_section, linkage_id
                )
                if linkage_lane is None:
                    continue

                linkage_level = utils.get_lane_level_from_lane(linkage_lane)

                if linkage_level != lane_level:
                    warnings.add(root.getpath(lane))

    return warnings


def _check_level_change_between_lane_sections(
    root: etree._ElementTree,
    current_lane_section: etree._ElementTree,
    previous_lane_section: etree._ElementTree,
    result: Result,
    rule_uid: str,
) -> None:
    """
    Check two consecutive lane section from a road if a false level occurs
    after a true consecutively.

    The predecessor/successor should be pointing to a valid lane id, otherwise
    it will be ignored.

    If lanes are linked twice by both predecessor and successor, the
    function will register the issue twice, one for each linkage.
    """

    predecessor_warnings = _get_linkage_level_warnings(
        root=root,
        current_lane_section=current_lane_section,
        target_lane_section=previous_lane_section,
        linkage_tag=models.LinkageTag.PREDECESSOR,
    )
    successor_warnings = _get_linkage_level_warnings(
        root=root,
        current_lane_section=previous_lane_section,
        target_lane_section=current_lane_section,
        linkage_tag=models.LinkageTag.SUCCESSOR,
    )

    warnings = predecessor_warnings | successor_warnings
    warnings = sorted(list(warnings))

    for warning in warnings:
        issue_id = result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            description="Lane levels are not the same in two consecutive lane sections",
            level=IssueSeverity.WARNING,
            rule_uid=rule_uid,
        )
        result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            issue_id=issue_id,
            xpath=warning,
            description="",
        )


def _check_level_change_linkage_roads(
    linkage_tag: models.LinkageTag,
    road: etree._ElementTree,
    road_id_map: Dict[int, etree._ElementTree],
    result: Result,
    rule_uid: str,
    root: etree._ElementTree,
) -> None:
    if linkage_tag == models.LinkageTag.PREDECESSOR:
        current_lane_section = utils.get_first_lane_section(road)
    elif linkage_tag == models.LinkageTag.SUCCESSOR:
        current_lane_section = utils.get_last_lane_section(road)
    else:
        return

    if current_lane_section is None:
        return

    all_lanes = utils.get_left_and_right_lanes_from_lane_section(current_lane_section)

    linkage = utils.get_road_linkage(road, linkage_tag)
    if linkage is None:
        return

    other_lane_section = utils.get_contact_lane_section_from_linked_road(
        linkage, road_id_map
    )

    if other_lane_section is None:
        return

    for lane in all_lanes:
        lane_level = utils.get_lane_level_from_lane(lane)

        if linkage_tag == models.LinkageTag.PREDECESSOR:
            linkage_lane_ids = utils.get_predecessor_lane_ids(lane)
        else:
            linkage_lane_ids = utils.get_successor_lane_ids(lane)

        for lane_id in linkage_lane_ids:
            other_lane = utils.get_lane_from_lane_section(
                other_lane_section.lane_section, lane_id
            )
            if other_lane is None:
                continue

            other_lane_level = utils.get_lane_level_from_lane(other_lane)
            if other_lane_level is not None and other_lane_level != lane_level:
                issue_id = result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Lane levels are not the same between two connected roads.",
                    level=IssueSeverity.WARNING,
                    rule_uid=rule_uid,
                )

                result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=root.getpath(lane),
                    description="",
                )

                s = None
                if linkage_tag == models.LinkageTag.PREDECESSOR:
                    s = 0
                if linkage_tag == models.LinkageTag.SUCCESSOR:
                    s = utils.get_road_length(road)

                if s is None:
                    continue

                inertial_point = (
                    utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
                        road, current_lane_section, lane, s
                    )
                )

                if inertial_point is not None:
                    result.add_inertial_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description="Lane levels are not the same between two connected roads.",
                    )


def _check_level_among_lane_sections(
    checker_data: models.CheckerData,
    rule_uid: str,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)
    for road in roads:
        lane_sections = utils.get_lane_sections(road)
        if len(lane_sections) >= 2:
            # check for lane level changing in between consecutive lane sections
            for i in range(1, len(lane_sections)):
                _check_level_change_between_lane_sections(
                    root=checker_data.input_file_xml_root,
                    current_lane_section=lane_sections[i],
                    previous_lane_section=lane_sections[i - 1],
                    result=checker_data.result,
                    rule_uid=rule_uid,
                )


def _check_level_among_roads(
    checker_data: models.CheckerData,
    road_id_map: Dict[int, etree._ElementTree],
    rule_uid: str,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)
    for road in roads:
        _check_level_change_linkage_roads(
            linkage_tag=models.LinkageTag.PREDECESSOR,
            road=road,
            road_id_map=road_id_map,
            result=checker_data.result,
            rule_uid=rule_uid,
            root=checker_data.input_file_xml_root,
        )
        _check_level_change_linkage_roads(
            linkage_tag=models.LinkageTag.SUCCESSOR,
            road=road,
            road_id_map=road_id_map,
            result=checker_data.result,
            rule_uid=rule_uid,
            root=checker_data.input_file_xml_root,
        )


def _check_level_in_lane_section(
    checker_data: models.CheckerData,
    rule_uid: str,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)
    for road in roads:
        lane_sections_with_length = (
            utils.get_sorted_lane_sections_with_length_from_road(road)
        )

        for lane_section_with_length in lane_sections_with_length:
            lane_section = lane_section_with_length.lane_section
            left_lanes_list = utils.get_left_lanes_from_lane_section(lane_section)
            right_lanes_list = utils.get_right_lanes_from_lane_section(lane_section)

            left_lanes_list = [
                lane for lane in left_lanes_list if utils.get_lane_id(lane) is not None
            ]

            right_lanes_list = [
                lane for lane in right_lanes_list if utils.get_lane_id(lane) is not None
            ]

            # sort by lane id to guarantee order while checking level
            # left ids goes monotonic increasing from 1
            sorted_left_lane = sorted(
                left_lanes_list, key=lambda lane: int(utils.get_lane_id(lane))
            )

            _check_true_level_on_side(
                checker_data.input_file_xml_root,
                sorted_left_lane,
                road,
                lane_section_with_length,
                checker_data.result,
                rule_uid,
            )

            # sort by lane abs(id) to guarantee order while checking level
            # right ids goes monotonic decreasing from -1
            sorted_right_lane = sorted(
                right_lanes_list, key=lambda lane: abs(utils.get_lane_id(lane))
            )

            _check_true_level_on_side(
                checker_data.input_file_xml_root,
                sorted_right_lane,
                road,
                lane_section_with_length,
                checker_data.result,
                rule_uid,
            )


def _check_level_among_junctions(
    checker_data: models.CheckerData,
    road_id_map: Dict[int, etree._ElementTree],
    rule_uid: str,
) -> None:
    for junction in utils.get_junctions(checker_data.input_file_xml_root):
        for connection in utils.get_connections_from_junction(junction):
            contacting_lane_sections = (
                utils.get_incoming_and_connection_contacting_lane_sections(
                    connection, road_id_map
                )
            )

            if contacting_lane_sections is None:
                continue

            for lane_link in utils.get_lane_links_from_connection(connection):
                incoming_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
                connection_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

                if incoming_lane_id is None or connection_lane_id is None:
                    continue

                incoming_lane = utils.get_lane_from_lane_section(
                    contacting_lane_sections.incoming, incoming_lane_id
                )
                connection_lane = utils.get_lane_from_lane_section(
                    contacting_lane_sections.connection, connection_lane_id
                )

                if incoming_lane is None or connection_lane is None:
                    continue

                incoming_level = utils.get_lane_level_from_lane(incoming_lane)
                connection_level = utils.get_lane_level_from_lane(connection_lane)

                if incoming_level != connection_level:
                    issue_id = checker_data.result.register_issue(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        description="Lane levels are not the same between incoming road and junction.",
                        level=IssueSeverity.WARNING,
                        rule_uid=rule_uid,
                    )

                    checker_data.result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        issue_id=issue_id,
                        xpath=checker_data.input_file_xml_root.getpath(incoming_lane),
                        description="",
                    )

                    issue_id = checker_data.result.register_issue(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        description="Lane levels are not the same between junction and incoming road.",
                        level=IssueSeverity.WARNING,
                        rule_uid=rule_uid,
                    )

                    checker_data.result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        issue_id=issue_id,
                        xpath=checker_data.input_file_xml_root.getpath(connection_lane),
                        description="",
                    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if there is any @Level=False after true until
    the lane border.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/2
    """
    logging.info("Executing road.lane.level.true.one_side check")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.lane.level_true_one_side",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    _check_level_in_lane_section(checker_data, rule_uid)
    _check_level_among_lane_sections(checker_data, rule_uid)
    _check_level_among_roads(checker_data, road_id_map, rule_uid)
    _check_level_among_junctions(checker_data, road_id_map, rule_uid)
