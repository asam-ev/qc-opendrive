from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData 

import logging


def check_road_min_length(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())
    min_length = float(checker_data.config['min_length'])

    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]
        roadLength = float(road.attrib["length"])
        if roadLength < min_length:
            message = f"road {roadID} is to short: {roadLength}"
            checker_data.checker.gen_issue(IssueLevel.INFORMATION, message, create_location_for_road(road, roadID, roadLength, None))


def get_checker_id():
    return 'check road min length'


def get_description():
    return 'check min road length'


def check(checker_data: CheckerData) -> None:
    check_road_min_length(checker_data)