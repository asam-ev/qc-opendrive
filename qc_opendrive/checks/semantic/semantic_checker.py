import logging

from lxml import etree

from qc_baselib import Configuration, Result

from qc_opendrive import constants

from qc_opendrive.checks.semantic import (
    semantic_constants,
    road_lane_level_true_one_side,
    road_lane_access_no_mix_of_deny_or_allow,
)


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing semantic checks")

    root = etree.parse(config.get_config_param("XodrFile"))

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description="Evaluates elements in the file and their semantics to guarantee they are in conformity with the standard.",
        summary="",
    )

    rules_list = [
        road_lane_level_true_one_side.check_rule,
        road_lane_access_no_mix_of_deny_or_allow.check_rule,
    ]

    for rule in rules_list:
        rule(root=root, config=config, result=result)

    logging.info(
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=semantic_constants.CHECKER_ID)}"
    )
