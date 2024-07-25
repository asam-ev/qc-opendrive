import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"


def _check_junctions_connection_one_connection_element(
    checker_data: models.CheckerData, rule_uid: str
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

    for connecting_road_id, connections in connecting_road_id_connections_map.items():
        # connecting road id cannot be appear in more than 1 <connection> element
        if len(connections) > 1:
            # we raise 1 issue with all repeated locations for each repeated id
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                description=f"Connecting road {connecting_road_id} shall be represented by only one <connection> element.",
                level=IssueSeverity.ERROR,
                rule_uid=rule_uid,
            )
            for connection in connections:
                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(connection),
                    description="Connection with reused connecting road id.",
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

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="junctions.connection.one_connection_element",
    )

    if checker_data.schema_version != RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_junctions_connection_one_connection_element(checker_data, rule_uid)
