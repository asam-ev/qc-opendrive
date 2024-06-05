from result_report import  IssueLevel, create_location_for_road
from checker_data import CheckerData 

import logging


def check_paramPoly3(checker_data: CheckerData) -> None:  
    logging.info(get_checker_id())
    epsilon_bV = float(checker_data.config['epsilon_bV'])
    
    for road in checker_data.data.findall("./road"):
        roadID = road.attrib["id"]    
        for geometry in road.findall("./planView/geometry"):
            sGeom = geometry.attrib["s"]
            paramPoly3 = geometry.findall("./paramPoly3")
            if len(paramPoly3) != 1:
                continue                        # no paramPoly3

            aU = float(paramPoly3[0].attrib["aU"])
            if aU != 0.0:
                message = f"road {roadID} has invalid paramPoly3 - aU != 0.0 ({aU}) at s={sGeom}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sGeom, None))

            aV = float(paramPoly3[0].attrib["aV"])
            if aV != 0.0:
                message = f"road {roadID} has invalid paramPoly3 - aV != 0.0 ({aV}) at s={sGeom}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sGeom, None))

            bV = float(paramPoly3[0].attrib["bV"])
            if abs(bV) > epsilon_bV:
                message = f"road {roadID} has invalid paramPoly3 - abs(bV) > {epsilon_bV} ({bV}) at s={sGeom}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sGeom, None))

            bU = float(paramPoly3[0].attrib["bU"])
            if bU <= 0.0:
                message = f"road {roadID} has invalid paramPoly3 - bU <= 0.0 ({bU}) at s={sGeom}"
                checker_data.checker.gen_issue(IssueLevel.WARNING, message, create_location_for_road(road, roadID, sGeom, None))
            

def get_checker_id():
    return 'check valid ParamPoly3'


def get_description():
    return 'check validity of ParamPoly3 attributes (the parameters @aU, @aV and @bV shall be zero, @bU shall be > 0)'


def check(checker_data: CheckerData) ->None:
    check_paramPoly3(checker_data)