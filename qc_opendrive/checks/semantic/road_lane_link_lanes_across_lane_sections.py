from dataclasses import dataclass
import logging

from typing import Union, List, Dict, Set
from enum import Enum

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.4.0"


def _raise_predecessor_issues(
    checker_data: models.CheckerData, rule_uid: str, lane_section: etree._ElementTree
) -> None:
    for lane in utils.get_left_and_right_lanes_from_lane_section(lane_section):
        predecessor_lane_ids = utils.get_predecessor_lane_ids(lane)
        for lane_id in predecessor_lane_ids:
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                description="Invalid predecessor lane id.",
                level=IssueSeverity.ERROR,
                rule_uid=rule_uid,
            )

            link = utils.get_lane_link_element(
                lane, lane_id, models.LinkageTag.PREDECESSOR
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(link),
                description="",
            )


def _raise_successor_issues(
    checker_data: models.CheckerData, rule_uid: str, lane_section: etree._ElementTree
) -> None:
    for lane in utils.get_left_and_right_lanes_from_lane_section(lane_section):
        successor_lane_ids = utils.get_successor_lane_ids(lane)
        for lane_id in successor_lane_ids:
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                description="Invalid successor lane id.",
                level=IssueSeverity.ERROR,
                rule_uid=rule_uid,
            )

            link = utils.get_lane_link_element(
                lane, lane_id, models.LinkageTag.SUCCESSOR
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(link),
                description="",
            )


def _check_two_lane_sections(
    checker_data: models.CheckerData,
    rule_uid: str,
    predecessor_lane_section: etree._ElementTree,
    successor_lane_section: etree._ElementTree,
) -> None:
    for lane in utils.get_left_and_right_lanes_from_lane_section(
        successor_lane_section
    ):
        current_lane_id = utils.get_lane_id(lane)
        predecessor_lane_ids = utils.get_predecessor_lane_ids(lane)
        for predecessor_lane_id in predecessor_lane_ids:
            predecessor_lane = utils.get_lane_from_lane_section(
                predecessor_lane_section, predecessor_lane_id
            )

            if predecessor_lane is None:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Invalid predecessor lane id.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                link = utils.get_lane_link_element(
                    lane, predecessor_lane_id, models.LinkageTag.PREDECESSOR
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(link),
                    description="",
                )

                continue

            successor_ids_of_predecessor_lane = utils.get_successor_lane_ids(
                predecessor_lane
            )

            if current_lane_id not in successor_ids_of_predecessor_lane:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Missing successor.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(predecessor_lane),
                    description="",
                )

    for lane in utils.get_left_and_right_lanes_from_lane_section(
        predecessor_lane_section
    ):
        current_lane_id = utils.get_lane_id(lane)
        successor_lane_ids = utils.get_successor_lane_ids(lane)
        for successor_lane_id in successor_lane_ids:
            successor_lane = utils.get_lane_from_lane_section(
                successor_lane_section, successor_lane_id
            )

            if successor_lane is None:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Invalid successor lane id.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                link = utils.get_lane_link_element(
                    lane, successor_lane_id, models.LinkageTag.SUCCESSOR
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(link),
                    description="",
                )

                continue

            predecessor_ids_of_successor_lane = utils.get_predecessor_lane_ids(
                successor_lane
            )

            if current_lane_id not in predecessor_ids_of_successor_lane:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Missing predecessor.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(successor_lane),
                    description="",
                )


def _check_middle_lane_sections(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    lane_sections = utils.get_lane_sections(road)

    if len(lane_sections) < 2:
        return

    for i in range(1, len(lane_sections)):
        current_lane_section = lane_sections[i]
        previous_lane_section = lane_sections[i - 1]
        _check_two_lane_sections(
            checker_data, rule_uid, previous_lane_section, current_lane_section
        )


def _check_first_lane_section(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    road_id_map: Dict[int, etree._ElementTree],
    rule_uid: str,
) -> None:
    first_lane_section = utils.get_first_lane_section(road)
    if first_lane_section is None:
        return

    predecessor_road_id = utils.get_predecessor_road_id(road)
    predecessor_road = road_id_map.get(predecessor_road_id)
    if predecessor_road is None:
        _raise_predecessor_issues(checker_data, rule_uid, first_lane_section)
        return

    last_lane_section_of_predecessor_road = utils.get_last_lane_section(
        predecessor_road
    )

    if last_lane_section_of_predecessor_road is None:
        _raise_predecessor_issues(checker_data, rule_uid, first_lane_section)
        return

    _check_two_lane_sections(
        checker_data,
        rule_uid,
        last_lane_section_of_predecessor_road,
        first_lane_section,
    )


def _check_last_lane_section(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    road_id_map: Dict[int, etree._ElementTree],
    rule_uid: str,
) -> None:
    last_lane_section = utils.get_last_lane_section(road)
    if last_lane_section is None:
        return

    successor_road_id = utils.get_successor_road_id(road)
    successor_road = road_id_map.get(successor_road_id)
    if successor_road is None:
        _raise_successor_issues(checker_data, rule_uid, last_lane_section)
        return

    first_lane_section_of_successor_road = utils.get_first_lane_section(successor_road)

    if first_lane_section_of_successor_road is None:
        _raise_successor_issues(checker_data, rule_uid, last_lane_section)
        return

    _check_two_lane_sections(
        checker_data,
        rule_uid,
        last_lane_section,
        first_lane_section_of_successor_road,
    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule: Lanes that continues across the lane sections shall be connected in both directions.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/3
    """
    logging.info("Executing road.lane.link.lanes_across_lane_sections check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.lane.link.lanes_across_lane_sections",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in utils.get_roads(checker_data.input_file_xml_root):
        _check_middle_lane_sections(checker_data, road, rule_uid)
        _check_first_lane_section(checker_data, road, road_id_map, rule_uid)
        _check_last_lane_section(checker_data, road, road_id_map, rule_uid)
