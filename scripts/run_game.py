#!/usr/bin/env python3
"""
Amazon Robotics Hackathon - Run Game Script

This script runs the game with a specified test case and driving algorithm.
"""

import argparse
import sys
import os
from ar_hackathon.engine.game_engine import GameEngine
from ar_hackathon.api.routing import drive_unit_next_move


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Run the Amazon Robotics Hackathon game.')
    parser.add_argument('test_case', help='Path to the test case JSON file')
    parser.add_argument('--driver', default='default', choices=['default', 'basic'],
                        help='Driving algorithm to use (default: default)')
    parser.add_argument('--step-by-step', action='store_true',
                        help='Run the game step by step (for debugging)')
    args = parser.parse_args()

    # Check if the test case file exists
    if not os.path.isfile(args.test_case):
        print(f"Error: Test case file '{args.test_case}' not found.")
        sys.exit(1)

    # Select the driving algorithm
    driver = drive_unit_next_move  # Default driver (student implementation)
    if args.driver == 'basic':
        from ar_hackathon.examples.basic_driver import basic_driver
        driver = basic_driver

    # Run the game
    print(f"Running game with test case: {args.test_case}")
    print(f"Using driver: {args.driver}")

    engine = GameEngine(args.test_case, driver)
    if args.step_by_step:
        is_finished = False

        while not is_finished:
            graph_state, is_finished = engine.step()
            print(f"Time step: {graph_state.current_time_step}")
            print(f"Active pods: {len(graph_state.active_pods)}")
            print(f"Delivered pods: {len(graph_state.delivered_pods)}")

            if not is_finished:
                input("Press Enter to continue to the next step...")

        score = engine.stats
    else:
        score = engine.run_until_finished()

    # Print the results
    print("\nGame Results:")
    print(f"Score: {score['score']}")
    print(f"Delivered {score['delivered_pods']} out of {score['total_pods']} pods "
          f"({score['delivery_percentage']:.2f}%)")
    print(f"Average delivery time: {score['average_delivery_time']:.2f} time steps")
    print(f"Total time steps: {score['total_time_steps']}")


if __name__ == '__main__':
    main()
