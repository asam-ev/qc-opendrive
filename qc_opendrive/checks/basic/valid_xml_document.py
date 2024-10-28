# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from lxml import etree
from qc_baselib import IssueSeverity
from qc_opendrive import constants
from qc_opendrive.base import models

CHECKER_ID = "check_asam_xodr_xml_valid_xml_document"
CHECKER_DESCRIPTION = "The input file must be a valid XML document."
CHECKER_PRECONDITIONS = set()
RULE_UID = "asam.net:xodr:1.0.0:xml.valid_xml_document"


def _is_xml_doc(file_path: str) -> tuple[bool, tuple[int, int]]:
    try:
        with open(file_path, "rb") as file:
            xml_content = file.read()
            etree.fromstring(xml_content)
            logging.info("- It is an xml document.")
        return True, None
    except etree.XMLSyntaxError as e:
        logging.error(f"- Error: {e}")
        logging.error(f"- Error occurred at line {e.lineno}, column {e.offset}")
        return False, (e.lineno, e.offset)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if input file is a valid xml document

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/88
    """
    logging.info("Executing valid_xml_document check")

    is_valid, error_location = _is_xml_doc(checker_data.xml_file_path)

    if not is_valid:
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description="The input file is not a valid xml document.",
            level=IssueSeverity.ERROR,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_file_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            row=error_location[0],
            column=error_location[1],
            description=f"Invalid xml file.",
        )
