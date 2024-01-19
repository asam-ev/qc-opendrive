from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import  IssueLevel, create_location_for_road
from checker_data import CheckerData 

import logging

def check_laneSection_min_length(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())
    min_length = float(checker_data.config['min_length'])

    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            laneSectionLength = laneSection.endS - laneSection.startS
            if laneSectionLength < min_length and laneSectionLength > 0.0:
                message = f"road {laneSection.roadId} has too short laneSection s={laneSection.startS} (lengths: {laneSectionLength})"
                checker_data.checker.gen_issue(IssueLevel.INFORMATION, message, create_location_for_road(road, laneSection.roadId, laneSection.startS, None))


def get_checker_id():
    return 'check lanesection minimum length'


def get_description():
    return 'check laneSection have minimum length'


def check(checker_data: CheckerData) ->None:
    check_laneSection_min_length(checker_data)