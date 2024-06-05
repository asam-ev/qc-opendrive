import os
import sys
import pytest

from src import main


def _compare_reports(src_report_path: str, target_report_path: str) -> None:
    example_xml_text = ""
    output_xml_text = ""
    with open(src_report_path, "r") as report_xml_file:
        example_xml_text = report_xml_file.read()
    with open(target_report_path, "r") as report_xml_file:
        output_xml_text = report_xml_file.read()

    assert output_xml_text == example_xml_text


@pytest.mark.parametrize(
    "target_file", ["17_invalid", "17_valid", "18_invalid", "18_valid"]
)
def test_road_lane_access_no_mix_of_deny_or_allow(
    target_file: str, monkeypatch
) -> None:
    configs_path = "tests/data/road_lane_access_no_mix_of_deny_or_allow/configs/"
    config_file = f"road_lane_access_no_mix_of_deny_or_allow_{target_file}_config.xml"

    target_config = os.path.join(configs_path, config_file)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "-c",
            target_config,
        ],
    )
    main.main()

    expected_outputs_path = (
        "tests/data/road_lane_access_no_mix_of_deny_or_allow/expected/"
    )
    expected_file = f"road_lane_access_no_mix_of_deny_or_allow_{target_file}.xqar"

    target_expected_output = os.path.join(expected_outputs_path, expected_file)

    _compare_reports(
        target_expected_output,
        "xodrBundleReport.xqar",
    )

    os.remove("xodrBundleReport.xqar")
