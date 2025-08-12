# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from lxml import etree
from qc_baselib import IssueSeverity

from qc_opendrive import basic_preconditions
from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.base.utils import get_s_from_geometry

CHECKER_ID = "check_asam_xodr_road_geometry_parampoly3_valid_parameters"
CHECKER_DESCRIPTION = (
    "The local u/v coordinate system should be aligned with the s/t coordinate system of the start point (meaning that the curve starts in the direction given by @hdg, and at the position given by @x and @y). To achieve this, the polynomial parameter coefficients have to be @aU=@aV=@bV=0, @bU>0."
)
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.geometry.paramPoly3.valid_parameters"


FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
        checker_data: models.CheckerData,
        geometry: etree._ElementTree,
):
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=CHECKER_DESCRIPTION,
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(geometry),
        description=CHECKER_DESCRIPTION,
    )


def _check_parampoly3_valid_parameters(
        checker_data: models.CheckerData,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        geometry_list = utils.get_road_plan_view_geometry_list(road)

        for geometry in geometry_list:
            length = utils.get_length_from_geometry(geometry)
            if length is None:
                continue

            param_poly3 = None
            for element in geometry.iter("paramPoly3"):
                param_poly3 = element

            if param_poly3 is None:
                continue

            if abs(utils.to_float(param_poly3.get("aU"))) > FLOAT_COMPARISON_THRESHOLD\
                or abs(utils.to_float(param_poly3.get("aV"))) > FLOAT_COMPARISON_THRESHOLD\
                or abs(utils.to_float(param_poly3.get("bV"))) > FLOAT_COMPARISON_THRESHOLD\
                or not utils.to_float(param_poly3.get("bU")) > FLOAT_COMPARISON_THRESHOLD:
                _raise_issue(checker_data, param_poly3)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.geometry.paramPoly3.valid_parameters

    Description: The local u/v coordinate system should be aligned with the s/t coordinate system of the start point
    (meaning that the curve starts in the direction given by @hdg, and at the position given by @x and @y). To achieve
    this, the polynomial parameter coefficients have to be @aU=@aV=@bV=0, @bU>0.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        This check currently relies on the accuracy of the scipy.integrate.quad method.
        The estimated absolute error of the numerical integration is included in
        the issue description message.
    """
    logging.info("Executing road.geometry.asc_order check")
    _check_parampoly3_valid_parameters(checker_data)
