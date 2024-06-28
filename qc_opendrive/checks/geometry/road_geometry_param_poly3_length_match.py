from dataclasses import dataclass
import logging

import numpy as np
from scipy.integrate import quad

from typing import Union, List, Dict, Set
from enum import Enum

from lxml import etree

from qc_baselib import Configuration, Result, IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.geometry import geometry_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
TOLERANCE_THRESHOLD = 0.001


def _integrand(t, du, dv) -> float:
    """
    The equation to calculate the length of a parametric curve represented by u(t), v(t)
    is integral of sqrt(du^2 + dv^2) dt.

    More info at
        - https://en.wikipedia.org/wiki/Arc_length
    """
    return np.sqrt(du(t) ** 2 + dv(t) ** 2)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.geometry.param_poly3.length_match

    Description: The actual curve length, as determined by numerical integration over
        the parameter range, should match '@Length'.

    Severity: WARNING

    Version range: [1.7.0, )

    Remark:
        This check currently relies on the accuracy of the scipy.integrate.quad method.
        The estimated absolute error of the numerical integration is included in the issue description message.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/5
    """
    logging.info("Executing road.lane.link.lanes_across_lane_sections check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=geometry_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.geometry.param_poly3.length_match",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    geometry_elements = checker_data.input_file_xml_root.xpath("//geometry")

    for geometry in geometry_elements:
        length = utils.get_length_from_geometry(geometry)
        if length is None:
            continue

        param_poly3 = utils.get_normalized_param_poly3_from_geometry(geometry)

        if param_poly3 is None:
            continue

        u = utils.poly3_to_polynomial(param_poly3.u)
        v = utils.poly3_to_polynomial(param_poly3.v)
        du = u.deriv()
        dv = v.deriv()

        integral_length, estimated_error = quad(_integrand, 0.0, 1.0, args=(du, dv))

        if np.abs(integral_length - length) > TOLERANCE_THRESHOLD:
            issue_id = checker_data.result.register_issue(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=geometry_constants.CHECKER_ID,
                description=f"Length does not match the actual curve length. The estimated absolute error from numerical integration is {estimated_error}",
                level=IssueSeverity.WARNING,
                rule_uid=rule_uid,
            )

            checker_data.result.add_xml_location(
                checker_bundle_name=constants.BUNDLE_NAME,
                checker_id=geometry_constants.CHECKER_ID,
                issue_id=issue_id,
                xpath=checker_data.input_file_xml_root.getpath(geometry),
                description=f"",
            )
