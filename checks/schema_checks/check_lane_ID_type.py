from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData 
from lxml import etree

import logging


def check_Lane_ID(lane: etree._Element, roadID: int, checker: Checker) ->None:
    id = lane.attrib["id"]
    idValue = int(id)
    if (idValue < -127 or idValue > 127):
        message = "road " + roadID + " " + lane.tag + " has invalid id " + id
        checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(lane))


def check_lane_ID_type(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]
        for lanesection in road.findall("./lanes/laneSection"):
            for lane in lanesection.findall("./left/lane"):
                check_Lane_ID(lane, roadID, checker_data.checker)
            for lane in lanesection.findall("./center/lane"):
                check_Lane_ID(lane, roadID, checker_data.checker)
            for lane in lanesection.findall("./right/lane"):
                check_Lane_ID(lane, roadID, checker_data.checker)


def get_checker_id():
    return 'check is Id type Int8'


def get_description():
    return 'check is lane id valid int 8 value'


def check(checker_data: CheckerData) ->None:
    check_lane_ID_type(checker_data)