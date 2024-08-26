import re
import numpy as np
from io import BytesIO
from typing import List, Dict, Union
from lxml import etree
import pyclothoids as pc
import transforms3d

from qc_opendrive.base import models

EPSILON = 1.0e-6
ZERO_OFFSET_POLY3 = models.OffsetPoly3(
    poly3=models.Poly3(a=0.0, b=0.0, c=0.0, d=0.0), s_offset=0.0
)


def get_root_without_default_namespace(path: str) -> etree._ElementTree:
    with open(path, "rb") as raw_file:
        xml_string = raw_file.read().decode()

        if "xmlns" in xml_string:
            xml_string = re.sub(' xmlns="[^"]+"', "", xml_string)

        return etree.parse(BytesIO(xml_string.encode()))


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


def get_linked_junction_id(
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
        if junction_id is None:
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


def get_arclen_param_poly3_from_geometry(
    geometry: etree._ElementTree,
) -> Union[None, models.ParamPoly3]:
    param_poly3 = None

    for element in geometry.iter("paramPoly3"):
        param_poly3 = element

    if param_poly3 is None:
        return None

    if param_poly3.get("pRange") != models.ParamPoly3Range.ARC_LENGTH:
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
        range=models.ParamPoly3Range.ARC_LENGTH,
    )


def arc_length_integrand(
    t: float, du: np.polynomial.Polynomial, dv: np.polynomial.Polynomial
) -> float:
    """
    The equation to calculate the length of a parametric curve represented by u(t), v(t)
    is integral of sqrt(du^2 + dv^2) dt.

    More info at
        - https://en.wikipedia.org/wiki/Arc_length
    """
    return np.sqrt(du(t) ** 2 + dv(t) ** 2)


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
) -> models.OffsetPoly3:
    return models.OffsetPoly3(
        poly3=models.Poly3(
            a=float(width.get("a")),
            b=float(width.get("b")),
            c=float(width.get("c")),
            d=float(width.get("d")),
        ),
        s_offset=float(width.get("sOffset")),
    )


def get_lane_width_poly3_list(lane: etree._Element) -> List[models.OffsetPoly3]:
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

    count = 0
    for lane_width_poly in lane_width_poly3_list:
        if lane_width_poly.s_offset > ds:
            break
        else:
            count += 1

    if count == 0:
        return None

    index = count - 1

    poly3_to_eval = poly3_to_polynomial(lane_width_poly3_list[index].poly3)

    return poly3_to_eval(ds)


def get_connections_between_road_and_junction(
    road_id: int,
    junction_id: int,
    road_id_map: Dict[int, etree._ElementTree],
    junction_id_map: Dict[int, etree._ElementTree],
    incoming_road_contact_point: models.ContactPoint,
) -> List[etree._Element]:
    """
    This function receives the a road id, a junction id and a contact point for
    the road where the junction contacts to and returns all connections to that
    specific contact point. It also receives the road and junction id map for
    the sake of simplicity.
    """
    linkage_connections = []

    junction = junction_id_map.get(junction_id)
    if junction is None:
        return []

    connections = get_connections_from_junction(junction)

    for connection in connections:
        incoming_road_id = get_incoming_road_id_from_connection(connection)
        connecting_road_id = get_connecting_road_id_from_connection(connection)

        if incoming_road_id is None or connecting_road_id is None:
            continue

        if incoming_road_id == road_id:
            connecting_road = road_id_map.get(connecting_road_id)
            if connecting_road is None:
                continue

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

            if connection_road_linkage.contact_point == incoming_road_contact_point:
                linkage_connections.append(connection)

    return linkage_connections


