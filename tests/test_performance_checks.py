import os
import pytest

from typing import List

from qc_baselib import IssueSeverity

from test_setup import *


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "elevation_valid",
            0,
            [],
        ),
        (
            "elevation_invalid_1",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
        (
            "elevation_invalid_2",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
        (
            "superelevation_valid",
            0,
            [],
        ),
        (
            "superelevation_invalid",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
        (
            "lane_offset_valid",
            0,
            [],
        ),
        (
            "lane_offset_invalid_1",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
        (
            "lane_offset_invalid_2",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
        (
            "lane_width_valid",
            0,
            [],
        ),
        (
            "lane_width_invalid",
            1,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[7]",
            ],
        ),
        (
            "lane_border_valid",
            0,
            [],
        ),
        (
            "lane_border_invalid",
            1,
            [
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
            ],
        ),
        (
            "line_geometry_valid",
            0,
            [],
        ),
        (
            "line_geometry_invalid",
            1,
            [
                "/OpenDRIVE/road",
            ],
        ),
    ],
)
def test_performance_avoid_redundant_info(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/performance_avoid_redundant_info/"
    target_file_name = f"performance_avoid_redundant_info_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:performance.avoid_redundant_info"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()
