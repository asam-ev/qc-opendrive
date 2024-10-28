# SPDX-License-Identifier: MPL-2.0
# Copyright 2024, ASAM e.V.
# This Source Code Form is subject to the terms of the Mozilla
# Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from dataclasses import dataclass
from typing import List

from lxml import etree

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils

from qc_opendrive import basic_preconditions


CHECKER_ID = "check_asam_xodr_road_lane_access_no_mix_of_deny_or_allow"
CHECKER_DESCRIPTION = (
    "Check if there is mixed content on access rules for the same sOffset on lanes."
)
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:road.lane.access.no_mix_of_deny_or_allow"


@dataclass
class SOffsetInfo:
    s_offset: float
    rule: str


def _check_all_roads(checker_data: models.CheckerData) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    for road in roads:
        lane_sections_with_length = (
            utils.get_sorted_lane_sections_with_length_from_road(road)
        )

        for lane_section_with_length in lane_sections_with_length:
            lane_section = lane_section_with_length.lane_section
            length = lane_section_with_length.length
            lanes = utils.get_left_and_right_lanes_from_lane_section(lane_section)
            s_section = utils.get_s_from_lane_section(lane_section)

            for lane in lanes:
                access_s_offset_info: List[SOffsetInfo] = []

                access: etree._Element
                for access in lane.iter("access"):
                    rule = access.get("rule")
                    if rule is None:
                        continue

                    s_offset = utils.get_s_offset_from_access(access)
                    if s_offset is None:
                        continue

                    for s_offset_info in access_s_offset_info:
                        if (
                            abs(s_offset_info.s_offset - s_offset) <= 1e-6
                            and rule != s_offset_info.rule
                        ):
                            issue_id = checker_data.result.register_issue(
                                checker_bundle_name=constants.BUNDLE_NAME,
                                checker_id=CHECKER_ID,
                                description="At a given s-position, either only deny or only allow values shall be given, not mixed.",
                                level=IssueSeverity.ERROR,
                                rule_uid=RULE_UID,
                            )

                            path = checker_data.input_file_xml_root.getpath(access)

                            previous_rule = s_offset_info.rule
                            current_rule = rule

                            checker_data.result.add_xml_location(
                                checker_bundle_name=constants.BUNDLE_NAME,
                                checker_id=CHECKER_ID,
                                issue_id=issue_id,
                                xpath=path,
                                description=f"First encounter of {current_rule} having {previous_rule} before.",
                            )

                            if s_section is None:
                                continue

                            s = s_section + s_offset + (length - s_offset) / 2.0
                            t = utils.get_t_middle_point_from_lane_by_s(
                                road, lane_section, lane, s
                            )

                            if t is None:
                                continue

                            inertial_point = utils.get_point_xyz_from_road(
                                road, s, t, 0.0
                            )
                            if inertial_point is not None:
                                checker_data.result.add_inertial_location(
                                    checker_bundle_name=constants.BUNDLE_NAME,
                                    checker_id=CHECKER_ID,
                                    issue_id=issue_id,
                                    x=inertial_point.x,
                                    y=inertial_point.y,
                                    z=inertial_point.z,
                                    description="Mixed access point.",
                                )

                    access_s_offset_info.append(
                        SOffsetInfo(
                            s_offset=s_offset,
                            rule=rule,
                        )
                    )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if there is mixed content on access rules for
    the same sOffset on lanes.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/1
    """
    logging.info("Executing road.lane.access.no_mix_of_deny_or_allow check")

    _check_all_roads(checker_data)