def get_connections_of_connecting_road(
    connecting_road_id: int,
    junction: etree._Element,
    connecting_road_contact_point: models.ContactPoint,
) -> List[etree._Element]:
    """
    This function receives a connecting road id, the junction element it belongs
    to and a target contact point to the road and returns all connection elements
    that connect to the road at the target contact point.
    """
    connections = get_connections_from_junction(junction)

    linkage_connections = []
    for connection in connections:
        connection_connecting_road_id = get_connecting_road_id_from_connection(
            connection
        )

        if connection_connecting_road_id is None:
            continue

        elif connection_connecting_road_id == connecting_road_id:
            contact_point = get_contact_point_from_connection(connection)

            if contact_point is None:
                continue

            elif contact_point == connecting_road_contact_point:
                linkage_connections.append(connection)

    return linkage_connections


def get_traffic_hand_rule_from_road(road: etree._Element) -> models.TrafficHandRule:
    rule = road.get("rule")

    if rule is None:
        # From standard:
        # When this attribute is missing, RHT is assumed.
        return models.TrafficHandRule.RHT
    else:
        return models.TrafficHandRule(rule)


def get_lane_section_s_offset(lane_section: etree._Element) -> Union[None, float]:
    s_offset = lane_section.get("sOffset")

    if s_offset is None:
        return None
    else:
        return float(s_offset)


def get_road_length(road: etree._ElementTree) -> Union[None, float]:
    length = road.get("length")
    if length is None:
        return None
    else:
        return float(length)


def get_s_coordinate_from_lane_section(
    lane_section: etree._ElementTree,
) -> Union[None, float]:
    s_coordinate = lane_section.get("s")
    if s_coordinate is None:
        return None
    else:
        return float(s_coordinate)


def get_borders_from_lane(lane: etree._ElementTree) -> List[models.OffsetPoly3]:
    border_list = []
    for border in lane.iter("border"):
        border_list.append(
            models.OffsetPoly3(
                models.Poly3(
                    a=float(border.get("a")),
                    b=float(border.get("b")),
                    c=float(border.get("c")),
                    d=float(border.get("d")),
                ),
                s_offset=float(border.get("sOffset")),
            )
        )

    return border_list


def get_sorted_lane_sections_with_length_from_road(
    road: etree._ElementTree,
) -> List[models.LaneSectionWithLength]:
    """
    If there is missing information so that lane section length cannot be computed, such as
    missing s-coordinate of lane section or missing road length, an empty list will be returned.
    """
    lane_sections = get_lane_sections(road)

    for lane_section in lane_sections:
        s_coordinate = get_s_coordinate_from_lane_section(lane_section)
        if s_coordinate is None:
            return []

    sorted_lane_sections = sorted(
        lane_sections,
        key=lambda lane_section: get_s_coordinate_from_lane_section(lane_section),
    )

    sorted_lane_sections_with_length = []
    for i in range(0, len(sorted_lane_sections)):
        lane_section = sorted_lane_sections[i]

        lane_section_start_point = get_s_coordinate_from_lane_section(lane_section)
        if lane_section_start_point is None:
            return []

        lane_section_end_point = None
        if i < len(sorted_lane_sections) - 1:
            next_lane_section = sorted_lane_sections[i + 1]
            lane_section_end_point = get_s_coordinate_from_lane_section(
                next_lane_section
            )
        else:
            road_length = get_road_length(road)
            if road_length is None:
                return []
            lane_section_end_point = road_length

        if lane_section_end_point is None:
            return []

        lane_section_length = lane_section_end_point - lane_section_start_point
        sorted_lane_sections_with_length.append(
            models.LaneSectionWithLength(
                lane_section=lane_section, length=lane_section_length
            )
        )

    return sorted_lane_sections_with_length


def get_road_elevations(road: etree._ElementTree) -> List[models.OffsetPoly3]:
    elevation_profile = road.find("elevationProfile")

    if elevation_profile is None:
        return []

    elevation_list = []
    for elevation in elevation_profile.iter("elevation"):
        elevation_list.append(
            models.OffsetPoly3(
                models.Poly3(
                    a=float(elevation.get("a")),
                    b=float(elevation.get("b")),
                    c=float(elevation.get("c")),
                    d=float(elevation.get("d")),
                ),
                s_offset=float(elevation.get("s")),
            )
        )

    return elevation_list


