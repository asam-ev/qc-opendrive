# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from qc_baselib import IssueSeverity, StatusType
from qc_opendrive import constants
from qc_opendrive.checks.basic import valid_xml_document, root_tag_is_opendrive
from qc_opendrive.base import models

CHECKER_ID = "check_asam_xodr_xml_fileheader_is_present"
CHECKER_DESCRIPTION = "Below the root element a tag with FileHeader must be defined."
CHECKER_PRECONDITIONS = {
    valid_xml_document.CHECKER_ID,
    root_tag_is_opendrive.CHECKER_ID,
}
RULE_UID = "asam.net:xodr:1.0.0:xml.fileheader_is_present"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Below the root element a tag with FileHeader must be defined

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/89
    """
    logging.info("Executing fileheader_is_present check")

    root = checker_data.input_file_xml_root.getroot()

    is_valid = False
    # Check if root contains a tag 'header'
    file_header_tag = root.find("header")
    if file_header_tag is not None:
        logging.info("- Root tag contains header -> OK")
        is_valid = True
    else:
        logging.error("- header not found under root element")
        is_valid = False

    if not is_valid:
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description="Issue flagging when no header is found under root element",
            level=IssueSeverity.ERROR,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(root),
            description=f"No child element header",
        )
