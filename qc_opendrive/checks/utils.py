from typing import List

from lxml import etree


def get_lanes(root: etree._ElementTree) -> List[etree._ElementTree]:
    lanes = []

    for lane in root.iter("lane"):
        lanes.append(lane)

    return lanes


def get_lane_sections(root: etree._ElementTree) -> List[etree._ElementTree]:
    lane_sections = []

    for lane_section in root.iter("laneSection"):
        lane_sections.append(lane_section)

    return lane_sections


def get_roads(root: etree._ElementTree) -> List[etree._ElementTree]:
    roads = []

    for road in root.iter("road"):
        roads.append(road)

    return roads


def xml_string_to_bool(value: str):
    return value.lower() in ("true",)


def get_standard_schema_version(root: etree._ElementTree) -> str:
    header = root.find("header")
    header_attrib = header.attrib
    version = f"{header_attrib['revMajor']}.{header_attrib['revMinor']}.0"
    return version
