# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import logging
import types

from qc_baselib import Configuration, Result, StatusType
from qc_baselib.models.result import RuleType

from qc_opendrive import constants
from qc_opendrive import version
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


def check_preconditions(
    checker: types.ModuleType, checker_data: models.CheckerData
) -> bool:
    """
    Check preconditions. If not satisfied then set status as SKIPPED and return False
    """
    if checker_data.result.all_checkers_completed_without_issue(
        checker.CHECKER_PRECONDITIONS
    ):
        return True
    else:
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.SKIPPED,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            checker.CHECKER_ID,
            "Preconditions are not satisfied. Skip the check.",
        )

        return False


def check_version(checker: types.ModuleType, checker_data: models.CheckerData) -> bool:
    """
    Check definition setting and applicable version.
    If not satisfied then set status as SKIPPED or ERROR and return False
    """
    schema_version = checker_data.schema_version

    rule_uid = RuleType(rule_uid=checker.RULE_UID)
    definition_setting_expr = f">={rule_uid.definition_setting}"
    match_definition_setting = version.match(schema_version, definition_setting_expr)

    applicable_version = getattr(checker, "APPLICABLE_VERSION", "")

    # Check whether applicable version specification is valid
    if not version.is_valid_version_expression(applicable_version):
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.ERROR,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            checker.CHECKER_ID,
            f"The applicable version {applicable_version} is not valid. Skip the check.",
        )

        return False

    # Check whether definition setting specification is valid
    if not version.is_valid_version_expression(definition_setting_expr):
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.ERROR,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            checker.CHECKER_ID,
            f"The definition setting {rule_uid.definition_setting} is not valid. Skip the check.",
        )

        return False

    # First, check applicable version
    if not version.match(schema_version, applicable_version):
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.SKIPPED,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME,
            checker.CHECKER_ID,
            f"Version {schema_version} is not valid according to the applicable version {applicable_version}. Skip the check.",
        )

        return False

    # Check definition setting if there is no applicable version or applicable version has no lower bound
    if not version.has_lower_bound(applicable_version):
        if not match_definition_setting:
            checker_data.result.set_checker_status(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=checker.CHECKER_ID,
                status=StatusType.SKIPPED,
            )

            checker_data.result.add_checker_summary(
                constants.BUNDLE_NAME,
                checker.CHECKER_ID,
                f"Version {schema_version} is not valid according to definition setting {definition_setting_expr}. Skip the check.",
            )

            return False

    return True


def execute_checker(
    checker: types.ModuleType,
    checker_data: models.CheckerData,
    version_required: bool = True,
) -> None:
    # Register checker
    checker_data.result.register_checker(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=checker.CHECKER_ID,
        description=checker.CHECKER_DESCRIPTION,
    )

    # Register rule uid
    checker_data.result.register_rule_by_uid(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=checker.CHECKER_ID,
        rule_uid=checker.RULE_UID,
    )

    # Check preconditions. If not satisfied then set status as SKIPPED and return
    satisfied_preconditions = check_preconditions(checker, checker_data)
    if not satisfied_preconditions:
        return

    # Check definition setting and applicable version
    if version_required:
        satisfied_version = check_version(checker, checker_data)
        if not satisfied_version:
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
    except Exception as e:
        # If any exception occurs during the check, set the status as ERROR
        checker_data.result.set_checker_status(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=checker.CHECKER_ID,
            status=StatusType.ERROR,
        )

        checker_data.result.add_checker_summary(
            constants.BUNDLE_NAME, checker.CHECKER_ID, f"Error: {str(e)}."
        )

        logging.exception(f"An error occur in {checker.CHECKER_ID}.")


def run_checks(config: Configuration, result: Result) -> None:
    checker_data = models.CheckerData(
        xml_file_path=config.get_config_param("InputFile"),
        input_file_xml_root=None,
        config=config,
        result=result,
        schema_version=None,
    )

    # 1. Run basic checks
    execute_checker(basic.valid_xml_document, checker_data, version_required=False)

    # Get xml root if the input file is a valid xml doc
    if result.all_checkers_completed_without_issue(
        {basic.valid_xml_document.CHECKER_ID}
    ):
        checker_data.input_file_xml_root = utils.get_root_without_default_namespace(
            checker_data.xml_file_path
        )

    execute_checker(basic.root_tag_is_opendrive, checker_data, version_required=False)
    execute_checker(basic.fileheader_is_present, checker_data, version_required=False)
    execute_checker(basic.version_is_defined, checker_data, version_required=False)

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
        description="OpenDrive checker bundle",
        version=constants.BUNDLE_VERSION,
        summary="",
    )
    result.set_result_version(version=constants.BUNDLE_VERSION)

    run_checks(config, result)

    result.copy_param_from_config(config)

    result.write_to_file(
        config.get_checker_bundle_param(
            checker_bundle_name=constants.BUNDLE_NAME, param_name="resultFile"
        ),
        generate_summary=True,
    )

    if args.generate_markdown:
        result.write_markdown_doc("generated_checker_bundle_doc.md")

    logging.info("Done")


if __name__ == "__main__":
    main()
