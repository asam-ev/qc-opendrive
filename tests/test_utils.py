# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import pytest
from lxml import etree
from qc_opendrive.base import utils


def test_get_root_without_default_namespace() -> None:
    # file containing namespace
    root = utils.get_root_without_default_namespace("tests/data/utils/namespace.xodr")
    assert type(root) == etree._ElementTree
    # file does not contain namespace
    root = utils.get_root_without_default_namespace(
        "tests/data/utils/Ex_Bidirectional_Junction.xodr"
    )
    assert type(root) == etree._ElementTree


def test_get_road_id_map() -> None:
    root = utils.get_root_without_default_namespace(
        "tests/data/utils/Ex_Bidirectional_Junction.xodr"
    )
    road_id_map = utils.get_road_id_map(root)
    assert len(road_id_map) == 6


def test_get_junction_id_map() -> None:
    root = utils.get_root_without_default_namespace(
        "tests/data/utils/Ex_Bidirectional_Junction.xodr"
    )
    junction_id_map = utils.get_junction_id_map(root)
    assert len(junction_id_map) == 1


def test_get_point_xyz_from_road_invalid_s() -> None:
    root = utils.get_root_without_default_namespace("tests/data/utils/simple_line.xodr")

    road = utils.get_roads(root)[0]

    point = utils.get_point_xyz_from_road(road, -0.001, -10, -20)

    assert point is None

    point = utils.get_point_xyz_from_road(road, 100.001, -10, -20)

    assert point is None


@pytest.mark.parametrize(
    "file_name,s,t,h,x,y,z",
    [
        ("simple_line.xodr", 30, -10, -20, 30, -10, -20),
        ("simple_line_heading.xodr", 30, 10, 20, -10, 30, 20),
        (
            "Ex_Line-Spiral-Arc.xodr",
            0,
            0,
            0,
            -56.53979238754325,
            -34.39446366782007,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            230,
            0,
            0,
            111.21223886865663,
            94.90682833835331,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            230,
            10,
            0,
            101.26793707002476,
            95.96080259692272,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            230,
            -10,
            0,
            121.1565406672885,
            93.8528540797839,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            120,
            10,
            0,
            52.61995309748058,
            14.38548916295234,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            120,
            -10,
            0,
            60.789014235577646,
            -3.870097382596728,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            150,
            10,
            0,
            74.12961916583495,
            29.09285535716386,
            0.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            150,
            10,
            20,
            74.12961916583495,
            29.09285535716386,
            20.0,
        ),
        (
            "Ex_Line-Spiral-Arc.xodr",
            150,
            -10,
            0,
            88.45632996588242,
            15.137735950587523,
            0.0,
        ),
        ("simple_line_elevation.xodr", 0, 0, 0, 0, 0, 0),
        ("simple_line_elevation.xodr", 5, 0, 0, 5, 0, 5),
        ("simple_line_elevation.xodr", 5, 10, 0, 5, 10, 5),
        ("simple_line_elevation.xodr", 5, -10, 0, 5, -10, 5),
        ("simple_line_heading_and_elevation.xodr", 0, 5, 0, -5, 0, 0),
        ("simple_line_heading_and_elevation.xodr", 0, -5, 0, 5, 0, 0),
        ("simple_line_heading_and_elevation.xodr", 20, -5, 0, 5, 20, 20),
        ("simple_line_heading_and_elevation.xodr", 20, 5, 0, -5, 20, 20),
        (
            "Ex_Line-Spiral-Arc_elevation.xodr",
            150,
            10,
            0,
            74.12961916583495,
            29.09285535716386,
            150,
        ),
        (
            "Ex_Line-Spiral-Arc_elevation.xodr",
            150,
            -10,
            0,
            88.45632996588242,
            15.137735950587523,
            150,
        ),
        (
            "simple_line_elevation.xodr",
            0,
            0,
            10,
            0,
            0,
            10,
        ),
        (
            "simple_line_elevation.xodr",
            0,
            0,
            -10,
            0,
            0,
            -10,
        ),
        (
            "simple_line_superelevation.xodr",
            0,
            0,
            0,
            0,
            0,
            0,
        ),
        (
            "simple_line_superelevation.xodr",
            0,
            5,
            0,
            0,
            3.535534483629909,
            3.5355333282354717,
        ),
        (
            "simple_line_superelevation.xodr",
            0,
            -5,
            0,
            0,
            -3.535534483629909,
            -3.5355333282354717,
        ),
        (
            "simple_line_superelevation.xodr",
            50,
            5,
            0,
            50,
            3.535534483629909,
            3.5355333282354717,
        ),
        (
            "simple_line_superelevation.xodr",
            50,
            -5,
            0,
            50,
            -3.535534483629909,
            -3.5355333282354717,
        ),
        (
            "simple_line_superelevation.xodr",
            0,
            0,
            10,
            0.0,
            -7.0710666564709435,
            7.071068967259818,
        ),
        (
            "simple_line_heading_and_elevation_and_superelevation.xodr",
            50,
            5,
            0,
            -3.5355344833850797,
            50,
            53.5355333282354717,
        ),
        (
            "simple_line_heading_and_elevation_and_superelevation.xodr",
            50,
            -5,
            0,
            3.53553448388698,
            50,
            50 - 3.5355333282354717,
        ),
        (
            "Ex_Line-Spiral-Arc_elevation_and_superelevation.xodr",
            150,
            -5,
            0,
            83.82560356938673,
            19.64835535961951,
            150 - 3.5355333282354717,
        ),
        (
            "Ex_Line-Spiral-Arc_elevation_and_superelevation.xodr",
            150,
            5,
            0,
            78.76034556233064,
            24.58223594813187,
            153.5355333282354717,
        ),
        (
            "Ex_Line-Spiral-Arc_elevation_and_superelevation.xodr",
            150,
            5,
            10,
            83.82560191408653,
            19.648356971986246,
            160.6066022954953,
        ),
        (
            "Ex_Line-Spiral-Arc_superelevation.xodr",
            150,
            -5,
            0,
            83.82560356938673,
            19.64835535961951,
            -3.5355333282354717,
        ),
        (
            "Ex_Line-Spiral-Arc_superelevation.xodr",
            150,
            5,
            0,
            78.76034556233064,
            24.58223594813187,
            3.5355333282354717,
        ),
        (
            "Ex_Line-Spiral-Arc_superelevation.xodr",
            150,
            5,
            10,
            83.82560191408653,
            19.648356971986246,
            10.60660229549529,
        ),
    ],
)
def test_get_point_xyz_from_road(file_name, s, t, h, x, y, z) -> None:
    root = utils.get_root_without_default_namespace(f"tests/data/utils/{file_name}")

    road = utils.get_roads(root)[0]
    point = utils.get_point_xyz_from_road(road, s, t, h)

    assert point.x == pytest.approx(x, abs=1e-6)
    assert point.y == pytest.approx(y, abs=1e-6)
    assert point.z == pytest.approx(z, abs=1e-6)
