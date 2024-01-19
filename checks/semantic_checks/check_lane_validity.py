from xodr.checks.semantic_checks.semantic_utilities import get_lanesection_at_s, collect_lanes_per_section
from result_report import IssueLevel, Checker, create_location_from_element
from checker_data import CheckerData
from lxml import etree

import logging


def check_validity(signal_object: etree._Element, traffic_rule: str, lanes_per_section: dict, checker: Checker) -> None:
    validity = signal_object.find("validity")
    if validity is None:                            # no valitidy, so nothing to check
        return
    
    # check if lanes exist at signal/object position
    id = signal_object.attrib['id']
    sValue = float(signal_object.attrib['s'])
    fromLane = validity.attrib['fromLane']
    toLane = validity.attrib['toLane']
    lanes = get_lanesection_at_s(sValue, lanes_per_section)
    if fromLane == '0' or toLane == '0':
        message = f"lane validity of {signal_object.tag} {id} references to invalid lane 0"
        checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(signal_object))
    if not fromLane in lanes:
        message = f"lane validity of {signal_object.tag} {id} references to not existing fromLane {fromLane}"
        checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(signal_object))
    if not toLane in lanes:
        message = f"lane validity of {signal_object.tag} {id} references to not existing toLane {toLane}"
        checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(signal_object))

    # check if from is lower                                # TODO from immer kleiner? oder abs(from) kleiner? Was wenn orientation both?
    #if int(fromLane) > int(toLane):
    #    message = f"lane validity of {signal_object.tag} {id} invalid. fromLane needs to be lower than or equal to toLane"
    #    checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(signal_object))
    
    # check orientation
    orientation = signal_object.attrib['orientation']
    error = ""
    if traffic_rule == 'RHT':                   # right hand traffic
        if orientation == '+':                  # negative lane ids
            if int(fromLane) > 0 or int(toLane) > 0:
                error = "negative"
        elif orientation == '-':                # positve lane ids
            if int(fromLane) < 0 or int(toLane) < 0:
                error = "positive"
    elif traffic_rule == 'LHT':                 # left hand traffic
        if orientation == '-':                  # negative lane ids
            if int(fromLane) > 0 or int(toLane) > 0:
                error = "negative"
        elif orientation == '+':                # positve lane ids
            if int(fromLane) < 0 or int(toLane) < 0:
                error = "positive"
    if error != "":
        message = f"lane validity of {signal_object.tag} {id} should be {error} for traffic rule {traffic_rule} with orientation {orientation}"
        checker.gen_issue(IssueLevel.WARNING, message, create_location_from_element(signal_object))


def check_lane_validity(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())
    
    for road in checker_data.data.findall("./road"):
        rule = 'RHT'
        if 'rule' in road.attrib:
            rule = road.attrib['rule']
        lanes_per_section = collect_lanes_per_section(road)
        for signal in road.findall("./signals/signal"):
            check_validity(signal, rule, lanes_per_section, checker_data.checker)
        for signal in road.findall("./signals/signalReference"):
            check_validity(signal, rule, lanes_per_section, checker_data.checker)
        for object in road.findall("./objects/object"):
            check_validity(object, rule, lanes_per_section, checker_data.checker)
        for object in road.findall("./objects/objectReference"):
            check_validity(object, rule, lanes_per_section, checker_data.checker)            


def get_checker_id():
    return 'check lane validity'


def get_description():
    return 'check if signal/object have valid lane validity also with regard to orientation'


def check(checker_data: CheckerData) ->None:
    check_lane_validity(checker_data)