def get_road_superelevations(road: etree._ElementTree) -> List[models.OffsetPoly3]:
    lateral_profile = road.find("lateralProfile")

    if lateral_profile is None:
        return []

    superelevation_list = []
    for superelevation in lateral_profile.iter("superelevation"):
        superelevation_list.append(
            models.OffsetPoly3(
                models.Poly3(
                    a=float(superelevation.get("a")),
                    b=float(superelevation.get("b")),
                    c=float(superelevation.get("c")),
                    d=float(superelevation.get("d")),
                ),
                s_offset=float(superelevation.get("s")),
            )
        )

    return superelevation_list


def get_lane_offsets_from_road(road: etree._ElementTree) -> List[models.OffsetPoly3]:
    lanes = road.find("lanes")

    if lanes is None:
        return []

    lane_offset_list = []
    for lane_offset in lanes.iter("laneOffset"):
        lane_offset_list.append(
            models.OffsetPoly3(
                models.Poly3(
                    a=float(lane_offset.get("a")),
                    b=float(lane_offset.get("b")),
                    c=float(lane_offset.get("c")),
                    d=float(lane_offset.get("d")),
                ),
                s_offset=float(lane_offset.get("s")),
            )
        )

    return lane_offset_list


def are_same_equations(first: models.OffsetPoly3, second: models.OffsetPoly3) -> bool:
    """
    This function checks if two equations are the same.
    Equation 1:
    f1(s) = a1 + b1*(s - s_offset1) + c1*(s - s_offset1)**2 + d1*(s - s_offset1)**3
    f2(s) = a2 + b2*(s - s_offset2) + c2*(s - s_offset2)**2 + d2*(s - s_offset2)**3

    The check is implemented as follows.
    Let f3(s) = f1(s) - f2(s).

    Explanding and simplifying f3(s), we obtain:
    f3(s) = a3 + b3 * s + c3 * s**2 + d3 * s**3

    f1(s) and f2(s) are considered the same if a3, b3, c3, d3 are zeros.
    """
    a3 = (
        first.poly3.a
        - second.poly3.a
        - first.poly3.b * first.s_offset
        + second.poly3.b * second.s_offset
        + first.poly3.c * first.s_offset**2
        - second.poly3.c * second.s_offset**2
        - first.poly3.d * first.s_offset**3
        + second.poly3.d * second.s_offset**3
    )

    b3 = (
        first.poly3.b
        - second.poly3.b
        - 2 * first.poly3.c * first.s_offset
        + 2 * second.poly3.c * second.s_offset
        + 3 * first.poly3.d * first.s_offset**2
        - 3 * second.poly3.d * second.s_offset**2
    )

    c3 = (
        first.poly3.c
        - second.poly3.c
        - 3 * first.poly3.d * first.s_offset
        + 3 * second.poly3.d * second.s_offset
    )

    d3 = first.poly3.d - second.poly3.d

    return (
        np.abs(a3) < EPSILON
        and np.abs(b3) < EPSILON
        and np.abs(c3) < EPSILON
        and np.abs(d3) < EPSILON
    )


def get_road_plan_view_geometry_list(
    road: etree._ElementTree,
) -> List[etree._ElementTree]:
    plan_view = road.find("planView")

    if plan_view is None:
        return []

    return list(plan_view.iter("geometry"))


def is_line_geometry(geometry: etree._ElementTree) -> bool:
    return geometry.find("line") is not None


def get_lane_direction(lane: etree._Element) -> Union[models.LaneDirection, None]:
    lane_direction = lane.get("direction")

    if lane_direction is None:
        # By the standard definition, if no direction is provided the standard
        # based on the traffic hand should be used.
        return models.LaneDirection.STANDARD
    elif lane_direction in iter(models.LaneDirection):
        return models.LaneDirection(lane_direction)
    else:
        return None


