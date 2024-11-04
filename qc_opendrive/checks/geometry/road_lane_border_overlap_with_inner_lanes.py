# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

from dataclasses import dataclass
import logging
from typing import List

import numpy as np
from lxml import etree

from qc_baselib import IssueSeverity, StatusType
from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_road_lane_border_overlap_with_inner_lanes"
CHECKER_DESCRIPTION = "Lane borders shall not intersect inner lanes."
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.4.0:road.lane.border.overlap_with_inner_lanes"

TOLERANCE_THRESHOLD = 1e-6


@dataclass
class BorderPair:
    left_lane_poly3: models.Poly3
    right_lane_poly3: models.Poly3
    ds_left_start: float
    ds_right_start: float
    ds_length: float


def _create_border_pairs(
    left_lane_borders: List[models.OffsetPoly3],
    right_lane_borders: List[models.OffsetPoly3],
    lane_section_length: float,
) -> List[BorderPair]:
    if len(left_lane_borders) == 0 or len(right_lane_borders) == 0:
        return []

    sorted_left_lane_borders = sorted(
        left_lane_borders, key=lambda border: border.s_offset
    )

    sorted_right_lane_borders = sorted(
        right_lane_borders, key=lambda border: border.s_offset
    )

    left_iterator = iter(sorted_left_lane_borders)
    right_iterator = iter(sorted_right_lane_borders)

    current_left = next(left_iterator)
    current_right = next(right_iterator)
    s_offset_start = 0.0

    next_left = next(left_iterator, None)
    next_right = next(right_iterator, None)

    border_pairs = []

    while True:
        # Construct the current pair
        next_left_s_offset = None
        if next_left is None:
            next_left_s_offset = lane_section_length
        else:
            next_left_s_offset = next_left.s_offset

        next_right_s_offset = None
        if next_right is None:
            next_right_s_offset = lane_section_length
        else:
            next_right_s_offset = next_right.s_offset

        s_offset_end = min(next_left_s_offset, next_right_s_offset)
        border_pairs.append(
            BorderPair(
                left_lane_poly3=current_left.poly3,
                right_lane_poly3=current_right.poly3,
                ds_left_start=(s_offset_start - current_left.s_offset),
                ds_right_start=(s_offset_start - current_right.s_offset),
                ds_length=(s_offset_end - s_offset_start),
            )
        )

        if next_left is None and next_right is None:
            break

        # Jump to the next pair
        if (
            next_left is not None
            and np.abs(next_left_s_offset - s_offset_end) <= TOLERANCE_THRESHOLD
        ):
            current_left = next_left
            next_left = next(left_iterator, None)

        if (
            next_right is not None
            and np.abs(next_right_s_offset - s_offset_end) <= TOLERANCE_THRESHOLD
        ):
            current_right = next_right
            next_right = next(right_iterator, None)

        s_offset_start = s_offset_end

    return border_pairs


def _raise_issue(
    checker_data: models.CheckerData,
    lane_section_with_length: models.LaneSectionWithLength,
    road,
    left_lane: etree._ElementTree,
    right_lane: etree._ElementTree,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"Outer lane border intersects or stays within inner lane border.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(left_lane),
        description=f"Outer lane border intersects or stays within inner lane border.",
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(right_lane),
        description=f"Outer lane border intersects or stays within inner lane border.",
    )

    s_section = utils.get_s_from_lane_section(lane_section_with_length.lane_section)

    if s_section is None:
        return

    s = s_section + lane_section_with_length.length / 2.0

    left_inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
        road, lane_section_with_length.lane_section, left_lane, s
    )

    if left_inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=left_inertial_point.x,
            y=left_inertial_point.y,
            z=left_inertial_point.z,
            description="Outer lane border intersects or stays within inner lane border.",
        )

    right_inertial_point = utils.get_middle_point_xyz_at_height_zero_from_lane_by_s(
        road, lane_section_with_length.lane_section, right_lane, s
    )

    if right_inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=right_inertial_point.x,
            y=right_inertial_point.y,
            z=right_inertial_point.z,
            description="Outer lane border intersects or stays within inner lane border.",
        )


