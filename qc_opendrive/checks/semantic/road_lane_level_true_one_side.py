import logging

from typing import Union, List

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils
from qc_opendrive.checks.semantic import semantic_constants

RULE_SUPPORTED_SCHEMA_VERSIONS = set(["1.7.0", "1.8.0"])


def _check_true_level_on_side(
    root: etree._ElementTree,
    side_lanes: List[etree._Element],
    result: Result,
    rule_uid: str,
) -> None:
    """
    Check on a sorted list of lanes if any false level occurs after a true.
    The side_lanes must be sorted in the order from the center to the border of the road.
    The side_lanes must contain lanes from only one side, that is, all the lane ids must be positive, or all the lane ids must be negative.
    If the lane ids are positive, the lane should be in the ascending order.
    If the lane ids are negative, the lane should be in the descending order.
    """
    found_true_level = False

    for index, lane in enumerate(side_lanes):
        lane_attrib = lane.attrib

        if "level" in lane_attrib:

            lane_level = utils.xml_string_to_bool(lane_attrib["level"])

            if lane_level == True:
                found_true_level = True

            elif lane_level == False and found_true_level == True:
                # lane_level is False when previous lane_level was True before
                issue_id = result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    description="Lane level False encountered on same side after True set.",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                path = root.getpath(lane)

                result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=semantic_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=path,
                    description=f"Lane id {index} @level=False where previous lane id @level=True.",
                )


# Check lane level change in between lane sections true to false and false
# to true
def _check_level_change_between_lane_sections(
    current_lane_section: etree._ElementTree, previous_lane_section: etree._ElementTree
) -> None:
    # TODO: Implement warning for change in between lane sections
    return


def check_rule(
    root: etree._ElementTree, config: Configuration, result: Result, schema_version: str
) -> None:
    """
    Implements a rule to check if there is any @Level=False after true until
    the lane border.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/2
    """
    logging.info("Executing road.lane.level.true.one_side check")

    if schema_version not in RULE_SUPPORTED_SCHEMA_VERSIONS:
        logging.info(f"Schema version {schema_version} not supported. Skipping rule.")
        return

    rule_uid = result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting="1.8.0",
        rule_full_name="road.lane.level.true.one_side",
    )

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

        _check_true_level_on_side(root, sorted_left_lane, result, rule_uid)

        # sort by lane abs(id) to guarantee order while checking level
        # right ids goes monotonic decreasing from -1
        sorted_right_lane = sorted(
            right_lanes_list, key=lambda lane: abs(int(lane.attrib["id"]))
        )

        _check_true_level_on_side(root, sorted_right_lane, result, rule_uid)

        # check for lane level changing in between consecutive lane sections
        _check_level_change_between_lane_sections(
            current_lane_section=lane_section,
            previous_lane_section=previous_lane_section,
        )
        previous_lane_section = lane_section
