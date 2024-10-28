# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import importlib.resources
import logging

from dataclasses import dataclass

from typing import List

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


@dataclass
class SchemaError:
    message: str
    line: int
    column: int


def _get_schema_errors(
    xml_file: str, schema_file: str, schema_version: str
) -> List[SchemaError]:
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
                SchemaError(
                    message=error.message,
                    line=error.line,
                    column=error.column,
                )
            )
    else:  # use xmlschema to support XSD schema 1.1 -> OpenDRIVE 1.8 and higher
        schema = xmlschema.XMLSchema11(schema_file)
        # Iterate over all validation errors
        xml_doc = etree.parse(xml_file)
        for error in schema.iter_errors(xml_doc):
            errors.append(
                SchemaError(
                    message=error.reason,
                    line=error.sourceline,
                    column=0,
                )
            )

    return errors


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

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            CHECKER_ID,
            f"Cannot find the schema file for ASAM OpenDrive version {schema_version}.",
        )

        return

    xsd_file_path = str(
        importlib.resources.files("qc_opendrive.schema").joinpath(xsd_file)
    )
    errors = _get_schema_errors(
        checker_data.config.get_config_param("InputFile"), xsd_file_path, schema_version
    )

    for error in errors:
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description="Issue flagging when input file does not follow its version schema",
            level=IssueSeverity.ERROR,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_file_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            row=error.line,
            column=error.column,
            description=error.message,
        )
