from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData 
from lxml import etree

import logging


# check lane order of one lane section side
def check_LaneID_Order(laneSection: LaneSection, startLaneID: int, side: str, checker: Checker) -> None:
    laneSide = laneSection.treeElement.find(side)
    if laneSide is None:
        return                      # no lanes on this side

    for lane in laneSide.findall("lane"):
        laneID = int(lane.attrib["id"])
        if startLaneID == 255: 
            startLaneID = laneID        
        text = f"road {laneSection.roadId} laneSection s={laneSection.startS} lane {laneID}"
        if startLaneID != laneID:
            message = text + " has invalid order - should be " + str(startLaneID)
            checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lane))
        startLaneID -= 1

def check_lanes_order(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            startLaneID = 255
            check_LaneID_Order(laneSection, startLaneID, "left", checker_data.checker)
            check_LaneID_Order(laneSection, startLaneID, "center", checker_data.checker)
            check_LaneID_Order(laneSection, startLaneID, "right", checker_data.checker)


def get_checker_id():
    return 'check road lane id order'


def get_description():
    return 'check Lane Order - check continuity, check id gaps'


def check(checker_data: CheckerData) ->None:
    check_lanes_order(checker_data)