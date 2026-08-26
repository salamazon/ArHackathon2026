# Amazon Robotics Hackathon 2026 - Drive Unit Routing

Welcome to the Amazon Robotics Hackathon! Your challenge is to route **drive units** - the robots that carry pods of inventory across a fulfillment center floor - from storage locations to pick stations as efficiently as possible.

The floor is a weighted graph: nodes are locations (storage, stations, travel waypoints) and edges are aisle segments that take time to traverse. Your algorithm decides, one time step at a time, where each drive unit moves next.

## Prerequisites

- Install Git: https://git-scm.com/downloads
- Install Python (includes pip): https://www.python.org/downloads/

## Installation

```bash
git clone <repository-url>
cd ArHackathon2026

# macOS / Linux
python3 -m pip install -e .

# Windows
py -m pip install -e .
```

> **Windows:** use `python` or `py -3` wherever the commands below say `python3`.

Re-run the install command if you change your environment; code changes to `routing.py` are picked up automatically because the install is editable.

## Your Task

Implement `drive_unit_next_move` in `ar_hackathon/api/routing.py`:

```python
def drive_unit_next_move(drive_unit_id: int, state: GraphState) -> Optional[int]:
    """
    Returns the ID of an adjacent node to move to, or None to wait.
    """
```

The engine calls this function once per **idle** drive unit per time step (units already moving along an edge are not asked). You are handed a deep copy of the full floor state, so you can inspect everything: nodes, edges, all drive units, and all pods.

### What you can return

