# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junctions_connection_one_connection_element"
CHECKER_DESCRIPTION = "Each connecting road shall be represented by exactly one element. A connecting road may contain as many lanes as required."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:junctions.connection.one_connection_element"
APPLICABLE_VERSION = "<=1.7.0"


def _check_junctions_connection_one_connection_element(
    checker_data: models.CheckerData,
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)

    connecting_road_id_connections_map: Dict[int, List[etree._Element]] = {}

    for junction in junctions:
        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            connecting_road_id = utils.get_connecting_road_id_from_connection(
                connection
            )

            if connecting_road_id is None:
                continue

            if connecting_road_id not in connecting_road_id_connections_map:
                connecting_road_id_connections_map[connecting_road_id] = []

            connecting_road_id_connections_map[connecting_road_id].append(connection)

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for connecting_road_id, connections in connecting_road_id_connections_map.items():
        # connecting road id cannot be appear in more than 1 <connection> element
        if len(connections) > 1:
            # we raise 1 issue with all repeated locations for each repeated id
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=CHECKER_ID,
                description=f"Connecting road {connecting_road_id} shall be represented by only one <connection> element.",
                level=IssueSeverity.ERROR,
                rule_uid=RULE_UID,
            )

            for connection in connections:
                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(connection),
                    description="Connection with reused connecting road id.",
                )

            connecting_road = road_id_map.get(connecting_road_id)
            if connecting_road is not None:
                inertial_point = utils.get_middle_point_xyz_from_road_reference_line(
                    connecting_road
                )

                if inertial_point is not None:
                    checker_data.result.add_inertial_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description="Connecting road being reused.",
                    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if a junction connecting roads are also used
    more than once.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/9

    Rule ID: junctions.connection.one_connection_element

    Description: Each connecting road shall be represented by exactly one
    element. A connecting road may contain as many lanes as required.

    Severity: ERROR

    Version range: From 1.7.0 to 1.7.0

    Rule Version: 0.1
    """
    logging.info("Executing junctions.connection.one_connection_element check")

    _check_junctions_connection_one_connection_element(checker_data)
