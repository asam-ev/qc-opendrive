# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from lxml import etree

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junctions_connection_end_opposite_linkage"
CHECKER_DESCRIPTION = 'The value "end" shall be used to indicate that the connectingroad runs along the opposite direction of the linkage indicated in the element.'
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:junctions.connection.end_opposite_linkage"


def _raise_issue(
    checker_data: models.CheckerData,
    connection: etree._Element,
    connection_road: etree._Element,
):
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"The value 'end' shall be used to indicate that the connecting road runs along the opposite direction of the linkage indicated in the element.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(connection),
        description=f"Contact point 'end' not used on successor road connection.",
    )

    inertial_point = utils.get_end_point_xyz_from_road_reference_line(connection_road)
    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description="Contact point 'end' not used on successor road connection.",
        )


def _check_junction_connection_end_opposite_linkage(
    checker_data: models.CheckerData,
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for junction in junctions:
        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            contact_point = utils.get_contact_point_from_connection(connection)
            if contact_point is None:
                continue

            if contact_point == models.ContactPoint.END:
                connection_road_id = utils.get_connecting_road_id_from_connection(
                    connection
                )
                if connection_road_id is None:
                    continue

                incoming_road_id = utils.get_incoming_road_id_from_connection(
                    connection
                )
                if incoming_road_id is None:
                    continue

                connection_road = road_id_map.get(connection_road_id)
                if connection_road is None:
                    continue

                successor_linkage = utils.get_road_linkage(
                    connection_road, models.LinkageTag.SUCCESSOR
                )
                if successor_linkage is None:
                    continue

                if successor_linkage.id != incoming_road_id:
                    _raise_issue(checker_data, connection, connection_road)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:junctions.connection.end_opposite_linkage

    Description: The value "end" shall be used to indicate that the connecting
    road runs along the opposite direction of the linkage indicated in the element.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        None

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/37
    """
    logging.info("Executing junctions.connection.end_opposite_linkage check")

    _check_junction_connection_end_opposite_linkage(checker_data)
