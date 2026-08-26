"""
Amazon Robotics Hackathon - GraphState Model

This module defines the GraphState class for the Amazon Robotics Hackathon.
It represents the full state of the warehouse floor at a point in time and
is the object handed to the player's drive_unit_next_move function.
"""

from typing import List, Optional
from ar_hackathon.models.node import Node
from ar_hackathon.models.edge import Edge
from ar_hackathon.models.drive_unit import DriveUnit
from ar_hackathon.models.pod import Pod


class GraphState:
    def __init__(self, current_time_step: int,
                 nodes: List[Node],
                 edges: List[Edge],
                 drive_units: List[DriveUnit],
                 active_pods: List[Pod]):
        self.current_time_step = current_time_step
        self.nodes = nodes
        self.edges = edges
        self.drive_units = drive_units
        self.active_pods = active_pods
        self.delivered_pods = []

    def get_node(self, node_id: int) -> Optional[Node]:
        """Find a node by its ID."""
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def get_edge(self, from_node: int, to_node: int) -> Optional[Edge]:
        """
        Find an edge allowing travel from from_node to to_node.

        Bidirectional edges match in either direction.
        """
        for edge in self.edges:
            if edge.connects(from_node, to_node):
                return edge
        return None

    def get_drive_unit(self, unit_id: int) -> Optional[DriveUnit]:
        """Find a drive unit by its ID."""
        for unit in self.drive_units:
            if unit.id == unit_id:
                return unit
        return None

    def get_pod(self, pod_id: str) -> Optional[Pod]:
        """Find a pod (active or delivered) by its ID."""
        for pod in self.active_pods:
            if pod.id == pod_id:
                return pod
        for pod in self.delivered_pods:
            if pod.id == pod_id:
                return pod
        return None

    def neighbors(self, node_id: int) -> List[int]:
        """Return the IDs of all nodes reachable from node_id via one edge."""
        result = []
        for edge in self.edges:
            if edge.from_node == node_id:
                result.append(edge.to_node)
            elif edge.bidirectional and edge.to_node == node_id:
                result.append(edge.from_node)
        return result

    def edge_occupancy(self, from_node: int, to_node: int) -> int:
        """
        Count the drive units currently traversing the edge between these
        nodes (both directions combined if the edge is bidirectional).
        """
        edge = self.get_edge(from_node, to_node)
        if edge is None:
            return 0

        count = 0
        for unit in self.drive_units:
            if unit.in_transit and edge.connects(unit.current_node, unit.transit_destination):
                count += 1
        return count

    def node_occupancy(self, node_id: int) -> int:
        """
        Count the drive units occupying this node plus those currently in
        transit toward it (inbound units reserve their slot on departure).
        """
        count = 0
        for unit in self.drive_units:
            if unit.in_transit:
                if unit.transit_destination == node_id:
                    count += 1
            elif unit.current_node == node_id:
                count += 1
        return count

    def deep_copy(self):
        """Create a deep copy of this GraphState."""
        nodes = [node.deep_copy() for node in self.nodes]
        edges = [edge.deep_copy() for edge in self.edges]
        drive_units = [unit.deep_copy() for unit in self.drive_units]
        active_pods = [pod.deep_copy() for pod in self.active_pods]

        new_state = GraphState(
            current_time_step=self.current_time_step,
            nodes=nodes,
            edges=edges,
            drive_units=drive_units,
            active_pods=active_pods
        )

        new_state.delivered_pods = [pod.deep_copy() for pod in self.delivered_pods]

        return new_state
