import logging

from lxml import etree

from qc_baselib import Configuration, Result, StatusType

from qc_opendrive import constants
from qc_opendrive.checks import utils, models

from qc_opendrive.checks.geometry import (
    geometry_constants,
    road_geometry_param_poly3_length_match,
)


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing geometry checks")

    root = etree.parse(config.get_config_param("XodrFile"))

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=geometry_constants.CHECKER_ID,
        description="Evaluates elements in the file and their geometrys to guarantee they are in conformity with the standard.",
        summary="",
    )

    odr_schema_version = utils.get_standard_schema_version(root)

    rule_list = [
        road_geometry_param_poly3_length_match.check_rule,
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
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=geometry_constants.CHECKER_ID)}"
    )

    # TODO: Add logic to deal with error or to skip it
    result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=geometry_constants.CHECKER_ID,
        status=StatusType.COMPLETED,
    )
