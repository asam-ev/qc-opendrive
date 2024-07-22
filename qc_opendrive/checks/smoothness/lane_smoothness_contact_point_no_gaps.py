import logging

import numpy as np

from scipy.special import fresnel
from dataclasses import dataclass

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.geometry import geometry_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
TOLERANCE_THRESHOLD = 0.001


@dataclass
class Point2D:
    x: float
    y: float


def calculate_line_point(s: float, x: float, y: float, heading: float) -> float:
    return Point2D(x=x + s * np.cos(heading), y=y + s * np.sin(heading))


def calculate_arc_point(
    s: float,
    x: float,
    y: float,
    heading: float,
    curvature: float,
) -> float:
    radius = 1 / curvature
    arc_x = radius * np.cos(s / radius)
    arc_y = radius * np.sin(s / radius)
    return Point2D(
        x=(x * np.cos(heading)) + arc_x,
        y=(y * np.sin(heading)) + arc_y,
    )


def calculate_spiral_point(
    s: float,
    x: float,
    y: float,
    heading: float,
    curv_start: float,
    curv_end: float,
) -> float:
    return s


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
    logging.info("Executing lane_smoothness.contact_point_no_gaps check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=geometry_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="lane_smoothness.contact_point_no_gaps",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return
