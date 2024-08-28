import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.checks.performance import performance_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
FLOAT_TOLERANCE = 1e-6


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

            inertial_point = utils.get_point_xyz_from_road_reference_line(
                road, next_superelevation.s_offset
            )
            if inertial_point is not None:
                checker_data.result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=performance_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Redudant superelevation declaration.",
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

            inertial_point = utils.get_point_xyz_from_road_reference_line(
                road, next_elevation.s_offset
            )
            if inertial_point is not None:
                checker_data.result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=performance_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Redudant elevation declaration.",
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

            s = next_lane_offset.s_offset
            t = utils.poly3_to_polynomial(next_lane_offset.poly3)(0.0)

            if s is None or t is None:
                continue

            inertial_point = utils.get_point_xyz_from_road(road, s, t, 0.0)
            if inertial_point is not None:
                checker_data.result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=performance_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Redudant lane offset declaration.",
                )


def _check_road_plan_view(
    checker_data: models.CheckerData, road: etree._ElementTree, rule_uid: str
) -> None:
    geometry_list = utils.get_road_plan_view_geometry_list(road)
    for i in range(len(geometry_list) - 1):
        current_geometry = geometry_list[i]
        next_geometry = geometry_list[i + 1]

        current_geometry_heading = utils.get_heading_from_geometry(current_geometry)
        next_geometry_heading = utils.get_heading_from_geometry(next_geometry)

        if current_geometry_heading is None or next_geometry_heading is None:
            continue

        if (
            utils.is_line_geometry(current_geometry)
            and utils.is_line_geometry(next_geometry)
            and abs(current_geometry_heading - next_geometry_heading) < FLOAT_TOLERANCE
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

            s_offset = utils.get_s_from_geometry(next_geometry)
            if s_offset is not None:
                inertial_point = utils.get_point_xyz_from_road_reference_line(
                    road, s_offset
                )
                if inertial_point is not None:
                    checker_data.result.add_inertial_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=performance_constants.CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description="Redundant line geometry declaration.",
                    )


def _check_lane_widths(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    lane_section: etree._ElementTree,
    lane: etree._ElementTree,
    rule_uid: str,
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

            s_section = utils.get_s_from_lane_section(lane_section)

            if s_section is None:
                continue

            s = s_section + next_width.s_offset

            inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
                road, lane_section, lane, s
            )

            if inertial_point is not None:
                checker_data.result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=performance_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Redudant lane width declaration.",
                )


def _check_lane_borders(
    checker_data: models.CheckerData,
    road: etree._ElementTree,
    lane_section: etree._ElementTree,
    lane: etree._ElementTree,
    rule_uid: str,
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

            s_section = utils.get_s_from_lane_section(lane_section)

            if s_section is None:
                continue

            s = s_section + next_border.s_offset

            inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
                road, lane_section, lane, s
            )

            if inertial_point is not None:
                checker_data.result.add_inertial_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=performance_constants.CHECKER_ID,
                    issue_id=issue_id,
                    x=inertial_point.x,
                    y=inertial_point.y,
                    z=inertial_point.z,
                    description="Redudant lane border declaration.",
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
                _check_lane_widths(checker_data, road, lane_section, lane, rule_uid)
                _check_lane_borders(checker_data, road, lane_section, lane, rule_uid)
