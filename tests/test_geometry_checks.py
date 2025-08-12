# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import pytest

from typing import List

from qc_baselib import IssueSeverity
from qc_opendrive.checks import geometry

from test_setup import *


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[2]",
            ],
        ),
        (
            "invalid_multiple_cases",
            3,
            [
                "/OpenDRIVE/road/planView/geometry[2]",
                "/OpenDRIVE/road/planView/geometry[3]",
                "/OpenDRIVE/road/planView/geometry[4]",
            ],
        ),
    ],
)
def test_road_geometry_param_poly3_length_match(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_param_poly3_length_match/"
    target_file_name = f"road_geometry_param_poly3_length_match_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.parampoly3.length_match"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_parampoly3_length_match.CHECKER_ID,
    )
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "valid_1",
            0,
            [],
        ),
        (
            "invalid",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection/right/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection/right/lane[2]",
            ],
        ),
        (
            "invalid_1",
            1,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection/left/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_border_overlap_with_inner_lanes(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_border_overlap_with_inner_lanes/"
    target_file_name = f"road_lane_border_overlap_with_inner_lanes_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.lane.border.overlap_with_inner_lanes"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_lane_border_overlap_with_inner_lanes.CHECKER_ID,
    )
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "invalid",
            3,
            [
                "/OpenDRIVE/road/planView/geometry[3]",
                "/OpenDRIVE/road/planView/geometry[4]",
                "/OpenDRIVE/road/planView/geometry[6]",
            ],
        ),
    ],
)
def test_road_geometry_parampoly3_arclength_range(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_parampoly3_arclength_range/"
    target_file_name = f"road_geometry_parampoly3_arclength_range_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.parampoly3.arclength_range"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_parampoly3_arclength_range.CHECKER_ID,
    )
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[2]",
            ],
        ),
    ],
)
def test_road_geometry_param_poly3_normalized_range(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_param_poly3_length_match/"
    target_file_name = f"road_geometry_param_poly3_length_match_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.parampoly3.normalized_range"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_parampoly3_normalized_range.CHECKER_ID,
    )
    cleanup_files()


# Examples from https://publications.pages.asam.net/standards/ASAM_OpenDRIVE/ASAM_OpenDRIVE_Specification/latest/specification/10_roads/10_03_road_linkage.html#top-86fc414c-6211-4777-b40e-466d4551d23e
@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid_1",
            0,
            [],
        ),
        (
            "valid_2",
            0,
            [],
        ),
        (
            "valid_3",
            0,
            [],
        ),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/road[2]",
            ],
        ),
    ],
)
def test_road_geometry_contact_point(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_contact_point/"
    target_file_name = f"{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.contact_point"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_contact_point.CHECKER_ID,
    )
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[3]",
            ],
        ),
    ],
)
def test_road_geometry_elem_asc_order(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_elem_asc_order/"
    target_file_name = f"{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.geometry.elem_asc_order"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_elem_asc_order.CHECKER_ID,
    )
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "valid",
            0,
            [],
        ),
        (
            "aU_invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[1]/paramPoly3",
            ],
        ),
        (
            "aV_invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[1]/paramPoly3",
            ],
        ),
        (
            "bU_invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[2]/paramPoly3",
            ],
        ),
        (
            "bV_invalid",
            1,
            [
                "/OpenDRIVE/road/planView/geometry[2]/paramPoly3",
            ],
        ),
    ],
)
def test_road_geometry_parampoly3_valid_parameters(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_geometry_parampoly3_valid_parameters/"
    target_file_name = f"{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.paramPoly3.valid_parameters"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        geometry.road_geometry_parampoly3_valid_parameters.CHECKER_ID,
    )
    cleanup_files()
