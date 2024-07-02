from typing import List, Dict, Union

from lxml import etree
from qc_opendrive.checks import models
import numpy as np


def get_lanes(root: etree._ElementTree) -> List[etree._ElementTree]:
    lanes = []

    for lane in root.iter("lane"):
        lanes.append(lane)

    return lanes


def get_lane_sections(road: etree._ElementTree) -> List[etree._ElementTree]:
    lane_sections = []

    for lane_section in road.iter("laneSection"):
        lane_sections.append(lane_section)

    return lane_sections


def get_last_lane_section(road: etree._ElementTree) -> Union[None, etree._ElementTree]:
    lane_sections = get_lane_sections(road)
    if len(lane_sections) > 0:
        return lane_sections[-1]
    else:
        return None


def get_first_lane_section(road: etree._ElementTree) -> Union[None, etree._ElementTree]:
    lane_sections = get_lane_sections(road)
    if len(lane_sections) > 0:
        return lane_sections[0]
    else:
        return None


def get_roads(root: etree._ElementTree) -> List[etree._ElementTree]:
    roads = []

    for road in root.iter("road"):
        roads.append(road)

    return roads


def get_road_id_map(root: etree._ElementTree) -> Dict[int, etree._ElementTree]:
    """
    Returns a dictionary where keys are the road IDs and values are the road.
    Roads without a valid ID are not included in the dictionary.
    If there are multiple roads with the same ID, a random road will be included in the dictionary
    """

    road_id_map = dict()

    for road in root.iter("road"):
        road_id = road.get("id")
        if road_id is not None:
            road_id_map[int(road_id)] = road

    return road_id_map


def get_junction_id_map(root: etree._ElementTree) -> Dict[int, etree._ElementTree]:
    """
    Returns a dictionary where keys are the junction IDs and values are the junction.
    Junctions without a valid ID are not included in the dictionary.
    If there are multiple junctions with the same ID, a random junction will be included in the dictionary
    """

    junction_id_map = dict()

    for junction in root.iter("junction"):
        junction_id = junction.get("id")
        if junction_id is not None:
            junction_id_map[int(junction_id)] = junction

    return junction_id_map


def get_left_lanes_from_lane_section(
    lane_section: etree._ElementTree,
) -> List[etree._Element]:
    left_lane = lane_section.find("left")
    if left_lane is not None:
        left_lanes_list = left_lane.findall("lane")
    else:
        left_lanes_list = []

    return left_lanes_list


def get_right_lanes_from_lane_section(
    lane_section: etree._ElementTree,
) -> List[etree._Element]:
    right_lane = lane_section.find("right")
    if right_lane is not None:
        right_lanes_list = right_lane.findall("lane")
    else:
        right_lanes_list = []

    return right_lanes_list


def get_left_and_right_lanes_from_lane_section(
    lane_section: etree._ElementTree,
) -> List[etree._Element]:
    left_lanes = get_left_lanes_from_lane_section(lane_section)
    right_lanes = get_right_lanes_from_lane_section(lane_section)

    return left_lanes + right_lanes


def xml_string_to_bool(value: str):
    return value.lower() in ("true",)


def get_standard_schema_version(root: etree._ElementTree) -> str:
    header = root.find("header")
    header_attrib = header.attrib
    version = f"{header_attrib['revMajor']}.{header_attrib['revMinor']}.0"
    return version


def get_road_linkage(
    road: etree._ElementTree, linkage_tag: models.LinkageTag
) -> Union[None, models.RoadLinkage]:
    road_link = road.find("link")
    if road_link is None:
        return None

    linkage = road_link.find(linkage_tag.value)

    if linkage is None:
        return None
    elif linkage.get("elementType") == "road":
        road_id = linkage.get("elementId")
        contact_point = linkage.get("contactPoint")
        if road_id is None or contact_point is None:
            return None
        else:
            return models.RoadLinkage(
                id=int(road_id), contact_point=models.ContactPoint(contact_point)
            )
    else:
        return None


def get_road_junction_linkage(
    road: etree._ElementTree, linkage_tag: models.LinkageTag
) -> Union[None, int]:
    road_link = road.find("link")
    if road_link is None:
        return None

    linkage = road_link.find(linkage_tag.value)

    if linkage is None:
        return None
    elif linkage.get("elementType") == "junction":
        junction_id = linkage.get("elementId")
        contact_point = linkage.get("contactPoint")
        if junction_id is None or contact_point is None:
            return None
        else:
            return int(junction_id)
    else:
        return None


