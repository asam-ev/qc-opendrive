# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

import numpy as np
from scipy.integrate import quad

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_geometry_parampoly3_length_match"
CHECKER_DESCRIPTION = "The actual curve length, as determined by numerical integration over the parameter range, should match '@Length'."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.geometry.parampoly3.length_match"

TOLERANCE_THRESHOLD = 0.001


def _check_all_roads(checker_data: models.CheckerData) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        geometries = utils.get_road_plan_view_geometry_list(road)

        for geometry in geometries:
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

            integral_length, estimated_error = quad(
                utils.arc_length_integrand, 0.0, 1.0, args=(du, dv)
            )

            if np.abs(integral_length - length) > TOLERANCE_THRESHOLD:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    description=f"Length does not match the actual curve length. The estimated absolute error from numerical integration is {estimated_error}",
                    level=IssueSeverity.WARNING,
                    rule_uid=RULE_UID,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(geometry),
                    description=f"Length does not match the actual curve length. The estimated absolute error from numerical integration is {estimated_error}",
                )

                s_coordinate = utils.get_s_from_geometry(geometry)
                if s_coordinate is None:
                    continue

                s_coordinate += length / 2.0

                inertial_point = utils.get_point_xyz_from_road_reference_line(
                    road, s_coordinate
                )

                if inertial_point is not None:
                    checker_data.result.add_inertial_location(
                        checker_bundle_name=constants.BUNDLE_NAME,
                        checker_id=CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description="Geometry where length doesn't match.",
                    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.geometry.parampoly3.length_match

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
    logging.info("Executing road.geometry.parampoly3.length_match check.")

    _check_all_roads(checker_data)
