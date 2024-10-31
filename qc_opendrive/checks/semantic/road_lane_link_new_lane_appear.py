# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from typing import Dict
from lxml import etree

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_lane_link_new_lane_appear"
CHECKER_DESCRIPTION = "If a new lane appears besides, only the continuing lane shall be connected to the original lane, not the appearing lane."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.lane.link.new_lane_appear"

FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
    checker_data: models.CheckerData,
    lane: etree._Element,
    width_zero_lane: etree._Element,
    issue_severity: IssueSeverity,
    linkage_tag: models.LinkageTag,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"If a new lane appears besides, only the continuing lane shall be connected to the original lane, not the appearing lane.",
        level=issue_severity,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description=f"Lane with {linkage_tag.value} with width zero.",
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(width_zero_lane),
        description=f"{linkage_tag.value.capitalize()} lane with width zero.",
    )


def _check_successor_with_width_zero_between_lane_sections(
    checker_data: models.CheckerData,
    current_lane_section: etree._ElementTree,
    next_lane_section: etree._ElementTree,
    contact_point: models.ContactPoint,
    next_lane_section_length: float,
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

            target_lane_width = None

            if contact_point == models.ContactPoint.START:
                target_lane_width = utils.evaluate_lane_width(successor_lane, 0.0)
            elif contact_point == models.ContactPoint.END:
                target_lane_width = utils.evaluate_lane_width(
                    successor_lane, next_lane_section_length
                )

            if (
                target_lane_width is not None
                and abs(target_lane_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                _raise_issue(
                    checker_data,
                    lane,
                    successor_lane,
                    IssueSeverity.ERROR,
                    models.LinkageTag.SUCCESSOR,
                )


def _check_predecessor_with_width_zero_between_lane_sections(
    checker_data: models.CheckerData,
    current_lane_section: etree._ElementTree,
    next_lane_section: etree._ElementTree,
    contact_point: models.ContactPoint,
    next_lane_section_length: float,
) -> None:
    current_lanes = utils.get_left_and_right_lanes_from_lane_section(
        current_lane_section
    )

    for lane in current_lanes:
        lane_id = utils.get_lane_id(lane)

        if lane_id is None:
            continue

        predecessor_lane_ids = utils.get_predecessor_lane_ids(lane)

        for predecessor_lane_id in predecessor_lane_ids:
            predecessor_lane = utils.get_lane_from_lane_section(
                next_lane_section, predecessor_lane_id
            )
            if predecessor_lane is None:
                continue

            target_lane_width = None

            if contact_point == models.ContactPoint.START:
                target_lane_width = utils.evaluate_lane_width(predecessor_lane, 0.0)
            elif contact_point == models.ContactPoint.END:
                target_lane_width = utils.evaluate_lane_width(
                    predecessor_lane, next_lane_section_length
                )

            if (
                target_lane_width is not None
                and abs(target_lane_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                _raise_issue(
                    checker_data,
                    lane,
                    predecessor_lane,
                    IssueSeverity.ERROR,
                    models.LinkageTag.PREDECESSOR,
                )


def _check_appearing_successor_with_width_zero_on_road(
    checker_data: models.CheckerData, road: etree._ElementTree
) -> None:
    lane_sections = utils.get_sorted_lane_sections_with_length_from_road(road)

    if len(lane_sections) < 2:
        return

    for index in range(len(lane_sections) - 1):
        current_lane_section = lane_sections[index].lane_section
        next_lane_section = lane_sections[index + 1].lane_section

        _check_successor_with_width_zero_between_lane_sections(
            checker_data,
            current_lane_section,
            next_lane_section,
            models.ContactPoint.START,
            lane_sections[index + 1].length,
        )


def _check_appearing_successor_road(
    checker_data: models.CheckerData,
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

    next_lane_section_length = 0.0
    lane_sections = utils.get_sorted_lane_sections_with_length_from_road(successor_road)
    if successor_linkage.contact_point == models.ContactPoint.START:
        next_lane_section_length = lane_sections[0].length
    elif successor_linkage.contact_point == models.ContactPoint.END:
        next_lane_section_length = lane_sections[len(lane_sections) - 1].length

    _check_successor_with_width_zero_between_lane_sections(
        checker_data,
        current_road_last_lane_section,
        successor_road_target_lane_section.lane_section,
        successor_linkage.contact_point,
        next_lane_section_length,
    )


def _check_appearing_predecessor_road(
    checker_data: models.CheckerData,
    road_id_map: Dict[int, etree._ElementTree],
    current_road_id: int,
    predecessor_road_id: int,
) -> None:
    current_road = road_id_map.get(current_road_id)

    if current_road is None:
        return

    predecessor_road = road_id_map.get(predecessor_road_id)

    if current_road is None or predecessor_road is None:
        return

    current_road_first_lane_section = utils.get_first_lane_section(current_road)

    predecessor_linkage = utils.get_road_linkage(
        current_road, models.LinkageTag.PREDECESSOR
    )

    predecessor_road_target_lane_section = (
        utils.get_contact_lane_section_from_linked_road(
            predecessor_linkage, road_id_map
        )
    )

    if predecessor_road_target_lane_section is None:
        return

    next_lane_section_length = 0.0
    lane_sections = utils.get_sorted_lane_sections_with_length_from_road(
        predecessor_road
    )
    if predecessor_linkage.contact_point == models.ContactPoint.START:
        next_lane_section_length = lane_sections[0].length
    elif predecessor_linkage.contact_point == models.ContactPoint.END:
        next_lane_section_length = lane_sections[len(lane_sections) - 1].length

    _check_predecessor_with_width_zero_between_lane_sections(
        checker_data,
        current_road_first_lane_section,
        predecessor_road_target_lane_section.lane_section,
        predecessor_linkage.contact_point,
        next_lane_section_length,
    )


def _check_appearing_successor_junction(
    checker_data: models.CheckerData,
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

        connection_contact_point = utils.get_contact_point_from_connection(connection)

        if connection_contact_point is None:
            continue

        for lane_link in lane_links:
            from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
            to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

            if from_lane_id is None or to_lane_id is None:
                continue

            connection_lane = utils.get_lane_from_lane_section(
                contact_lane_sections.connection, to_lane_id
            )

            connection_lane_contact_width = None
            if connection_contact_point == models.ContactPoint.START:
                connection_lane_contact_width = utils.evaluate_lane_width(
                    connection_lane, 0.0
                )
            elif connection_contact_point == models.ContactPoint.END:
                connection_road_length = utils.get_road_length(connection_road)
                s_connection_lane_section = utils.get_s_from_lane_section(
                    contact_lane_sections.connection
                )
                if connection_road_length is None or s_connection_lane_section is None:
                    continue

                connection_lane_contact_width = utils.evaluate_lane_width(
                    connection_lane, connection_road_length - s_connection_lane_section
                )

            if (
                connection_lane_contact_width is not None
                and abs(connection_lane_contact_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                current_road_lane = utils.get_lane_from_lane_section(
                    contact_lane_sections.incoming, from_lane_id
                )
                if current_road_lane is None:
                    continue
                _raise_issue(
                    checker_data,
                    current_road_lane,
                    connection_lane,
                    IssueSeverity.ERROR,
                    models.LinkageTag.SUCCESSOR,
                )


def _check_appearing_predecessor_junction(
    checker_data: models.CheckerData,
    junction_id_map: Dict[int, etree._ElementTree],
    road_id_map: Dict[int, etree._ElementTree],
    road_id: int,
    predecessor_junction_id: int,
) -> None:
    predecessor_connections = utils.get_connections_between_road_and_junction(
        road_id,
        predecessor_junction_id,
        road_id_map,
        junction_id_map,
        models.ContactPoint.START,  # ROAD START == ROAD PREDECESSOR
    )

    for connection in predecessor_connections:
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

        connection_contact_point = utils.get_contact_point_from_connection(connection)

        for lane_link in lane_links:
            from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
            to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

            if from_lane_id is None or to_lane_id is None:
                continue

            connection_lane = utils.get_lane_from_lane_section(
                contact_lane_sections.connection, to_lane_id
            )

            connection_lane_contact_width = None
            if connection_contact_point == models.ContactPoint.START:
                connection_lane_contact_width = utils.evaluate_lane_width(
                    connection_lane, 0.0
                )
            elif connection_contact_point == models.ContactPoint.END:
                connection_road_length = utils.get_road_length(connection_road)
                s_connection_lane_section = utils.get_s_from_lane_section(
                    contact_lane_sections.connection
                )
                if connection_road_length is None or s_connection_lane_section is None:
                    continue

                connection_lane_contact_width = utils.evaluate_lane_width(
                    connection_lane, connection_road_length - s_connection_lane_section
                )

            if (
                connection_lane_contact_width is not None
                and abs(connection_lane_contact_width) < FLOAT_COMPARISON_THRESHOLD
            ):
                current_road_lane = utils.get_lane_from_lane_section(
                    contact_lane_sections.incoming, from_lane_id
                )
                if current_road_lane is None:
                    continue
                _raise_issue(
                    checker_data,
                    current_road_lane,
                    connection_lane,
                    IssueSeverity.ERROR,
                    models.LinkageTag.PREDECESSOR,
                )


def _check_road_lane_link_new_lane_appear(checker_data: models.CheckerData) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        _check_appearing_successor_with_width_zero_on_road(checker_data, road)

        successor_road_id = utils.get_successor_road_id(road)

        if successor_road_id is not None:
            _check_appearing_successor_road(
                checker_data, road_id_map, road_id, successor_road_id
            )

        predecessor_road_id = utils.get_predecessor_road_id(road)

        if predecessor_road_id is not None:
            _check_appearing_predecessor_road(
                checker_data, road_id_map, road_id, predecessor_road_id
            )

        successor_junction_id = utils.get_linked_junction_id(
            road, models.LinkageTag.SUCCESSOR
        )
        if successor_junction_id is not None:
            _check_appearing_successor_junction(
                checker_data,
                junction_id_map,
                road_id_map,
                road_id,
                successor_junction_id,
            )

        predecessor_junction_id = utils.get_linked_junction_id(
            road, models.LinkageTag.PREDECESSOR
        )

        if predecessor_junction_id is not None:
            _check_appearing_predecessor_junction(
                checker_data,
                junction_id_map,
                road_id_map,
                road_id,
                predecessor_junction_id,
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

    _check_road_lane_link_new_lane_appear(checker_data)
