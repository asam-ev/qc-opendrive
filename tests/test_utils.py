import pytest
from lxml import etree
from qc_opendrive.base import utils


def test_get_road_id_map() -> None:
    root = etree.parse("tests/data/utils/Ex_Bidirectional_Junction.xodr")
    road_id_map = utils.get_road_id_map(root)
    assert len(road_id_map) == 6


def test_get_junction_id_map() -> None:
    root = etree.parse("tests/data/utils/Ex_Bidirectional_Junction.xodr")
    junction_id_map = utils.get_junction_id_map(root)
    assert len(junction_id_map) == 1
