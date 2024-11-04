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

CHECKER_ID = "check_asam_xodr_road_lane_link_lanes_across_lane_sections"
CHECKER_DESCRIPTION = "Lanes that continues across the lane sections shall be connected in both directions."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.lane.link.lanes_across_lane_sections"


def _check_two_lane_sections_one_direction(
    checker_data: models.CheckerData,
    first_lane_section: models.ContactingLaneSection,
    second_lane_section: models.ContactingLaneSection,
) -> None:
    for lane in utils.get_left_and_right_lanes_from_lane_section(
        first_lane_section.lane_section
    ):
        current_lane_id = utils.get_lane_id(lane)
        if current_lane_id is None:
            continue

        connecting_lane_ids_of_first_lane = utils.get_connecting_lane_ids(
            lane, first_lane_section.linkage_tag
        )
        for connecting_lane_id_of_first_lane in connecting_lane_ids_of_first_lane:
            connecting_lane = utils.get_lane_from_lane_section(
                second_lane_section.lane_section, connecting_lane_id_of_first_lane
            )

            if connecting_lane is None:
                continue

            connecting_lane_ids_of_second_lane = utils.get_connecting_lane_ids(
                connecting_lane, second_lane_section.linkage_tag
            )

            if current_lane_id not in connecting_lane_ids_of_second_lane:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    description="Missing lane link.",
                    level=IssueSeverity.ERROR,
                    rule_uid=RULE_UID,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(connecting_lane),
                    description="Missing lane link.",
                )


def _check_two_lane_sections(
    checker_data: models.CheckerData,
    first_lane_section: models.ContactingLaneSection,
    second_lane_section: models.ContactingLaneSection,
) -> None:
    _check_two_lane_sections_one_direction(
        checker_data, first_lane_section, second_lane_section
    )
    _check_two_lane_sections_one_direction(
        checker_data, second_lane_section, first_lane_section
    )


def _check_middle_lane_sections(
    checker_data: models.CheckerData, road: etree._ElementTree
) -> None:
    lane_sections = utils.get_lane_sections(road)

    if len(lane_sections) < 2:
        return

    for i in range(1, len(lane_sections)):
        current_lane_section = lane_sections[i]
        previous_lane_section = lane_sections[i - 1]
        _check_two_lane_sections(
            checker_data,
            models.ContactingLaneSection(
                lane_section=previous_lane_section,
                linkage_tag=models.LinkageTag.SUCCESSOR,
            ),
            models.ContactingLaneSection(
                lane_section=current_lane_section,
                linkage_tag=models.LinkageTag.PREDECESSOR,
            ),
        )


def _check_first_lane_section(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    road_id_map: Dict[int, etree._ElementTree],
) -> None:
    first_lane_section = utils.get_first_lane_section(road)
    if first_lane_section is None:
        return
    first_contacting_lane_section = models.ContactingLaneSection(
        lane_section=first_lane_section, linkage_tag=models.LinkageTag.PREDECESSOR
    )

    predecessor_linkage = utils.get_road_linkage(road, models.LinkageTag.PREDECESSOR)
    if predecessor_linkage is None:
        return

    other_contacting_lane_section = utils.get_contact_lane_section_from_linked_road(
        predecessor_linkage, road_id_map
    )

    if other_contacting_lane_section is None:
        return

    _check_two_lane_sections(
        checker_data,
        first_contacting_lane_section,
        other_contacting_lane_section,
    )


def _check_last_lane_section(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    road_id_map: Dict[int, etree._ElementTree],
) -> None:
    last_lane_section = utils.get_last_lane_section(road)
    if last_lane_section is None:
        return

    last_contacting_lane_section = models.ContactingLaneSection(
        lane_section=last_lane_section, linkage_tag=models.LinkageTag.SUCCESSOR
    )

    successor_linkage = utils.get_road_linkage(road, models.LinkageTag.SUCCESSOR)
    if successor_linkage is None:
        return

    other_contacting_lane_section = utils.get_contact_lane_section_from_linked_road(
        successor_linkage, road_id_map
    )

    if other_contacting_lane_section is None:
        return

    _check_two_lane_sections(
        checker_data,
        last_contacting_lane_section,
        other_contacting_lane_section,
    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.lane.link.lanes_across_lane_sections

    Description: Lanes that continues across the lane sections shall be connected in both directions.

    Severity: ERROR

    Version range: [1.7.0, )

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/3
    """
    logging.info("Executing road.lane.link.lanes_across_lane_sections check.")

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in utils.get_roads(checker_data.input_file_xml_root):
        # For all roads, no matter whether they belong to a junction or not, middle lane sections
        # shall always be connected
        _check_middle_lane_sections(checker_data, road)

        # For all roads not belonging to a junction, the first and the last lane sections shall be checked.
        # For roads belonging to a junction, ignore this rule for the first and the last lane section
        # due to the following statement from the standard:
        #     "The <link> element shall be omitted if the lane starts or ends in a junction or has no link."
        if not utils.road_belongs_to_junction(road):
            _check_first_lane_section(checker_data, road, road_id_map)
            _check_last_lane_section(checker_data, road, road_id_map)
