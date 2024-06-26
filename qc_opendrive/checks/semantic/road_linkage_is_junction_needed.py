import logging

from lxml import etree

from qc_baselib import IssueSeverity

from qc_opendrive import constants
from qc_opendrive.checks import utils, models
from qc_opendrive.checks.semantic import semantic_constants

RULE_INITIAL_SUPPORTED_SCHEMA_VERSION = "1.7.0"


def _raise_road_linkage_is_junction_issue(
    checker_data: models.CheckerData,
    rule_uid: str,
    road_linkage_element: etree._Element,
    linkage_tag: models.LinkageTag,
) -> None:
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        description=f"Road cannot have ambiguous {linkage_tag.value}",
        level=IssueSeverity.ERROR,
        rule_uid=rule_uid,
    )

    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=semantic_constants.CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(road_linkage_element),
        description="",
    )


def _check_road_linkage_is_junction_needed(
    checker_data: models.CheckerData, rule_uid: str
) -> None:
    roads = utils.get_roads(checker_data.input_file_xml_root)

    if len(roads) < 2:
        return

    road_linkage_successor_set = set()
    road_linkage_predecessor_set = set()

    for road in roads:
        road_junction_id = utils.get_road_junction_id(road)

        # Verify if road is part of junction, connecting roads can have multiple
        # successors point to them and be predecessor of multiple roads.
        # We don't need to verify this rule for junction roads.
        if road_junction_id is None or road_junction_id == -1:
            road_predecessor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.PREDECESSOR
            )

            if road_predecessor_linkage is not None:
                # in case another road use the same predecessor the linkage is
                # unclear
                if road_predecessor_linkage.id in road_linkage_predecessor_set:
                    predecessor_link = utils.get_road_link_element(
                        road, road_predecessor_linkage.id, models.LinkageTag.PREDECESSOR
                    )
                    _raise_road_linkage_is_junction_issue(
                        checker_data,
                        rule_uid,
                        predecessor_link,
                        models.LinkageTag.PREDECESSOR,
                    )
                else:
                    road_linkage_predecessor_set.add(road_predecessor_linkage.id)

            road_successor_linkage = utils.get_road_linkage(
                road, models.LinkageTag.SUCCESSOR
            )

            if road_successor_linkage is not None:
                # in case another road use the same successor the linkage is
                # unclear
                if road_successor_linkage.id in road_linkage_successor_set:
                    successor_link = utils.get_road_link_element(
                        road, road_successor_linkage.id, models.LinkageTag.SUCCESSOR
                    )
                    _raise_road_linkage_is_junction_issue(
                        checker_data,
                        rule_uid,
                        successor_link,
                        models.LinkageTag.SUCCESSOR,
                    )
                else:
                    road_linkage_successor_set.add(road_successor_linkage.id)


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
