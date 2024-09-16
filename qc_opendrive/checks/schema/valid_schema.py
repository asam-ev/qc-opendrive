import importlib.resources
import logging

from typing import List, Tuple

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.schema import schema_files
from qc_opendrive.base import models, utils

import xmlschema
from lxml import etree

from qc_opendrive.checks.basic import (
    valid_xml_document,
    root_tag_is_opendrive,
    fileheader_is_present,
    version_is_defined,
)

CHECKER_ID = "check_asam_xodr_xml_valid_schema"
CHECKER_DESCRIPTION = "Input xml file must be valid according to the schema."
CHECKER_PRECONDITIONS = {
    valid_xml_document.CHECKER_ID,
    root_tag_is_opendrive.CHECKER_ID,
    fileheader_is_present.CHECKER_ID,
    version_is_defined.CHECKER_ID,
}
RULE_UID = "asam.net:xodr:1.0.0:xml.valid_schema"


def find_xpath_from_position(xml_tree, target_line, target_column):

    # Function to build XPath from the element
    def build_xpath(element):
        path = []
        while element is not None:
            siblings = list(element.itersiblings(preceding=True))
            index = len(siblings) + 1
            path.insert(0, f"{element.tag}[{index}]")
            element = element.getparent()
        return "/" + "/".join(path)

    # Find element by searching for position
    def find_element_by_position(element):
        if hasattr(element, "sourceline") and element.sourceline == target_line:
            # Rough estimation of column position
            # 'position' attribute might not always be available, so this is approximate
            if hasattr(element, "position") and element.position[1] == target_column:
                return element
        for child in element:
            found = find_element_by_position(child)
            if found:
                return found
        return None

    # Start from the root element
    root = xml_tree.getroot()
    element = find_element_by_position(root)

    # If element is found, build its XPath
    if element is not None:
        return build_xpath(element)
    else:
        return "Element not found"


def _is_schema_compliant(
    xml_file: str, schema_file: str, schema_version: str
) -> tuple[bool, List[Tuple]]:
    """Check if input xml tree  is valid against the input schema file (.xsd)

    Args:
        xml_file (etree._ElementTree): XML tree to test
        schema_file (str): XSD file path containing the schema for the validation

    Returns:
        bool: True if file pointed by xml_file is valid w.r.t. input schema file. False otherwise
    """

    split_result = schema_version.split(".")
    major = utils.to_int(split_result[0])
    minor = utils.to_int(split_result[1])
    errors = []

    if major is None or minor is None:
        return False, errors

    # use LXML for XSD 1.0 with better error level -> OpenDRIVE 1.7 and lower
    if major <= 1 and minor <= 7:
        schema = etree.XMLSchema(etree.parse(schema_file))
        xml_tree = etree.parse(xml_file)
        schema.validate(xml_tree)
        for error in schema.error_log:
            errors.append(
                (
                    find_xpath_from_position(xml_tree, error.line, error.column),
                    error.message,
                )
            )
    else:  # use xmlschema to support XSD schema 1.1 -> OpenDRIVE 1.8 and higher
        schema = xmlschema.XMLSchema11(schema_file)
        # Iterate over all validation errors
        for error in schema.iter_errors(xml_file):
            errors.append((error.path, error.message))

    # Return True and None if there are no errors, otherwise False and the list of errors
    if not errors:
        logging.info("- XML is valid.")
        return True, None
    else:
        logging.error("- XML is invalid!")
        for error in errors:
            logging.error(f"- Error: {error[1]}")
            logging.error(f"- Path: {error[0]}")

        return False, errors


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if input file is valid according to OpenDRIVE schema

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/86
    """
    logging.info("Executing valid_schema check")

    schema_version = checker_data.schema_version

    xsd_file = schema_files.SCHEMA_FILES.get(schema_version)

    if xsd_file is None:
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            status=StatusType.SKIPPED,
        )

        return

    xsd_file_path = str(
        importlib.resources.files("qc_opendrive.schema").joinpath(xsd_file)
    )
    schema_compliant, errors = _is_schema_compliant(
        checker_data.config.get_config_param("InputFile"), xsd_file_path, schema_version
    )

    if not schema_compliant:

        for error in errors:
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=CHECKER_ID,
                description="Issue flagging when input file does not follow its version schema",
                level=IssueSeverity.ERROR,
                rule_uid=RULE_UID,
            )
            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=CHECKER_ID,
                issue_id=issue_id,
                xpath=error[0],
                description=error[1],
            )
