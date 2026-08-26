"""
Amazon Robotics Hackathon - Edge Model

This module defines the Edge class for the Amazon Robotics Hackathon.
An edge is an aisle segment between two nodes on the warehouse floor.
"""

from typing import Optional


class Edge:
    def __init__(self, from_node: int, to_node: int, weight: float,
                 capacity: Optional[int] = None, bidirectional: bool = True):
        """Initialize an edge (an aisle segment between two nodes).

        Args:
            from_node: ID of the node this edge starts at.
            to_node: ID of the node this edge leads to.
            weight: Time steps required to traverse this aisle.
            capacity: Edge capacity — how many DRIVE UNITS can be traversing
                this aisle at the same time (both directions combined if the
                edge is bidirectional). This counts drive units, not pods.
                None means unlimited.
            bidirectional: Whether the aisle can be traveled in both directions.
        """
        self.from_node = from_node
        self.to_node = to_node
        self.weight = weight  # Time steps required to traverse this edge
        # Maximum number of drive units that may be traversing this edge at
        # the same time (both directions combined if bidirectional).
        # None means unlimited.
        self.capacity = capacity
        self.bidirectional = bidirectional

    def connects(self, from_node: int, to_node: int) -> bool:
        """Check whether this edge allows travel from from_node to to_node."""
        if self.from_node == from_node and self.to_node == to_node:
            return True
        if self.bidirectional and self.from_node == to_node and self.to_node == from_node:
            return True
        return False

    def __repr__(self):
        arrow = "<->" if self.bidirectional else "->"
        return (f"Edge({self.from_node}{arrow}{self.to_node}, "
                f"weight={self.weight}, capacity={self.capacity})")

    def deep_copy(self):
        """Create a deep copy of this Edge."""
        return Edge(
            from_node=self.from_node,
            to_node=self.to_node,
            weight=self.weight,
            capacity=self.capacity,
            bidirectional=self.bidirectional
        )
