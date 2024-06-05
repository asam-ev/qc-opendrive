import logging
from typing import Dict, Set

from lxml import etree

from qc_baselib import Configuration, Report, IssueSeverity

import constants
import checks.utils as utils

CHECKER_ID = "semantic_xodr"


def check_invalid_road_lane_access_no_mix_of_deny_or_allow(
    root: etree._ElementTree, config: Configuration, report: Report
) -> None:
    """
    Implements a rule to check if there is mixed content on access rules for
    the same sOffset on lanes.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/1
    """
    logging.info("Executing road.lane.access.no_mix_of_deny_or_allow check")

    lanes = utils.get_lanes(root=root)
    issue_count = 0
    lane: etree._Element
    for lane in lanes:
        access_s_offset_info: Dict[str, Set[str]] = {}

        access: etree._Element
        for access in lane.iter("access"):
            access_attr = access.attrib

            if access_attr["sOffset"] not in access_s_offset_info:
                access_s_offset_info[access_attr["sOffset"]] = set()
                access_s_offset_info[access_attr["sOffset"]].add(access_attr["rule"])
            elif (
                access_attr["rule"] not in access_s_offset_info[access_attr["sOffset"]]
            ):
                report.register_issue_to_checker(
                    bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_count,
                    description="At a given s-position, either only deny or only allow values shall be given, not mixed.",
                    level=IssueSeverity.ERROR,
                )
                path = root.getpath(access)
                previous_rule = list(access_s_offset_info[access_attr["sOffset"]])[0]
                current_rule = access_attr["rule"]
                report.add_xml_location_to_issue(
                    bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_count,
                    xpath=path,
                    description=f"First encounter of {current_rule} having {previous_rule} before.",
                )
                issue_count += 1

    logging.info(f"Issues found - {issue_count}")


def run_checks(config: Configuration, report: Report) -> None:
    logging.info("Executing semantic checks")

    root = etree.parse(config.get_config_param("XodrFile"))

    report.register_checker_to_bundle(
        bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description="Evaluates elements in the file and their semantics to guarantee they are in conformity with the standard.",
        summary="",
    )

    check_invalid_road_lane_access_no_mix_of_deny_or_allow(
        root=root, config=config, report=report
    )
