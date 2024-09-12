import logging
from lxml import etree
from qc_baselib import IssueSeverity, Result
from qc_opendrive import constants
from qc_opendrive.checks.basic import basic_constants


def is_unsigned_short(value: int) -> bool:
    """Helper function to check if a value is within the xsd:unsignedShort range (0-65535)."""
    try:
        num = int(value)
        return 0 <= num <= 65535
    except ValueError:
        return False


def check_rule(tree: etree._ElementTree, result: Result) -> bool:
    """
    The header tag must have the attributes revMajor and revMinor and of type unsignedShort.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/90
    """
    logging.info("Executing version_is_defined check")

    rule_uid = result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=basic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting="1.0.0",
        rule_full_name="xml.version_is_defined",
    )

    root = tree.getroot()

    is_valid = True
    # Check if root contains a tag 'header'
    file_header_tag = root.find("header")

    if file_header_tag is None:
        logging.error("- No header found, cannot check version. Skipping...")
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

        issue_id = result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=basic_constants.CHECKER_ID,
            description="Issue flagging when revMajor revMinor attribute of header are missing or invalid",
            level=IssueSeverity.ERROR,
            rule_uid=rule_uid,
        )

        result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=basic_constants.CHECKER_ID,
            issue_id=issue_id,
            xpath=tree.getpath(file_header_tag),
            description=f"header tag has invalid or missing version info",
        )

        return False
    else:
        logging.info(f"- header version correctly defined: {rev_major}.{rev_minor}")
    return True
