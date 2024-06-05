from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData 
from lxml import etree

import logging


def check_connection_road_laneID(junction: etree._Element, connection: etree._Element, checkIncomingRoad: bool, checker_data: CheckerData) -> None:
    # find road
    if checkIncomingRoad:
        roadID = connection.attrib['incomingRoad']
    elif 'connectingRoad' in connection.attrib:
        roadID = connection.attrib['connectingRoad']
    else:
        roadID = connection.attrib['linkedRoad']
    searchStringRoad = "./road[@id='" + roadID + "']"
    road = checker_data.data.find(searchStringRoad)
    if road is None:
        return              # checked by schema

    # check linked lanes
    searchStr = "from" if checkIncomingRoad else "to"
    junctionID = junction.attrib['id']
    connectionID = connection.attrib['id']
    contactPoint = connection.attrib['contactPoint']
    for laneLink in connection.findall("./laneLink"):
        # get linked lane
        linkedLane = int(laneLink.attrib[searchStr])
        if linkedLane == 0:
            message = "connection " + connectionID + " of junction " + junctionID + " has invalid lanelink: Lane " + str(linkedLane)
            checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(connection)) 
            continue

        # get lanes to search for linked lane
        lanesections = road.findall("./lanes/laneSection")
        if len(lanesections) == 0:
            continue            # checked by schema        
        frontLaneSection = linkedLane > 0 if checkIncomingRoad else contactPoint == "start"
        lanesection = lanesections[0] if  frontLaneSection else lanesections[-1]
        side = "left" if linkedLane > 0 else "right"
        lanes = lanesection.find("./" + side)

        # try to find linkedLane in road
        if lanes is not None:
            foundLane = False
            for lane in lanes.findall("./lane"):
                laneID = int(lane.attrib['id'])
                if linkedLane == laneID:
                    foundLane = True
                    break
            if foundLane:
                continue

        frontBack = "front" if frontLaneSection else "back"
        message = "connection " + connectionID + " of junction " + junctionID + " has invalid lanelink: Lane " + str(linkedLane) + " not found at " + frontBack + " of road " + roadID
        checker_data.checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(connection))  


def check_junction_lane_linkage(checker_data: CheckerData) -> None: 
    logging.info(get_checker_id())
    for junction in checker_data.data.findall("./junction"):
        for connection in junction.findall("./connection"):
            # check incomingRoad
            check_connection_road_laneID(junction, connection, True, checker_data)
            # check connectingRoad
            check_connection_road_laneID(junction, connection, False, checker_data)


def get_checker_id():
    return 'check junction lane linkage'


def get_description():
    return 'check if linked lanes of junction exist in linked road'


def check(checker_data: CheckerData) ->None:
    check_junction_lane_linkage(checker_data)