def get_heading_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    heading = geometry.get("hdg")

    if heading is None:
        return None

    return float(heading)


def get_s_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    s = geometry.get("s")
    if s is None:
        return None
    else:
        return float(s)


def get_x_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    x = geometry.get("x")
    if x is None:
        return None
    else:
        return float(x)


def get_y_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    y = geometry.get("y")
    if y is None:
        return None
    else:
        return float(y)


def get_corresponding_road_geometry_by_s(
    road: etree._ElementTree, s: float
) -> Union[None, etree._ElementTree]:
    length = get_road_length(road)

    if s < 0.0 or s > length:
        return None

    geometries = get_road_plan_view_geometry_list(road)

    if len(geometries) == 0:
        return None

    previous_geometry = None
    for geometry in geometries:
        geometry_s = get_s_from_geometry(geometry)
        if geometry_s is None:
            continue

        if geometry_s > s:
            return previous_geometry

        previous_geometry = geometry

    return geometries[-1]


def get_geometry_arc(geometry: etree._Element) -> Union[None, etree._Element]:
    return geometry.find("arc")


def get_geometry_line(geometry: etree._Element) -> Union[None, etree._Element]:
    return geometry.find("line")


def get_geometry_spiral(geometry: etree._Element) -> Union[None, etree._Element]:
    return geometry.find("spiral")


def calculate_line_point(
    s: float, s0: float, x0: float, y0: float, heading: float
) -> models.Point2D:
    return models.Point2D(
        x=x0 + ((s - s0) * np.cos(heading)),
        y=y0 + ((s - s0) * np.sin(heading)),
    )


def get_curvature_from_arc(arc: etree._Element) -> Union[None, float]:
    curvature = arc.get("curvature")
    if curvature is None:
        return None
    else:
        return float(curvature)


def calculate_arc_point(
    s: float,
    s0: float,
    x0: float,
    y0: float,
    heading: float,
    curvature: float,
) -> models.Point2D:
    radius = 1 / curvature
    theta_f = (s - s0) * curvature - np.pi / 2
    arc_x = x0 + radius * (np.cos(theta_f + heading) - np.sin(heading))
    arc_y = y0 + radius * (np.sin(theta_f + heading) + np.cos(heading))

    return models.Point2D(
        x=arc_x,
        y=arc_y,
    )


def get_curv_start_from_spiral(spiral: etree._Element) -> Union[None, float]:
    curvStart = spiral.get("curvStart")
    if curvStart is None:
        return None
    else:
        return float(curvStart)


def get_curv_end_from_spiral(spiral: etree._Element) -> Union[None, float]:
    curvEnd = spiral.get("curvEnd")
    if curvEnd is None:
        return None
    else:
        return float(curvEnd)


def calculate_spiral_point(
    s: float,
    s0: float,
    x0: float,
    y0: float,
    heading: float,
    curv_start: float,
    curv_end: float,
    length: float,
) -> models.Point2D:
    # curvature rate given by
    # A = (K1 - K0) / L
    kd = (curv_end - curv_start) / length

    # Standard clothoid for the given parameters
    clothoid = pc.Clothoid.StandardParams(x0, y0, heading, curv_start, kd, length)

    return models.Point2D(x=clothoid.X(s - s0), y=clothoid.Y(s - s0))


def calculate_poly3_arclen_point(
    s: float,
    poly3_arclen: models.ParamPoly3,
    s0: float,
    x0: float,
    y0: float,
    heading: float,
) -> models.Point2D:
    x_poly3 = poly3_to_polynomial(poly3_arclen.u)
    y_poly3 = poly3_to_polynomial(poly3_arclen.v)

    x = x_poly3(s - s0)
    y = y_poly3(s - s0)

    xt = (np.cos(heading) * x) - (np.sin(heading) * y) + x0
    yt = (np.sin(heading) * x) + (np.cos(heading) * y) + y0

    return models.Point2D(x=xt, y=yt)


