import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.performance import performance_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"


def _check_road_superelevations(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    superelevation_list = utils.get_road_superelevations(road)
    for i in range(len(superelevation_list) - 1):
        current_superelevation = superelevation_list[i]
        next_superelevation = superelevation_list[i + 1]
        if utils.are_same_equations(current_superelevation, next_superelevation):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant superelevation declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(road),
                description=f"",
            )


def _check_road_elevations(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    elevation_list = utils.get_road_elevations(road)
    for i in range(len(elevation_list) - 1):
        current_elevation = elevation_list[i]
        next_elevation = elevation_list[i + 1]
        if utils.are_same_equations(current_elevation, next_elevation):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant elevation declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(road),
                description=f"",
            )


def _check_lane_offsets(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    lane_offset_list = utils.get_lane_offsets_from_road(road)
    for i in range(len(lane_offset_list) - 1):
        current_lane_offset = lane_offset_list[i]
        next_lane_offset = lane_offset_list[i + 1]
        if utils.are_same_equations(current_lane_offset, next_lane_offset):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant lane offset declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(road),
                description=f"",
            )


def _check_road_plan_view(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    geometry_list = utils.get_road_plan_view_geometry_list(road)
    for i in range(len(geometry_list) - 1):
        current_geometry = geometry_list[i]
        next_geometry = geometry_list[i + 1]

        if utils.is_line_geometry(current_geometry) and utils.is_line_geometry(
            next_geometry
        ):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant line geometry declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(road),
                description=f"",
            )


def _check_lane_widths(
    checker_data: models.CheckerData, lane: etree._ElementTree, rule_uid: str
) -> None:
    widths = utils.get_lane_width_poly3_list(lane)
    for i in range(len(widths) - 1):
        current_width = widths[i]
        next_width = widths[i + 1]
        if utils.are_same_equations(current_width, next_width):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant lane width declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(lane),
                description=f"",
            )


def _check_lane_borders(
    checker_data: models.CheckerData, lane: etree._ElementTree, rule_uid: str
) -> None:
    borders = utils.get_borders_from_lane(lane)
    for i in range(len(borders) - 1):
        current_border = borders[i]
        next_border = borders[i + 1]
        if utils.are_same_equations(current_border, next_border):
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                description=f"Redudant lane border declaration.",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=performance_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(lane),
                description=f"",
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:performance.avoid_redundant_info

    Description: Redundant elements should be avoided
        Currently support:
            - Road elevation
            - Road superelevation
            - Lane offset
            - Lane width
            - Lane border
            - Consecutive line geometries

    Severity: WARNING

    Version range: [1.7.0, )

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/20
    """
    logging.info("Executing performance.avoid_redundant_info check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=performance_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="performance.avoid_redundant_info",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    road_list = utils.get_roads(checker_data.input_file_xml_root)

    for road in road_list:
        _check_road_elevations(checker_data, road, rule_uid)
        _check_road_superelevations(checker_data, road, rule_uid)
        _check_lane_offsets(checker_data, road, rule_uid)
        _check_road_plan_view(checker_data, road, rule_uid)

        lane_sections = utils.get_lane_sections(road)
        for lane_section in lane_sections:
            lanes = utils.get_left_and_right_lanes_from_lane_section(lane_section)
            for lane in lanes:
                _check_lane_widths(checker_data, lane, rule_uid)
                _check_lane_borders(checker_data, lane, rule_uid)
