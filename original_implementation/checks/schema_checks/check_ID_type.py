from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData 
from lxml import etree

import logging


def check_ID(element: etree._Element, checker: Checker) -> None:
    id = element.attrib["id"]
    if type(id) != int:
        return

    idValue = int(id)
    if (idValue < 0 or idValue > 4294967295):
         message = element.tag + " has invalid id " + id
         checker.gen_issue(IssueLevel.ERROR, message, create_location_from_element(element))


def check_ID_type(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        check_ID(road, checker_data.checker)
        for signal in road.findall("./signals/signal"):
            check_ID(signal, checker_data.checker)
        for signal in road.findall("./signals/signalReference"):
            check_ID(signal, checker_data.checker)
        for object in road.findall("./objects/object"):
            check_ID(object, checker_data.checker)
        for object in road.findall("./objects/objectReference"):
            check_ID(object, checker_data.checker)
        for object in road.findall("./objects/tunnel"):
            check_ID(object, checker_data.checker)
        for object in road.findall("./objects/bridge"):
            check_ID(object, checker_data.checker)

    for junction in checker_data.data.findall("./junction"):
        check_ID(junction, checker_data.checker)


def get_checker_id():
    return 'check is Id type UInt32'


def get_description():
    return 'check is id(road, junction, signal, object, bridge, tunnel, refObj) valid unsigned int 32 value.'


def check(checker_data: CheckerData) ->None:
    check_ID_type(checker_data)