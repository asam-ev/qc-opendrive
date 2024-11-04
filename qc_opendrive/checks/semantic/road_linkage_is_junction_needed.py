# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from typing import Dict, List
from lxml import etree
from typing import Optional

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_linkage_is_junction_needed"
CHECKER_DESCRIPTION = "Two roads shall only be linked directly, if the linkage is clear. If the relationship to successor or predecessor is ambiguous, junctions shall be used."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.linkage.is_junction_needed"


def _raise_road_linkage_is_junction_needed_issue(
    checker_data: models.CheckerData,
    road_linkage_elements: List[etree._Element],
    linkage_tag: models.LinkageTag,
    problematic_road: Optional[etree._ElementTree],
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"Road cannot have ambiguous {linkage_tag.value}, a junction is needed.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )

    for element in road_linkage_elements:
        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(element),
            description=f"Road cannot have ambiguous {linkage_tag.value}, a junction is needed.",
        )

    if problematic_road is not None:
        inertial_point = None
        if linkage_tag == models.LinkageTag.PREDECESSOR:
            inertial_point = utils.get_start_point_xyz_from_road_reference_line(
                problematic_road
            )
        elif linkage_tag == models.LinkageTag.SUCCESSOR:
            inertial_point = utils.get_end_point_xyz_from_road_reference_line(
                problematic_road
            )

        if inertial_point is not None:
            checker_data.result.add_inertial_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=CHECKER_ID,
                issue_id=issue_id,
                x=inertial_point.x,
                y=inertial_point.y,
                z=inertial_point.z,
                description="Point where the linkage is not clear.",
            )


def _create_contact_point_id_from_road_linkage(road_linkage: models.RoadLinkage) -> str:
    return f"{road_linkage.id}-{road_linkage.contact_point.value}"


def _get_road_linkage_from_contact_point_id(
    contact_point_id: str,
) -> models.RoadLinkage:
    contact_point_id_split = contact_point_id.split("-")
    return models.RoadLinkage(
        id=int(contact_point_id_split[0]),
        contact_point=models.ContactPoint(contact_point_id_split[1]),
    )


def _check_road_linkage_is_junction_needed(checker_data: models.CheckerData) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    if len(road_id_map) < 2:
        return

    road_contact_point_map: Dict[str, List[etree._Element]] = {}

    for _, road in road_id_map.items():
        # Verify if road is not part of a junction to proceed.
        # Junction connecting roads can share common successors or predecessors
        # and they are used to distinguish ambiguity.
        # We don't need to verify this rule for junction roads.
        if not utils.road_belongs_to_junction(road):
            road_predecessor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.PREDECESSOR
            )

            if road_predecessor_linkage is not None:
                contact_point_id = _create_contact_point_id_from_road_linkage(
                    road_predecessor_linkage
                )
                if contact_point_id not in road_contact_point_map:
                    road_contact_point_map[contact_point_id] = []
                predecessor_link = utils.get_road_link_element(
                    road, road_predecessor_linkage.id, models.LinkageTag.PREDECESSOR
                )

                road_contact_point_map[contact_point_id].append(predecessor_link)

            road_successor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.SUCCESSOR
            )

            if road_successor_linkage is not None:
                contact_point_id = _create_contact_point_id_from_road_linkage(
                    road_successor_linkage
                )
                if contact_point_id not in road_contact_point_map:
                    road_contact_point_map[contact_point_id] = []
                successor_link = utils.get_road_link_element(
                    road, road_successor_linkage.id, models.LinkageTag.PREDECESSOR
                )

                road_contact_point_map[contact_point_id].append(successor_link)

    for contact_point_id, elements in road_contact_point_map.items():
        # in case two roads use the same contact point for a "target" road the
        # linkage is unclear
        if len(elements) > 1:
            road_linkage = _get_road_linkage_from_contact_point_id(contact_point_id)

            linkage_tag = None

            if road_linkage.contact_point == models.ContactPoint.END:
                linkage_tag = models.LinkageTag.SUCCESSOR
            elif road_linkage.contact_point == models.ContactPoint.START:
                linkage_tag = models.LinkageTag.PREDECESSOR
            else:
                continue

            problematic_road = road_id_map.get(road_linkage.id)

            _raise_road_linkage_is_junction_needed_issue(
                checker_data, elements, linkage_tag, problematic_road
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.linkage.is_junction_needed

    Description: Two roads shall only be linked directly, if the linkage is clear.
    If the relationship to successor or predecessor is ambiguous, junctions
    shall be used.

    Severity: ERROR

    Version range: [1.4.0, )

    Remark:
        None

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/4
    """
    logging.info("Executing road.linkage.is_junction_needed check")

    _check_road_linkage_is_junction_needed(checker_data)