def calculate_poly3_norm_point(
    s: float,
    poly3_norm: models.ParamPoly3,
    s0: float,
    x0: float,
    y0: float,
    heading: float,
    length: float,
) -> models.Point2D:
    x_poly3 = poly3_to_polynomial(poly3_norm.u)
    y_poly3 = poly3_to_polynomial(poly3_norm.v)

    x = x_poly3((s - s0) / length)
    y = y_poly3((s - s0) / length)

    xt = (np.cos(heading) * x) - (np.sin(heading) * y) + x0
    yt = (np.sin(heading) * x) + (np.cos(heading) * y) + y0

    return models.Point2D(x=xt, y=yt)


def get_point_xy_from_geometry(
    geometry: etree._ElementTree, s: float
) -> Union[None, models.Point2D]:
    x0 = get_x_from_geometry(geometry)
    y0 = get_y_from_geometry(geometry)
    s0 = get_s_from_geometry(geometry)
    heading = get_heading_from_geometry(geometry)
    length = get_length_from_geometry(geometry)

    if any(var is None for var in [x0, y0, s0, heading, length]):
        return None

    line = get_geometry_line(geometry)
    arc = get_geometry_arc(geometry)
    spiral = get_geometry_spiral(geometry)
    poly3_arclen = get_arclen_param_poly3_from_geometry(geometry)
    poly3_norm = get_normalized_param_poly3_from_geometry(geometry)

    if line is not None:
        return calculate_line_point(s=s, s0=s0, x0=x0, y0=y0, heading=heading)
    elif arc is not None:
        arc_curvature = get_curvature_from_arc(arc)

        if arc_curvature is None:
            return None

        return calculate_arc_point(
            s=s,
            s0=s0,
            x0=x0,
            y0=y0,
            heading=heading,
            curvature=arc_curvature,
        )

    elif spiral is not None:
        curv_start = get_curv_start_from_spiral(spiral)
        curv_end = get_curv_end_from_spiral(spiral)

        if curv_end is None or curv_start is None:
            return None

        return calculate_spiral_point(
            s=s,
            s0=s0,
            x0=x0,
            y0=y0,
            heading=heading,
            curv_start=curv_start,
            curv_end=curv_end,
            length=length,
        )
    elif poly3_arclen is not None:
        return calculate_poly3_arclen_point(
            s=s,
            poly3_arclen=poly3_arclen,
            s0=s0,
            x0=x0,
            y0=y0,
            heading=heading,
        )
    elif poly3_norm is not None:
        return calculate_poly3_norm_point(
            s=s,
            poly3_norm=poly3_norm,
            s0=s0,
            x0=x0,
            y0=y0,
            heading=heading,
            length=length,
        )
    else:
        return None


def get_corresponding_road_elevation_by_s(
    road: etree._ElementTree, s: float
) -> Union[None, models.OffsetPoly3]:
    length = get_road_length(road)
    if s < 0.0 or s > length:
        return None

    elevation_list = get_road_elevations(road)

    # As the default elevation is zero, we return ZERO_OFFSET_POLY3.
    if len(elevation_list) == 0:
        return ZERO_OFFSET_POLY3

    previous_elevation = ZERO_OFFSET_POLY3

    for elevation in elevation_list:
        if elevation.s_offset > s:
            return previous_elevation

        previous_elevation = elevation

    return elevation_list[-1]


def calculate_elevation_value(elevation: models.OffsetPoly3, s: float) -> float:
    f_elevation = poly3_to_polynomial(elevation.poly3)
    return f_elevation(s - elevation.s_offset)


def get_point_xy_from_road_reference_line(
    road: etree._ElementTree, s: float
) -> Union[None, models.Point2D]:
    geometry = get_corresponding_road_geometry_by_s(road, s)
    if geometry is None:
        return None

    point_2d = get_point_xy_from_geometry(geometry, s)
    if point_2d is None:
        return None

    return models.Point2D(x=point_2d.x, y=point_2d.y)


