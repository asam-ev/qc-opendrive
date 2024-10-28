# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junctions_connection_connect_road_no_incoming_road"
CHECKER_DESCRIPTION = "Connecting roads shall not be incoming roads."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:junctions.connection.connect_road_no_incoming_road"


def _check_junctions_connection_connect_road_no_incoming_road(
    checker_data: models.CheckerData,
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for junction in junctions:
        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            incoming_road_id = utils.get_incoming_road_id_from_connection(connection)
            if incoming_road_id is None:
                continue

            incoming_road = road_id_map.get(incoming_road_id)
            if incoming_road is None:
                continue

            if utils.road_belongs_to_junction(incoming_road):
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    description=f"Connecting roads shall not be incoming roads.",
                    level=IssueSeverity.ERROR,
                    rule_uid=RULE_UID,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(connection),
                    description="Connection with connecting road found as incoming road.",
                )

                successor_junction_id = utils.get_linked_junction_id(
                    incoming_road, models.LinkageTag.SUCCESSOR
                )
                predecessor_junction_id = utils.get_linked_junction_id(
                    incoming_road, models.LinkageTag.PREDECESSOR
                )

                junction_id = utils.get_junction_id(junction)

                if junction_id is None:
                    continue

                inertial_point = None
                if successor_junction_id == junction_id:
                    inertial_point = utils.get_end_point_xyz_from_road_reference_line(
                        incoming_road
                    )
                elif predecessor_junction_id == junction_id:
                    inertial_point = utils.get_start_point_xyz_from_road_reference_line(
                        incoming_road
                    )
                else:
                    inertial_point = (
                        utils.get_middle_point_xyz_from_road_reference_line(
                            incoming_road
                        )
                    )

                if inertial_point is not None:
                    checker_data.result.add_inertial_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description="Incoming road which is also a connecting road.",
                    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if a junction connecting roads are also incoming
    roads.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/6
    """
    logging.info("Executing junctions.connection.connect_road_no_incoming_road check")

    _check_junctions_connection_connect_road_no_incoming_road(checker_data)
