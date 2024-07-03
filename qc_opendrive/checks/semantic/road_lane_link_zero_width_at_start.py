import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"

FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
    checker_data: models.CheckerData,
    rule_uid: str,
    lane: etree._Element,
    issue_severity: IssueSeverity,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description=f" Lanes that have a width of zero at the beginning of the lane section shall have no predecessor element.",
        level=issue_severity,
        rule_uid=rule_uid,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(lane),
        description="Lane with width zero and predecessors.",
    )


def _raise_issue_based_on_lane_id(
    lane: etree._Element,
    lane_id: int,
    checker_data: models.CheckerData,
    rule_uid: str,
) -> None:
    if lane_id == 0:
        # Because of backward compatibility, this rule does
        # not apply to lane 0 (i.e. it is not allowed to have
        # a width (see Rule 77) but it might have a predecessor).
        # In this case the severity level should be changed
        # to "WARNING"
        _raise_issue(checker_data, rule_uid, lane, IssueSeverity.WARNING)
    else:
        _raise_issue(checker_data, rule_uid, lane, IssueSeverity.ERROR)


def _check_road_lane_link_zero_width_at_start(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
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
                            lane,
                            lane_id,
                            checker_data,
                            rule_uid,
                        )


def _check_incoming_road_junction_predecessor_lane_width_zero(
    checker_data: models.CheckerData,
    rule_uid: str,
    road: etree._Element,
    road_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
) -> None:
    predecessor_junction_id = utils.get_road_junction_linkage(
        road, models.LinkageTag.PREDECESSOR
    )

    if predecessor_junction_id is None:
        return

    predecessor_connections = utils.get_all_road_linkage_junction_connections(
        road_id,
        predecessor_junction_id,
        road_id_map,
        junction_id_map,
        models.LinkageTag.PREDECESSOR,
    )

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

            for connection in predecessor_connections:
                lane_links = utils.get_lane_links_from_connection(connection)

                for lane_link in lane_links:
                    from_lane_id = utils.get_from_attribute_from_lane_link(lane_link)

                    if from_lane_id is None:
                        continue

                    if from_lane_id == lane_id:
                        _raise_issue_based_on_lane_id(
                            lane,
                            lane_id,
                            checker_data,
                            rule_uid,
                        )


def _check_connecting_road_predecessor_lane_width_zero(
    checker_data: models.CheckerData,
    rule_uid: str,
    road: etree._Element,
    road_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
) -> None:
    road_junction_id = utils.get_road_junction_id(road)

    if road_junction_id is None:
        return

    junction = junction_id_map.get(road_junction_id)

    if junction is None:
        return

    connections = utils.get_connections_from_junction(junction)

    predecessor_connections = []
    for connection in connections:
        contact_point = utils.get_contact_point_from_connection(connection)
        if contact_point is not None and contact_point == models.ContactPoint.START:
            predecessor_connections.append(connection)

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

            for connection in predecessor_connections:
                lane_links = utils.get_lane_links_from_connection(connection)

                for lane_link in lane_links:
                    to_lane_id = utils.get_to_attribute_from_lane_link(lane_link)

                    if to_lane_id is None:
                        continue

                    if to_lane_id == lane_id:
                        _raise_issue_based_on_lane_id(
                            lane,
                            lane_id,
                            checker_data,
                            rule_uid,
                        )


def _check_junction_road_lane_link_zero_width_at_start(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road_id, road in road_id_map.items():
        if utils.road_belongs_to_junction(road):
            _check_connecting_road_predecessor_lane_width_zero(
                checker_data, rule_uid, road, road_id, road_id_map, junction_id_map
            )
        else:
            _check_incoming_road_junction_predecessor_lane_width_zero(
                checker_data, rule_uid, road, road_id, road_id_map, junction_id_map
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

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.lane.link.zero_width_at_start",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_road_lane_link_zero_width_at_start(checker_data, rule_uid)
    _check_junction_road_lane_link_zero_width_at_start(checker_data, rule_uid)
