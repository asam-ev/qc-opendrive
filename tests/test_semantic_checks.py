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


def check_issues_xpath_match(issues_count: int, issue_xpath: List[int]):
    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    checker = result.get_checker_result(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
    )

    assert checker.checker_id == semantic_constants.CHECKER_ID
    assert len(checker.issues) == issues_count

    if len(issue_xpath) > 0:
        for index, xpath in enumerate(issue_xpath):
            assert len(checker.issues[index].locations) == 1
            assert len(checker.issues[index].locations[0].xml_location) == 1
            assert checker.issues[index].locations[0].xml_location[0].xpath == xpath


def check_issues_severity_match(issues_count: int, issue_severity: List[IssueSeverity]):
    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    checker = result.get_checker_result(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
    )

    assert checker.checker_id == semantic_constants.CHECKER_ID
    assert len(checker.issues) == issues_count

    if len(issue_severity) > 0:
        for index, severity in enumerate(issue_severity):
            assert checker.issues[index].level == severity


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
    "target_file,issues_count,issue_xpath",
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
    target_file: str, issues_count: int, issue_xpath: List[str], monkeypatch
) -> None:
    base_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/"
    target_file_name = f"road_lane_access_no_mix_of_deny_or_allow_{target_file}.xodr"

    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    check_issues_xpath_match(issues_count, issue_xpath)

    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issues_count,issue_xpath",
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
    target_file: str, issues_count: int, issue_xpath: List[str], monkeypatch
) -> None:
    base_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/"
    target_file_name = f"close_match_{target_file}.xodr"

    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    check_issues_xpath_match(issues_count, issue_xpath)

    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issues_count,issue_xpath,issue_severity",
    [
        ("valid", 0, [], []),
        (
            "invalid",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection/right/lane[3]",
            ],
            [IssueSeverity.ERROR, IssueSeverity.ERROR],
        ),
        ("invalid_older_schema_version", 0, [], []),
    ],
)
def test_road_lane_true_level_one_side(
    target_file: str,
    issues_count: int,
    issue_xpath: List[str],
    issue_severity: List[IssueSeverity],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side/"
    target_file_name = f"road_lane_level_true_one_side_{target_file}.xodr"

    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    check_issues_xpath_match(issues_count, issue_xpath)
    check_issues_severity_match(issues_count, issue_severity)

    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issues_count,issue_xpath,issue_severity",
    [
        ("valid", 0, [], []),
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
            [
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
            ],
        ),
        ("valid_wrong_predecessor", 0, [], []),
        (
            "invalid_wrong_predecessor",
            2,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[2]",
            ],
            [
                IssueSeverity.WARNING,
                IssueSeverity.WARNING,
            ],
        ),
    ],
)
def test_road_lane_true_level_one_side_lane_section(
    target_file: str,
    issues_count: int,
    issue_xpath: List[str],
    issue_severity: List[IssueSeverity],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_level_true_one_side_lanesection/"
    target_file_name = f"road_lane_level_true_one_side_lanesection_{target_file}.xodr"

    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    check_issues_xpath_match(issues_count, issue_xpath)
    check_issues_severity_match(issues_count, issue_severity)

    cleanup_files()
