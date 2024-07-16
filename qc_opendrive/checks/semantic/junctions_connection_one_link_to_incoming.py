import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.8.0"


def _raise_lane_linkage_issue(
    checker_data: models.CheckerData, rule_uid: str, lane_link: etree._Element
):
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


def _is_rht_lane_direction_valid(
    to_lane_id: int,
    to_lane_direction: models.LaneDirection,
    from_lane_id: int,
    from_lane_direction: models.LaneDirection,
    predecessor_road_linkage: models.RoadLinkage,
    successor_road_linkage: models.RoadLinkage,
    connection_contact_point: models.ContactPoint,
) -> bool:
    """
    This function checks if RHT incoming traffic to a RHT junction has
    valid driving direction lane linkage.
    """
    # If both lanes have bidirectional traffic the lane can have incoming traffic
    # to the junction.
    if (
        to_lane_direction == models.LaneDirection.BOTH
        and from_lane_direction == models.LaneDirection.BOTH
    ):
        return True

    # If lanes have reversed driving direction than the expected is that they
    # should be treated exactly as the opposite side (identified by the id signal)
    if from_lane_direction == models.LaneDirection.REVERSED:
        from_lane_id *= -1

    if to_lane_direction == models.LaneDirection.REVERSED:
        to_lane_id *= -1

    if (
        connection_contact_point == models.ContactPoint.START
        and predecessor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to RIGHT lanes.
            if to_lane_id < 0:
                return False
        else:
            if predecessor_road_linkage.contact_point == models.ContactPoint.END:
                if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                    return False
                elif from_lane_id > 0 or to_lane_id > 0:
                    return False
            elif predecessor_road_linkage.contact_point == models.ContactPoint.START:
                if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                    return False
                elif from_lane_id < 0 or to_lane_id > 0:
                    return False

    if (
        connection_contact_point == models.ContactPoint.END
        and successor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to LEFT lanes.
            if to_lane_id > 0:
                return False
        else:
            if successor_road_linkage.contact_point == models.ContactPoint.END:
                if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                    return False
                elif from_lane_id > 0 or to_lane_id < 0:
                    return False
            elif successor_road_linkage.contact_point == models.ContactPoint.START:
                if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                    return False
                elif from_lane_id < 0 or to_lane_id < 0:
                    return False

    return True


def _is_lht_lane_direction_valid(
    to_lane_id: int,
    to_lane_direction: models.LaneDirection,
    from_lane_id: int,
    from_lane_direction: models.LaneDirection,
    predecessor_road_linkage: models.RoadLinkage,
    successor_road_linkage: models.RoadLinkage,
    connection_contact_point: models.ContactPoint,
) -> bool:
    """
    This function checks if LHT incoming traffic to a LHT junction has
    valid driving direction lane linkage.
    """
    # If both lanes have bidirectional traffic the lane can have incoming traffic
    # to the junction.
    if (
        to_lane_direction == models.LaneDirection.BOTH
        and from_lane_direction == models.LaneDirection.BOTH
    ):
        return True

    # If lanes have reversed driving direction than the expected is that they
    # should be treated exactly as the opposite side (identified by the id signal)
    if from_lane_direction == models.LaneDirection.REVERSED:
        from_lane_id *= -1

    if to_lane_direction == models.LaneDirection.REVERSED:
        to_lane_id *= -1

    if (
        connection_contact_point == models.ContactPoint.START
        and predecessor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to LEFT lanes.
            if to_lane_id < 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id < 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id < 0:
                return False

    if (
        connection_contact_point == models.ContactPoint.END
        and successor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to RIGHT lanes.
            if to_lane_id > 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id > 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id > 0:
                return False

    return True


def _is_lht_to_rht_lane_direction_valid(
    to_lane_id: int,
    to_lane_direction: models.LaneDirection,
    from_lane_id: int,
    from_lane_direction: models.LaneDirection,
    predecessor_road_linkage: models.RoadLinkage,
    successor_road_linkage: models.RoadLinkage,
    connection_contact_point: models.ContactPoint,
) -> bool:
    """
    This function checks if LHT mixed incoming traffic to a RHT junction has
    valid driving direction lane linkage.
    """
    # If both lanes have bidirectional traffic the lane can have incoming traffic
    # to the junction.
    if (
        to_lane_direction == models.LaneDirection.BOTH
        and from_lane_direction == models.LaneDirection.BOTH
    ):
        return True

    # If lanes have reversed driving direction than the expected is that they
    # should be treated exactly as the opposite side (identified by the id signal)
    if from_lane_direction == models.LaneDirection.REVERSED:
        from_lane_id *= -1

    if to_lane_direction == models.LaneDirection.REVERSED:
        to_lane_id *= -1

    if (
        connection_contact_point == models.ContactPoint.START
        and predecessor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to RIGHT lanes.
            if to_lane_id > 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id > 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id > 0:
                return False

    if (
        connection_contact_point == models.ContactPoint.END
        and successor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to LEFT lanes.
            if to_lane_id < 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id < 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id < 0:
                return False

    return True


def _is_rht_to_lht_lane_direction_valid(
    to_lane_id: int,
    to_lane_direction: models.LaneDirection,
    from_lane_id: int,
    from_lane_direction: models.LaneDirection,
    predecessor_road_linkage: models.RoadLinkage,
    successor_road_linkage: models.RoadLinkage,
    connection_contact_point: models.ContactPoint,
) -> bool:
    """
    This function checks if RHT mixed incoming traffic to a LHT junction has
    valid driving direction lane linkage.
    """
    # If both lanes have bidirectional traffic the lane can have incoming traffic
    # to the junction.
    if (
        to_lane_direction == models.LaneDirection.BOTH
        and from_lane_direction == models.LaneDirection.BOTH
    ):
        return True

    # If lanes have reversed driving direction than the expected is that they
    # should be treated exactly as the opposite side (identified by the id signal)
    if from_lane_direction == models.LaneDirection.REVERSED:
        from_lane_id *= -1

    if to_lane_direction == models.LaneDirection.REVERSED:
        to_lane_id *= -1

    if (
        connection_contact_point == models.ContactPoint.START
        and predecessor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to LEFT lanes.
            if to_lane_id < 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id < 0:
                return False
        elif predecessor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id < 0:
                return False

    if (
        connection_contact_point == models.ContactPoint.END
        and successor_road_linkage is not None
    ):
        if from_lane_direction == models.LaneDirection.BOTH:
            # If incoming lane has both directions it can only have the
            # connection to the incoming direction on junction.
            # For this case to RIGHT lanes.
            if to_lane_id > 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.END:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id > 0:
                return False
            elif from_lane_id > 0 or to_lane_id > 0:
                return False
        elif successor_road_linkage.contact_point == models.ContactPoint.START:
            if to_lane_direction == models.LaneDirection.BOTH and from_lane_id < 0:
                return False
            elif from_lane_id < 0 or to_lane_id > 0:
                return False

    return True


def _check_connection_lane_link_same_direction(
    checker_data: models.CheckerData,
    road_id_map: Dict[int, etree._ElementTree],
    connection: etree._Element,
    rule_uid: str,
) -> None:
    connection_contact_point = utils.get_contact_point_from_connection(connection)

    if connection_contact_point is None:
        return

    incoming_road_id = utils.get_incoming_road_id_from_connection(connection)
    connecting_road_id = utils.get_connecting_road_id_from_connection(connection)

    if connecting_road_id is None or incoming_road_id is None:
        return

    connecting_road = road_id_map.get(connecting_road_id)
    incoming_road = road_id_map.get(incoming_road_id)

    if connecting_road is None or incoming_road is None:
        return

    connecting_road_predecessor = utils.get_road_linkage(
        connecting_road, models.LinkageTag.PREDECESSOR
    )
    connecting_road_successor = utils.get_road_linkage(
        connecting_road, models.LinkageTag.SUCCESSOR
    )

    connection_traffic_hand = utils.get_traffic_hand_rule_from_road(connecting_road)
    incoming_traffic_hand = utils.get_traffic_hand_rule_from_road(incoming_road)
    lane_links = utils.get_lane_links_from_connection(connection)

    contacting_lane_sections = (
        utils.get_incoming_and_connection_contacting_lane_sections(
            connection, road_id_map
        )
    )

    if contacting_lane_sections is None:
        return

    for lane_link in lane_links:
        from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)
        to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

        if from_lane_id is None or to_lane_id is None:
            continue

        from_lane = utils.get_lane_from_lane_section(
            contacting_lane_sections.incoming, from_lane_id
        )
        to_lane = utils.get_lane_from_lane_section(
            contacting_lane_sections.connection, to_lane_id
        )

        if from_lane is None or to_lane is None:
            continue

        from_lane_direction = utils.get_lane_direction(from_lane)
        to_lane_direction = utils.get_lane_direction(to_lane)

        if from_lane_direction is None or to_lane_direction is None:
            continue

        if connection_traffic_hand == models.TrafficHandRule.RHT:
            if incoming_traffic_hand == models.TrafficHandRule.RHT:
                if not _is_rht_lane_direction_valid(
                    to_lane_id,
                    to_lane_direction,
                    from_lane_id,
                    from_lane_direction,
                    connecting_road_predecessor,
                    connecting_road_successor,
                    connection_contact_point,
                ):
                    _raise_lane_linkage_issue(checker_data, rule_uid, lane_link)
            else:
                if not _is_lht_to_rht_lane_direction_valid(
                    to_lane_id,
                    to_lane_direction,
                    from_lane_id,
                    from_lane_direction,
                    connecting_road_predecessor,
                    connecting_road_successor,
                    connection_contact_point,
                ):
                    _raise_lane_linkage_issue(checker_data, rule_uid, lane_link)

        elif connection_traffic_hand == models.TrafficHandRule.LHT:
            if incoming_traffic_hand == models.TrafficHandRule.LHT:
                if not _is_lht_lane_direction_valid(
                    to_lane_id,
                    to_lane_direction,
                    from_lane_id,
                    from_lane_direction,
                    connecting_road_predecessor,
                    connecting_road_successor,
                    connection_contact_point,
                ):
                    _raise_lane_linkage_issue(checker_data, rule_uid, lane_link)
            else:
                if not _is_rht_to_lht_lane_direction_valid(
                    to_lane_id,
                    to_lane_direction,
                    from_lane_id,
                    from_lane_direction,
                    connecting_road_predecessor,
                    connecting_road_successor,
                    connection_contact_point,
                ):
                    _raise_lane_linkage_issue(checker_data, rule_uid, lane_link)


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
