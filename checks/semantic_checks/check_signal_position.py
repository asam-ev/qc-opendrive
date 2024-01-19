from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData 

import logging


# check signal postion 
def check_signal_postion_for_road(road, signal, checker_data: CheckerData):
    epsilon_s_on_road = float(checker_data.config['epsilon_s_on_road'])
    max_range_signal_t = float(checker_data.config['max_range_signal_t'])
    max_range_signal_zOffset = float(checker_data.config['max_range_signal_zOffset'])
    roadID = road.attrib["id"]
    signalID = signal.attrib["id"]
    signalS = float(signal.attrib["s"])   
    signalT = float(signal.attrib["t"])     

    # check s position
    roadLength = float(road.attrib["length"])
    if signalS - roadLength > epsilon_s_on_road:
        message = f"signal {signalID} of road {roadID} has too high s value {signalS} (road length = {roadLength})"
        signalS = roadLength        
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(signal ,roadID, signalS, signalT))

    # check t position
    if signalT < -max_range_signal_t or signalT > max_range_signal_t:
        message = f"signal {signalID} of road {roadID} has t value {signalT} out of range (-{max_range_signal_t}, +{max_range_signal_t})"
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(signal ,roadID, signalS, 0.0))

    # check z position
    if signal.tag != "signalReference":
        signalZOffset = float(signal.attrib["zOffset"])
        if signalZOffset < -max_range_signal_zOffset or signalZOffset > max_range_signal_zOffset:
            message = f"signal {signalID} of road {roadID} has zOffset value {signalZOffset} out of range (-{max_range_signal_zOffset}, +{max_range_signal_zOffset})"
            checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(signal ,roadID, signalS, signalT))


def check_signal_position(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for signal in road.findall("./signals/signal"):
            check_signal_postion_for_road(road, signal, checker_data)         
        for signal in road.findall("./signals/signalReference"):
            check_signal_postion_for_road(road, signal, checker_data)


def get_checker_id():
    return 'check signal position'


def get_description():
    return 'check if signal position is valid - s value is in range of road length, t and zOffset in range given by config file'


def check(checker_data: CheckerData)-> None:
    check_signal_position(checker_data)