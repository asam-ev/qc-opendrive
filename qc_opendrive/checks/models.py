from dataclasses import dataclass
from enum import Enum
from lxml import etree

from qc_baselib import Configuration, Result


@dataclass
class CheckerData:
    input_file_xml_root: etree._ElementTree
    config: Configuration
    result: Result
    schema_version: str


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


@dataclass
class WidthPoly3:
    poly3: Poly3
    s_offset: float
