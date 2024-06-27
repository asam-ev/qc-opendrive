import logging

from typing import Dict, Set, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.4.0"


def _check_junctions_connection_connect_road_no_incoming_road(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)

    incoming_road_ids = set()
    connecting_road_ids = set()

    incoming_road_connection_map: Dict[int, List[etree._Element]] = {}

    for junction in junctions:
        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            incoming_road_id = utils.get_connection_incoming_roa_id(connection)
            connecting_road_id = utils.get_connection_connecting_roa_id(connection)

            incoming_road_ids.add(incoming_road_id)
            connecting_road_ids.add(connecting_road_id)

            if incoming_road_id not in incoming_road_connection_map:
                incoming_road_connection_map[incoming_road_id] = []

            incoming_road_connection_map[incoming_road_id].append(connection)

    incoming_connecting_intersection = incoming_road_ids.intersection(
        connecting_road_ids
    )

    for intersection_road_id in list(incoming_connecting_intersection):
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            description=f"Connecting roads shall not be incoming roads.",
            level=IssueSeverity.ERROR,
            rule_uid=rule_uid,
        )

        for element in incoming_road_connection_map[intersection_road_id]:
            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(element),
                description="Connection with connecting road found as incoming road.",
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if a junction connecting roads are also incoming
    roads.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/6
    """
    logging.info("Executing junctions.connection.connect_road_no_incoming_road check")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="junctions.connection.connect_road_no_incoming_road",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_junctions_connection_connect_road_no_incoming_road(checker_data, rule_uid)
