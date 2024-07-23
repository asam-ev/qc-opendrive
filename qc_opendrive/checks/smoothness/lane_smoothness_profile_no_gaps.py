import logging

import numpy as np

from typing import Union
from dataclasses import dataclass
from lxml import etree
from scipy.spatial import distance

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.smoothness import smoothness_constants


import matplotlib.pyplot as plt


RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
# This parameter needs to be configurable later
TOLERANCE_THRESHOLD = 0.1  # meters


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID:

    Description:

    Severity:

    Version range: []

    Remark:

    More info at
        -
    """
    logging.info("Executing lane_smoothness.profile_no_gaps check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=smoothness_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="lane_smoothness.profile_no_gaps",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    plt.figure(figsize=(10, 6))

    for road_id, road in road_id_map.items():
        geometries = utils.get_road_plan_view_geometry_list(road)

        # We can only calculate gaps with 2 or more geometries
        if len(geometries) < 2:
            continue

        # we are assuming geometries is a sorted list on s position
        previous_end_point: Union[models.Point2D, None] = None
        previous_geometry: Union[etree._Element, None] = None
        for geometry in geometries:

            x0 = utils.get_x_from_geometry(geometry)
            y0 = utils.get_y_from_geometry(geometry)
            s0 = utils.get_s_from_geometry(geometry)
            heading = utils.get_heading_from_geometry(geometry)
            length = utils.get_length_from_geometry(geometry)

            if (
                x0 is None
                or y0 is None
                or heading is None
                or length is None
                or s0 is None
            ):
                # what to do when intermediate geometry cannot be calculated?
                # assume we restart the gap search?
                # raise an issue?
                previous_end_point = None
                previous_geometry = None
                continue
            if road_id == 77:
                print(x0, y0, s0, heading, length)

            if previous_end_point is not None:
                gap_size = distance.euclidean(
                    (previous_end_point.x, previous_end_point.y),
                    (x0, y0),
                )
                if gap_size > TOLERANCE_THRESHOLD:
                    # print(
                    #     f"gs = {gap_size}\npp = {(previous_end_point.x, previous_end_point.y)}\n p={(x0, y0)}"
                    # )
                    issue_id = checker_data.result.register_issue(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=smoothness_constants.CHECKER_ID,
                        description=f"The transition between geometry elements should be defined with no gaps.",
                        level=IssueSeverity.ERROR,
                        rule_uid=rule_uid,
                    )

                    checker_data.result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=smoothness_constants.CHECKER_ID,
                        issue_id=issue_id,
                        xpath=checker_data.input_file_xml_root.getpath(
                            previous_geometry
                        ),
                        description=f"First geometry element",
                    )
                    checker_data.result.add_xml_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=smoothness_constants.CHECKER_ID,
                        issue_id=issue_id,
                        xpath=checker_data.input_file_xml_root.getpath(geometry),
                        description=f"Second geometry element",
                    )

            line = utils.get_geometry_line(geometry)
            arc = utils.get_geometry_arc(geometry)
            spiral = utils.get_geometry_spiral(geometry)

            end_point = None
            if line is not None:
                end_point = utils.calculate_line_point(
                    s=s0 + length, s0=s0, x0=x0, y0=y0, heading=heading
                )

                if road_id == 77:
                    x_out = []
                    y_out = []
                    s = np.linspace(s0, s0 + length, 100)
                    for si in s:
                        p = utils.calculate_line_point(
                            s=si, s0=s0, x0=x0, y0=y0, heading=heading
                        )
                        # print(si, p)
                        x_out.append(p.x)
                        y_out.append(p.y)
                    plt.plot(x_out, y_out, label="line(x,y)")
            elif arc is not None:
                arc_curvature = utils.get_curvature_from_arc(arc)

                if arc_curvature is None:
                    previous_end_point = None
                    previous_geometry = None
                    continue

                end_point = utils.calculate_arc_point(
                    s=s0 + length,
                    s0=s0,
                    x0=x0,
                    y0=y0,
                    heading=heading,
                    curvature=arc_curvature,
                )

                if road_id == 77:
                    x_out = []
                    y_out = []
                    s = np.linspace(s0, s0 + length, 100)
                    for si in s:
                        p = utils.calculate_arc_point(
                            s=si,
                            s0=s0,
                            x0=x0,
                            y0=y0,
                            heading=heading,
                            curvature=arc_curvature,
                        )
                        x_out.append(p.x)
                        y_out.append(p.y)
                    plt.plot(x_out, y_out, label="arc(x,y)")

            elif spiral is not None:
                curv_start = utils.get_curv_start_from_spiral(spiral)
                curv_end = utils.get_curv_end_from_spiral(spiral)

                if curv_end is None or curv_start is None:
                    previous_end_point = None
                    previous_geometry = None
                    continue

                end_point = utils.calculate_spiral_point(
                    s=s0 + length,
                    s0=s0,
                    x0=x0,
                    y0=y0,
                    heading=heading,
                    curv_start=curv_start,
                    curv_end=curv_end,
                    length=length,
                )

                if road_id == 77:
                    x_out = []
                    y_out = []
                    s = np.linspace(s0, s0 + length, 100)
                    for si in s:
                        p = utils.calculate_spiral_point(
                            s=si,
                            s0=s0,
                            x0=x0,
                            y0=y0,
                            heading=heading,
                            curv_start=curv_start,
                            curv_end=curv_end,
                            length=length,
                        )
                        x_out.append(p.x)
                        y_out.append(p.y)
                    plt.plot(x_out, y_out, label="spiral(x,y)")

            else:
                previous_end_point = None
                previous_geometry = None
                continue

            previous_end_point = end_point
            previous_geometry = geometry

    plt.title("Multiple Curves Plot")
    plt.xlabel("x")
    plt.ylabel("y")

    # Add a legend
    plt.legend()

    plt.savefig("road_77_curves.png")
