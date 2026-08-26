"""
Amazon Robotics Hackathon - Basic Driver Example

This module provides a sample implementation of the drive_unit_next_move
function. It greedily takes the cheapest nearby aisle with no lookahead
while completely ignoring the other drive units, so it wanders the floor
and loses pods on all but the simplest cases. This is not a good
algorithm and is intended as an example only.
"""

from typing import Dict, Optional, Set
from ar_hackathon.models.graph_state import GraphState

visited: Dict[int, Set[int]] = {}


def basic_driver(drive_unit_id: int, state: GraphState) -> Optional[int]:
    unit = state.get_drive_unit(drive_unit_id)
    if unit is None or unit.in_transit:
        return None

    unit_visited = visited.setdefault(drive_unit_id, set())
    unit_visited.add(unit.current_node)

    if unit.carrying:
        pod = state.get_pod(unit.carrying[0])
        target = pod.destination_station if pod else None
    else:
        target = None
        for pod in state.active_pods:
            if pod.carried_by is None and pod.current_node is not None:
                target = pod.current_node
                break

    best_next = None
    best_weight = float('inf')
    for neighbor in state.neighbors(unit.current_node):
        if target is not None and neighbor == target:
            return neighbor
        if neighbor in unit_visited:
            continue
        edge = state.get_edge(unit.current_node, neighbor)
        if edge is not None and edge.weight < best_weight:
            best_weight = edge.weight
            best_next = neighbor

    if best_next is None:
        for neighbor in state.neighbors(unit.current_node):
            edge = state.get_edge(unit.current_node, neighbor)
            if edge is not None and edge.weight < best_weight:
                best_weight = edge.weight
                best_next = neighbor

    return best_next
