# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging
from typing import Optional

from lxml import etree
from numpy.ma.core import true_divide
from qc_baselib import IssueSeverity

from qc_opendrive import basic_preconditions
from qc_opendrive import constants
from qc_opendrive.base import models, utils

CHECKER_ID = "check_asam_xodr_road_geometry_contact_point"
CHECKER_DESCRIPTION = (
    "If two roads are connected without a junction, the road reference line of a new road shall always begin at the <contactPoint> element of its successor or predecessor road. The road reference lines may be directed in opposite directions."
)
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.geometry.contact_point"


FLOAT_COMPARISON_THRESHOLD = 1e-6


def _raise_issue(
        checker_data: models.CheckerData,
        road: etree._ElementTree,
        contact_point: models.Point3D,
):
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description="The road reference line does not begin at the contact point of its predecessor or successor.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(road),
        description="The road reference line does not begin at the contact point of its predecessor or successor.",
    )

    if contact_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=contact_point.x,
            y=contact_point.y,
            z=contact_point.z,
            description="The road reference line does not begin at the contact point of its predecessor or successor.",
        )


def _xcessor_contact_point_has_issue(xcessor, road_contact_point_xyz, road_id_map) -> Optional[models.Point3D]:
    if xcessor is None:
        return None

    if xcessor.get("elementType") == "junction":
        return None

    xcessor_road = road_id_map.get(utils.to_int(xcessor.get("elementId")))
    if xcessor_road is None:
        return None

    contact_point = xcessor.get("contactPoint")
    if contact_point is None:
        return None

    xcessor_contact_point_xyz = utils.get_point_xyz_from_contact_point(xcessor_road, contact_point)
    if xcessor_contact_point_xyz is None:
        return None

    # allow error in the order of 1e-6 for floating point comparison of coordinates
    if any(
            abs(getattr(road_contact_point_xyz, attr) - getattr(xcessor_contact_point_xyz, attr))
            >= FLOAT_COMPARISON_THRESHOLD
            for attr in ("x", "y", "z")
    ):
        return xcessor_contact_point_xyz

    return None


def _check_junctions_connection_lane_follow_direction(
        checker_data: models.CheckerData,
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for road in roads:
        # if it is a junction, rule does not apply
        if utils.to_int(road.get("junction")) == 1:
            continue

        road_start = (road.find("link").find("predecessor"),
                      utils.get_start_point_xyz_from_road_reference_line(road))
        road_end = (road.find("link").find("successor"),
                    utils.get_end_point_xyz_from_road_reference_line(road))

        for road_side in (road_start, road_end):
            xcessor_contact_point_xyz_with_issue = _xcessor_contact_point_has_issue(*road_side, road_id_map)
            if xcessor_contact_point_xyz_with_issue is not None:
                _raise_issue(checker_data, road, xcessor_contact_point_xyz_with_issue)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:road.geometry.contact_point

    Description: If two roads are connected without a junction, the road reference line of a new road shall always begin
    at the <contactPoint> element of its successor or predecessor road. The road reference lines may be directed in opposite directions.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        This check currently relies on the accuracy of the scipy.integrate.quad method.
        The estimated absolute error of the numerical integration is included in
        the issue description message.
    """
    logging.info("Executing road.geometry.contact_point check")
    _check_junctions_connection_lane_follow_direction(checker_data)
