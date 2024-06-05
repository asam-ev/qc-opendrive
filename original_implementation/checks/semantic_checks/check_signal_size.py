from result_report import IssueLevel, create_location_for_road
from checker_data import CheckerData 

import logging


# check signal postion 
def check_signal_postion_for_road(road, signal, checker_data: CheckerData):
    max_signal_width = float(checker_data.config['max_signal_width'])
    max_signal_height = float(checker_data.config['max_signal_height'])
    roadID = road.attrib["id"]
    signalID = signal.attrib["id"]
    signalS = float(signal.attrib["s"])   
    signalT = float(signal.attrib["t"])     

    # check width
    signalWidth = float(signal.attrib["width"])
    if signalWidth > max_signal_width:
        message = f"signal {signalID} of road {roadID} has too high width value {signalWidth} (max = {max_signal_width})"
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(signal ,roadID, signalS, signalT))

    # check height
    signalheight = float(signal.attrib["height"])     
    if signalheight > max_signal_height:
        message = f"signal {signalID} of road {roadID} has too high height value {signalheight} (max = {max_signal_height})"
        checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(signal ,roadID, signalS, signalT))


def check_signal_size(checker_data: CheckerData) -> None:
    logging.info(get_checker_id())

    for road in checker_data.data.findall("./road"):
        for signal in road.findall("./signals/signal"):
            check_signal_postion_for_road(road, signal, checker_data)


def get_checker_id():
    return 'check signal size'


def get_description():
    return 'check if signal size is valid - width and height in range given by config file'


def check(checker_data: CheckerData)-> None:
    check_signal_size(checker_data)