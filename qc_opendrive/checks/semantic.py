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
    rule: str


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
                        issue_id = result.register_issue(
                            checker_bundle_name=constants.BUNDLE_NAME,
                            checker_id=CHECKER_ID,
                            description="At a given s-position, either only deny or only allow values shall be given, not mixed.",
                            level=IssueSeverity.ERROR,
                        )

                        path = root.getpath(access)

                        previous_rule = s_offset_info.rule
                        current_rule = access_attr["rule"]

                        result.add_xml_location(
                            checker_bundle_name=constants.BUNDLE_NAME,
                            checker_id=CHECKER_ID,
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


# check on a sorted by id list of lanes if any false level occurs after a true
def _check_true_level_on_side(
    root: etree._ElementTree, side_lanes: List[etree._Element], result: Result
) -> None:
    first_level_true_index = len(side_lanes)

    for index, lane in enumerate(side_lanes):
        lane_attrib = lane.attrib

        if "level" in lane_attrib:

            lane_level = utils.xml_string_to_bool(lane_attrib["level"])

            if lane_level == True and index < first_level_true_index:
                first_level_true_index = index
            elif lane_level == False and index > first_level_true_index:
                issue_id = result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    description="Lane level False encountered on same side after True set.",
                    level=IssueSeverity.ERROR,
                )

                path = root.getpath(lane)

                result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_id,
                    xpath=path,
                    description=f"Lane id {index} @level=False where lane id {first_level_true_index} @level=True.",
                )


# Check lane level change in between lane sections true to false and false
# to true
def _check_level_change_between_lane_sections(
    current_lane_section: etree._ElementTree, previous_lane_section: etree._ElementTree
) -> None:
    # TODO: Implement warning for change in between lane sections
    return


def check_invalid_road_lane_level_true_one_side(
    root: etree._ElementTree, config: Configuration, result: Result
) -> None:
    """
    Implements a rule to check if there is any @Level=False after true until
    the lane border.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/2
    """
    logging.info("Executing road.lane.level.true.one_side check")

    lane_sections = utils.get_lane_sections(root)

    # Sort by s attribute to guarantee order
    sorted_lane_sections = sorted(
        lane_sections, key=lambda section: float(section.attrib["s"])
    )

    previous_lane_section: Union[etree._ElementTree, None] = None

    for lane_section in sorted_lane_sections:
        left_lane = lane_section.find("left")
        if left_lane is not None:
            left_lanes_list = left_lane.findall("lane")
        else:
            left_lanes_list = []

        right_lane = lane_section.find("right")
        if right_lane is not None:
            right_lanes_list = right_lane.findall("lane")
        else:
            right_lanes_list = []

        # sort by lane id to guarantee order while checking level
        # right ids goes monotonic increasing from 1
        sorted_left_lane = sorted(
            left_lanes_list, key=lambda lane: int(lane.attrib["id"])
        )

        _check_true_level_on_side(root, sorted_left_lane, result)

        # sort by lane abs(id) to guarantee order while checking level
        # right ids goes monotonic decreasing from -1
        sorted_right_lane = sorted(
            right_lanes_list, key=lambda lane: abs(int(lane.attrib["id"]))
        )

        _check_true_level_on_side(root, sorted_right_lane, result)

        # check for lane level changing in between consecutive lane sections
        _check_level_change_between_lane_sections(
            current_lane_section=lane_section,
            previous_lane_section=previous_lane_section,
        )
        previous_lane_section = lane_section


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

    check_invalid_road_lane_level_true_one_side(root=root, config=config, result=result)

    logging.info(
        f"Issues found - {result.get_checker_issue_count(checker_bundle_name=constants.BUNDLE_NAME, checker_id=CHECKER_ID)}"
    )
