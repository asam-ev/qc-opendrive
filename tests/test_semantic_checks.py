import os
import sys

from src import main


def _compare_reports(src_report_path: str, target_report_path: str) -> None:
    example_xml_text = ""
    output_xml_text = ""
    with open(src_report_path, "r") as report_xml_file:
        example_xml_text = report_xml_file.read()
    with open(target_report_path, "r") as report_xml_file:
        output_xml_text = report_xml_file.read()

    assert output_xml_text == example_xml_text


def test_road_lane_access_no_mix_of_deny_or_allow_17_invalid(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "main.py",
            "-c",
            "tests/data/road_lane_access_no_mix_of_deny_or_allow/configs/road_lane_access_no_mix_of_deny_or_allow_17_invalid_config.xml",
        ],
    )
    main.main()

    _compare_reports(
        "tests/data/road_lane_access_no_mix_of_deny_or_allow/expected/road_lane_access_no_mix_of_deny_or_allow_17_invalid.xqar",
        "xodrBundleReport.xqar",
    )

    os.remove("xodrBundleReport.xqar")