def get_predecessor_road_id(road: etree._ElementTree) -> Union[None, int]:
    linkage = get_road_linkage(road, models.LinkageTag.PREDECESSOR)
    if linkage is None:
        return None
    else:
        return linkage.id


def get_successor_road_id(road: etree._ElementTree) -> Union[None, int]:
    linkage = get_road_linkage(road, models.LinkageTag.SUCCESSOR)
    if linkage is None:
        return None
    else:
        return linkage.id


def get_predecessor_lane_ids(lane: etree._ElementTree) -> List[int]:
    links = lane.findall("link")

    predecessors = []
    for link in links:
        linkages = link.findall("predecessor")
        for linkage in linkages:
            predecessor_id = linkage.get("id")
            if predecessor_id is not None:
                predecessors.append(int(predecessor_id))

    return predecessors


def get_successor_lane_ids(lane: etree._ElementTree) -> List[int]:
    links = lane.findall("link")

    successors = []
    for link in links:
        linkages = link.findall("successor")
        for linkage in linkages:
            successor_id = linkage.get("id")
            if successor_id is not None:
                successors.append(int(successor_id))

    return successors


def get_lane_link_element(
    lane: etree._ElementTree, link_id: int, linkage_tag: models.LinkageTag
) -> Union[None, etree._ElementTree]:
    links = lane.findall("link")
    if linkage_tag == models.LinkageTag.PREDECESSOR:
        for link in links:
            linkages = link.findall("predecessor")
            for linkage in linkages:
                predecessor_id = linkage.get("id")
                if predecessor_id is not None and link_id == int(predecessor_id):
                    return linkage

        return None
    elif linkage_tag == models.LinkageTag.SUCCESSOR:
        for link in links:
            linkages = link.findall("successor")
            for linkage in linkages:
                successor_id = linkage.get("id")
                if successor_id is not None and link_id == int(successor_id):
                    return linkage

        return None
    else:
        return None


def get_lane_from_lane_section(
    lane_section: etree._ElementTree, lane_id: int
) -> Union[None, etree._ElementTree]:
    lanes = get_left_and_right_lanes_from_lane_section(lane_section)

    for lane in lanes:
        current_id = lane.get("id")
        if current_id is not None and int(current_id) == lane_id:
            return lane

    return None


def get_lane_level_from_lane(lane: etree._ElementTree) -> bool:
    return lane.get("level") == "true"


def get_junctions(root: etree._ElementTree) -> List[etree._ElementTree]:
    return list(root.iter("junction"))


def get_lane_links_from_connection(
    connection: etree._ElementTree,
) -> List[etree._ElementTree]:
    return list(connection.iter("laneLink"))


def get_connections_from_junction(
    junction: etree._ElementTree,
) -> List[etree._ElementTree]:
    return list(junction.iter("connection"))


def get_lane_id(lane: etree._ElementTree) -> Union[None, int]:
    lane_id = lane.get("id")
    if lane_id is None:
        return None
    else:
        return int(lane_id)


def get_road_junction_id(road: etree._ElementTree) -> Union[None, int]:
    junction_id = road.get("junction")
    if junction_id is None:
        return None
    else:
        return int(junction_id)


def get_road_link_element(
    road: etree._ElementTree, link_id: int, linkage_tag: models.LinkageTag
) -> Union[None, etree._ElementTree]:
    links = road.findall("link")
    if linkage_tag == models.LinkageTag.PREDECESSOR:
        for link in links:
            linkages = link.findall("predecessor")
            for linkage in linkages:
                predecessor_id = linkage.get("elementId")
                if predecessor_id is not None and link_id == int(predecessor_id):
                    return linkage

        return None
    elif linkage_tag == models.LinkageTag.SUCCESSOR:
        for link in links:
            linkages = link.findall("successor")
            for linkage in linkages:
                successor_id = linkage.get("elementId")
                if successor_id is not None and link_id == int(successor_id):
                    return linkage

        return None
    else:
        return None


def road_belongs_to_junction(road: etree._Element) -> bool:
    road_junction_id = get_road_junction_id(road)
    if road_junction_id is None or road_junction_id == -1:
        return False
    else:
        return True


def get_incoming_road_id_from_connection(
    connection: etree._Element,
) -> Union[None, int]:
    incoming_road_id = connection.get("incomingRoad")
    if incoming_road_id is None:
        return None
    else:
        return int(incoming_road_id)


