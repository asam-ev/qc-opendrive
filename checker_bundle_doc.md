# Checker bundle: xodrBundle

* Build version:  0.1.0
* Description:    OpenDrive checker bundle

## Parameters

* InputFile: The path of the input file.

## Checkers

### semantic_xodr

* Description: Evaluates elements in the file and their semantics to guarantee they are in conformity with the standard.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.lane.level_true_one_side
  * asam.net:xodr:1.7.0:road.lane.access.no_mix_of_deny_or_allow
  * asam.net:xodr:1.4.0:road.lane.link.lanes_across_lane_sections
  * asam.net:xodr:1.4.0:road.linkage.is_junction_needed
  * asam.net:xodr:1.7.0:road.lane.link.zero_width_at_start
  * asam.net:xodr:1.7.0:road.lane.link.zero_width_at_end
  * asam.net:xodr:1.4.0:road.lane.link.new_lane_appear
  * asam.net:xodr:1.4.0:junctions.connection.connect_road_no_incoming_road
  * asam.net:xodr:1.7.0:junctions.connection.one_connection_element
  * asam.net:xodr:1.8.0:junctions.connection.one_link_to_incoming
  * asam.net:xodr:1.7.0:junctions.connection.start_along_linkage
  * asam.net:xodr:1.7.0:junctions.connection.end_opposite_linkage

### geometry_xodr

* Description: Evaluates elements in the file and their geometrys to guarantee they are in conformity with the standard.
* Addressed rules:
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.length_match
  * asam.net:xodr:1.4.0:road.lane.border.overlap_with_inner_lanes
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.arclength_range
  * asam.net:xodr:1.7.0:road.geometry.parampoly3.normalized_range

### performance_xodr

* Description: Evaluates elements in the file to guarantee they are optimized.
* Addressed rules:
  * asam.net:xodr:1.7.0:performance.avoid_redundant_info

### smoothness_xodr

* Description: Evaluates elements in the file and their geometries to guarantee they are in conformity with the standard definition of smoothness.
* Addressed rules:
  * asam.net:xodr:1.7.0:lane_smoothness.contact_point_no_horizontal_gaps
