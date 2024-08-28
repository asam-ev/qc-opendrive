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
            "many_invalid",
            29,
            [
                "/OpenDRIVE/road[11]/lanes/laneSection[1]/right/lane[3]",
                "/OpenDRIVE/road[11]/lanes/laneSection[2]/right/lane[4]",
                "/OpenDRIVE/road[11]/lanes/laneSection[1]/right/lane[4]",
                "/OpenDRIVE/road[11]/lanes/laneSection[2]/right/lane[5]",
                "/OpenDRIVE/road[12]/lanes/laneSection[1]/left/lane[3]",
                "/OpenDRIVE/road[12]/lanes/laneSection[2]/left/lane[4]",
                "/OpenDRIVE/road[12]/lanes/laneSection[1]/left/lane[4]",
                "/OpenDRIVE/road[12]/lanes/laneSection[2]/left/lane[5]",
                "/OpenDRIVE/road[12]/lanes/laneSection[1]/right/lane[5]",
                "/OpenDRIVE/road[12]/lanes/laneSection[2]/right/lane[4]",
                "/OpenDRIVE/road[15]/planView/geometry[2]",
                "/OpenDRIVE/road[15]/planView/geometry[3]",
                "/OpenDRIVE/road[3]/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road[6]/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road[3]/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road[6]/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road[3]/lanes/laneSection/left/lane[3]",
                "/OpenDRIVE/road[6]/lanes/laneSection/left/lane[3]",
                "/OpenDRIVE/road[9]/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road[10]/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road[9]/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road[10]/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road[9]/lanes/laneSection/left/lane[3]",
                "/OpenDRIVE/road[10]/lanes/laneSection/left/lane[3]",
            ],
        ),
        (
            "simple_valid",
            0,
            [],
        ),
    ],
)
def test_road_lane_access_no_mix_of_deny_or_allow_examples(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/smoothness_example/"
    target_file_name = f"{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()
