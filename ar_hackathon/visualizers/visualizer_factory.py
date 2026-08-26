"""
Amazon Robotics Hackathon - Visualizer Factory

This module provides a factory for creating visualizer instances.
"""

from ar_hackathon.visualizers.base_visualizer import BaseVisualizer
from ar_hackathon.visualizers.network_visualizer import NetworkVisualizer


class VisualizerFactory:
    """Factory class for creating visualizer instances."""

    @staticmethod
    def create_visualizer(visualizer_type: str) -> BaseVisualizer:
        """
        Create a visualizer instance based on the specified type.

        Args:
            visualizer_type: Type of visualizer to create ('network', etc.)

        Returns:
            An instance of a class implementing the BaseVisualizer interface
        """
        if visualizer_type == 'network':
            return NetworkVisualizer()
        # Add more visualizer types as needed
        else:
            raise ValueError(f"Unknown visualizer type: {visualizer_type}")
