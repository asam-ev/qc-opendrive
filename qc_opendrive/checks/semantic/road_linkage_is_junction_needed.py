import logging

from typing import Dict, Set, List
from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.4.0"


def _raise_road_linkage_is_junction_needed_issue(
    checker_data: models.CheckerData,
    rule_uid: str,
    road_linkage_elements: List[etree._Element],
    linkage_tag: models.LinkageTag,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description=f"Road cannot have ambiguous {linkage_tag.value}, a junction is needed.",
        level=IssueSeverity.ERROR,
        rule_uid=rule_uid,
    )

    for element in road_linkage_elements:
        checker_data.result.add_xml_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=semantic_constants.CHECKER_ID,
            issue_id=issue_id,
            xpath=checker_data.input_file_xml_root.getpath(element),
            description="",
        )


def _check_road_linkage_is_junction_needed(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    if len(roads) < 2:
        return

    road_linkage_successor_map: Dict[int, Set] = {}
    road_linkage_predecessor_map: Dict[int, Set] = {}

    for road in roads:
        # Verify if road is not part of a junction to proceed.
        # Junction connecting roads can share common successors or predecessors
        # and they are used to distinguish ambiguity.
        # We don't need to verify this rule for junction roads.
        if not utils.road_belongs_to_junction(road):
            road_predecessor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.PREDECESSOR
            )

            if road_predecessor_linkage is not None:
                predecessor_link = utils.get_road_link_element(
                    road, road_predecessor_linkage.id, models.LinkageTag.PREDECESSOR
                )
                if road_predecessor_linkage.id not in road_linkage_predecessor_map:
                    road_linkage_predecessor_map[road_predecessor_linkage.id] = set()

                road_linkage_predecessor_map[road_predecessor_linkage.id].add(
                    predecessor_link
                )

            road_successor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.SUCCESSOR
            )

            if road_successor_linkage is not None:
                # in case another road use the same successor the linkage is
                # unclear
                successor_link = utils.get_road_link_element(
                    road, road_successor_linkage.id, models.LinkageTag.SUCCESSOR
                )
                if road_successor_linkage.id not in road_linkage_successor_map:
                    road_linkage_successor_map[road_successor_linkage.id] = set()

                road_linkage_successor_map[road_successor_linkage.id].add(
                    successor_link
                )

    for predecessor_elements in road_linkage_predecessor_map.values():
        # in case two roads use the same predecessor the linkage is
        # unclear
        if len(predecessor_elements) > 1:
            _raise_road_linkage_is_junction_needed_issue(
                checker_data,
                rule_uid,
                list(predecessor_elements),
                models.LinkageTag.PREDECESSOR,
            )

    for successor_elements in road_linkage_successor_map.values():
        # in case two roads road use the same successor the linkage is
        # unclear
        if len(successor_elements) > 1:
            _raise_road_linkage_is_junction_needed_issue(
                checker_data,
                rule_uid,
                list(predecessor_elements),
                models.LinkageTag.SUCCESSOR,
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Implements a rule to check if a junction is needed in roads linkage in case
    of ambiguity.

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/4
    """
    logging.info("Executing road.linkage.is_junction_needed check")

    rule_uid = checker_data.result.register_rule(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        emanating_entity="asam.net",
        standard="xodr",
        definition_setting=RULE_INITIAL_SUPPORTED_SCHEMA_VERSION,
        rule_full_name="road.linkage.is_junction_needed",
    )

    if checker_data.schema_version < RULE_INITIAL_SUPPORTED_SCHEMA_VERSION:
        logging.info(
            f"Schema version {checker_data.schema_version} not supported. Skipping rule."
        )
        return

    _check_road_linkage_is_junction_needed(checker_data, rule_uid)
