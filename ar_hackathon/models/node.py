"""
Amazon Robotics Hackathon - Node Model

This module defines the Node class for the Amazon Robotics Hackathon.
A node is a location on the warehouse floor: a storage location, a
station, or a plain travel waypoint.
"""

from typing import Optional


class Node:
    def __init__(self, node_id: int, name: str = None, node_type: str = "travel",
                 capacity: Optional[int] = None):
        """Initialize a node (a location on the warehouse floor).

        Args:
            node_id: Unique identifier for this node.
            name: Human-readable name.
            node_type: One of "storage", "station", or "travel".
            capacity: Node capacity — how many DRIVE UNITS this node can hold
                at once. Units already here and units on their way here both
                count toward the limit. This counts drive units, not pods;
                for a station it is the number of docks. None means unlimited.
        """
        self.id = node_id
        self.name = name if name is not None else str(node_id)
        self.node_type = node_type  # "storage", "station", or "travel"
        # Maximum number of drive units that may occupy this node or be
        # in transit toward it at the same time. None means unlimited.
        self.capacity = capacity

    def __repr__(self):
        return f"Node(id={self.id}, type='{self.node_type}', capacity={self.capacity})"

    def deep_copy(self):
        """Create a deep copy of this Node."""
        return Node(
            node_id=self.id,
            name=self.name,
            node_type=self.node_type,
            capacity=self.capacity
        )
