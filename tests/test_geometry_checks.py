import os
import sys
import pytest

from typing import List

from qc_baselib import IssueSeverity

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
    rule_uid = "asam.net:xodr:1.7.0:road.geometry.param_poly3.length_match"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
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
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()
