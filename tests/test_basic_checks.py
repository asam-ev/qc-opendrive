import os
import pytest
from test_setup import *
from qc_baselib import Result, IssueSeverity, StatusType
from qc_opendrive.checks import basic


def test_valid_xml_document_positive(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_xml_document/"
    target_file_name = f"xml.valid_xml_document.positive.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.valid_xml_document.CHECKER_ID)
        == StatusType.COMPLETED
    )

    assert (
        len(result.get_issues_by_rule_uid("asam.net:xodr:1.0.0:xml.valid_xml_document"))
        == 0
    )

    cleanup_files()


def test_valid_xml_document_negative(
    monkeypatch,
) -> None:
    base_path = "tests/data/valid_xml_document/"
    target_file_name = f"xml.valid_xml_document.negative.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.valid_xml_document.CHECKER_ID)
        == StatusType.COMPLETED
    )

    xml_doc_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.valid_xml_document"
    )
    assert len(xml_doc_issues) == 1
    assert xml_doc_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_root_tag_is_opendrive_positive(
    monkeypatch,
) -> None:
    base_path = "tests/data/root_tag_is_opendrive/"
    target_file_name = f"positive.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.root_tag_is_opendrive.CHECKER_ID)
        == StatusType.COMPLETED
    )

    assert (
        len(
            result.get_issues_by_rule_uid(
                "asam.net:xodr:1.0.0:xml.root_tag_is_opendrive"
            )
        )
        == 0
    )

    cleanup_files()


def test_root_tag_is_opendrive_negative(
    monkeypatch,
) -> None:
    base_path = "tests/data/root_tag_is_opendrive/"
    target_file_name = f"negative.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.root_tag_is_opendrive.CHECKER_ID)
        == StatusType.COMPLETED
    )

    xml_doc_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.root_tag_is_opendrive"
    )
    assert len(xml_doc_issues) == 1
    assert xml_doc_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_fileheader_is_present_positive(
    monkeypatch,
) -> None:
    base_path = "tests/data/fileheader_is_present/"
    target_file_name = f"positive.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.fileheader_is_present.CHECKER_ID)
        == StatusType.COMPLETED
    )

    assert (
        len(
            result.get_issues_by_rule_uid(
                "asam.net:xodr:1.0.0:xml.fileheader_is_present"
            )
        )
        == 0
    )

    cleanup_files()


def test_fileheader_is_present_negative(
    monkeypatch,
) -> None:
    base_path = "tests/data/fileheader_is_present/"
    target_file_name = f"negative.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.fileheader_is_present.CHECKER_ID)
        == StatusType.COMPLETED
    )

    xml_doc_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.fileheader_is_present"
    )
    assert len(xml_doc_issues) == 1
    assert xml_doc_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_version_is_defined__positive(
    monkeypatch,
) -> None:
    base_path = "tests/data/version_is_defined/"
    target_file_name = f"positive.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        == StatusType.COMPLETED
    )

    assert (
        len(result.get_issues_by_rule_uid("asam.net:xodr:1.0.0:xml.version_is_defined"))
        == 0
    )

    cleanup_files()


def test_version_is_defined_negative_attr(
    monkeypatch,
) -> None:
    base_path = "tests/data/version_is_defined/"
    target_file_name = f"negative_no_attr.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        == StatusType.COMPLETED
    )

    xml_doc_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.version_is_defined"
    )
    assert len(xml_doc_issues) == 1
    assert xml_doc_issues[0].level == IssueSeverity.ERROR
    cleanup_files()


def test_version_is_defined_negative_type(
    monkeypatch,
) -> None:
    base_path = "tests/data/version_is_defined/"
    target_file_name = f"negative_no_type.xodr"
    target_file_path = os.path.join(base_path, target_file_name)

    create_test_config(target_file_path)

    launch_main(monkeypatch)

    result = Result()
    result.load_from_file(REPORT_FILE_PATH)

    assert (
        result.get_checker_status(basic.version_is_defined.CHECKER_ID)
        == StatusType.COMPLETED
    )

    xml_doc_issues = result.get_issues_by_rule_uid(
        "asam.net:xodr:1.0.0:xml.version_is_defined"
    )
    assert len(xml_doc_issues) == 1
    assert xml_doc_issues[0].level == IssueSeverity.ERROR
    cleanup_files()
