import logging

from lxml import etree

from qc_baselib import Configuration, Result, StatusType

from qc_opendrive import constants
from qc_opendrive.base import utils, models

from qc_opendrive.checks.smoothness import (
    smoothness_constants,
    lane_smoothness_contact_point_no_gaps,
)


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing smoothness checks")

    root = etree.parse(config.get_config_param("InputFile"))

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        description="Evaluates elements in the file and their geometries to guarantee they are in conformity with the standard definition of smoothness.",
        summary="",
    )

    odr_schema_version = utils.get_standard_schema_version(root)

    rule_list = [
        lane_smoothness_contact_point_no_gaps.check_rule,
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
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=smoothness_constants.CHECKER_ID)}"
    )

    # TODO: Add logic to deal with error or to skip it
    result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        status=StatusType.COMPLETED,
    )
