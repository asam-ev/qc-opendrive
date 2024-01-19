from xodr.checks.semantic_checks.semantic_utilities import LaneSection, getConnectedRoad
from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData 
from lxml import etree

import logging

# check if lane link id neighbour lane section
def check_Lane_Link(laneID: int, link: etree._Element, linkType: str, laneSection: LaneSection, checker_data: CheckerData) -> bool:
    linkNode = link.find(linkType)
    if linkNode is None:                        # lane has no link on this side
        return True

    neighbourLaneSection = laneSection.treeElement.getprevious() if linkType == "predecessor" else laneSection.treeElement.getnext()
    if neighbourLaneSection is None or neighbourLaneSection.tag != 'laneSection':
        connectedRoad = getConnectedRoad(laneSection.roadElement, linkType, checker_data)
        if connectedRoad is None:
            return True                          # checked in check_road_linkage_backward
        lanesections = connectedRoad.treeElement.findall("./lanes/laneSection")
        if len(lanesections) == 0:
            return True                          # checked by schema
       
        if connectedRoad.contactPoint == "":
            return True                          # TODO get lanesection by s for virtual junctions
        else:
            neighbourLaneSection = lanesections[0] if connectedRoad.contactPoint == "start" else lanesections[-1]
    
    linkedID = linkNode.attrib["id"]
    side = "left" if int(linkedID) > 0 else "right"            # TODO side bestimmen? bidirectional lanes? 
    neighbourLaneSide = neighbourLaneSection.find(side)
    if neighbourLaneSide is None:              # no lanes at expected side of neighbour lanesection
        return False

    # find lane id in neighbour lanes
    searchString = "./lane[@id='" + linkedID + "']"
    linkedLane = neighbourLaneSide.findall(searchString)
    if len(linkedLane) == 0:                  # lane not found
        return False
    return True


# check if all lane links of side have valid ids to previous or next lane section
def check_LaneID_Linkage(laneSection: LaneSection, side: str, checker_data: CheckerData) -> None:
    laneSide = laneSection.treeElement.find(side)
    if laneSide is None:                        # no lanes on this side
        return
    
    # check all lane links
    for lane in laneSide.findall("lane"):
        link = lane.find("link")
        if link is None:                        # lane has no linked lane
            continue

        laneID = int(lane.attrib["id"])
        # is lane id in previous lane section / road
        if not check_Lane_Link(laneID, link, "predecessor", laneSection, checker_data):
            message = f"road {laneSection.roadId} has invalid (not existing) linked predecessor lane in laneSection s={laneSection.startS}, lane={laneID}"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lane))

        # is lane id in next lane section / road
        if not check_Lane_Link(laneID, link, "successor", laneSection, checker_data):
            message = f"road {laneSection.roadId} has invalid (not existing) linked successor lane in laneSection s={laneSection.startS}, lane={laneID}"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lane))


def check_lanes_ids_linkage(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for laneSectionElement in road.findall("./lanes/laneSection"):
            laneSection = LaneSection(road, laneSectionElement)
            check_LaneID_Linkage(laneSection, "left", checker_data)
            check_LaneID_Linkage(laneSection, "right", checker_data)


def get_checker_id():
    return 'check road lane linkage'


def get_description():
    return 'check lane have valid Predecessor/Successor lane ids (to adjacent street lanes or lane sections)'


def check(checker_data: CheckerData) ->None:
    check_lanes_ids_linkage(checker_data)