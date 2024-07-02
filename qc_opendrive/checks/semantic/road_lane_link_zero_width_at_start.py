import logging

from typing import Dict, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"

FLOAT_COMPARISON_THRESHOLD = 1e-3


def _check_road_lane_link_zero_width_at_start(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        lane_sections = utils.get_lane_sections(road)

        for section in lane_sections:
            lanes = utils.get_left_and_right_lanes_from_lane_section(section)

            for lane in lanes:
                if utils.evaluate_lane_width(lane, 0.0) < FLOAT_COMPARISON_THRESHOLD:
                    # This rule only evaluate explicit predecessor.
                    # Other rules verify if any implicit predecessor was not
                    # properly registered.
                    predecessor_lane_ids = utils.get_predecessor_lane_ids(lane)

                    if len(predecessor_lane_ids) > 0:
                        lane_id = utils.get_lane_id(lane)
                        if lane_id == 0:
                            print("warning")
                        else:
                            print("error")


def _check_junction_road_lane_link_zero_width_at_start(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)
    junction_id_map = utils.get_junction_id_map(checker_data.input_file_xml_root)

    for road in roads:
        # Connecting roads should not have road linkage to other junctions, it
        # is checked by other rules.
        if utils.road_belongs_to_junction(road):
            continue

        predecessor_junction_id = utils.get_road_junction_linkage(
            road, models.LinkageTag.PREDECESSOR
        )

        if predecessor_junction_id is None:
            continue

        predecessor_junction = junction_id_map[junction_id_map]
        connections = utils.get_connections_from_junction(predecessor_junction)

        first_lane_section = utils.get_first_lane_section(road)
        lanes = utils.get_left_and_right_lanes_from_lane_section(first_lane_section)

        for lane in lanes:
            if utils.evaluate_lane_width(lane, 0.0) < FLOAT_COMPARISON_THRESHOLD:
                lane_id = utils.get_lane_id(lane)
                if lane_id is None:
                    continue

                for connection in connections:
                    lane_links = utils.get_lane_links_from_connection(connection)

                    for lane_link in lane_links:
                        from_lane_id = utils.get_from_attribute_from_lane_link(
                            lane_link
                        )

                        if from_lane_id is None:
                            continue

                        if from_lane_id == lane_id:
                            print("error - junction")


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
