import os
import sys
import pytest

import main

from qc_opendrive import constants, checks

from qc_baselib import Configuration, Result

CONFIG_FILE_PATH = "bundle_config.xml"
REPORT_FILE_PATH = "xodr_bundle_report.xqar"


@pytest.mark.parametrize(
    "target_file,issues_count,issue_xpath",
    [
        ("17_invalid", 1, "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[3]"),
        ("17_valid", 0, ""),
        ("18_invalid", 1, "/OpenDRIVE/road/lanes/laneSection/left/lane[1]/access[2]"),
        ("18_valid", 0, ""),
    ],
)
def test_road_lane_access_no_mix_of_deny_or_allow(
    target_file: str, issues_count: int, issue_xpath: str, monkeypatch
) -> None:
    base_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/"
    target_file_name = f"road_lane_access_no_mix_of_deny_or_allow_{target_file}.xodr"

    target_file_path = os.path.join(base_path, target_file_name)

    test_config = Configuration()
    test_config.set_config_param(name="XodrFile", value=target_file_path)
    test_config.register_checker_bundle(checker_bundle_name=constants.BUNDLE_NAME)
    test_config.set_checker_bundle_param(
        checker_bundle_name=constants.BUNDLE_NAME,
        name="resultFile",
        value=REPORT_FILE_PATH,
    )
    print(test_config._configuration.to_xml())
    test_config.write_to_file(CONFIG_FILE_PATH)

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

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    checker = result.get_checker_result(
        checker_bundle_name=constants.BUNDLE_NAME, checker_id=checks.semantic.CHECKER_ID
    )

    assert checker.checker_id == checks.semantic.CHECKER_ID
    assert len(checker.issues) == issues_count

    if issue_xpath != "":
        assert len(checker.issues[0].locations) == 1
        assert len(checker.issues[0].locations[0].xml_location) == 1
        assert checker.issues[0].locations[0].xml_location[0].xpath == issue_xpath

    os.remove(REPORT_FILE_PATH)
    os.remove(CONFIG_FILE_PATH)
