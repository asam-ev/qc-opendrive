import logging

from dataclasses import dataclass
from typing import Union, Dict, Set, List

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils

CHECKER_ID = "semantic_xodr"


@dataclass
class SOffsetInfo:
    s_offset: float
    rules: Set


def _get_s_offset_info(
    access_s_offset_info: List[SOffsetInfo], s_offset: float
) -> Union[SOffsetInfo, None]:

    return next(
        (
            s_offset_info
            for s_offset_info in access_s_offset_info
            if abs(s_offset_info.s_offset - s_offset) <= 1e-6
        ),
        None,
    )


# TODO: Add logic to handle that this rule only applied to xord 1.7 and 1.8
def check_invalid_road_lane_access_no_mix_of_deny_or_allow(
    root: etree._ElementTree, config: Configuration, result: Result
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
        access_s_offset_info: List[SOffsetInfo] = []

        access: etree._Element
        for access in lane.iter("access"):
            access_attr = access.attrib

            if "rule" in access_attr:
                s_off_set_info = _get_s_offset_info(
                    access_s_offset_info=access_s_offset_info,
                    s_offset=float(access_attr["sOffset"]),
                )

                if s_off_set_info is None:
                    access_s_offset_info.append(
                        SOffsetInfo(
                            s_offset=float(access_attr["sOffset"]),
                            rules=set([access_attr["rule"]]),
                        )
                    )
                elif access_attr["rule"] not in s_off_set_info.rules:
                    result.register_issue(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=CHECKER_ID,
                        issue_id=issue_count,
                        description="At a given s-position, either only deny or only allow values shall be given, not mixed.",
                        level=IssueSeverity.ERROR,
                    )
                    path = root.getpath(access)
                    previous_rule = list(s_off_set_info.rules)[0]
                    current_rule = access_attr["rule"]
                    result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=CHECKER_ID,
                        issue_id=issue_count,
                        xpath=path,
                        description=f"First encounter of {current_rule} having {previous_rule} before.",
                    )
                    issue_count += 1

    logging.info(f"Issues found - {issue_count}")


def run_checks(config: Configuration, result: Result) -> None:
    logging.info("Executing semantic checks")

    root = etree.parse(config.get_config_param("XodrFile"))

    result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description="Evaluates elements in the file and their semantics to guarantee they are in conformity with the standard.",
        summary="",
    )

    check_invalid_road_lane_access_no_mix_of_deny_or_allow(
        root=root, config=config, result=result
    )
