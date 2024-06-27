import os
import sys
import pytest

from typing import List

import main

from qc_opendrive import constants, checks
from qc_opendrive.checks.semantic import semantic_constants

from qc_baselib import Configuration, Result, IssueSeverity

CONFIG_FILE_PATH = "bundle_config.xml"
REPORT_FILE_PATH = "xodr_bundle_report.xqar"


def create_test_config(target_file_path: str):
    test_config = Configuration()
    test_config.set_config_param(name="XodrFile", value=target_file_path)
    test_config.register_checker_bundle(checker_bundle_name=constants.BUNDLE_NAME)
    test_config.set_checker_bundle_param(
        checker_bundle_name=constants.BUNDLE_NAME,
        name="resultFile",
        value=REPORT_FILE_PATH,
    )

    test_config.write_to_file(CONFIG_FILE_PATH)


def check_issues(
    rule_uid: str, issue_count: int, issue_xpath: List[str], severity: IssueSeverity
):
    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    issues = result.get_issues_by_rule_uid(rule_uid)

    assert len(issues) == issue_count

    locations = set()
    for issue in issues:
        for issue_location in issue.locations:
            for xml_location in issue_location.xml_location:
                locations.add(xml_location.xpath)

    for xpath in issue_xpath:
        assert xpath in locations

    for issue in issues:
        assert issue.level == severity


def launch_main(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "-c",
            CONFIG_FILE_PATH,
        ],
    )
    main.main()


def cleanup_files():
    os.remove(REPORT_FILE_PATH)
    os.remove(CONFIG_FILE_PATH)


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "17_invalid",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[3]",
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[3]",
            ],
        ),
        ("17_valid", 0, []),
        ("18_invalid", 1, ["/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[2]"]),
        ("18_valid", 0, []),
        ("17_invalid_older_schema_version", 0, []),
    ],
)
def test_road_lane_access_no_mix_of_deny_or_allow_examples(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/"
    target_file_name = f"road_lane_access_no_mix_of_deny_or_allow_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.access.no_mix_of_deny_or_allow"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        (
            "single_issue",
            1,
            ["/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[3]"],
        ),
        (
            "multiple_issue",
            3,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[3]",
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[4]",
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[4]",
            ],
        ),
    ],
)
def test_road_lane_access_no_mix_of_deny_or_allow_close_match(
    target_file: str, issue_count: int, issue_xpath: List[str], monkeypatch
) -> None:
    base_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/"
    target_file_name = f"close_match_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.access.no_mix_of_deny_or_allow"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection/right/lane[3]",
            ],
        ),
        ("invalid_older_schema_version", 0, []),
    ],
)
def test_road_lane_true_level_one_side(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side/"
    target_file_name = f"road_lane_level_true_one_side_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.level_true_one_side"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            8,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[3]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[3]",
            ],
        ),
        ("valid_wrong_predecessor", 0, []),
        (
            "invalid_wrong_predecessor",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_true_level_one_side_lane_section(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side_lanesection/"
    target_file_name = f"road_lane_level_true_one_side_lanesection_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.level_true_one_side"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            4,
            [
                "/OpenDRIVE/road[1]/lanes/laneSection[1]/left/lane[1]",
                "/OpenDRIVE/road[1]/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road[1]/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road[2]/lanes/laneSection/left/lane[1]",
            ],
        ),
    ],
)
def test_road_lane_true_level_one_side_road(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side_road/"
    target_file_name = f"road_lane_level_true_one_side_road_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.level_true_one_side"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid_incoming",
            3,  # Two issues raised in junction, one issue raised in road
            [
                "/OpenDRIVE/road[1]/lanes/laneSection/right/lane",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane",
            ],
        ),
    ],
)
def test_road_lane_true_level_one_side_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side_junction/"
    target_file_name = f"road_lane_level_true_one_side_junction_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.level_true_one_side"
    issue_severity = IssueSeverity.WARNING

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        # 3 issues for invalid predecessors + 3 issues for missing successors
        (
            "invalid_no_predecessor_road",
            6,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[1]/link/predecessor",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[2]/link/predecessor",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[3]/link/predecessor",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[3]",
            ],
        ),
        # 2 no link issues + 2 invalid link issues + 2 no link from the previous invalid link issues
        (
            "invalid",
            6,
            [
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[1]/link/predecessor",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[3]/link/predecessor",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[3]",
            ],
        ),
    ],
)
def test_road_lane_link_lanes_across_lane_sections(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_lanes_across_lane_sections/"
    target_file_name = f"road_lane_link_lanes_across_lane_sections_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.lane.link.lanes_across_lane_sections"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/road[2]/link/predecessor",
                "/OpenDRIVE/road[3]/link/predecessor",
            ],
        ),
    ],
)
def test_road_linkage_is_junction_needed(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_linkage_is_junction_needed/"
    target_file_name = f"road_linkage_is_junction_needed_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.linkage.is_junction_needed"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


#
@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            2,
            [
                "/OpenDRIVE/junction[2]/connection[1]",
                "/OpenDRIVE/junction[2]/connection[2]",
            ],
        ),
    ],
)
def test_junctions_connection_road_no_incoming_road(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junctions_connection_connect_road_no_incoming_road/"
    target_file_name = (
        f"junctions_connection_connect_road_no_incoming_road_{target_file}.xodr"
    )
    rule_uid = "asam.net:xodr:1.4.0:junctions.connection.connect_road_no_incoming_road"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()
