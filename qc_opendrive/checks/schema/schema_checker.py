import logging

from lxml import etree

from qc_baselib import Configuration, Result, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.schema import schema_files

from qc_opendrive.checks.schema import (
    schema_constants,
    valid_schema,
)


def skip_checks(result: Result) -> None:

    if schema_constants.CHECKER_ID not in result.get_checker_ids(constants.BUNDLE_NAME):
        result.register_checker(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=schema_constants.CHECKER_ID,
            description="Check if xml properties of input file are properly set",
            summary="",
        )

    logging.error(
        f"Invalid xml input file. Checker {schema_constants.CHECKER_ID} skipped"
    )
    result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=schema_constants.CHECKER_ID,
        status=StatusType.SKIPPED,
    )


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing schema checks")

    root = utils.get_root_without_default_namespace(
        config.get_config_param("InputFile")
    )
    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=schema_constants.CHECKER_ID,
        description="Check if xml properties of input file are properly set",
        summary="",
    )
    odr_schema_version = utils.get_standard_schema_version(root)

    checker_data = models.CheckerData(
        input_file_xml_root=root,
        config=config,
        result=result,
        schema_version=odr_schema_version,
    )
    if checker_data.schema_version not in schema_files.SCHEMA_FILES:

        logging.error(
            f"Version {checker_data.schema_version} unsupported. Checker {schema_constants.CHECKER_ID} skipped"
        )
        result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=schema_constants.CHECKER_ID,
            status=StatusType.SKIPPED,
        )
        return

    rule_list = [valid_schema.check_rule]

    for rule in rule_list:
        rule(checker_data=checker_data)

    logging.info(
        f"Issues found - {checker_data.result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=schema_constants.CHECKER_ID)}"
    )

    # TODO: Add logic to deal with error or to skip it
    checker_data.result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=schema_constants.CHECKER_ID,
        status=StatusType.COMPLETED,
    )
