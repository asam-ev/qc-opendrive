from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData

import logging


def check_laneSection_valid_s(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]
        roadLength = float(road.attrib["length"])
        prevLaneSectionStart = -1.0
        for laneSection in road.findall("./lanes/laneSection"):
            sLaneSection = float(laneSection.attrib["s"])
            if sLaneSection > roadLength:
                message = f"road {roadID} has laneSection with invalid (too high) s={sLaneSection} (roadLength={roadLength})"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sLaneSection, None))
            elif prevLaneSectionStart == -1.0 and sLaneSection != 0.0:
                message = f"road {roadID} has laneSection with invalid s={sLaneSection} (first laneSection needs to start at s=0.0)"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sLaneSection, None))
            elif prevLaneSectionStart >= sLaneSection:
                message = f"road {roadID} has laneSection with invalid (not ascending) s={sLaneSection}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sLaneSection, None))
            prevLaneSectionStart = sLaneSection


def get_checker_id():
    return 'check lanescetion s'


def get_description():
    return 'check laneSection have valid s in road length'


def check(checker_data: CheckerData) -> None:
    check_laneSection_valid_s(checker_data)