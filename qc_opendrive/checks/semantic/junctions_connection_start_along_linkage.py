import logging

from lxml import etree

from qc_baselib import IssueSeverity, StatusType

from qc_opendrive import constants
from qc_opendrive.base import models, utils
from qc_opendrive import basic_preconditions

CHECKER_ID = "check_asam_xodr_junctions_connection_start_along_linkage"
CHECKER_DESCRIPTION = 'The value "start" shall be used to indicate that the connecting road runs along the linkage indicated in the element.'
CHECKER_PRECONDITIONS = basic_preconditions.CHECKER_PRECONDITIONS
RULE_UID = "asam.net:xodr:1.7.0:junctions.connection.start_along_linkage"


def _raise_issue(
    checker_data: models.CheckerData,
    connection: etree._Element,
    connection_road: etree._Element,
):
    issue_id = checker_data.result.register_issue(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        description=f"The value 'start' shall be used to indicate that the connecting road runs along the linkage indicated in the element.",
        level=IssueSeverity.ERROR,
        rule_uid=RULE_UID,
    )
    checker_data.result.add_xml_location(
        checker_bundle_name=constants.BUNDLE_NAME,
        checker_id=CHECKER_ID,
        issue_id=issue_id,
        xpath=checker_data.input_file_xml_root.getpath(connection),
        description=f"Contact point 'start' not used on predecessor road connection.",
    )

    inertial_point = utils.get_start_point_xyz_from_road_reference_line(connection_road)
    if inertial_point is not None:
        checker_data.result.add_inertial_location(
            checker_bundle_name=constants.BUNDLE_NAME,
            checker_id=CHECKER_ID,
            issue_id=issue_id,
            x=inertial_point.x,
            y=inertial_point.y,
            z=inertial_point.z,
            description="Contact point 'start' not used on predecessor road connection.",
        )


def _check_junction_connection_start_along_linkage(
    checker_data: models.CheckerData,
) -> None:
    junctions = utils.get_junctions(checker_data.input_file_xml_root)
    road_id_map = utils.get_road_id_map(checker_data.input_file_xml_root)

    for junction in junctions:

        connections = utils.get_connections_from_junction(junction)

        for connection in connections:
            contact_point = utils.get_contact_point_from_connection(connection)
            if contact_point is None:
                continue

            if contact_point == models.ContactPoint.START:
                connection_road_id = utils.get_connecting_road_id_from_connection(
                    connection
                )
                if connection_road_id is None:
                    continue

                incoming_road_id = utils.get_incoming_road_id_from_connection(
                    connection
                )
                if incoming_road_id is None:
                    continue

                connection_road = road_id_map.get(connection_road_id)
                if connection_road is None:
                    continue

                predecessor_linkage = utils.get_road_linkage(
                    connection_road, models.LinkageTag.PREDECESSOR
                )
                if predecessor_linkage is None:
                    continue

                if predecessor_linkage.id != incoming_road_id:
                    _raise_issue(checker_data, connection, connection_road)


def check_rule(checker_data: models.CheckerData) -> None:
    """
    Rule ID: asam.net:xodr:1.7.0:junctions.connection.start_along_linkage

    Description: The value "start" shall be used to indicate that the connecting
    road runs along the linkage indicated in the element.

    Severity: ERROR

    Version range: [1.7.0, )

    Remark:
        None

    More info at
        - https://github.com/asam-ev/qc-opendrive/issues/36
    """
    logging.info("Executing junctions.connection.start_along_linkage check")

    _check_junction_connection_start_along_linkage(checker_data)
