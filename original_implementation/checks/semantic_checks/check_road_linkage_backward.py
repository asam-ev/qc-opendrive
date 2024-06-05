from xodr.checks.semantic_checks.semantic_utilities import ConnectedRoad, getConnectedRoad
from result_report import IssueLevel, create_location_from_element
from checker_data import CheckerData
from lxml import etree
import logging


def check_road_linkage_backward(checker_data: CheckerData, linkTypeStr: str) -> None:
    logging.info(f'{get_checker_id()} for {linkTypeStr}')
    
    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]
        junctionID = road.attrib["junction"]

        # get connected road
        connectedRoad = getConnectedRoad(road, linkTypeStr, checker_data)
        if connectedRoad is None:
            continue                                # no connected road found
        elif connectedRoad.contactPoint == "":
            continue                                # main road of virtual juctions is not linked to junction

        # get link of connected road
        connectedLink = connectedRoad.treeElement.find("link")
        if (connectedLink is None):
            message = f"{linkTypeStr} of road {roadID} is linked to {connectedRoad.contactPoint} of road {connectedRoad.Id}, but reverse link does not exist!"
            checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(connectedRoad.treeElement))
            continue         
        connectedLinkType = "predecessor" if connectedRoad.contactPoint == "start" else "successor"
        connectedLinkTypeNode = connectedLink.find(connectedLinkType)
        if (connectedLinkTypeNode is None):
            message = f"{linkTypeStr} of road {roadID} is linked to {connectedRoad.contactPoint} of road {connectedRoad.Id}, but reverse link does not exist!"
            checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(connectedRoad.treeElement))
            continue

        # get info from re connected road
        reConnectID = connectedLinkTypeNode.attrib["elementId"]
        reConnectLinkType = connectedLinkTypeNode.attrib["elementType"]
        if (reConnectLinkType == "junction" and reConnectID == junctionID):
            # link from junction road to junction
            continue
        elif (reConnectLinkType == "road" and reConnectID == roadID):
            continue
        else:
            message = f"{linkTypeStr} of road {roadID} is linked to {connectedRoad.contactPoint} of road {connectedRoad.Id}, but reverse link does not exist!"
            checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(connectedLinkTypeNode))


def get_checker_id():
    return 'check road backward linkage'


def get_description():
    return 'check if linked elements are also linked to original element'


def check(checker_data: CheckerData) ->None:
    check_road_linkage_backward(checker_data, "predecessor")
    check_road_linkage_backward(checker_data, "successor")