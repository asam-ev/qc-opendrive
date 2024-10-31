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

CHECKER_ID = "check_asam_xodr_road_lane_link_zero_width_at_end"
CHECKER_DESCRIPTION = "Lanes that have a width of zero at the end of the lane section shall have no successor element."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end"

FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    lane_section_with_length: models.LaneSectionWithLength,
    lane: etree._Element,
    issue_severity: IssueSeverity,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f" Lanes that have a width of zero at the end of the lane section shall have no successor element.",
        level=issue_severity,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description="Lane with width zero and successors.",
    )

    s_section = utils.get_s_from_lane_section(lane_section_with_length.lane_section)

    if s_section is None:
        return

    s = s_section + lane_section_with_length.length

    inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
        road, lane_section_with_length.lane_section, lane, s
    )
    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description="Lane with width zero and successors.",
        )


def _raise_issue_based_on_lane_id(
    lane: etree._Element,
    lane_id: int,
    road: etree._ElementTree,
    lane_section_with_length: models.LaneSectionWithLength,
    checker_data: models.CheckerData,
) -> None:
    if lane_id == 0:
        # Because of backward compatibility, this rule does
        # not apply to lane 0 (i.e. it is not allowed to have
        # a width (see Rule 77) but it might have a predecessor).
        # In this case the severity level should be changed
        # to "WARNING"
        _raise_issue(
            checker_data,
            road,
            lane_section_with_length,
            lane,
            IssueSeverity.WARNING,
        )
    else:
        _raise_issue(
            checker_data,
            road,
            lane_section_with_length,
            lane,
            IssueSeverity.ERROR,
        )


def _check_road_lane_link_zero_width_at_end(checker_data: models.CheckerData) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        lane_sections_with_length = (
            utils.get_sorted_lane_sections_with_length_from_road(road)
        )

        for lane_section in lane_sections_with_length:
            lanes = utils.get_left_and_right_lanes_from_lane_section(
                lane_section.lane_section
            )

            for lane in lanes:
                lane_end_width = utils.evaluate_lane_width(lane, lane_section.length)
                if lane_end_width is None:
                    continue

                if abs(lane_end_width) < FLOAT_COMPARISON_THRESHOLD:
                    # This rule only evaluate explicit successor.
                    # Other rules verify if any implicit successor was not
                    # properly registered.
                    successor_lane_ids = utils.get_successor_lane_ids(lane)

                    if len(successor_lane_ids) > 0:
                        lane_id = utils.get_lane_id(lane)
                        _raise_issue_based_on_lane_id(
                            lane,
                            lane_id,
                            road,
                            lane_section,
                            checker_data,
                        )


def _check_incoming_road_junction_successor_lane_width_zero(
    checker_data: models.CheckerData,
    road: etree._Element,
    road_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
) -> None:
    successor_junction_id = utils.get_linked_junction_id(
        road, models.LinkageTag.SUCCESSOR
    )

    if successor_junction_id is None:
        return

    successor_connections = utils.get_connections_between_road_and_junction(
        road_id,
        successor_junction_id,
        road_id_map,
        junction_id_map,
        models.ContactPoint.END,
    )

    lane_ids_with_successor = set()
    for connection in successor_connections:
        lane_links = utils.get_lane_links_from_connection(connection)

        for lane_link in lane_links:
            from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)

            if from_lane_id is None:
                continue

            lane_ids_with_successor.add(from_lane_id)

    lane_sections_with_length = utils.get_sorted_lane_sections_with_length_from_road(
        road
    )

    if len(lane_sections_with_length) == 0:
        return

    last_lane_section = lane_sections_with_length[-1]

    lanes = utils.get_left_and_right_lanes_from_lane_section(
        last_lane_section.lane_section
    )

    for lane in lanes:
        lane_end_width = utils.evaluate_lane_width(lane, last_lane_section.length)
        if lane_end_width is None:
            continue

        if abs(lane_end_width) < FLOAT_COMPARISON_THRESHOLD:
            lane_id = utils.get_lane_id(lane)
            if lane_id is None:
                continue

            if lane_id in lane_ids_with_successor:
                _raise_issue_based_on_lane_id(
                    lane,
                    lane_id,
                    road,
                    last_lane_section,
                    checker_data,
                )


def _check_connecting_road_lane_width_zero_with_successor(
    checker_data: models.CheckerData,
    road: etree._Element,
    road_id: int,
    junction_id_map: Dict[int, etree._ElementTree],
) -> None:
    road_junction_id = utils.get_road_junction_id(road)

    if road_junction_id is None:
        return

    junction = junction_id_map.get(road_junction_id)

    if junction is None:
        return

    successor_connections = utils.get_connections_of_connecting_road(
        road_id, junction, models.ContactPoint.END
    )

    lane_ids_with_successor = set()
    for connection in successor_connections:
        lane_links = utils.get_lane_links_from_connection(connection)

        for lane_link in lane_links:
            to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

            if to_lane_id is None:
                continue

            lane_ids_with_successor.add(to_lane_id)

    lane_sections_with_length = utils.get_sorted_lane_sections_with_length_from_road(
        road
    )

    if len(lane_sections_with_length) == 0:
        return

    last_lane_section = lane_sections_with_length[-1]
    lanes = utils.get_left_and_right_lanes_from_lane_section(
        last_lane_section.lane_section
    )

    for lane in lanes:
        lane_end_width = utils.evaluate_lane_width(lane, last_lane_section.length)
        if lane_end_width is None:
            continue

        if abs(lane_end_width) < FLOAT_COMPARISON_THRESHOLD:
            lane_id = utils.get_lane_id(lane)
            if lane_id is None:
                continue

            if lane_id in lane_ids_with_successor:
                _raise_issue_based_on_lane_id(
                    lane,
                    lane_id,
                    road,
                    last_lane_section,
                    checker_data,
                )


def _check_junction_road_lane_link_zero_width_at_end(
    checker_data: models.CheckerData,
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        if utils.road_belongs_to_junction(road):
            _check_connecting_road_lane_width_zero_with_successor(
                checker_data, road, road_id, junction_id_map
            )
        else:
            _check_incoming_road_junction_successor_lane_width_zero(
                checker_data, road, road_id, road_id_map, junction_id_map
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end

    Description: Lanes that have a width of zero at the end of the lane section
    shall have no successor element.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        Because of backward compatibility, this rule does not apply to lane 0
        (i.e. it is not allowed to have a width (see Rule 77) but it might have
        a predecessor). In this case the severity level should be changed to
        "WARNING".

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/21
    """
    logging.info("Executing road.lane.link.zero_width_at_end check")

    _check_road_lane_link_zero_width_at_end(checker_data)
    _check_junction_road_lane_link_zero_width_at_end(checker_data)
