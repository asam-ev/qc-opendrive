import logging
import os

from lxml import etree

from qc_baselib import Configuration, Result, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils

from qc_opendrive.checks.basic import (
    basic_constants,
    valid_xml_document,
    root_tag_is_opendrive,
    fileheader_is_present,
    version_is_defined,
)


def run_checks(config: Configuration, result: Result) -> bool:
    logging.info("Executing basic checks")

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=basic_constants.CHECKER_ID,
        description="Check if basic properties of input file are properly set",
        summary="",
    )

    xml_file_path = config.get_config_param("InputFile")

    is_xml = valid_xml_document.check_rule(xml_file_path, result)
    root = None
    checker_data = None

    basic_rule_list = [
        root_tag_is_opendrive.check_rule,
        fileheader_is_present.check_rule,
        version_is_defined.check_rule,
    ]

    validation_result = is_xml
    if validation_result:
        root = utils.get_root_without_default_namespace(xml_file_path)

        for rule in basic_rule_list:
            validation_result = validation_result and rule(root, result)
            if not validation_result:
                break

    if not validation_result:
        logging.warning(
            "There are problems with input file. Error found in basic rules!"
        )
    else:
        logging.info("Basic rules check successfull. Input file is valid")

    logging.info(
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=basic_constants.CHECKER_ID)}"
    )

    # TODO: Add logic to deal with error or to skip it
    result.set_checker_status(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=basic_constants.CHECKER_ID,
        status=StatusType.COMPLETED,
    )

    return validation_result
