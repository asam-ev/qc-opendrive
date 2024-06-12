from dataclasses import dataclass
from lxml import etree

from qc_baselib import Configuration, Result


@dataclass
class CheckerData:
    input_file_xml_root: etree._ElementTree
    config: Configuration
    result: Result
    schema_version: str
