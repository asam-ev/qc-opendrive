# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from qc_baselib import IssueSeverity, StatusType
from qc_opendrive import constants
from qc_opendrive.checks.basic import valid_xml_document
from qc_opendrive.base import models

CHECKER_ID = "check_asam_xodr_xml_root_tag_is_opendrive"
CHECKER_DESCRIPTION = "The root element of a valid XML document must be OpenSCENARIO."
CHECKER_PRECONDITIONS = {valid_xml_document.CHECKER_ID}
RULE_UID = "asam.net:xodr:1.0.0:xml.root_tag_is_opendrive"


def check_rule(checker_data: models.CheckerData) -> bool:
    """
    The root element of a valid XML document must be OpenDRIVE

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/88
    """
    logging.info("Executing root_tag_is_opendrive check")

    root = checker_data.input_file_xml_root.getroot()

    is_valid = False
    if root.tag == "OpenDRIVE":
        logging.info("- Root tag is 'OpenDRIVE'")
        is_valid = True
    else:
        logging.error("- Root tag is not 'OpenDRIVE'")
        is_valid = False

    if not is_valid:
        issue_id = checker_data.result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            description="Issue flagging when root tag is not OpenDRIVE",
            level=IssueSeverity.ERROR,
            rule_uid=RULE_UID,
        )

        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(root),
            description=f"Root is not OpenDRIVE",
        )
