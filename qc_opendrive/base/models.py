from dataclasses import dataclass
from enum import Enum
from lxml import etree
from typing import Union

from qc_baselib import Configuration, Result


@dataclass
class CheckerData:
    xml_file_path: str
    input_file_xml_root: Union[None, etree._ElementTree]
    config: Configuration
    result: Result
    schema_version: Union[None, str]


class LinkageTag(str, Enum):
    PREDECESSOR = "predecessor"
    SUCCESSOR = "successor"


class ContactPoint(str, Enum):
    START = "start"
    END = "end"


@dataclass
class RoadLinkage:
    id: int
    contact_point: ContactPoint


@dataclass
class Poly3:
    a: float
    b: float
    c: float
    d: float


class ParamPoly3Range(str, Enum):
    ARC_LENGTH = "arcLength"
    NORMALIZED = "normalized"


@dataclass
class ParamPoly3:
    u: Poly3
    v: Poly3
    range: ParamPoly3Range


@dataclass
class ContactingLaneSection:
    lane_section: etree._ElementTree
    linkage_tag: LinkageTag


@dataclass
class ContactingLaneSections:
    incoming: etree._ElementTree
    connection: etree._ElementTree


class TrafficHandRule(str, Enum):
    LHT = "LHT"
    RHT = "RHT"


@dataclass
class LaneSectionWithLength:
    lane_section: etree._ElementTree
    length: float


@dataclass
class OffsetPoly3:
    poly3: Poly3
    s_offset: float


class LaneDirection(str, Enum):
    STANDARD = "standard"
    REVERSED = "reversed"
    BOTH = "both"


@dataclass
class Point3D:
    x: float
    y: float
    z: float


@dataclass
class Point2D:
    x: float
    y: float
