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
        # 3 issues for missing successors
        (
            "invalid_no_predecessor_road",
            3,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[3]",
            ],
        ),
        # 2 no link issues + 2 missing successors
        (
            "invalid_non_existing_lanes",
            4,
            [
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[3]",
            ],
        ),
        # 2 no lane link + 2 missing successors + 2 missing predecessors
        (
            "invalid_wrong_id",
            6,
            [
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane[3]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[1]",
                "/OpenDRIVE/road/lanes/laneSection[2]/left/lane[2]",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
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


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("valid", 0, []),
        (
            "invalid",
            1,
            [
                "/OpenDRIVE/junction/connection[1]",
                "/OpenDRIVE/junction/connection[2]",
            ],
        ),
    ],
)
def test_junctions_connection_one_connection_element(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junctions_connection_one_connection_element/"
    target_file_name = f"junctions_connection_one_connection_element_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:junctions.connection.one_connection_element"
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
                "/OpenDRIVE/junction/connection[1]",
                "/OpenDRIVE/junction/connection[2]",
                "/OpenDRIVE/junction/connection[2]/laneLink",
            ],
        ),
        (
            "valid_LHT",
            0,
            [],
        ),
        (
            "invalid_LHT",
            2,
            [
                "/OpenDRIVE/junction/connection[1]",
                "/OpenDRIVE/junction/connection[2]",
                "/OpenDRIVE/junction/connection[2]/laneLink",
            ],
        ),
    ],
)
def test_junctions_connection_one_link_to_incoming(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junctions_connection_one_link_to_incoming/"
    target_file_name = f"junctions_connection_one_link_to_incoming_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming"
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
                "/OpenDRIVE/junction/connection[5]/laneLink",
            ],
        ),
    ],
)
def test_junctions_connection_one_link_to_incoming_bidirectional(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junctions_connection_one_link_to_incoming/"
    target_file_name = f"Ex_Bidirectional_Junction_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()


@pytest.mark.parametrize(
    "target_file,issue_count,issue_xpath",
    [
        ("Ex_Entry_Exit", 0, []),
    ],
)
def test_junctions_connection_one_link_to_incoming_direct(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/examples/"
    target_file_name = f"{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming"
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
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_start(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start"
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
                "/OpenDRIVE/road[3]/lanes/laneSection/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_start_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_junction_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start"
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
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_start_inside_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = (
        f"road_lane_link_new_lane_appear_inside_junction_{target_file}.xodr"
    )
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start"
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
                "/OpenDRIVE/road/lanes/laneSection[1]/left/lane[1]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_end(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end"
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
                "/OpenDRIVE/road[1]/lanes/laneSection/left/lane[1]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_end_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_junction_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end"
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
                "/OpenDRIVE/road[2]/lanes/laneSection/left/lane[1]",
            ],
        ),
    ],
)
def test_road_lane_link_zero_width_at_end_inside_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = (
        f"road_lane_link_new_lane_appear_inside_junction_{target_file}.xodr"
    )
    rule_uid = "asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end"
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
                "/OpenDRIVE/road/lanes/laneSection[1]/right/lane",
                "/OpenDRIVE/road/lanes/laneSection[2]/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_new_lane_appear(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.lane.link.new_lane_appear"
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
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane",
                "/OpenDRIVE/road[3]/lanes/laneSection/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_new_lane_appear_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = f"road_lane_link_new_lane_appear_junction_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.4.0:road.lane.link.new_lane_appear"
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
                "/OpenDRIVE/road[1]/lanes/laneSection/right/lane",
                "/OpenDRIVE/road[2]/lanes/laneSection/right/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_new_lane_appear_inside_junction(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = (
        f"road_lane_link_new_lane_appear_inside_junction_{target_file}.xodr"
    )
    rule_uid = "asam.net:xodr:1.4.0:road.lane.link.new_lane_appear"
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
                "/OpenDRIVE/road[1]/lanes/laneSection/right/lane",
                "/OpenDRIVE/road[2]/lanes/laneSection/left/lane[2]",
            ],
        ),
    ],
)
def test_road_lane_link_new_lane_appear_end_contact_point(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/road_lane_link_new_lane_appear/"
    target_file_name = (
        f"road_lane_link_new_lane_appear_end_contact_point_{target_file}.xodr"
    )
    rule_uid = "asam.net:xodr:1.4.0:road.lane.link.new_lane_appear"
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
                "/OpenDRIVE/junction/connection[2]",
            ],
        ),
    ],
)
def test_junction_connection_start_along_linkage(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junction_connection_linkage/"
    target_file_name = f"junction_connection_linkage_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:junctions.connection.start_along_linkage"
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
                "/OpenDRIVE/junction/connection[1]",
            ],
        ),
    ],
)
def test_junction_connection_end_opposite_linkage(
    target_file: str,
    issue_count: int,
    issue_xpath: List[str],
    monkeypatch,
) -> None:
    base_path = "tests/data/junction_connection_linkage/"
    target_file_name = f"junction_connection_linkage_{target_file}.xodr"
    rule_uid = "asam.net:xodr:1.7.0:junctions.connection.end_opposite_linkage"
    issue_severity = IssueSeverity.ERROR

    target_file_path = os.path.join(base_path, target_file_name)
    create_test_config(target_file_path)
    launch_main(monkeypatch)
    check_issues(rule_uid, issue_count, issue_xpath, issue_severity)
    cleanup_files()
