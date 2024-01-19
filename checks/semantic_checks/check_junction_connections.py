from xodr.checks.semantic_checks.semantic_utilities import getDrivingLanesAtSide, getConnectedRoad
from result_report import IssueLevel, create_location_from_element
from checker_data import CheckerData 

import logging


def check_junction_connections(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())
    for junction in checker_data.data.findall("./junction"):
        junctionID = junction.attrib['id']

        # get all connection roads from connections
        connectionRoads = []
        for connection in junction.findall("./connection"):
            if not 'connectingRoad' in connection.attrib:
                continue                                        # direct junctions have no connection roads

            connectingRoadID = connection.attrib['connectingRoad']
            incomingRoadID = connection.attrib['incomingRoad']
            contactPoint = connection.attrib['contactPoint']
            if connectingRoadID not in connectionRoads:
                connectionRoads.append(connectingRoadID)
            
            searchStringRoad = "./road[@id='" + connectingRoadID + "']"
            connectingRoad = checker_data.data.find(searchStringRoad)
            if connectingRoad is None:
                continue                            # checked by schema
            
            connectedRoadFront = getConnectedRoad(connectingRoad, "predecessor", checker_data)
            connectedRoadBack = getConnectedRoad(connectingRoad, "successor" , checker_data)
            if connectedRoadFront is None or connectedRoadBack is None:
                message = f"connectingRoad {connectingRoadID} of junction {junctionID} has no predecessor or successor!"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(connection))

            connectedRoad = connectedRoadFront if contactPoint == "start" else connectedRoadBack
            if connectedRoad is None or connectedRoad.Id != incomingRoadID:
                message = f"In junction {junctionID} connectingRoad {connectingRoadID} is connected with incomingRoad {incomingRoadID}, but the connecting road has different linkage!"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(connection))

        searchString = "./road[@junction='" + junctionID + "']"
        for road in checker_data.data.findall(searchString):
            roadID = road.attrib['id']
            if roadID not in connectionRoads:
                # check if road has driving lanes - if not it does not need a connection entry
                foundDrivingLane = False
                for laneSection in road.findall("./lanes/laneSection"):
                    drivingLanes = list()
                    getDrivingLanesAtSide(laneSection, "both", drivingLanes)
                    if len(drivingLanes) != 0:
                        foundDrivingLane = True

                if foundDrivingLane:
                    message = f"road {roadID} belongs to junction {junctionID}, but no connection for this road exists!"
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(junction))


def get_checker_id():
    return 'check junction connections'


def get_description():
    return 'check if junction connection exists for connecting road'


def check(checker_data: CheckerData) ->None:
    check_junction_connections(checker_data)