from xodr.checks.semantic_checks.semantic_utilities import getDrivingLanesAtSide
from result_report import IssueLevel, create_location_from_element
from checker_data import CheckerData
from lxml import etree

import logging

def getDrivingLanesTowardsJunction(road: etree._Element, junctionID: str):
    drivingLanes = list()
    link = road.find("link")
    if link is None:
        return drivingLanes, False                           # checked by check_road_linkage_backward + TODO neuer Check Connection = ConRoads
    
    lanesections = road.findall("./lanes/laneSection")
    if len(lanesections) == 0:
        return drivingLanes, False                           # checked by schema

    leftHandTraffic = False
    if 'rule' in road.attrib and road.attrib['rule'] == "LHT":
        leftHandTraffic = True

    # check if pred and/or succ of road is junction
    predElement = link.find("predecessor")
    succElement = link.find("successor")
    foundLinkedRoad = False
    if predElement is not None:
        predecessor = predElement.attrib["elementId"]
        if predecessor == junctionID:
            foundLinkedRoad = True
            getDrivingLanesAtSide(lanesections[0], "right" if leftHandTraffic else "left", drivingLanes)
    if succElement is not None:
        successor =  succElement.attrib["elementId"]
        if successor == junctionID:
            foundLinkedRoad = True
            getDrivingLanesAtSide(lanesections[-1], "left" if leftHandTraffic else "right", drivingLanes)

    return drivingLanes, foundLinkedRoad

def check_driving_lanes_continue_in_junction(checker_data: CheckerData) -> None:   
    logging.info(get_checker_id())
    for junction in checker_data.data.findall("./junction"):
        junctionID = junction.attrib['id']
        junctionType = junction.attrib['type']
        if junctionType == 'direct':
            continue                                    # for direct junctions incomingroad may have no driving lanes towards junction
                                                        # TODO really? Or has sample data been corrupt?

        # get all roads that lead into the junction and their linked lanes
        incomingRoadDict = {}
        for connection in junction.findall("./connection"):
            incomingRoadID = connection.attrib['incomingRoad']
            if incomingRoadID in incomingRoadDict:
                for lanelink in connection.findall("./laneLink"):
                    incomingRoadDict[incomingRoadID].add(lanelink.attrib['from'])
            else:
                newLinkedLanes = set()
                for lanelink in connection.findall("./laneLink"):
                    newLinkedLanes.add(lanelink.attrib['from'])
                incomingRoadDict[incomingRoadID] = newLinkedLanes

        for incomingRoadID, linkedLanes in incomingRoadDict.items():
            # find incoming road
            searchString = "./road[@id='" + incomingRoadID + "']"
            road = checker_data.data.find(searchString)
            if road is None:
                continue                            # checked by schema

            # get driving lanes of incoming road and check if all are linked
            drivingLanes, foundLinkedRoad = getDrivingLanesTowardsJunction(road, junctionID)
            if not foundLinkedRoad:
                continue                            # checked by schema
            if len(drivingLanes) == 0:
                message = "junction " + junctionID + " has linked road " + incomingRoadID + " without driving lanes towards junction"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(junction))                    
                continue

            for drivingLane in drivingLanes:
                if drivingLane not in linkedLanes:        
                    message = "junction " + junctionID + " has no connection to driving lane " + drivingLane + " of road " + incomingRoadID
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(junction))


def get_checker_id():
    return 'check driving lanes continue in junction'


def get_description():
    return 'check road lane links of juction connection - each driving lane of the incoming roads must have a connection in the junction'


def check(checker_data: CheckerData) ->None:
    check_driving_lanes_continue_in_junction(checker_data)