import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.4.0"

FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
    checker_data: models.CheckerData,
    rule_uid: str,
    lane: etree._Element,
    successor_width_zero_lane: etree._Element,
    issue_severity: IssueSeverity,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description=f"If a new lane appears besides, only the continuing lane shall be connected to the original lane, not the appearing lane.",
        level=issue_severity,
        rule_uid=rule_uid,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description="Lane with successors with width zero.",
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(successor_width_zero_lane),
        description="Successor lane with width zero.",
    )


def _check_successor_with_width_zero_between_lane_sections(
    checker_data: models.CheckerData,
    rule_uid: str,
    current_lane_section: etree._ElementTree,
    next_lane_section: etree._ElementTree,
) -> None:
    current_lanes = utils.get_left_and_right_lanes_from_lane_section(
        current_lane_section
    )

    for lane in current_lanes:
        lane_id = utils.get_lane_id(lane)

        if lane_id is None:
            continue

        successor_lane_ids = utils.get_successor_lane_ids(lane)

        for successor_lane_id in successor_lane_ids:
            successor_lane = utils.get_lane_from_lane_section(
                next_lane_section, successor_lane_id
            )
            if successor_lane is None:
                continue

            start_lane_width = utils.evaluate_lane_width(successor_lane, 0.0)

            if (
                start_lane_width is not None
                and abs(start_lane_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                _raise_issue(
                    checker_data,
                    rule_uid,
                    lane,
                    successor_lane,
                    IssueSeverity.ERROR,
                )


def _check_appearing_successor_with_width_zero_on_road(
    checker_data: models.CheckerData, rule_uid: str, road: etree._ElementTree
) -> None:
    lane_sections = utils.get_lane_sections(road)

    if len(lane_sections) < 2:
        return

    for index in range(len(lane_sections) - 1):
        current_lane_section = lane_sections[index]
        next_lane_section = lane_sections[index + 1]
        _check_successor_with_width_zero_between_lane_sections(
            checker_data, rule_uid, current_lane_section, next_lane_section
        )


def _check_appearing_successor_road(
    checker_data: models.CheckerData,
    rule_uid: str,
    road_id_map: Dict[int, etree._ElementTree],
    current_road_id: int,
    successor_road_id: int,
) -> None:
    current_road = road_id_map.get(current_road_id)

    if current_road is None:
        return

    successor_road = road_id_map.get(successor_road_id)

    if current_road is None or successor_road is None:
        return

    current_road_last_lane_section = utils.get_last_lane_section(current_road)

    successor_linkage = utils.get_road_linkage(
        current_road, models.LinkageTag.SUCCESSOR
    )

    successor_road_target_lane_section = (
        utils.get_contact_lane_section_from_linked_road(successor_linkage, road_id_map)
    )

    if successor_road_target_lane_section is None:
        return

    _check_successor_with_width_zero_between_lane_sections(
        checker_data,
        rule_uid,
        current_road_last_lane_section,
        successor_road_target_lane_section.lane_section,
    )


def _check_appearing_successor_junction(
    checker_data: models.CheckerData,
    rule_uid: str,
    junction_id_map: Dict[int, etree._ElementTree],
    road_id_map: Dict[int, etree._ElementTree],
    road_id: int,
    successor_junction_id: int,
) -> None:
    successor_connections = utils.get_connections_between_road_and_junction(
        road_id,
        successor_junction_id,
        road_id_map,
        junction_id_map,
        models.ContactPoint.END,  # ROAD END == ROAD SUCCESSOR
    )

    for connection in successor_connections:
        connecting_road_id = utils.get_connecting_road_id_from_connection(connection)
        if connecting_road_id is None:
            continue

        connection_road = road_id_map.get(connecting_road_id)

        if connection_road is None:
            continue

        contact_lane_sections = (
            utils.get_incoming_and_connection_contacting_lane_sections(
                connection, road_id_map
            )
        )

        if contact_lane_sections is None:
            continue

        lane_links = utils.get_lane_links_from_connection(connection)

        for lane_link in lane_links:
            from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
            to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

            if from_lane_id is None or to_lane_id is None:
                continue

            connection_lane = utils.get_lane_from_lane_section(
                contact_lane_sections.connection, to_lane_id
            )

            connection_lane_start_width = utils.evaluate_lane_width(
                connection_lane, 0.0
            )

            if (
                connection_lane_start_width is not None
                and abs(connection_lane_start_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                current_road_lane = utils.get_lane_from_lane_section(
                    contact_lane_sections.incoming, from_lane_id
                )
                if current_road_lane is None:
                    continue
                _raise_issue(
                    checker_data,
                    rule_uid,
                    current_road_lane,
                    connection_lane,
                    IssueSeverity.ERROR,
                )


def _check_road_lane_link_new_lane_appear(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        _check_appearing_successor_with_width_zero_on_road(checker_data, rule_uid, road)

        successor_road_id = utils.get_successor_road_id(road)

        if successor_road_id is not None:
            _check_appearing_successor_road(
                checker_data, rule_uid, road_id_map, road_id, successor_road_id
            )
        else:
            successor_junction_id = utils.get_linked_junction_id(
                road, models.LinkageTag.SUCCESSOR
            )

            if successor_junction_id is None:
                continue

            _check_appearing_successor_junction(
                checker_data,
                rule_uid,
                junction_id_map,
                road_id_map,
                road_id,
                successor_junction_id,
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.lane.link.new_lane_appear

    Description: If a new lane appears besides, only the continuing lane shall
    be connected to the original lane, not the appearing lane.

    Severity: ERROR

    Version range: [1.4.0, )

    Remark:
        None

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/8
    """
    logging.info("Executing road.lane.link.new_lane_appear check")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.lane.link.new_lane_appear",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_road_lane_link_new_lane_appear(checker_data, rule_uid)