def _intersect_or_stay_within(border_pair: BorderPair) -> bool:
    """
    Check if the two borders intersect or the left border stays within the right lane border
    by the following condition:

    Let f(ds) = t_left(ds + left_start) - t_right(ds + right_start)
    where t(ds) =  a + b*ds + c*ds^2 + d*ds^3

    For ds in range [0, length], check if f(ds) >= 0

    This function expands f(ds) and check if f(ds) is always non-negative when ds is in [0, length].
    As f(ds) is a third order polynomial, the check is done based on the following conditions
    Condition 1: f(0) >= 0
    Condition 2: f(length) >= 0
    Condition 3: for all the real roots of the equation f'(ds) = 0
        If a root belongs to [0, length] then f(root) >= 0
    """
    # f(ds) = a + b*ds + c*ds^2 + d*ds^3
    a = (
        border_pair.left_lane_poly3.a
        - border_pair.right_lane_poly3.a
        + border_pair.left_lane_poly3.b * border_pair.ds_left_start
        - border_pair.right_lane_poly3.b * border_pair.ds_right_start
        + border_pair.left_lane_poly3.c * border_pair.ds_left_start**2
        - border_pair.right_lane_poly3.c * border_pair.ds_right_start**2
        + border_pair.left_lane_poly3.d * border_pair.ds_left_start**3
        - border_pair.right_lane_poly3.d * border_pair.ds_right_start**3
    )

    b = (
        border_pair.left_lane_poly3.b
        - border_pair.right_lane_poly3.b
        + 2 * border_pair.left_lane_poly3.c * border_pair.ds_left_start
        - 2 * border_pair.right_lane_poly3.c * border_pair.ds_right_start
        + 3 * border_pair.left_lane_poly3.d * border_pair.ds_left_start**2
        - 3 * border_pair.right_lane_poly3.d * border_pair.ds_right_start**2
    )

    c = (
        border_pair.left_lane_poly3.c
        - border_pair.right_lane_poly3.c
        + 3 * border_pair.left_lane_poly3.d * border_pair.ds_left_start
        - 3 * border_pair.right_lane_poly3.d * border_pair.ds_right_start
    )
    d = border_pair.left_lane_poly3.d - border_pair.right_lane_poly3.d

    f = np.polynomial.Polynomial([a, b, c, d])
    if f(0) < -TOLERANCE_THRESHOLD or f(border_pair.ds_length) < -TOLERANCE_THRESHOLD:
        return True

    f_deriv = f.deriv()
    roots = f_deriv.roots()
    real_roots = [x for x in roots if np.isreal(x)]
    for real_root in real_roots:
        if f(real_root) < -TOLERANCE_THRESHOLD:
            return True

    return False


def _check_overlap(
    left_lane: etree._ElementTree,
    right_lane: etree._ElementTree,
    lane_section_with_length: models.LaneSectionWithLength,
    road: etree._ElementTree,
    checker_data: models.CheckerData,
) -> None:
    """
    Check if a left lane overlap with a right lane.
    """
    left_lane_borders = utils.get_borders_from_lane(left_lane)
    right_lane_borders = utils.get_borders_from_lane(right_lane)

    border_pairs = _create_border_pairs(
        left_lane_borders, right_lane_borders, lane_section_with_length.length
    )

    for border_pair in border_pairs:
        has_issue = _intersect_or_stay_within(border_pair)
        if has_issue:
            _raise_issue(
                checker_data,
                lane_section_with_length,
                road,
                left_lane,
                right_lane,
            )
            return


def _check_overlap_among_lane_list(
    lanes: List[etree._ElementTree],
    lane_section_with_length: models.LaneSectionWithLength,
    road: etree._ElementTree,
    checker_data: models.CheckerData,
) -> None:
    lanes = [lane for lane in lanes if utils.get_lane_id(lane) is not None]
    sorted_lanes = sorted(lanes, key=lambda lane: utils.get_lane_id(lane))
    for right_lane_index in range(0, len(sorted_lanes)):
        for left_lane_index in range(right_lane_index + 1, len(sorted_lanes)):
            _check_overlap(
                sorted_lanes[left_lane_index],
                sorted_lanes[right_lane_index],
                lane_section_with_length,
                road,
                checker_data,
            )


def _check_road(road: etree._ElementTree, checker_data: models.CheckerData) -> None:
    sorted_lane_sections_with_length = (
        utils.get_sorted_lane_sections_with_length_from_road(road)
    )

    for lane_section in sorted_lane_sections_with_length:
        left_lanes = utils.get_left_lanes_from_lane_section(lane_section.lane_section)
        _check_overlap_among_lane_list(left_lanes, lane_section, road, checker_data)

        right_lanes = utils.get_right_lanes_from_lane_section(lane_section.lane_section)
        _check_overlap_among_lane_list(right_lanes, lane_section, road, checker_data)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.lane.border.overlap_with_inner_lanes

    Description: Lane borders shall not intersect inner lanes.

    Severity: ERROR

    Version range: [1.4.0, )

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/7
    """
    logging.info("Executing road.lane.border.overlap_with_inner_lanes check.")

    road_list = utils.get_roads(checker_data.input_file_xml_root)

    for road in road_list:
        _check_road(road, checker_data)
