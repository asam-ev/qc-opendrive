import logging

from dataclasses import dataclass
from typing import List

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models

from qc_opendrive.checks.semantic import semantic_constants


@dataclass
class SOffsetInfo:
    s_offset: float
    rule: str


RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if there is mixed content on access rules for
    the same sOffset on lanes.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/1
    """
    logging.info("Executing road.lane.access.no_mix_of_deny_or_allow check")

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.lane.access.no_mix_of_deny_or_allow",
    )

    lanes = utils.get_lanes(root=checker_data.input_file_xml_root)

    lane: etree._Element
    for lane in lanes:
        access_s_offset_info: List[SOffsetInfo] = []

        access: etree._Element
        for access in lane.iter("access"):
            access_attr = access.attrib

            if "rule" in access_attr:
                s_offset = float(access_attr["sOffset"])
                rule = access_attr["rule"]

                for s_offset_info in access_s_offset_info:
                    if (
                        abs(s_offset_info.s_offset - s_offset) <= 1e-6
                        and rule != s_offset_info.rule
                    ):
                        issue_id = checker_data.result.register_issue(
                            checker_bundle_name=constants.BUNDLE_NAME,
                            checker_id=semantic_constants.CHECKER_ID,
                            description="At a given s-position, either only deny or only allow values shall be given, not mixed.",
                            level=IssueSeverity.ERROR,
                            rule_uid=rule_uid,
                        )

                        path = checker_data.input_file_xml_root.getpath(access)

                        previous_rule = s_offset_info.rule
                        current_rule = access_attr["rule"]

                        checker_data.result.add_xml_location(
                            checker_bundle_name=constants.BUNDLE_NAME,
                            checker_id=semantic_constants.CHECKER_ID,
                            issue_id=issue_id,
                            xpath=path,
                            description=f"First encounter of {current_rule} having {previous_rule} before.",
                        )

                access_s_offset_info.append(
                    SOffsetInfo(
                        s_offset=float(access_attr["sOffset"]),
                        rule=access_attr["rule"],
                    )
                )
