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


def _create_contact_point_id_from_road_linkage(road_linkage: models.RoadLinkage) -> str:
    return f"{road_linkage.id}-{road_linkage.contact_point.value}"


def _get_road_linkage_from_contact_point_id(
    contact_point_id: str,
) -> models.RoadLinkage:
    contact_point_id_split = contact_point_id.split("-")
    return models.RoadLinkage(
        id=contact_point_id_split[0],
        contact_point=models.ContactPoint(contact_point_id_split[1]),
    )


def _check_road_linkage_is_junction_needed(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    if len(roads) < 2:
        return

    road_contact_point_map: Dict[str, List[etree._Element]] = {}

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
                contact_point_id = _create_contact_point_id_from_road_linkage(
                    road_predecessor_linkage
                )
                if contact_point_id not in road_contact_point_map:
                    road_contact_point_map[contact_point_id] = []
                predecessor_link = utils.get_road_link_element(
                    road, road_predecessor_linkage.id, models.LinkageTag.PREDECESSOR
                )

                road_contact_point_map[contact_point_id].append(predecessor_link)

            road_successor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.SUCCESSOR
            )

            if road_successor_linkage is not None:
                contact_point_id = _create_contact_point_id_from_road_linkage(
                    road_successor_linkage
                )
                if contact_point_id not in road_contact_point_map:
                    road_contact_point_map[contact_point_id] = []
                successor_link = utils.get_road_link_element(
                    road, road_successor_linkage.id, models.LinkageTag.PREDECESSOR
                )

                road_contact_point_map[contact_point_id].append(successor_link)

    for contact_point_id, elements in road_contact_point_map.items():
        # in case two roads use the same contact point for a "target" road the
        # linkage is unclear
        if len(elements) > 1:
            road_linkage = _get_road_linkage_from_contact_point_id(contact_point_id)

            linkage_tag = None

            if road_linkage.contact_point == models.ContactPoint.END:
                linkage_tag = models.LinkageTag.SUCCESSOR
            elif road_linkage.contact_point == models.ContactPoint.START:
                linkage_tag = models.LinkageTag.PREDECESSOR
            else:
                return

            _raise_road_linkage_is_junction_needed_issue(
                checker_data,
                rule_uid,
                elements,
                linkage_tag,
            )


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.4.0:road.linkage.is_junction_needed

    Description: Two roads shall only be linked directly, if the linkage is clear.
    If the relationship to successor or predecessor is ambiguous, junctions
    shall be used.

    Severity: ERROR

    Version range: [1.4.0, )

    Remark:
        None

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
