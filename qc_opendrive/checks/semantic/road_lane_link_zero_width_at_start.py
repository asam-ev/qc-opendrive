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

CHECKER_ID = "check_asam_xodr_road_lane_link_zero_width_at_start"
CHECKER_DESCRIPTION = "Lanes that have a width of zero at the beginning of the lane section shall have no predecessor element."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start"

FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    lane_section: etree._ElementTree,
    lane: etree._Element,
    issue_severity: IssueSeverity,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f" Lanes that have a width of zero at the beginning of the lane section shall have no predecessor element.",
        level=issue_severity,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description="Lane with width zero and predecessors.",
    )

    s = utils.get_s_from_lane_section(lane_section)

    if s is None:
        return

    inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
        road, lane_section, lane, s
    )

    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description="Lane with width zero and predecessors.",
        )


def _raise_issue_based_on_lane_id(
    road: etree._ElementTree,
    lane_section: etree._ElementTree,
    lane: etree._Element,
    lane_id: int,
    checker_data: models.CheckerData,
) -> None:
    if lane_id == 0:
        # Because of backward compatibility, this rule does
        # not apply to lane 0 (i.e. it is not allowed to have
        # a width (see Rule 77) but it might have a predecessor).
        # In this case the severity level should be changed
        # to "WARNING"
        _raise_issue(checker_data, road, lane_section, lane, IssueSeverity.WARNING)
    else:
        _raise_issue(checker_data, road, lane_section, lane, IssueSeverity.ERROR)


def _check_road_lane_link_zero_width_at_start(checker_data: models.CheckerData) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        lane_sections = utils.get_lane_sections(road)

        for section in lane_sections:
            lanes = utils.get_left_and_right_lanes_from_lane_section(section)

            for lane in lanes:
                lane_start_width = utils.evaluate_lane_width(lane, 0.0)
                if lane_start_width is None:
                    continue

                if lane_start_width < FLOAT_COMPARISON_THRESHOLD:
                    # This rule only evaluate explicit predecessor.
                    # Other rules verify if any implicit predecessor was not
                    # properly registered.
                    predecessor_lane_ids = utils.get_predecessor_lane_ids(lane)

                    if len(predecessor_lane_ids) > 0:
                        lane_id = utils.get_lane_id(lane)
                        _raise_issue_based_on_lane_id(
                            road,
                            section,
                            lane,
                            lane_id,
                            checker_data,
                        )


def _check_incoming_road_junction_predecessor_lane_width_zero(
    checker_data: models.CheckerData,
    road: etree._Element,
    road_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
) -> None:
    predecessor_junction_id = utils.get_linked_junction_id(
        road, models.LinkageTag.PREDECESSOR
    )

    if predecessor_junction_id is None:
        return

    predecessor_connections = utils.get_connections_between_road_and_junction(
        road_id,
        predecessor_junction_id,
        road_id_map,
        junction_id_map,
        models.ContactPoint.START,
    )

    lane_ids_with_predecessor = set()
    for connection in predecessor_connections:
        lane_links = utils.get_lane_links_from_connection(connection)

        for lane_link in lane_links:
            from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)

            if from_lane_id is None:
                continue

            lane_ids_with_predecessor.add(from_lane_id)

    first_lane_section = utils.get_first_lane_section(road)
    lanes = utils.get_left_and_right_lanes_from_lane_section(first_lane_section)

    for lane in lanes:
        lane_start_width = utils.evaluate_lane_width(lane, 0.0)
        if lane_start_width is None:
            continue

        if lane_start_width < FLOAT_COMPARISON_THRESHOLD:
            lane_id = utils.get_lane_id(lane)
            if lane_id is None:
                continue

            if lane_id in lane_ids_with_predecessor:
                _raise_issue_based_on_lane_id(
                    road,
                    first_lane_section,
                    lane,
                    lane_id,
                    checker_data,
                )


def _check_connecting_road_lane_width_zero_with_predecessor(
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

    predecessor_connections = utils.get_connections_of_connecting_road(
        road_id, junction, models.ContactPoint.START
    )

    lane_ids_with_predecessor = set()
    for connection in predecessor_connections:
        lane_links = utils.get_lane_links_from_connection(connection)

        for lane_link in lane_links:
            to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

            if to_lane_id is None:
                continue

            lane_ids_with_predecessor.add(to_lane_id)

    first_lane_section = utils.get_first_lane_section(road)
    lanes = utils.get_left_and_right_lanes_from_lane_section(first_lane_section)

    for lane in lanes:
        lane_start_width = utils.evaluate_lane_width(lane, 0.0)
        if lane_start_width is None:
            continue

        if lane_start_width < FLOAT_COMPARISON_THRESHOLD:
            lane_id = utils.get_lane_id(lane)
            if lane_id is None:
                continue

            if lane_id in lane_ids_with_predecessor:
                _raise_issue_based_on_lane_id(
                    road,
                    first_lane_section,
                    lane,
                    lane_id,
                    checker_data,
                )


def _check_junction_road_lane_link_zero_width_at_start(
    checker_data: models.CheckerData,
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        if utils.road_belongs_to_junction(road):
            _check_connecting_road_lane_width_zero_with_predecessor(
                checker_data, road, road_id, junction_id_map
            )
        else:
            _check_incoming_road_junction_predecessor_lane_width_zero(
                checker_data, road, road_id, road_id_map, junction_id_map
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start

    Description: Lanes that have a width of zero at the beginning of the lane
    section shall have no predecessor element.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        Because of backward compatibility, this rule does not apply to lane 0
        (i.e. it is not allowed to have a width (see Rule 77) but it might have
        a predecessor). In this case the severity level should be changed to
        "WARNING".

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/22
    """
    logging.info("Executing road.lane.link.zero_width_at_start check")

    _check_road_lane_link_zero_width_at_start(checker_data)
    _check_junction_road_lane_link_zero_width_at_start(checker_data)
