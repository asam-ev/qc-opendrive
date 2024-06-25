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
