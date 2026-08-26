"""
Amazon Robotics Hackathon - TestCase Model

This module defines the TestCase class for the Amazon Robotics Hackathon.
"""

from typing import Dict, Any
from ar_hackathon.models.node import Node
from ar_hackathon.models.edge import Edge
from ar_hackathon.models.drive_unit import DriveUnit
from ar_hackathon.models.pod import Pod


class TestCase:
    """
    Represents a test case from an input JSON file.

    This class models the structure of the input file according to the schema.
    """

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize a TestCase from a dictionary loaded from a JSON file.

        Args:
            data: Dictionary containing the test case data
        """
        # Metadata
        self.metadata = data.get("metadata", {})
        self.max_time_steps = self.metadata.get("max_time_steps", 100)
        self.description = self.metadata.get("description", "")

        # Nodes - keep as a simple list matching the schema
        self.nodes = []
        for node_data in data.get("nodes", []):
            node = Node(
                node_id=node_data["id"],
                name=node_data.get("name"),
                node_type=node_data.get("type", "travel"),
                capacity=node_data.get("capacity")
            )
            self.nodes.append(node)

        # Edges - keep as a simple list matching the schema
        self.edges = []
        for edge_data in data.get("edges", []):
            edge = Edge(
                from_node=edge_data["from_node"],
                to_node=edge_data["to_node"],
                weight=edge_data["weight"],
                capacity=edge_data.get("capacity"),
                bidirectional=edge_data.get("bidirectional", True)
            )
            self.edges.append(edge)

        # Drive units - keep as a simple list matching the schema
        self.drive_units = []
        for unit_data in data.get("drive_units", []):
            unit = DriveUnit(
                unit_id=unit_data["id"],
                current_node=unit_data["start_node"],
                capacity=unit_data.get("capacity", 1)
            )
            self.drive_units.append(unit)

        # Pods - store in a map indexed by entry_time
        # Each entry is a list of Pod objects
        self.pods_by_time = {}
        for pod_data in data.get("pods", []):
            pod = Pod(
                pod_id=pod_data["id"],
                current_node=pod_data["source_node"],
                destination_station=pod_data["destination_station"],
                entry_time=pod_data["entry_time"]
            )

            if pod.entry_time not in self.pods_by_time:
                self.pods_by_time[pod.entry_time] = []

            self.pods_by_time[pod.entry_time].append(pod)

    def total_pods(self) -> int:
        """Total number of pods defined in this test case."""
        return sum(len(pods) for pods in self.pods_by_time.values())

    def num_remaining_pods(self, current_time: int) -> int:
        """
        Calculate the number of pods that have not yet entered the system at the given time.

        Args:
            current_time: The next time step the simulation will run

        Returns:
            The total count of pods scheduled to enter at or after that time step
        """
        remaining_count = 0

        for entry_time, pods in self.pods_by_time.items():
            # >= because the step for current_time has not run yet: pods with
            # entry_time == current_time still spawn at the start of that step
            if entry_time >= current_time:
                remaining_count += len(pods)

        return remaining_count
