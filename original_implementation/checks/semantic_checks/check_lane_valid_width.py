from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import IssueLevel, Checker, create_location_for_road
from checker_data import CheckerData 
from lxml import etree
from scipy.optimize import minimize_scalar

import logging


def checkLaneWidth(laneSection: LaneSection, side: str, checker_data: CheckerData):
    laneSide = laneSection.treeElement.find(side)
    if laneSide is None:
        return                              # lanesection has no lanes on this side
    
    epsilon_sOffset = float(checker_data.config['epsilon_sOffset'])

    for lane in laneSide.findall("lane"):
        laneID = int(lane.attrib["id"])
        for width in lane.findall("width"):
            a = float(width.attrib["a"])
            if a < 0.0:
                sOffset = float(width.attrib["sOffset"])
                message = f"road {laneSection.roadId} has invalid width:{a} in laneSection s={laneSection.startS} lane={laneID} sOffset={sOffset}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(width, laneSection.roadId, float(laneSection.startS) + sOffset, None))
                continue

            b = float(width.attrib["b"])
            c = float(width.attrib["c"])
            d = float(width.attrib["d"])
            if b == 0.0 and c == 0.0 and d == 0.0:
                continue                                # constant polynom does not need to be checked

            # get range of polynom
            sOffset = float(width.attrib["sOffset"])
            sOffsetNext = laneSection.endS - laneSection.startS
            nextElement = width.getnext()
            if nextElement is not None and nextElement.tag == "width":
                sOffsetNext = float(nextElement.attrib["sOffset"])
            if sOffsetNext <= sOffset:
                continue;                               # invalid sOffsets are checked in separate check

            # calc minimum polynom value in range
            def f(x):
                return d * x ** 3 + c * x ** 2 + b * x + a                    
            res = minimize_scalar(f, bounds=(0.0, sOffsetNext - sOffset), method='bounded')

            if res.success != True:
                sOffset = float(width.attrib["sOffset"])
                message = f"road {laneSection.roadId} has invalid width in laneSection s={laneSection.startS} lane={laneID} sOffset={sOffset}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(width, laneSection.roadId, float(laneSection.startS) + sOffset, None))
            elif res.fun < epsilon_sOffset:
                sOffset = float(width.attrib["sOffset"])
                message = f"road {laneSection.roadId} has invalid width:{res.fun} in laneSection s={laneSection.startS} lane={laneID} sOffset={sOffset}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(width, laneSection.roadId, float(laneSection.startS) + sOffset + res.x, None))


def check_lane_valid_width(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())
    
    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            checkLaneWidth(laneSection, "left", checker_data)
            checkLaneWidth(laneSection, "right", checker_data)
            checkLaneWidth(laneSection, "center", checker_data)


def get_checker_id():
    return 'check road lane width'


def get_description():
    return 'check lane width must always be greater than 0 or at the start/end point of a lanesection >= 0'


def check(checker_data: CheckerData) ->None:
    check_lane_valid_width(checker_data)