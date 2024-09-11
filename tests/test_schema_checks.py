import os
import pytest
from test_setup import *
from qc_opendrive import constants
from qc_opendrive.checks.schema import schema_constants
from qc_baselib import Result, IssueSeverity, StatusType


def test_valid_schema_positive17(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"positive17.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        len(result.get_issues_by_rule_uid("asam.net:xodr:1.0.0:xml.valid_schema")) == 0
    )

    cleanup_files()


def test_valid_schema_positive18(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"positive18.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        len(result.get_issues_by_rule_uid("asam.net:xodr:1.0.0:xml.valid_schema")) == 0
    )

    cleanup_files()


def test_valid_schema_negative18(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"negative18.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)
    schema_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.valid_schema"
    )
    assert len(schema_issues) == 1
    assert schema_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_valid_schema_negative16(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"negative16.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)
    schema_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.valid_schema"
    )
    assert len(schema_issues) == 1
    assert schema_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_valid_schema_negative17(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"negative17.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)
    schema_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.valid_schema"
    )
    assert len(schema_issues) == 1
    assert schema_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_unsupported_schema_version(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_schema/"
    target_file_name = f"unsupported_schema.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    schema_result = result.get_checker_result(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=schema_constants.CHECKER_ID,
    )

    schema_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.valid_schema"
    )
    assert len(schema_issues) == 0
    assert schema_result.status == StatusType.SKIPPED
    cleanup_files()
