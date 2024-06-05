from xodr.checks.semantic_checks.semantic_utilities import LaneSection
from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData 
from lxml import etree

import logging


def checkLanePropSOffsets(lane: etree._Element, laneSection: LaneSection, lanePropertyName: str, checker_data: CheckerData):
    laneID = int(lane.attrib["id"])
    prevSOffset = float(-1.0)
    for laneProperty in lane.findall(lanePropertyName):
        sOffset = float(laneProperty.attrib["sOffset"])
        if sOffset < 0.0:
            sOffset = max(0.0, prevSOffset)                  # no issue as it is checked by schema already
        elif sOffset <= prevSOffset and lanePropertyName != "access":
            message = f"road {laneSection.roadId} has invalid (not ascending) sOffset:{str(sOffset)} in laneSection s={laneSection.startS} lane={str(laneID)} {lanePropertyName}"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(laneProperty, laneSection.roadId, laneSection.startS + sOffset, None))
        elif (lanePropertyName == "width" or lanePropertyName == "border") and prevSOffset == -1.0 and sOffset != 0.0:
            message = f"road {laneSection.roadId} has invalid (first element not zero) sOffset:{str(sOffset)} in laneSection s={laneSection.startS} lane={str(laneID)} {lanePropertyName}"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(laneProperty, laneSection.roadId, laneSection.startS, None))
        elif laneSection.startS + sOffset - laneSection.endS > checker_data.config['epsilon_length']:
            if sOffset != 0.0:                              # otherwise no issue as this is checked by check_lanesection_valid_s
                message = f"road {laneSection.roadId} has invalid (too high) sOffset:{str(sOffset)} in laneSection s={laneSection.startS} lane={str(laneID)} {lanePropertyName}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(laneProperty, laneSection.roadId, laneSection.endS, None))
        prevSOffset = sOffset


def checkLaneSOffsets(laneSection: LaneSection, side: str, checker_data: CheckerData):
    laneSide = laneSection.treeElement.find(side)
    if laneSide is None:
        return                              # lanesection has no lanes on this side
    
    for lane in laneSide.findall("lane"):
         if side != "center":
             checkLanePropSOffsets(lane, laneSection, "width", checker_data)
             checkLanePropSOffsets(lane, laneSection, "material", checker_data)
             checkLanePropSOffsets(lane, laneSection, "speed", checker_data)
             checkLanePropSOffsets(lane, laneSection, "access", checker_data)
         checkLanePropSOffsets(lane, laneSection, "border", checker_data)
         checkLanePropSOffsets(lane, laneSection, "height", checker_data)
         checkLanePropSOffsets(lane, laneSection, "roadMark", checker_data)
         checkLanePropSOffsets(lane, laneSection, "rule", checker_data)


def check_lane_valid_sOffset(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())
    
    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            checkLaneSOffsets(laneSection, "left", checker_data)
            checkLaneSOffsets(laneSection, "right", checker_data)
            checkLaneSOffsets(laneSection, "center", checker_data)


def get_checker_id():
    return 'check road lane sOffset'


def get_description():
    return 'check lane sOffsets (must be ascending, not too high) and sometimes be zero'


def check(checker_data: CheckerData) ->None:
    check_lane_valid_sOffset(checker_data)