from result_report import IssueLevel, create_location_from_element, create_location_for_road
from checker_data import CheckerData 
from lxml import etree

import logging


def check_object_postion_for_road(road: etree.Element, object: etree.Element, checker_data: CheckerData) -> None:
    epsilon_s_on_road = float(checker_data.config['epsilon_s_on_road'])
    max_range_object_t = float(checker_data.config['max_range_object_t'])
    max_range_object_zOffset = float(checker_data.config['max_range_object_zOffset'])
    roadID = road.attrib["id"]
    roadLength = float(road.attrib["length"])
    objectID = object.attrib["id"]

    # check s position
    objectS = float(object.attrib["s"])            
    if objectS - roadLength > epsilon_s_on_road:
        message = f"object {objectID} of road {roadID} has too high s value {objectS} (road length = {roadLength})"
        objectS = roadLength
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, None))

    # check t position
    if object.tag != "tunnel" and object.tag != "bridge":
        objectT = float(object.attrib["t"]) 
        if objectT < -max_range_object_t or objectT > max_range_object_t:
            message = f"object {objectID} of road {roadID} has t value {objectT} out of range (-{max_range_object_t}, +{max_range_object_t})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))

    # check zOffset
    if object.tag == "object":
        objectZOffset = float(object.attrib["zOffset"])
        if objectZOffset < -max_range_object_zOffset or objectZOffset > max_range_object_zOffset:
            message = f"object {objectID} of road {roadID} has zOffset value {objectZOffset} out of range (-{max_range_object_zOffset}, +{max_range_object_zOffset})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(object, roadID, objectS, objectT))

    # check length of tunnel, bridge
    if object.tag == "tunnel" or object.tag == "bridge":
        objectLength = float(object.attrib["length"]) 
        if objectS  + objectLength - roadLength  > epsilon_s_on_road:
            message = f"{object.tag} {objectID} of road {roadID} is too long (EndS = {objectS  + objectLength}, road length = {roadLength})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(object))
                

def check_object_position(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for object in road.findall("./objects/object"):
            check_object_postion_for_road(road, object, checker_data)         
        for object in road.findall("./objects/objectReference"):
            check_object_postion_for_road(road, object, checker_data)
        for object in road.findall("./objects/tunnel"):
            check_object_postion_for_road(road, object, checker_data)            
        for object in road.findall("./objects/bridge"):
            check_object_postion_for_road(road, object, checker_data)            


def get_checker_id():
    return 'check object position'


def get_description():
    return 'check if object position is valid - s value is in range of road length, t and zOffset in range given by config file'


def check(checker_data: CheckerData) -> None:
    check_object_position(checker_data)