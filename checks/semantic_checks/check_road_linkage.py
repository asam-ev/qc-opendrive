from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData 
from lxml import etree

import logging


def find_link_id(checker_data: CheckerData, road: etree._Element, link: etree._Element, linkTypeStr: str):
    connectedElement = link.find(linkTypeStr)
    if connectedElement is None:
        return                  # road has no predecessor/successor
    
    # create searchstring for linked element
    connectedId = connectedElement.attrib["elementId"]
    connectedType = connectedElement.attrib["elementType"]
    if connectedType == "road":
        searchString = "./road[@id='" + connectedId + "']"
    elif connectedType == "junction":
        searchString = "./junction[@id='" + connectedId + "']"
    else:
        return                  # checked by schema

    # get linked element
    linkedElements = checker_data.data.findall(searchString)
    if len(linkedElements) == 0:
        currentRoadID = road.attrib["id"]
        message = f"{linkTypeStr} {connectedType} (id={connectedId}) of road {currentRoadID} not found!"
        checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_for_road(connectedElement, currentRoadID, None, None))


def check_road_linkage(checker_data: CheckerData, linkTypeStr: str) -> None:
    logging.info(f'{get_checker_id()} for {linkTypeStr}')
    for road in checker_data.data.findall("./road"):
        link = road.find("link")
        if link is not None:
            find_link_id(checker_data, road, link, linkTypeStr)


def get_checker_id():
    return 'check road linkage Pre/Suc'


def get_description():
    return 'checks if linked Predecessor/Successor road/junction exists'


def check(checker_data: CheckerData) ->None:
    check_road_linkage(checker_data, "predecessor")
    check_road_linkage(checker_data, "successor")