- The ID of a node adjacent to the unit's current node → the unit starts traversing that edge.
- `None` (or the unit's current node) → the unit waits one time step. Waiting is a legitimate tactic for yielding a busy aisle.
- Anything invalid (no such edge, full edge, full station, garbage) → the move is ignored and the unit waits.

### Pickups and deliveries are automatic

- A drive unit with free carrying capacity that is standing at a node with a waiting pod **picks it up** (lowest unit ID first when several units are present).
- A drive unit standing at a carried pod's destination station **drops it off**.

You never issue pickup/drop commands - you steer, the floor does the rest. To claim a pod, be the first unit to reach it.

## Game Mechanics

Each time step the engine:

1. Spawns pods whose `entry_time` has arrived.
2. Resolves deliveries and pickups for units standing at nodes.
3. Polls your `drive_unit_next_move` for each idle unit, **in ascending unit ID order**. Valid moves are committed immediately, so when two units contend for the same edge or station slot, the lower ID wins and the other is blocked (it waits this step).
4. Advances units in transit; arrivals resolve their deliveries/pickups the same step.
5. Increments time.

### Capacities and collisions

- **Edge capacity** - the maximum number of drive units traversing an aisle at once (both directions combined on bidirectional edges). Trying to enter a full aisle blocks the drive unit for that step. A capacity-1 aisle is a narrow corridor: expect traffic jams if everyone takes the shortest path.
- **Node capacity** - the maximum number of drive units occupying a node *plus* drive units currently inbound to it. Inbound drive units reserve their slot when they depart, so you can never be stranded mid-aisle. A capacity-1 station is a single dock: don't park there.
- **Drive unit capacity** - how many pods a drive unit can carry at once (default 1).

Units are never destroyed; a blocked move just wastes time. Wasted time is what costs you points.

### A note on coordination

The function is called per drive unit, but nothing stops you from planning globally: the full state is in every call, and module-level variables in your `routing.py` persist between calls. Deciding *which* unit chases *which* pod is most of the game from Level 2 onward.

## Difficulty Levels

- **Level 1 - Shortest path.** A single drive unit ferries pods one route at a time. Weighted-graph search is all you need.
- **Level 2 - Sharing the floor.** Multiple drive units, narrow (capacity-1) aisles. You decide which unit takes which pod and how to route around each other. Greedy assignment with a priority queue is a good start; it is not the end.
- **Level 3 - Capacity limits.** Each station has a limited number of docks, so only so many drive units fit at once. Drive units may also carry more than one pod at a time. Pods flow from multiple storage areas. Open-ended: batching, sequencing, and dock discipline all matter.

## Scoring

Each delivered pod earns `100 × e^(-delivery_duration / 50)` points, where `delivery_duration` is the number of time steps between the pod entering the system and its delivery. The total is normalized so a theoretically instant delivery of every pod scores 100. Undelivered pods score 0 - the simulation ends at `max_time_steps` regardless.

Faster deliveries score more; leaving pods stranded hurts most of all. No solution will be able to achieve a score of 100.

## Running Test Cases

```bash
# Run your implementation
python3 scripts/run_game.py test_cases/level1/test_case_1.json

# Run the (deliberately naive) example driver
python3 scripts/run_game.py test_cases/level1/test_case_1.json --driver basic

# Watch it one step at a time
python3 scripts/run_game.py test_cases/level1/test_case_1.json --step-by-step
```

The test cases in `test_cases/` are for practice. When you submit, your
solution is evaluated against **additional hidden test cases** of similar size
and difficulty - don't overfit to the provided ones. Your final score is the
sum of your scores across all evaluation test cases.

## Visualization

Watch your drive units move around the floor:

```bash
python3 scripts/visualize.py test_cases/level1/test_case_1.json --driver basic
```

This runs the simulation and writes `visualization_output/animation.html`. You can view it in your browser by running the following and pasting the output into your browser address bar:

```bash
echo "file:///$(pwd)/visualization_output/animation.html"
```

Use the play button / slider to step through time. Storage nodes are orange squares, stations are purple diamonds, drive units are dots (blue empty, green carrying) drawn partway along an aisle while in transit, and an aisle turns red when it is at capacity.

**Green = carrying, blue = empty.**

Kaleido requires Google Chrome to be installed for PNG export. If Chrome is not installed, run with `--format html` - the animation is unaffected.

Note that there is a glitch with the visualizer where the drive units will appear to jump around the first time it runs. Let it run, then drag the slider back to the start and they won't jump around.

The example driver (`ar_hackathon/examples/basic_driver.py`) greedily takes the cheapest nearby aisle with no lookahead and ignores every other drive unit. It loses pods on all but the simplest cases. Beating it is your baseline.

## Rules

1. Only `ar_hackathon/api/routing.py` may be modified and submitted. Fill in your team name and email in its header.
2. Python standard library only - no external packages.
3. Each call to `drive_unit_next_move` must return within **1 second**; a timeout or exception counts as a wait.
4. Each test case must complete within **2 minutes** on the grading machine.
5. Invalid moves are silently ignored (the unit waits). The engine, models, and test cases are fixed - don't fight the referee.

## Submission

1. Open `team.json` and fill in your team `"name"` and member `"emails"`.
   The `"submit_url"` is already filled in - leave it alone.
2. Make sure your team name and email are also in the header of `routing.py`
   (that's how we contact you if the scoring system hiccups).
3. Run:

```bash
python3 submit.py
```

You can submit as many times as you like; your latest submission is the one
that counts. Scores take a few minutes to appear on the leaderboard. Your
team **name** is your identity on the leaderboard - pick a distinctive one
and keep using exactly the same spelling all day, or your submissions will
land on separate leaderboard rows.

## Project Structure

```
ArHackathon2026/
├── ar_hackathon/
│   ├── api/
│   │   └── routing.py          # YOUR IMPLEMENTATION GOES HERE
│   ├── engine/
│   │   └── game_engine.py      # Simulation engine
│   ├── examples/
│   │   └── basic_driver.py     # Naive example driver
│   ├── models/
│   │   ├── drive_unit.py       # DriveUnit: position, transit, carrying
│   │   ├── edge.py             # Edge: weight, capacity, bidirectional
│   │   ├── graph_state.py      # GraphState: everything, plus lookup helpers
│   │   ├── node.py             # Node: type (storage/station/travel), capacity
│   │   ├── pod.py              # Pod: source, destination station, timing
│   │   └── test_case.py        # Test case loader
│   ├── utils/
│   │   ├── json_loader.py
│   │   └── routing_utils.py    # is_valid_move - the referee's rulebook
│   ├── visualizers/            # Plotly floor renderer + animation
│   └── simulation_runner.py    # Drives the engine for the visualizer
├── scripts/
│   ├── run_game.py             # CLI runner
│   └── visualize.py            # Renders a run to animation.html
└── test_cases/
    ├── schema.json             # Test case JSON schema
    ├── level1/                 # test_case_1, test_case_2
    ├── level2/                 # test_case_3, test_case_4
    └── level3/                 # test_case_5, test_case_6
```
