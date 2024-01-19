from result_report import IssueLevel, create_location_from_element
from checker_data import CheckerData
from enum import Enum

import logging

class Direction(Enum):
    Ascending = 1
    Descending = 2
    Invalid = 3

def calc_direction(current, last, invalid, direction) -> bool:
    if direction == Direction.Invalid and last != invalid:
        if current == last:
            return False
        elif current > last:
            direction = Direction.Ascending
        else: 
            direction = Direction.Descending   
    return True

def check_direction(current, last, invalid, direction) -> bool:
    if direction != Direction.Invalid:
        if direction == Direction.Ascending and current <= last:
            return False
        elif direction == Direction.Descending and current >= last:
            return False
    return True

def check_junction_lane_linkage_order(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())
    invalid = 999
    for junction in checker_data.data.findall("./junction"):
        junctionID = junction.attrib['id']
        for connection in junction.findall("./connection"):
            connectionID = connection.attrib['id']
            lastFrom = invalid
            lastTo = invalid
            directionFrom = Direction.Invalid # 0 - larger, 1 - smaller
            directionTo = Direction.Invalid
            for lanelink in connection.findall("./laneLink"):
                currentFrom = lanelink.attrib['from']
                currentTo = lanelink.attrib['to']
                if currentTo == 0 or currentFrom == 0:
                    continue                        # already checked in check_junction_lane_linkage
                
                # calc direction
                if calc_direction(currentFrom, lastFrom, invalid, directionFrom) == False:
                    message = "connection " + connectionID + " of junction " + junctionID + " has invalid(equal) lane id for from: " + currentFrom
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lanelink))
                if calc_direction(currentTo, lastTo, invalid, directionTo) == False:
                    message = "connection " + connectionID + " of junction " + junctionID + " has invalid(equal) lane id for to: " + currentTo
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lanelink))
                    
                if check_direction(currentFrom, lastFrom, invalid, directionFrom) == False:
                    message = "connection " + connectionID + " of junction " + junctionID + " has invalid lane order for from: " + currentFrom
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lanelink))

                if check_direction(currentTo, lastTo, invalid, directionTo) == False:
                    message = "connection " + connectionID + " of junction " + junctionID + " has invalid lane order for to: " + currentTo
                    checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(lanelink))

                lastFrom = currentFrom
                lastTo = currentTo


def get_checker_id():
    return 'check junction lane linkage order'


def get_description():
    return 'check lane linkage order of juction connection'


def check(checker_data: CheckerData) ->None:
    check_junction_lane_linkage_order(checker_data)