def get_connecting_road_id_from_connection(
    connection: etree._Element,
) -> Union[None, int]:
    connecting_road_id = connection.get("connectingRoad")
    if connecting_road_id is None:
        return None
    else:
        return int(connecting_road_id)


def get_contact_point_from_connection(
    connection: etree._Element,
) -> Union[None, models.ContactPoint]:
    contact_point_str = connection.get("contactPoint")
    if contact_point_str is None:
        return None
    else:
        return models.ContactPoint(contact_point_str)


def get_from_attribute_from_lane_link(lane_link: etree._Element) -> Union[int, None]:
    from_attribute = lane_link.get("from")
    if from_attribute is None:
        return None
    else:
        return int(from_attribute)


def get_to_attribute_from_lane_link(lane_link: etree._Element) -> Union[int, None]:
    to_attribute = lane_link.get("to")
    if to_attribute is None:
        return None
    else:
        return int(to_attribute)


def get_length_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    length = geometry.get("length")
    if length is None:
        return None
    else:
        return float(length)


def get_normalized_param_poly3_from_geometry(
    geometry: etree._ElementTree,
) -> Union[None, models.ParamPoly3]:
    param_poly3 = None

    for element in geometry.iter("paramPoly3"):
        param_poly3 = element

    if param_poly3 is None:
        return None

    if param_poly3.get("pRange") != models.ParamPoly3Range.NORMALIZED:
        return None

    return models.ParamPoly3(
        u=models.Poly3(
            a=float(param_poly3.get("aU")),
            b=float(param_poly3.get("bU")),
            c=float(param_poly3.get("cU")),
            d=float(param_poly3.get("dU")),
        ),
        v=models.Poly3(
            a=float(param_poly3.get("aV")),
            b=float(param_poly3.get("bV")),
            c=float(param_poly3.get("cV")),
            d=float(param_poly3.get("dV")),
        ),
        range=models.ParamPoly3Range.NORMALIZED,
    )


def poly3_to_polynomial(poly3: models.Poly3) -> np.polynomial.Polynomial:
    return np.polynomial.Polynomial([poly3.a, poly3.b, poly3.c, poly3.d])


def get_contact_lane_section_from_linked_road(
    linkage: etree._ElementTree, road_id_map: Dict[int, etree._ElementTree]
) -> Union[None, models.ContactingLaneSection]:
    linked_road = road_id_map.get(linkage.id)
    if linked_road is None:
        return

    contact_lane_section = None

    if linkage.contact_point == models.ContactPoint.START:
        contact_lane_section = models.ContactingLaneSection(
            lane_section=get_first_lane_section(linked_road),
            linkage_tag=models.LinkageTag.PREDECESSOR,
        )
    elif linkage.contact_point == models.ContactPoint.END:
        contact_lane_section = models.ContactingLaneSection(
            lane_section=get_last_lane_section(linked_road),
            linkage_tag=models.LinkageTag.SUCCESSOR,
        )

    return contact_lane_section


def get_contact_lane_section_from_junction_connection_road(
    connection_road: etree._ElementTree, contact_point: models.ContactPoint
) -> Union[None, etree._ElementTree]:
    contact_lane_section = None

    if contact_point == models.ContactPoint.START:
        contact_lane_section = get_first_lane_section(connection_road)
    elif contact_point == models.ContactPoint.END:
        contact_lane_section = get_last_lane_section(connection_road)

    return contact_lane_section


def get_incoming_and_connection_contacting_lane_sections(
    connection: etree._ElementTree, road_id_map: Dict[int, etree._ElementTree]
) -> Union[None, models.ContactingLaneSections]:
    connection_road_id = get_connecting_road_id_from_connection(connection)
    incoming_road_id = get_incoming_road_id_from_connection(connection)

    if connection_road_id is None or incoming_road_id is None:
        return None

    connection_road = road_id_map.get(connection_road_id)
    incoming_road = road_id_map.get(incoming_road_id)

    if connection_road is None or incoming_road is None:
        return None

    connection_contact_point = get_contact_point_from_connection(connection)
    connection_lane_section = get_contact_lane_section_from_junction_connection_road(
        connection_road, connection_contact_point
    )

    if connection_lane_section is None:
        return None

    connection_road_linkage = None
    if connection_contact_point == models.ContactPoint.START:
        connection_road_linkage = get_road_linkage(
            connection_road, models.LinkageTag.PREDECESSOR
        )
    elif connection_contact_point == models.ContactPoint.END:
        connection_road_linkage = get_road_linkage(
            connection_road, models.LinkageTag.SUCCESSOR
        )

    if connection_road_linkage is None:
        return None

    incoming_lane_section = None
    if connection_road_linkage.contact_point == models.ContactPoint.START:
        incoming_lane_section = get_first_lane_section(incoming_road)
    elif connection_road_linkage.contact_point == models.ContactPoint.END:
        incoming_lane_section = get_last_lane_section(incoming_road)

    if incoming_lane_section is None:
        return None

    return models.ContactingLaneSections(
        incoming=incoming_lane_section,
        connection=connection_lane_section,
    )


