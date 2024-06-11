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


def xml_string_to_bool(value: str):
    return value.lower() in ("true",)
