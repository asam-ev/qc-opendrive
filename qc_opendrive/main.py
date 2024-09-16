import argparse
import logging
import types

from qc_baselib import Configuration, Result, StatusType
from qc_baselib.models.common import ParamType

from qc_opendrive import constants
from qc_opendrive.checks import semantic
from qc_opendrive.checks import geometry
from qc_opendrive.checks import performance
from qc_opendrive.checks import smoothness
from qc_opendrive.checks import basic
from qc_opendrive.checks import schema
from qc_opendrive.base import models, utils

logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


def args_entrypoint() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="QC OpenDrive Checker",
        description="This is a collection of scripts for checking validity of OpenDrive (.xodr) files.",
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-c", "--config_path")
    parser.add_argument("-g", "--generate_markdown", action="store_true")

    return parser.parse_args()


def execute_checker(
    checker: types.ModuleType,
    checker_data: models.CheckerData,
    required_definition_setting: bool = True,
) -> None:
    # Register checker
    checker_data.result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=checker.CHECKER_ID,
        description=checker.CHECKER_DESCRIPTION,
    )

    # Register rule uid
    splitted_rule_uid = checker.RULE_UID.split(":")
    if len(splitted_rule_uid) != 4:
        raise RuntimeError(f"Invalid rule uid: {checker.RULE_UID}")

    checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=checker.CHECKER_ID,
        emanating_entity=splitted_rule_uid[0],
        standard=splitted_rule_uid[1],
        definition_setting=splitted_rule_uid[2],
        rule_full_name=splitted_rule_uid[3],
    )

    # Check preconditions. If not satisfied then set status as SKIPPED and return
    if not checker_data.result.all_checkers_completed_without_issue(
        checker.CHECKER_PRECONDITIONS
    ):
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.SKIPPED,
        )

        return

    # Checker definition setting. If not satisfied then set status as SKIPPED and return
    if required_definition_setting:
        schema_version = checker_data.schema_version
        definition_setting = splitted_rule_uid[2]
        if (
            schema_version is None
            or utils.compare_versions(schema_version, definition_setting) < 0
        ):
            checker_data.result.set_checker_status(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=checker.CHECKER_ID,
                status=StatusType.SKIPPED,
            )

            return

    # Execute checker
    try:
        checker.check_rule(checker_data)

        # If checker is not explicitly set as SKIPPED, then set it as COMPLETED
        if (
            checker_data.result.get_checker_status(checker.CHECKER_ID)
            != StatusType.SKIPPED
        ):
            checker_data.result.set_checker_status(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=checker.CHECKER_ID,
                status=StatusType.COMPLETED,
            )
    except Exception:
        # If any exception occurs during the check, set the status as ERROR
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.ERROR,
        )


def run_checks(config: Configuration, result: Result) -> None:
    checker_data = models.CheckerData(
        xml_file_path=config.get_config_param("InputFile"),
        input_file_xml_root=None,
        config=config,
        result=result,
        schema_version=None,
    )

    # 1. Run basic checks
    execute_checker(
        basic.valid_xml_document, checker_data, required_definition_setting=False
    )

    # Get xml root if the input file is a valid xml doc
    if result.all_checkers_completed_without_issue(
        {basic.valid_xml_document.CHECKER_ID}
    ):
        checker_data.input_file_xml_root = utils.get_root_without_default_namespace(
            checker_data.xml_file_path
        )

    execute_checker(
        basic.root_tag_is_opendrive, checker_data, required_definition_setting=False
    )
    execute_checker(
        basic.fileheader_is_present, checker_data, required_definition_setting=False
    )
    execute_checker(
        basic.version_is_defined, checker_data, required_definition_setting=False
    )

    # Get schema version if it exists
    if result.all_checkers_completed_without_issue(
        {
            basic.valid_xml_document.CHECKER_ID,
            basic.root_tag_is_opendrive.CHECKER_ID,
            basic.fileheader_is_present.CHECKER_ID,
            basic.version_is_defined.CHECKER_ID,
        }
    ):
        checker_data.schema_version = utils.get_standard_schema_version(
            checker_data.input_file_xml_root
        )

    # 2. Run schema check
    execute_checker(schema.valid_schema, checker_data)

    # 3. Run semantic checks
    execute_checker(semantic.road_lane_level_true_one_side, checker_data)
    execute_checker(semantic.road_lane_access_no_mix_of_deny_or_allow, checker_data)
    execute_checker(semantic.road_lane_link_lanes_across_lane_sections, checker_data)
    execute_checker(semantic.road_linkage_is_junction_needed, checker_data)
    execute_checker(semantic.road_lane_link_zero_width_at_start, checker_data)
    execute_checker(semantic.road_lane_link_zero_width_at_end, checker_data)
    execute_checker(semantic.road_lane_link_new_lane_appear, checker_data)
    execute_checker(
        semantic.junctions_connection_connect_road_no_incoming_road, checker_data
    )
    execute_checker(semantic.junctions_connection_one_connection_element, checker_data)
    execute_checker(semantic.junctions_connection_one_link_to_incoming, checker_data)
    execute_checker(semantic.junctions_connection_start_along_linkage, checker_data)
    execute_checker(semantic.junctions_connection_end_opposite_linkage, checker_data)

    # 4. Run geometry checks
    execute_checker(geometry.road_geometry_parampoly3_length_match, checker_data)
    execute_checker(geometry.road_lane_border_overlap_with_inner_lanes, checker_data)
    execute_checker(geometry.road_geometry_parampoly3_arclength_range, checker_data)
    execute_checker(geometry.road_geometry_parampoly3_normalized_range, checker_data)

    # 5. Run performance checks
    execute_checker(performance.performance_avoid_redundant_info, checker_data)

    # 6. Run smoothness checks
    execute_checker(
        smoothness.lane_smoothness_contact_point_no_horizontal_gaps, checker_data
    )


def main():
    args = args_entrypoint()

    logging.info("Initializing checks")

    config = Configuration()
    config.load_from_file(xml_file_path=args.config_path)

    result = Result()
    result.register_checker_bundle(
        name=constants.BUNDLE_NAME,
        build_date="2024-06-05",
        description="OpenDrive checker bundle",
        version=constants.BUNDLE_VERSION,
        summary="",
    )
    result.set_result_version(version=constants.BUNDLE_VERSION)

    input_file_path = config.get_config_param("InputFile")
    input_param = ParamType(name="InputFile", value=input_file_path)
    result.get_checker_bundle_result(constants.BUNDLE_NAME).params.append(input_param)

    run_checks(config, result)

    result.write_to_file(
        config.get_checker_bundle_param(
            checker_bundle_name=constants.BUNDLE_NAME, param_name="resultFile"
        )
    )

    if args.generate_markdown:
        result.write_markdown_doc("generated_checker_bundle_doc.md")

    logging.info("Done")


if __name__ == "__main__":
    main()