def get_point_xyz_from_road_reference_line(
    road: etree._ElementTree, s: float
) -> Union[None, models.Point3D]:
    point_2d = get_point_xy_from_road_reference_line(road, s)

    if point_2d is None:
        return None

    elevation = get_corresponding_road_elevation_by_s(road, s)

    if elevation is None:
        return None

    elevation_value = calculate_elevation_value(elevation, s)

    return models.Point3D(x=point_2d.x, y=point_2d.y, z=elevation_value)


def get_start_point_xyz_from_road_reference_line(
    road: etree._ElementTree,
) -> Union[None, models.Point3D]:
    start_s = 0.0
    return get_point_xyz_from_road_reference_line(road, start_s)


def get_end_point_xyz_from_road_reference_line(
    road: etree._ElementTree,
) -> Union[None, models.Point3D]:
    end_s = get_road_length(road)
    return get_point_xyz_from_road_reference_line(road, end_s)


def get_middle_point_xyz_from_road_reference_line(
    road: etree._ElementTree,
) -> Union[None, models.Point3D]:
    middle_s = get_road_length(road) / 2.0
    return get_point_xyz_from_road_reference_line(road, middle_s)


def get_junction_id(junction: etree._ElementTree) -> Union[None, int]:
    id = junction.get("id")
    if id is None:
        return None
    else:
        return int(id)


def get_heading_from_geometry(geometry: etree._ElementTree) -> Union[None, float]:
    heading = geometry.get("hdg")

    if heading is None:
        return None

    return float(heading)


def calculate_arc_point_heading(
    s: float,
    s0: float,
    heading: float,
    curvature: float,
) -> float:
    heading = heading + curvature * (s - s0)
    return heading


def calculate_spiral_point_heading(
    s: float,
    s0: float,
    x0: float,
    y0: float,
    heading: float,
    curv_start: float,
    curv_end: float,
    length: float,
) -> float:
    kd = (curv_end - curv_start) / length
    clothoid = pc.Clothoid.StandardParams(x0, y0, heading, curv_start, kd, length)

    return clothoid.Theta(s - s0)


def calculate_poly3_arclen_heading(
    s: float,
    poly3_arclen: models.ParamPoly3,
    s0: float,
    heading: float,
) -> float:
    x_poly3_deriv = poly3_to_polynomial(poly3_arclen.u).deriv()
    y_poly3_deriv = poly3_to_polynomial(poly3_arclen.v).deriv()

    x = x_poly3_deriv(s - s0)
    y = y_poly3_deriv(s - s0)

    heading = np.arctan2(y, x)
    return heading


def calculate_poly3_norm_heading(
    s: float,
    poly3_norm: models.ParamPoly3,
    s0: float,
    heading: float,
    length: float,
) -> float:
    x_poly3_deriv = poly3_to_polynomial(poly3_norm.u).deriv()
    y_poly3_deriv = poly3_to_polynomial(poly3_norm.v).deriv()

    x = x_poly3_deriv((s - s0) / length)
    y = y_poly3_deriv((s - s0) / length)

    heading = np.arctan2(y, x)
    return heading


