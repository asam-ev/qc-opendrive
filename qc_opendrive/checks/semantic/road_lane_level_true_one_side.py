import logging

from typing import Union, List, Dict, Set
from enum import Enum

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
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


class LinkageTag(str, Enum):
    PREDECESSOR = "predecessor"
    SUCCESSOR = "successor"


def _get_lane_level(lanes: List[etree._Element], lane_id: int) -> Union[str, None]:
    return next(
        (lane.attrib["level"] for lane in lanes if int(lane.attrib["id"]) == lane_id),
        None,
    )


def _get_linkage_level_warnings(
    root: etree._ElementTree,
    current_lanes: List[etree._Element],
    target_lanes: List[etree._Element],
    linkage_tag: LinkageTag,
):
    warnings: Set[str] = set()

    for lane in current_lanes:
        lane_id = int(lane.attrib["id"])
        lane_level = lane.attrib["level"]

        links: Union[None, List[etree._Element]] = lane.findall("link")
        for link in links:
            linkages: List[etree._Element] = link.findall(linkage_tag)

            for linkage in linkages:
                linkage_id = int(linkage.attrib["id"])
                linkage_level = _get_lane_level(target_lanes, linkage_id)

                if linkage_level is not None and linkage_level != lane_level:
                    warnings.add(root.getpath(lane))

    return warnings


def _check_level_change_between_lane_sections(
    root: etree._ElementTree,
    current_lanes: List[etree._Element],
    previous_lanes: List[etree._Element],
    result: Result,
    rule_uid: str,
) -> None:
    """
    Check two consecutive lane section from a road if a false level occurs
    after a true consecutively.

    The predecessor/successor should be pointing to a valid lane id, otherwise
    it will be ignored.

    If lanes are linked twice by both predecessor and successor, the
    function will register the issue twice, one for each linkage.
    """

    predecessor_warnings = _get_linkage_level_warnings(
        root=root,
        current_lanes=current_lanes,
        target_lanes=previous_lanes,
        linkage_tag=LinkageTag.PREDECESSOR,
    )
    successor_warnings = _get_linkage_level_warnings(
        root=root,
        current_lanes=previous_lanes,
        target_lanes=current_lanes,
        linkage_tag=LinkageTag.SUCCESSOR,
    )

    warnings = predecessor_warnings | successor_warnings
    warnings = sorted(list(warnings))

    for warning in warnings:
        issue_id = result.register_issue(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            description="",
            level=IssueSeverity.WARNING,
            rule_uid=rule_uid,
        )
        result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            issue_id=issue_id,
            xpath=warning,
            description="",
        )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if there is any @Level=False after true until
    the lane border.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/2
    """
    logging.info("Executing road.lane.level.true.one_side check")

    if checker_data.schema_version not in RULE_SUPPORTED_SCHEMA_VERSIONS:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=checker_data.schema_version,
        rule_full_name="road.lane.level.true.one_side",
    )

    roads = utils.get_roads(checker_data.input_file_xml_root)

    road_previous_left_lane: List[etree._Element] = []
    road_previous_right_lane: List[etree._Element] = []

    for road in roads:
        lane_sections = utils.get_lane_sections(road)

        # Sort by s attribute to guarantee order
        sorted_lane_sections = sorted(
            lane_sections, key=lambda section: float(section.attrib["s"])
        )

        previous_left_lane: List[etree._Element] = []
        previous_right_lane: List[etree._Element] = []

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

            _check_true_level_on_side(
                checker_data.input_file_xml_root,
                sorted_left_lane,
                checker_data.result,
                rule_uid,
            )

            # sort by lane abs(id) to guarantee order while checking level
            # right ids goes monotonic decreasing from -1
            sorted_right_lane = sorted(
                right_lanes_list, key=lambda lane: abs(int(lane.attrib["id"]))
            )

            _check_true_level_on_side(
                checker_data.input_file_xml_root,
                sorted_right_lane,
                checker_data.result,
                rule_uid,
            )

            # check for lane level changing in between consecutive lane sections
            _check_level_change_between_lane_sections(
                root=checker_data.input_file_xml_root,
                current_lanes=sorted_left_lane,
                previous_lanes=previous_left_lane,
                result=checker_data.result,
                rule_uid=rule_uid,
            )
            _check_level_change_between_lane_sections(
                root=checker_data.input_file_xml_root,
                current_lanes=sorted_right_lane,
                previous_lanes=previous_right_lane,
                result=checker_data.result,
                rule_uid=rule_uid,
            )

            previous_left_lane = sorted_left_lane
            previous_right_lane = sorted_right_lane

    # Test lane section level continuity in between roads.
    _check_level_change_between_lane_sections(
        root=checker_data.input_file_xml_root,
        current_lanes=previous_left_lane,
        previous_lanes=road_previous_left_lane,
        result=checker_data.result,
        rule_uid=rule_uid,
    )
    _check_level_change_between_lane_sections(
        root=checker_data.input_file_xml_root,
        current_lanes=previous_right_lane,
        previous_lanes=road_previous_right_lane,
        result=checker_data.result,
        rule_uid=rule_uid,
    )

    road_previous_left_lane = previous_left_lane
    road_previous_right_lane = previous_right_lane
