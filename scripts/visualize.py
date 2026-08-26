#!/usr/bin/env python3
"""
Amazon Robotics Hackathon - Visualization Script

This script visualizes the graph state and drive unit movements.
"""

import argparse
import sys
import os
from ar_hackathon.simulation_runner import SimulationRunner
from ar_hackathon.visualizers.visualizer_factory import VisualizerFactory


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Visualize the Amazon Robotics Hackathon game.')
    parser.add_argument('test_case', help='Path to the test case JSON file')
    parser.add_argument('--driver', default='default', choices=['default', 'basic'],
                        help='Driving algorithm to use (default: default)')
    parser.add_argument('--output-dir', default='./visualization_output',
                        help='Directory to save visualization outputs')
    parser.add_argument('--max-frames', type=int, default=None,
                        help='Maximum number of frames to generate')
    parser.add_argument('--format', default='both', choices=['html', 'images', 'both'],
                        help='Output format (default: both)')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode (step by step)')
    parser.add_argument('--visualizer', default='network', choices=['network'],
                        help='Visualization backend to use (default: network)')
    args = parser.parse_args()

    # Check if the test case file exists
    if not os.path.isfile(args.test_case):
        print(f"Error: Test case file '{args.test_case}' not found.")
        sys.exit(1)

    # Create the simulation runner
    print(f"Visualizing game with test case: {args.test_case}")
    print(f"Using driver: {args.driver}")

    runner = SimulationRunner(args.test_case, args.driver)

    if args.interactive:
        # Run the simulation step by step
        engine = runner.engine
        engine.reset()
        is_finished = False

        while not is_finished:
            graph_state, is_finished = engine.step()
            print(f"Time step: {graph_state.current_time_step}")
            print(f"Active pods: {len(graph_state.active_pods)}")
            print(f"Delivered pods: {len(graph_state.delivered_pods)}")

            if not is_finished:
                input("Press Enter to continue to the next step...")

        print("\nGame Results:")
        print(f"Delivered {engine.stats['delivered_pods']} out of {engine.stats['total_pods']} pods "
              f"({engine.stats['delivery_percentage']:.2f}%)")
        print(f"Average delivery time: {engine.stats['average_delivery_time']:.2f} time steps")
        print(f"Total time steps: {engine.stats['total_time_steps']}")
    else:
        # Create the visualizer
        visualizer = VisualizerFactory.create_visualizer(args.visualizer)

        # Calculate the layout first for visualizers that support it
        if args.visualizer == 'network':
            from ar_hackathon.visualizers.network_visualizer import NetworkVisualizer
            if isinstance(visualizer, NetworkVisualizer):
                visualizer.calculate_layout(
                    runner.engine.test_case.nodes,
                    runner.engine.test_case.edges
                )

        # Run the full simulation and generate visualization
        runner.run_simulation(
            visualizer,
            output_dir=args.output_dir,
            max_frames=args.max_frames,
            save_html=(args.format in ['html', 'both']),
            save_images=(args.format in ['images', 'both'])
        )

        print(f"Visualization complete. Output saved to {args.output_dir}")
        print(f"Animation file: {os.path.join(args.output_dir, 'animation.html')}")


if __name__ == '__main__':
    main()
