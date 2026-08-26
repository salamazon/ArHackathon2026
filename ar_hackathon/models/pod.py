"""
Amazon Robotics Hackathon - Pod Model

This module defines the Pod class for the Amazon Robotics Hackathon.
A pod is a shelf of inventory that must be carried from a storage node
to its destination station by a drive unit.
"""

from typing import Optional


class Pod:
    def __init__(self, pod_id: str, current_node: Optional[int], destination_station: int,
                 entry_time: int):
        self.id = pod_id
        self.current_node = current_node  # None while being carried by a drive unit
        self.destination_station = destination_station  # Final destination station node
        self.entry_time = entry_time
        self.delivery_time = None  # Will be set when the pod is delivered
        self.carried_by = None  # ID of the drive unit carrying this pod, or None

    def __repr__(self):
        if self.carried_by is not None:
            status = f"carried by DU {self.carried_by}"
        else:
            status = f"at node {self.current_node}"
        return f"Pod(id='{self.id}', {status}, dest={self.destination_station})"

    def deep_copy(self):
        """Create a deep copy of this Pod."""
        new_pod = Pod(
            pod_id=self.id,
            current_node=self.current_node,
            destination_station=self.destination_station,
            entry_time=self.entry_time
        )
        new_pod.delivery_time = self.delivery_time
        new_pod.carried_by = self.carried_by
        return new_pod
