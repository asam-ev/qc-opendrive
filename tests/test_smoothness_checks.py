# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import pytest

from typing import List

from qc_baselib import IssueSeverity
from qc_opendrive.checks import smoothness

from test_setup import *


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "many_invalid",
            41,
            [
                "/OpenDRIVE/road[1]/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane[3]",
                "/OpenDRIVE/road[1]/lanes/laneSection/left/lane[2]",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane[2]",
                "/OpenDRIVE/road[1]/lanes/laneSection/left/lane[3]",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane[1]",
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
        (
            "junction_invalid_conn_smoothness",
            2,
            [
                "/OpenDRIVE/road[1]/lanes/laneSection/right/lane",
                "/OpenDRIVE/road[3]/lanes/laneSection/left/lane",
                "/OpenDRIVE/road[2]/lanes/laneSection/left/lane",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane",
            ],
        ),
        (
            "junction_valid_conn_smoothness",
            0,
            [],
        ),
        (
            "multiple_successor_invalid",
            1,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
            ],
        ),
        (
            "multiple_successor_valid",
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
    check_issues(
        rule_uid,
        issue_count,
        issue_xpath,
        issue_severity,
        smoothness.lane_smoothness_contact_point_no_horizontal_gaps.CHECKER_ID,
    )
    cleanup_files()
