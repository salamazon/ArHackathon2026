"""
Amazon Robotics Hackathon - Game Engine

This module implements the core game engine for the Amazon Robotics Hackathon.
"""

from typing import Dict, Optional, Any, Callable, TypeVar, Tuple
import concurrent.futures
import logging
import math
from ar_hackathon.models.graph_state import GraphState
from ar_hackathon.models.drive_unit import DriveUnit
from ar_hackathon.utils.json_loader import load_test_case
from ar_hackathon.utils.routing_utils import is_valid_move

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameEngine:
    """
    Game engine for the Amazon Robotics Hackathon.

    This class encapsulates the game simulation logic, allowing step-by-step
    execution or running the entire simulation at once.
    """

    def __init__(self, test_case_path: str, player_algorithm: Callable[[int, GraphState], Optional[int]]):
        """
        Initialize the game engine with a test case and player algorithm.

        Args:
            test_case_path: Path to the JSON test case file
            player_algorithm: Function implementing the drive unit routing algorithm
        """
        self.test_case_path = test_case_path
        self.player_algorithm = player_algorithm
        self.test_case = load_test_case(test_case_path)
        self.graph_state = self._initialize_graph_state()
        self.is_finished = False
        self.stats = {}

    def _initialize_graph_state(self) -> GraphState:
        """Initialize graph state from the test case."""
        # Deep copies keep the test case pristine so reset() is always clean
        return GraphState(
            current_time_step=0,
            nodes=[node.deep_copy() for node in self.test_case.nodes],
            edges=[edge.deep_copy() for edge in self.test_case.edges],
            drive_units=[unit.deep_copy() for unit in self.test_case.drive_units],
            active_pods=[]
        )

    def reset(self) -> None:
        """Reset the game to its initial state."""
        self.graph_state = self._initialize_graph_state()
        self.is_finished = False
        self.stats = {}

    def step(self) -> Tuple[GraphState, bool]:
        """
        Advance the game by one time step.

        Returns:
            graph_state: The updated graph state
            is_finished: Whether the game is finished
        """
        if self.is_finished:
            return self.graph_state, True

        # 1. Process new pods entering the system
        self._process_new_pods()

        # 2. Resolve deliveries and pickups for drive units standing at nodes
        self._process_deliveries_and_pickups()

        # 3. For each drive unit that's not in transit, call the player's algorithm
        self._route_drive_units()

        # 4. Advance drive units in transit
        self._advance_drive_units()

        # 5. Resolve deliveries and pickups for drive units that just arrived
        self._process_deliveries_and_pickups()

        # 6. Advance time step
        self.graph_state.current_time_step += 1

        # 7. Check if game is over
        self.is_finished = self._is_game_over()

        # 8. Calculate stats if game is over
        if self.is_finished:
            self.stats = self._calculate_score()

        return self.graph_state, self.is_finished

    def run_until_finished(self) -> Dict[str, Any]:
        """
        Run the game until it's finished.

        Returns:
            stats: Dictionary containing the final score and statistics
        """
        while not self.is_finished:
            self.step()

        return self.stats

    def _is_game_over(self) -> bool:
        """Check if the game is over."""
        # Check if there are no more pods to spawn or deliver
        if self.test_case.num_remaining_pods(self.graph_state.current_time_step) == 0 and not self.graph_state.active_pods:
            return True

        # Check if the maximum time steps have been reached
        return self.graph_state.current_time_step >= self.test_case.max_time_steps

    def _process_new_pods(self) -> None:
        """Process pods that enter the system at the current time step."""
        # Get pods entering at the current time step
        new_pods = self.test_case.pods_by_time.get(self.graph_state.current_time_step, [])

        # Add deep copies so the test case stays reusable across resets
        self.graph_state.active_pods.extend(pod.deep_copy() for pod in new_pods)

    def _process_deliveries_and_pickups(self) -> None:
        """
        Deliver and pick up pods for every drive unit standing at a node.

        Deliveries happen first (freeing capacity), then pickups. Both are
        automatic: a drive unit standing at a pod's destination station
        drops it off, and a drive unit with free capacity standing at a
        node with a waiting pod picks it up. When several units stand at
        the same node, the lowest unit ID picks up first.
        """
        for unit in sorted(self.graph_state.drive_units, key=lambda u: u.id):
            if unit.in_transit:
                continue

            # Deliveries
            for pod_id in list(unit.carrying):
                pod = self.graph_state.get_pod(pod_id)
                if pod is not None and pod.destination_station == unit.current_node:
                    unit.carrying.remove(pod_id)
                    pod.carried_by = None
                    pod.current_node = unit.current_node
                    pod.delivery_time = self.graph_state.current_time_step
                    self.graph_state.active_pods.remove(pod)
                    self.graph_state.delivered_pods.append(pod)

            # Pickups
            if unit.has_capacity:
                waiting_pods = [pod for pod in self.graph_state.active_pods
                                if pod.carried_by is None and pod.current_node == unit.current_node]
                waiting_pods.sort(key=lambda p: (p.entry_time, p.id))
                for pod in waiting_pods:
                    if not unit.has_capacity:
                        break
                    pod.carried_by = unit.id
                    pod.current_node = None
                    unit.carrying.append(pod.id)

    def _route_drive_units(self) -> None:
        """
        Route drive units using the player's algorithm.

        Units are polled in ascending ID order and each valid move is
        committed immediately, so when two units contend for the same
        edge or node slot the lower ID wins and the other is blocked
        (it stays where it is for this time step).
        """
        for unit in sorted(self.graph_state.drive_units, key=lambda u: u.id):
            if not unit.in_transit:
                next_node = safe_execute(
                    self.player_algorithm,
                    unit.id,
                    self.graph_state.deep_copy(),
                    timeout_seconds=1,
                    default_return_value=None  # Stay at current node if timeout/exception
                )

                if next_node is not None and is_valid_move(self.graph_state, unit, next_node):
                    self._move_drive_unit(unit, next_node)

    def _move_drive_unit(self, unit: DriveUnit, next_node: int) -> bool:
        """Start moving a drive unit from its current node to the next node."""
        edge = self.graph_state.get_edge(unit.current_node, next_node)

        # If no edge exists, the move is invalid
        if edge is None:
            return False

        # Update drive unit transit information. Edge and node occupancy are
        # derived from transit state, so no counters need to be maintained.
        unit.in_transit = True
        unit.transit_destination = next_node
        unit.transit_remaining_time = edge.weight

        return True

    def _advance_drive_units(self) -> None:
        """Advance all drive units that are in transit."""
        for unit in self.graph_state.drive_units:
            if unit.in_transit:
                # Decrement remaining time
                unit.transit_remaining_time -= 1

                # Check if the drive unit has arrived
                if unit.transit_remaining_time <= 0:
                    # Update drive unit location
                    unit.current_node = unit.transit_destination

                    # Reset transit data
                    unit.in_transit = False
                    unit.transit_destination = None
                    unit.transit_remaining_time = 0

    def _calculate_score(self) -> Dict[str, Any]:
        """
        Calculate the final score based on delivered pods.

        Uses a per-pod scoring scheme where each pod gets points based on
        how quickly it was delivered. The total score is normalized to a 0-100 scale.
        """
        # Calculate basic stats
        delivered_pods = len(self.graph_state.delivered_pods)
        total_pods = self.test_case.total_pods()

        # Base score for delivering a pod
        base_points = 100

        # Calculate score for each pod
        total_score = 0
        total_delivery_time = 0

        for pod in self.graph_state.delivered_pods:
            # Calculate delivery duration
            delivery_duration = pod.delivery_time - pod.entry_time
            total_delivery_time += delivery_duration

            # Calculate time efficiency factor (decreases as delivery time increases)
            # Using an exponential decay function: e^(-delivery_duration/50)
            # This gives diminishing returns for faster deliveries
            time_factor = math.exp(-delivery_duration / 50)

            # Calculate pod score
            pod_score = base_points * time_factor
            total_score += pod_score

        # Calculate average delivery time
        average_delivery_time = (total_delivery_time / delivered_pods) if delivered_pods > 0 else 0
        delivery_percentage = (delivered_pods / total_pods * 100) if total_pods > 0 else 0

        # Normalize the score (0-100)
        # Maximum possible score would be base_points * total_pods (if all delivered instantly)
        max_possible_score = base_points * total_pods
        normalized_score = (total_score / max_possible_score * 100) if max_possible_score > 0 else 0

        return {
            "score": normalized_score,
            "raw_score": total_score,
            "delivered_pods": delivered_pods,
            "total_pods": total_pods,
            "delivery_percentage": delivery_percentage,
            "average_delivery_time": average_delivery_time,
            "total_time_steps": self.graph_state.current_time_step
        }


T = TypeVar('T')
def safe_execute(func: Callable[..., T], *args: Any, timeout_seconds: int = 10,
                default_return_value: Optional[Any] = None, **kwargs: Any) -> Optional[T]:
    """
    Execute a function safely with timeout and exception handling.

    Args:
        func: The function to execute
        args: Positional arguments to pass to the function
        timeout_seconds: Maximum execution time in seconds
        default_return_value: Value to return if the function times out or raises an exception
        kwargs: Keyword arguments to pass to the function

    Returns:
        The function's return value, or default_return_value if an exception occurs
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
            return default_return_value
        except Exception as e:
            logger.warning(f"Function {func.__name__} raised an exception: {str(e)}")
            return default_return_value
