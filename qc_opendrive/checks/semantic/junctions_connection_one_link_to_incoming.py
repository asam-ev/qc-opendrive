import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.8.0"


def _check_connection_lane_link_same_direction(
    checker_data: models.CheckerData,
    road_id_map: Dict[int, etree._ElementTree],
    connection: etree._Element,
    rule_uid: str,
) -> None:
    contact_point = utils.get_contact_point_from_connection(connection)

    if contact_point is None:
        return

    incoming_road_id = utils.get_incoming_road_id_from_connection(connection)
    connecting_road_id = utils.get_connecting_road_id_from_connection(connection)

    if incoming_road_id is None or connecting_road_id is None:
        return

    incoming_road = road_id_map[incoming_road_id]
    connecting_road = road_id_map[connecting_road_id]

    # Get connecting road target lane section based on connection contact point
    connection_lane_section = None
    if contact_point == models.ContactPoint.START:
        connection_lane_section = utils.get_first_lane_section(connecting_road)
    elif contact_point == models.ContactPoint.END:
        connection_lane_section = utils.get_last_lane_section(connecting_road)
    else:
        return

    # The linkage from the incoming to the connecting road is defined in the
    # connecting road linkage, there is the information if the connecting
    # road connects to the end or start of the incoming road.

    # Check if predecessor is the linkage, otherwise tries with the successor
    incoming_linkage = utils.get_road_linkage(
        connecting_road, models.LinkageTag.PREDECESSOR
    )
    if incoming_linkage is None or (
        incoming_linkage is not None and incoming_linkage.id != incoming_road_id
    ):
        incoming_linkage = utils.get_road_linkage(
            connecting_road, models.LinkageTag.SUCCESSOR
        )

    if incoming_linkage is None or (
        incoming_linkage is not None and incoming_linkage.id != incoming_road_id
    ):
        return

    incoming_lane_section = None
    if incoming_linkage.contact_point == models.ContactPoint.START:
        incoming_lane_section = utils.get_first_lane_section(incoming_road)
    elif incoming_linkage.contact_point == models.ContactPoint.END:
        incoming_lane_section = utils.get_last_lane_section(incoming_road)
    else:
        return

    lane_links = utils.get_lane_links_from_connection(connection)

    if connection_lane_section is None or incoming_lane_section is None:
        return

    for lane_link in lane_links:
        from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
        to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

        from_lane = utils.get_lane_from_lane_section(
            incoming_lane_section, from_lane_id
        )
        to_lane = utils.get_lane_from_lane_section(connection_lane_section, to_lane_id)

        if from_lane is None or to_lane is None:
            # raise one issue if a lane link is found in the opposite direction
            # of the connecting road
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                description=f"A connecting road shall only have the <laneLink> element for that direction.",
                level=IssueSeverity.ERROR,
                rule_uid=rule_uid,
            )
            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=semantic_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(lane_link),
                description=f"Lane link in opposite direction.",
            )


def _check_junctions_connection_one_link_to_incoming(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    connection_road_link_map: Dict[int, Dict[int, List[etree._Element]]] = {}

    for junction in junctions:
        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            incoming_road_id = utils.get_incoming_road_id_from_connection(connection)
            connecting_road_id = utils.get_connecting_road_id_from_connection(
                connection
            )

            if incoming_road_id not in connection_road_link_map:
                connection_road_link_map[incoming_road_id] = {}
            if connecting_road_id not in connection_road_link_map[incoming_road_id]:
                connection_road_link_map[incoming_road_id][connecting_road_id] = []

            connection_road_link_map[incoming_road_id][connecting_road_id].append(
                connection
            )

            _check_connection_lane_link_same_direction(
                checker_data, road_id_map, connection, rule_uid
            )

    for incoming_road_id, connecting_road_map in connection_road_link_map.items():
        for connecting_road_id, connections in connecting_road_map.items():
            if len(connections) > 1:
                # raise one issue if the pair (incoming_road_id, connecting_road_id)
                # appears in more than one connection.
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description=f"Connecting road {connecting_road_id} shall be represented by at most one <connection> element per incoming road id.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )
                for connection in connections:
                    checker_data.result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=semantic_constants.CHECKER_ID,
                        issue_id=issue_id,
                        xpath=checker_data.input_file_xml_root.getpath(connection),
                        description=f"Connection with reused (incoming_road_id, connecting_road_id) = ({incoming_road_id}, {connecting_road_id}) pair.",
                    )

    return


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming

    Description: Each connecting road shall be associated with at most one
    <connection> element per incoming road. A connecting road shall only have
    the <laneLink> element for that direction.

    Severity: ERROR

    Version range: [1.8.0, )

    Remark:
        None

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/10
    """
    logging.info("Executing junctions.connection.one_link_to_incoming check")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="junctions.connection.one_link_to_incoming",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_junctions_connection_one_link_to_incoming(checker_data, rule_uid)
