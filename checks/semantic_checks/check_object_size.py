from result_report import IssueLevel, create_location_from_element, create_location_for_road
from checker_data import CheckerData 
from lxml import etree

import logging


def check_object_postion_for_road(road: etree.Element, object: etree.Element, checker_data: CheckerData) -> None:
    max_object_length = float(checker_data.config['max_object_length'])
    max_object_width = float(checker_data.config['max_object_width'])
    max_object_radius = float(checker_data.config['max_object_radius'])
    max_object_height = float(checker_data.config['max_object_height'])
    roadID = road.attrib["id"]
    objectID = object.attrib["id"]
    objectS = float(object.attrib["s"])
    objectT = float(object.attrib["t"])     

    # check if width + length or radius is present
    objectLengthAttrib = object.attrib.get("length")
    objectWidthAttrib = object.attrib.get("width")
    objectRadiusAttrib = object.attrib.get("radius")
    if (not objectLengthAttrib or not objectWidthAttrib) and not objectRadiusAttrib:
        message = f"object {objectID} of road {roadID} has no defined size. Length and width or radius must be provided"
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))
    elif objectRadiusAttrib and (objectLengthAttrib or objectWidthAttrib):
        message = f"object {objectID} of road {roadID} has defined length/width and radius. Only length/width or radius expected"
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))
    elif objectRadiusAttrib:
        objectRadius = float(object.attrib["radius"])
        if objectRadius < 0.0 or objectRadius > max_object_radius:          # TODO 3x < 0.0 check-> sollte eigentlich das Schema checken, tut es aber nicht in 1.5 (bei 2/3 in 1.7)
            message = f"object {objectID} of road {roadID} has invalid radius {objectRadius} out of range (0-{max_object_radius})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))
    else:
        objectLength = float(object.attrib["length"])
        objectWidth = float(object.attrib["width"])
        if objectLength < 0.0 or objectLength > max_object_length:
            message = f"object {objectID} of road {roadID} has invalid length {objectLength} out of range (0-{max_object_length})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))
        if objectWidth < 0.0 or objectWidth > max_object_width:
            message = f"object {objectID} of road {roadID} has invalid width {objectWidth} out of range (0-{max_object_width})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))

def check_object_size(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for object in road.findall("./objects/object"):
            check_object_postion_for_road(road, object, checker_data)         

def get_checker_id():
    return 'check object size'


def get_description():
    return 'check if object size is valid - width and length, radius and height in range given by config file'


def check(checker_data: CheckerData) -> None:
    check_object_size(checker_data)