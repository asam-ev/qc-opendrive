from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import IssueLevel, Checker, create_location_for_road
from checker_data import CheckerData

import logging

def check_lane_type_side(laneSection: LaneSection, side: str, checker: Checker) -> None:
    laneSide = laneSection.treeElement.find(side)
    if laneSide is None:
        return                              # lanesection has no lanes on this side

    for lane in laneSide.findall("lane"):
        laneID = int(lane.attrib["id"])
        laneType = lane.attrib["type"]
        if laneType == "none":
            message = f"road {laneSection.roadId} has invalid lanetype {laneType} in laneSection s={laneSection.startS} lane={str(laneID)}"
            checker.gen_issue(IssueLevel.INFORMATION, message, create_location_for_road(lane, laneSection.roadId, laneSection.startS, None))
                

def check_lane_type(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            check_lane_type_side(laneSection, "left", checker_data.checker)
            check_lane_type_side(laneSection, "right", checker_data.checker)


def get_checker_id():
    return 'check road lane type "none"'


def get_description():
    return 'check lane type "none" is allowed, but has no information content'


def check(checker_data: CheckerData) ->None:
    check_lane_type(checker_data)