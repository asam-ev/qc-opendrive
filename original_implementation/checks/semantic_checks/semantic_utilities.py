from checker_data import CheckerData
from lxml import etree


def get_lanesection_at_s(s: float, lanes_per_section: dict) -> list:
    current_lanesection = lanes_per_section[0.0]
    for key in lanes_per_section:
        if key > s:                                     # TODO, was zurückgeben, wenn bei s eine LaneSection startet/endet
            return current_lanesection
        else:
            current_lanesection = lanes_per_section[key]
    return current_lanesection

def get_lanes(laneSection: etree._Element, side: str, lanes: list) -> None:
    laneSide = laneSection.find(side)
    if laneSide is not None:
        for lane in laneSide.findall("./lane"):
            lanes.append(lane.attrib['id'])

def collect_lanes_per_section(road: etree._Element) -> dict:
    lanes_per_section = dict()
    for laneSection in road.findall("./lanes/laneSection"):
        sValue = float(laneSection.attrib['s'])
        lanes = list()
        get_lanes(laneSection, "left", lanes)
        get_lanes(laneSection, "center", lanes)
        get_lanes(laneSection, "right", lanes)
        lanes_per_section[sValue] = lanes
    return lanes_per_section

class LaneSection:
    def __init__(self, road: etree._Element, laneSection: etree._Element):
        self.treeElement = laneSection
        self.roadElement = road
        self.roadId = road.attrib["id"]
        self.startS = float(laneSection.attrib["s"])
        self.endS = float(road.attrib["length"])
        nextLaneSection = laneSection.getnext()
        if nextLaneSection is not None:
             self.endS = float(nextLaneSection.attrib["s"])

class ConnectedRoad:
    def __init__(self, connectedRoad: etree._Element, Id: str, contactPoint: str):
        self.treeElement = connectedRoad
        self.Id = Id
        self.contactPoint = contactPoint

def getConnectedRoad(road: etree._Element, linkType: str, checker_data: CheckerData) -> ConnectedRoad:
    link = road.find("link")
    if link is None:                        # road has no links
        return None     
    linkTypeNode = link.find(linkType)
    if linkTypeNode is None:                # road has no predecessor/successor
        return None
    connectLinkType = linkTypeNode.attrib["elementType"]
    if connectLinkType != "road":           # road is not connected to another road
        return None
    connectRoadID = linkTypeNode.attrib["elementId"]
    searchString = "./road[@id='" + connectRoadID + "']"
    connectedRoad = checker_data.data.find(searchString)
    if connectedRoad is None:
        return None                         # connected road is not found -> checked in check_road_linkage.py

    if "contactPoint" not in linkTypeNode.attrib:
        contactPoint = ""
    else:
        contactPoint = linkTypeNode.attrib["contactPoint"]
    return ConnectedRoad(connectedRoad, connectRoadID, contactPoint)

def getDrivingLanesAtSide(laneSection :etree._Element, side: str, drivingLanes: list):
    if side == "left" or side == "both":
        lanes = laneSection.find("./left")
        if lanes is not None:                                        # there may be no lane on this side
            for lane in lanes.findall("./lane"):
                laneType = lane.attrib['type']
                if (laneType == "driving" or laneType == "entry" or laneType == "exit" or laneType == "onRamp" or laneType == "offRamp" or 
                    laneType == "connectionRamp"):            # TODO weitere? .... config file
                    drivingLanes.append(lane.attrib['id'])

    if side == "right" or side == "both":
        lanes = laneSection.find("./right")
        if lanes is not None:                                        # there may be no lane on this side
            for lane in lanes.findall("./lane"):
                laneType = lane.attrib['type']
                if (laneType == "driving" or laneType == "entry" or laneType == "exit" or laneType == "onRamp" or laneType == "offRamp" or 
                    laneType == "connectionRamp"):            # TODO weitere? .... config file
                    drivingLanes.append(lane.attrib['id'])                    
