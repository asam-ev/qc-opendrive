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

CHECKER_ID = "check_asam_xodr_road_geometry_elem_asc_order"
CHECKER_DESCRIPTION = (
    "<geometry> elements shall be defined in ascending order along the road reference line according to the s-coordinate."
)
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.geometry.elem_asc_order"


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


def _check_geometry_elements_in_ascending_order(
        checker_data: models.CheckerData,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        geometry_list = utils.get_road_plan_view_geometry_list(road)
        last_s_coordinate = 0.0
        for geometry in geometry_list:
            current_s_coordinate = get_s_from_geometry(geometry)

            if current_s_coordinate >= last_s_coordinate:
                last_s_coordinate = current_s_coordinate
            else:
                _raise_issue(checker_data, geometry)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.geometry.elem_asc_order

    Description: <geometry> elements shall be defined in ascending order along the road reference line according to the
    s-coordinate.

    Severity: ERROR

    Version range: [1.4.0, )

    Remark:
        This check currently relies on the accuracy of the scipy.integrate.quad method.
        The estimated absolute error of the numerical integration is included in
        the issue description message.
    """
    logging.info("Executing road.geometry.asc_order check")
    _check_geometry_elements_in_ascending_order(checker_data)
