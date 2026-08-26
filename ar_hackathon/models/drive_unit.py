"""
Amazon Robotics Hackathon - Drive Unit Model

This module defines the DriveUnit class for the Amazon Robotics Hackathon.
A drive unit is a robot that carries pods between nodes on the warehouse
floor.
"""

from typing import List


class DriveUnit:
    def __init__(self, unit_id: int, current_node: int, capacity: int = 1):
        """Initialize a drive unit.

        Args:
            unit_id: Unique identifier for this drive unit.
            current_node: ID of the node the unit currently occupies.
            capacity: Drive unit's pod capacity — the maximum number of PODS this unit can
                carry at the same time (default 1). This counts pods, not
                drive units; when the number of pods being carried reaches
                this value the drive unit is full and cannot pick up another pod
                until it delivers one.
        """
        self.id = unit_id
        self.current_node = current_node
        self.capacity = capacity  # Maximum number of pods this unit can carry at once
        self.carrying: List[str] = []  # IDs of the pods currently being carried

        # Transit tracking attributes
        self.in_transit = False
        self.transit_destination = None  # Node this unit is currently moving toward
        self.transit_remaining_time = 0  # Time steps remaining until arrival

    @property
    def has_capacity(self) -> bool:
        """Whether this drive unit can pick up another pod."""
        return len(self.carrying) < self.capacity

    def __repr__(self):
        if self.in_transit:
            status = f"moving {self.current_node}->{self.transit_destination}"
        else:
            status = f"at node {self.current_node}"
        return f"DriveUnit(id={self.id}, {status}, carrying={self.carrying})"

    def deep_copy(self):
        """Create a deep copy of this DriveUnit."""
        new_unit = DriveUnit(
            unit_id=self.id,
            current_node=self.current_node,
            capacity=self.capacity
        )
        new_unit.carrying = list(self.carrying)
        new_unit.in_transit = self.in_transit
        new_unit.transit_destination = self.transit_destination
        new_unit.transit_remaining_time = self.transit_remaining_time
        return new_unit
