"""
Amazon Robotics Hackathon - Routing Utilities

This module provides utility functions for moving drive units in the
Amazon Robotics Hackathon.
"""

from ar_hackathon.models.graph_state import GraphState
from ar_hackathon.models.drive_unit import DriveUnit


def is_valid_move(graph_state: GraphState, drive_unit: DriveUnit, next_node: int) -> bool:
    """
    Check if moving a drive unit to a specific node is a valid move.

    Args:
        graph_state: Current graph state
        drive_unit: Drive unit to move
        next_node: ID of the node to move the drive unit to

    Returns:
        bool: True if the move is valid, False otherwise
    """
    # The returned value must be a node ID (bool is excluded explicitly
    # because it is a subclass of int)
    if not isinstance(next_node, int) or isinstance(next_node, bool):
        return False

    # Check if the drive unit is already in transit
    if drive_unit.in_transit:
        return False

    # Staying at the current node is a wait, not a move
    if next_node == drive_unit.current_node:
        return False

    # Find the edge between the current node and the next node
    edge = graph_state.get_edge(drive_unit.current_node, next_node)

    # If no edge exists, the move is invalid
    if edge is None:
        return False

    # Check if the edge has available capacity (edge capacity limits how many drive units share an aisle/edge)
    if edge.capacity is not None:
        if graph_state.edge_occupancy(drive_unit.current_node, next_node) >= edge.capacity:
            return False

    # Check if the destination node has available capacity (node capacity limits how many drive units a node/station holds)
    node = graph_state.get_node(next_node)
    if node is not None and node.capacity is not None:
        if graph_state.node_occupancy(next_node) >= node.capacity:
            return False

    # All checks passed, the move is valid
    return True
