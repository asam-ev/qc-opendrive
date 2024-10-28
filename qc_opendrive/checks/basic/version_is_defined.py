# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from qc_baselib import IssueSeverity, StatusType
from qc_opendrive import constants
from qc_opendrive.checks.basic import (
    valid_xml_document,
    root_tag_is_opendrive,
    fileheader_is_present,
)
from qc_opendrive.base import utils, models

CHECKER_ID = "check_asam_xodr_xml_version_is_defined"
CHECKER_DESCRIPTION = "The FileHeader tag must have the attributes revMajor and revMinor and of type unsignedShort."
CHECKER_PRECONDITIONS = {
    valid_xml_document.CHECKER_ID,
    root_tag_is_opendrive.CHECKER_ID,
    fileheader_is_present.CHECKER_ID,
}
RULE_UID = "asam.net:xodr:1.0.0:xml.version_is_defined"


def is_unsigned_short(value: int) -> bool:
    """Helper function to check if a value is within the xsd:unsignedShort range (0-65535)."""
    num = utils.to_int(value)

    if num is None:
        return False
    else:
        return 0 <= num <= 65535


def check_rule(checker_data: models.CheckerData) -> bool:
    """
    The header tag must have the attributes revMajor and revMinor and of type unsignedShort.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/90
    """
    logging.info("Executing version_is_defined check")

    root = checker_data.input_file_xml_root.getroot()

    is_valid = True
    # Check if root contains a tag 'header'
    file_header_tag = root.find("header")

    if file_header_tag is None:
        logging.error("- No header found, cannot check version. Skipping...")

        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            status=StatusType.SKIPPED,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            CHECKER_ID,
            f"The xml file does not contains the 'header' tag.",
        )

        return True

    # Check if 'header' has the attributes 'revMajor' and 'revMinor'
    if (
        "revMajor" not in file_header_tag.attrib
        or "revMinor" not in file_header_tag.attrib
    ):
        logging.error("- 'header' tag does not have both 'revMajor' and 'revMinor'")
        is_valid = False

    if is_valid:
        # Check if 'attr1' and 'attr2' are xsd:unsignedShort (i.e., in the range 0-65535)
        rev_major = file_header_tag.attrib["revMajor"]
        rev_minor = file_header_tag.attrib["revMinor"]

        if not is_unsigned_short(rev_major) or not is_unsigned_short(rev_minor):
            logging.error(
                "- 'revMajor' and/or 'revMinor' are not xsd:unsignedShort (0-65535)"
            )
            is_valid = False

    if not is_valid:
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description="Issue flagging when revMajor revMinor attribute of header are missing or invalid",
            level=IssueSeverity.ERROR,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(file_header_tag),
            description=f"Header tag has invalid or missing version info",
        )
