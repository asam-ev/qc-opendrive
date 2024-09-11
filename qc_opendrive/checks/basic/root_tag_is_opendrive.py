import logging
from lxml import etree
from qc_baselib import IssueSeverity, Result
from qc_opendrive import constants
from qc_opendrive.checks.basic import basic_constants


def check_rule(tree: etree._ElementTree, result: Result) -> bool:
    """
    The root element of a valid XML document must be OpenDRIVE

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/88
    """
    logging.info("Executing root_tag_is_opendrive check")

    rule_uid = result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=basic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting="1.0.0",
        rule_full_name="xml.root_tag_is_opendrive",
    )

    root = tree.getroot()

    is_valid = False
    if root.tag == "OpenDRIVE":
        logging.info("- Root tag is 'OpenDRIVE'")
        is_valid = True
    else:
        logging.error("- Root tag is not 'OpenDRIVE'")
        is_valid = False

    if not is_valid:

        issue_id = result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=basic_constants.CHECKER_ID,
            description="Issue flagging when root tag is not OpenDRIVE",
            level=IssueSeverity.ERROR,
            rule_uid=rule_uid,
        )

        result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=basic_constants.CHECKER_ID,
            issue_id=issue_id,
            xpath=tree.getpath(root),
            description=f"Root is not OpenDRIVE",
        )

        return False

    return True