def get_connecting_lane_ids(
    lane: etree._ElementTree, linkage_tag: models.LinkageTag
) -> List[int]:
    if linkage_tag == models.LinkageTag.PREDECESSOR:
        return get_predecessor_lane_ids(lane)
    elif linkage_tag == models.LinkageTag.SUCCESSOR:
        return get_successor_lane_ids(lane)
    else:
        return []


def get_poly3_from_width(
    width: etree._ElementTree,
) -> models.WidthPoly3:
    return models.WidthPoly3(
        poly3=models.Poly3(
            a=float(width.get("a")),
            b=float(width.get("b")),
            c=float(width.get("c")),
            d=float(width.get("d")),
        ),
        s_offset=float(width.get("sOffset")),
    )


def get_lane_width_poly3_list(lane: etree._Element) -> List[models.WidthPoly3]:
    width_poly3 = []
    for width in lane.iter("width"):
        width_poly3.append(get_poly3_from_width(width))
    return width_poly3


def evaluate_lane_width(lane: etree._Element, ds: float) -> Union[None, float]:
    # This function follows the assumption that the width elements for a given
    # lane follow the standard rules for width elements.
    #
    # Standard width rules:
    # - The width of a lane shall remain valid until a new <width> element is
    #   defined or the lane section ends.
    # - A new <width> element shall be defined when the variables of the
    #   polynomial function change.
    # - <width> elements shall be defined in ascending order according to the
    #   s-coordinate.
    # - Width (ds) shall be greater than or equal to zero.
    #

    lane_id = get_lane_id(lane)

    if lane_id == 0:
        return 0.0

    lane_width_poly3_list = get_lane_width_poly3_list(lane)

    if len(lane_width_poly3_list) == 0:
        return None

    current_s_offset = lane_width_poly3_list[0].s_offset
    index = 0
    while ds >= current_s_offset and index < len(lane_width_poly3_list):
        current_s_offset = lane_width_poly3_list[index].s_offset
        index += 1

    if index > 0:
        index -= 1
    else:
        return None

    poly3_to_eval = poly3_to_polynomial(lane_width_poly3_list[index].poly3)

    return poly3_to_eval(ds)


def get_all_road_linkage_junction_connections(
    road_id: int,
    junction_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
    linkage_tag: models.LinkageTag,
) -> List[etree._Element]:
    linkage_connections = []
    linkage_junction = junction_id_map[junction_id]
    connections = get_connections_from_junction(linkage_junction)

    target_contact_point = None
    if linkage_tag == models.LinkageTag.PREDECESSOR:
        target_contact_point = models.ContactPoint.START
    elif linkage_tag == models.LinkageTag.SUCCESSOR:
        target_contact_point = models.ContactPoint.END
    else:
        return []

    for connection in connections:
        incoming_road_id = get_incoming_road_id_from_connection(connection)
        connecting_road_id = get_connecting_road_id_from_connection(connection)

        if incoming_road_id is None or connecting_road_id is None:
            continue

        if incoming_road_id == road_id:
            connecting_road = road_id_map[connecting_road_id]

            connection_contact_point = get_contact_point_from_connection(connection)

            connection_road_linkage = None
            if connection_contact_point == models.ContactPoint.START:
                connection_road_linkage = get_road_linkage(
                    connecting_road, models.LinkageTag.PREDECESSOR
                )
            elif connection_contact_point == models.ContactPoint.END:
                connection_road_linkage = get_road_linkage(
                    connecting_road, models.LinkageTag.SUCCESSOR
                )

            if connection_road_linkage is None:
                continue

            if connection_road_linkage.contact_point == target_contact_point:
                linkage_connections.append(connection)

    return linkage_connections
