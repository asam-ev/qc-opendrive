import logging

from lxml import etree

from qc_baselib import Configuration, Result, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils

from qc_opendrive.checks.semantic import (
    semantic_constants,
    road_lane_level_true_one_side,
    road_lane_access_no_mix_of_deny_or_allow,
    road_lane_link_lanes_across_lane_sections,
    road_linkage_is_junction_needed,
    road_lane_link_zero_width_at_start,
    road_lane_link_zero_width_at_end,
    road_lane_link_new_lane_appear,
    junctions_connection_connect_road_no_incoming_road,
    junctions_connection_one_connection_element,
    junctions_connection_one_link_to_incoming,
    junctions_connection_start_along_linkage,
    junctions_connection_end_opposite_linkage,
)


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing semantic checks")

    root = utils.get_root(config.get_config_param("InputFile"))

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description="Evaluates elements in the file and their semantics to guarantee they are in conformity with the standard.",
        summary="",
    )

    odr_schema_version = utils.get_standard_schema_version(root)

    rule_list = [
        road_lane_level_true_one_side.check_rule,
        road_lane_access_no_mix_of_deny_or_allow.check_rule,
        road_lane_link_lanes_across_lane_sections.check_rule,
        road_linkage_is_junction_needed.check_rule,
        road_lane_link_zero_width_at_start.check_rule,
        road_lane_link_zero_width_at_end.check_rule,
        road_lane_link_new_lane_appear.check_rule,
        junctions_connection_connect_road_no_incoming_road.check_rule,
        junctions_connection_one_connection_element.check_rule,
        junctions_connection_one_link_to_incoming.check_rule,
        junctions_connection_start_along_linkage.check_rule,
        junctions_connection_end_opposite_linkage.check_rule,
    ]

    checker_data = models.CheckerData(
        input_file_xml_root=root,
        config=config,
        result=result,
        schema_version=odr_schema_version,
    )

    for rule in rule_list:
        rule(checker_data=checker_data)

    logging.info(
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=semantic_constants.CHECKER_ID)}"
    )

    # TODO: Add logic to deal with error or to skip it
    result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        status=StatusType.COMPLETED,
    )
