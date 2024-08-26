import logging

import numpy as np
from scipy.integrate import quad

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive.checks.geometry import geometry_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"
TOLERANCE_THRESHOLD = 0.001


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.geometry.parampoly3.arclength_range

    Description: If @prange="arcLength", p shall be chosen in [0, @Length from geometry].

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        This check currently relies on the accuracy of the scipy.integrate.quad method.
        The estimated absolute error of the numerical integration is included in
        the issue description message.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/38
    """
    logging.info("Executing road.geometry.parampoly3.arclength_range check.")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=geometry_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.geometry.parampoly3.arclength_range",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        geometry_list = utils.get_road_plan_view_geometry_list(road)

        for geometry in geometry_list:
            length = utils.get_length_from_geometry(geometry)
            if length is None:
                continue

            param_poly3 = utils.get_arclen_param_poly3_from_geometry(geometry)

            if param_poly3 is None:
                continue

            u = utils.poly3_to_polynomial(param_poly3.u)
            v = utils.poly3_to_polynomial(param_poly3.v)
            du = u.deriv()
            dv = v.deriv()

            integral_length, estimated_error = quad(
                utils.arc_length_integrand, 0.0, length, args=(du, dv)
            )

            if np.abs(integral_length - length) > TOLERANCE_THRESHOLD:
                issue_id = checker_data.result.register_issue(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=geometry_constants.CHECKER_ID,
                    description=f"Length does not match the actual curve length. The estimated absolute error from numerical integration is {estimated_error}",
                    level=IssueSeverity.ERROR,
                    rule_uid=rule_uid,
                )

                checker_data.result.add_xml_location(
                    checker_bundle_name=constants.BUNDLE_NAME,
                    checker_id=geometry_constants.CHECKER_ID,
                    issue_id=issue_id,
                    xpath=checker_data.input_file_xml_root.getpath(geometry),
                    description=f"",
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
                        checker_id=geometry_constants.CHECKER_ID,
                        issue_id=issue_id,
                        x=inertial_point.x,
                        y=inertial_point.y,
                        z=inertial_point.z,
                        description=f"Length does not match the actual curve length. The estimated absolute error from numerical integration is {estimated_error}",
                    )