def get_heading_from_geometry_by_s(
    geometry: etree._Element, s: float
) -> Union[None, float]:
    x0 = get_x_from_geometry(geometry)
    y0 = get_y_from_geometry(geometry)
    s0 = get_s_from_geometry(geometry)
    heading = get_heading_from_geometry(geometry)
    length = get_length_from_geometry(geometry)

    if any(var is None for var in [x0, y0, s0, heading, length]):
        return None

    line = get_geometry_line(geometry)
    arc = get_geometry_arc(geometry)
    spiral = get_geometry_spiral(geometry)
    poly3_arclen = get_arclen_param_poly3_from_geometry(geometry)
    poly3_norm = get_normalized_param_poly3_from_geometry(geometry)

    if line is not None:
        return heading
    elif arc is not None:
        arc_curvature = get_curvature_from_arc(arc)

        if arc_curvature is None:
            return None

        return calculate_arc_point_heading(
            s=s,
            s0=s0,
            heading=heading,
            curvature=arc_curvature,
        )
    elif spiral is not None:
        curv_start = get_curv_start_from_spiral(spiral)
        curv_end = get_curv_end_from_spiral(spiral)

        if curv_end is None or curv_start is None:
            return None

        return calculate_spiral_point_heading(
            s=s,
            s0=s0,
            x0=x0,
            y0=y0,
            heading=heading,
            curv_start=curv_start,
            curv_end=curv_end,
            length=length,
        )
    elif poly3_arclen is not None:
        return calculate_poly3_arclen_heading(
            s=s,
            poly3_arclen=poly3_arclen,
            s0=s0,
            heading=heading,
        )
    elif poly3_norm is not None:
        return calculate_poly3_norm_heading(
            s=s,
            poly3_norm=poly3_norm,
            s0=s0,
            heading=heading,
            length=length,
        )
    else:
        return None


def get_heading_from_road_reference_line(
    road: etree._ElementTree, s: float
) -> Union[None, float]:
    geometry = get_corresponding_road_geometry_by_s(road, s)

    if geometry is None:
        return None

    return get_heading_from_geometry_by_s(geometry, s)


def calculate_elevation_angle(
    elevation: models.OffsetPoly3, s: float
) -> Union[None, float]:
    ds = poly3_to_polynomial(elevation.poly3).deriv()(s - elevation.s_offset)
    if ds is None:
        return None
    else:
        return np.arctan(ds)


def get_pitch_from_road_reference_line(
    road: etree._ElementTree, s: float
) -> Union[None, float]:
    elevation = get_corresponding_road_elevation_by_s(road, s)

    if elevation is None:
        return None

    # The negation is because head down is positive pitch
    return -calculate_elevation_angle(elevation, s)


def get_corresponding_road_superelevation_by_s(
    road: etree._ElementTree, s: float
) -> Union[None, models.OffsetPoly3]:
    length = get_road_length(road)
    if s < 0.0 or s > length:
        return None

    superelevations = get_road_superelevations(road)

    # As the default superelevation is zero, we return ZERO_OFFSET_POLY3 as default.
    if len(superelevations) == 0:
        return ZERO_OFFSET_POLY3

    previous_superelevation = ZERO_OFFSET_POLY3

    for superelevation in superelevations:
        if superelevation.s_offset > s:
            return previous_superelevation

        previous_superelevation = superelevation

    return superelevations[-1]


def get_roll_from_road_reference_line(
    road: etree._ElementTree, s: float
) -> Union[None, float]:
    superelevation = get_corresponding_road_superelevation_by_s(road, s)

    if superelevation is None:
        return None

    poly3 = poly3_to_polynomial(superelevation.poly3)

    return poly3(s - superelevation.s_offset)


def get_point_xyz_from_road(
    road: etree._ElementTree, s: float, t: float, h: float
) -> Union[None, models.Point3D]:
    yaw = get_heading_from_road_reference_line(road, s)
    # A reference line doesn't have pitch.
    pitch = 0.0
    roll = get_roll_from_road_reference_line(road, s)

    if yaw is None or pitch is None or roll is None:
        return None

    rotation = transforms3d.euler.euler2mat(yaw, pitch, roll, "rzyx")
    d_point = rotation.dot(np.array([0.0, t, h]))

    ref_line_point = get_point_xy_from_road_reference_line(road, s)
    if ref_line_point is None:
        return None

    return models.Point3D(
        x=ref_line_point.x + d_point[0],
        y=ref_line_point.y + d_point[1],
        z=d_point[2],
    )
