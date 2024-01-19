from result_report import  IssueLevel, create_location_for_road
from checker_data import CheckerData

import logging


def check_road_geometry_length(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())
    epsilon_length = float(checker_data.config['epsilon_length'])
    min_length = float(checker_data.config['min_length'])

    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]
        roadLength = road.attrib["length"]
        for geometry in road.findall("./planView/geometry"):
            sGeom = float(geometry.attrib["s"])
            lengthGeom = float(geometry.attrib["length"])

            endLength = float(roadLength)
            nextGeometry = geometry.getnext()
            if nextGeometry != None:
                endLength = float(nextGeometry.attrib["s"])

            diff = endLength - sGeom - lengthGeom
            if abs(diff) > epsilon_length:
                message = f"road {roadID} geometry {sGeom} has invalid length ({lengthGeom}) to next geometry or end (should be {endLength - sGeom})"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sGeom, None))
            if lengthGeom < min_length:
                message = f"road {roadID} geometry {sGeom} has invalid (too short) length {lengthGeom}"
                checker_data.checker.gen_issue(IssueLevel.INFORMATION, message, create_location_for_road(road, roadID, sGeom, None))



def get_checker_id():
    return 'check road geometry length'


def get_description():
    return 'check the length of a geometry element (s + length = s of next)'


def check(checker_data: CheckerData) -> None:
    check_road_geometry_length(checker_data)