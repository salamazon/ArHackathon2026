"""
Amazon Robotics Hackathon - Network Visualizer

This module renders the warehouse floor as a network diagram using plotly:
nodes (storage / stations / travel waypoints), aisles with their weights and
capacities, pods waiting at nodes, and drive units - including units drawn
partway along an aisle while in transit. Frames can be saved individually
and stitched into an animated HTML with play/pause controls.
"""

import logging
import math
import os
from typing import Any, Dict, List, Tuple

import networkx as nx
import plotly.graph_objects as go

from ar_hackathon.models.graph_state import GraphState
from ar_hackathon.visualizers.base_visualizer import BaseVisualizer

logger = logging.getLogger(__name__)

# Colorblind-safe (Okabe-Ito) palette
NODE_COLORS = {
    "storage": "#E69F00",  # orange
    "station": "#CC79A7",  # reddish purple
    "travel": "#999999",   # gray
}
NODE_SYMBOLS = {
    "storage": "square",
    "station": "diamond",
    "travel": "circle",
}
EDGE_COLOR = "#BBBBBB"
EDGE_CONGESTED_COLOR = "#D55E00"  # vermillion: edge at capacity
DU_EMPTY_COLOR = "#0072B2"        # blue: drive unit without a pod
DU_CARRYING_COLOR = "#009E73"     # bluish green: drive unit carrying pods
POD_LABEL_COLOR = "#E69F00"


class NetworkVisualizer(BaseVisualizer):
    """Plotly-based network visualizer for the warehouse floor."""

    FIGURE_WIDTH = 1000
    FIGURE_HEIGHT = 750

    def __init__(self):
        self.positions: Dict[int, Tuple[float, float]] = {}
        self.x_range = (-1.3, 1.3)
        self.y_range = (-1.3, 1.3)
        self._image_export_failed = False

    def calculate_layout(self, nodes: List[Any], edges: List[Any]) -> None:
        """
        Compute fixed node positions for the whole simulation.

        Args:
            nodes: List of Node objects from the test case
            edges: List of Edge objects from the test case
        """
        graph = nx.Graph()
        for node in nodes:
            graph.add_node(node.id)
        for edge in edges:
            graph.add_edge(edge.from_node, edge.to_node)

        k = 1.2 / math.sqrt(max(len(nodes), 1))
        self.positions = {
            node_id: (float(x), float(y))
            for node_id, (x, y) in nx.spring_layout(graph, k=k, seed=42).items()
        }

        xs = [p[0] for p in self.positions.values()]
        ys = [p[1] for p in self.positions.values()]
        margin = 0.3
        x_min, x_max = min(xs) - margin, max(xs) + margin
        y_min, y_max = min(ys) - margin, max(ys) + margin

        aspect = self.FIGURE_WIDTH / self.FIGURE_HEIGHT
        x_span, y_span = x_max - x_min, y_max - y_min
        if x_span < y_span * aspect:
            extra = (y_span * aspect - x_span) / 2
            x_min, x_max = x_min - extra, x_max + extra
        else:
            extra = (x_span / aspect - y_span) / 2
            y_min, y_max = y_min - extra, y_max + extra

        self.x_range = (x_min, x_max)
        self.y_range = (y_min, y_max)

    def create_frame(self, graph_state: GraphState, frame_number: int) -> go.Figure:
        """
        Create a visualization frame for the current graph state.

        Every frame contains the same trace list (one per edge, then nodes,
        edge labels, pod counts, drive units, stats) so the frames can be
        used directly in a plotly animation.
        """
        if not self.positions:
            self.calculate_layout(graph_state.nodes, graph_state.edges)

        fig = go.Figure()

        for edge in graph_state.edges:
            self._add_edge_trace(fig, graph_state, edge)

        self._add_node_trace(fig, graph_state)
        self._add_edge_label_trace(fig, graph_state)
        self._add_pod_count_trace(fig, graph_state)
        self._add_drive_unit_trace(fig, graph_state)
        self._add_stats_trace(fig, graph_state)

        fig.update_layout(
            title=f"Amazon Robotics Hackathon - time step {graph_state.current_time_step}",
            width=self.FIGURE_WIDTH,
            height=self.FIGURE_HEIGHT,
            showlegend=False,
            plot_bgcolor="white",
            xaxis=dict(range=list(self.x_range), visible=False),
            yaxis=dict(range=list(self.y_range), visible=False),
        )

        return fig

    def save_frame(self, frame: go.Figure, output_dir: str, frame_number: int,
                  save_html: bool, save_images: bool) -> None:
        """Save a frame to disk as HTML and/or PNG."""
        if save_html:
            html_path = os.path.join(output_dir, f"frame_{frame_number:04d}.html")
            frame.write_html(html_path, config={"displayModeBar": False})

        if save_images:
            img_path = os.path.join(output_dir, f"frame_{frame_number:04d}.png")
            try:
                frame.write_image(img_path, width=self.FIGURE_WIDTH, height=self.FIGURE_HEIGHT)
            except Exception as e:
                # PNG export needs a working kaleido; HTML output still works without it
                if not self._image_export_failed:
                    logger.warning(f"Image export unavailable ({e}); saving HTML only")
                    self._image_export_failed = True

    def create_animation(self, frames: List[go.Figure], output_dir: str) -> None:
        """Create an animated HTML file from a list of frames."""
        if not frames:
            return

        fig = go.Figure(data=frames[0].data, layout=frames[0].layout)
        fig.frames = [
            go.Frame(data=frame.data, layout=frame.layout, name=str(i))
            for i, frame in enumerate(frames)
        ]
        self._add_animation_controls(fig, len(frames))

        animation_path = os.path.join(output_dir, "animation.html")
        fig.write_html(animation_path, config={"displayModeBar": False})

    def _add_animation_controls(self, fig: go.Figure, frame_count: int) -> None:
        """Add play/pause buttons and a time-step slider."""
        fig.update_layout(
            updatemenus=[{
                "type": "buttons",
                "direction": "left",
                "x": 0.05, "y": -0.05,
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [None, {
                            "frame": {"duration": 600, "redraw": True},
                            "fromcurrent": True,
                            "transition": {"duration": 0},
                        }],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [[None], {
                            "frame": {"duration": 0, "redraw": False},
                            "mode": "immediate",
                        }],
                    },
                ],
            }],
            sliders=[{
                "x": 0.15, "y": -0.02,
                "len": 0.8,
                "currentvalue": {"prefix": "Time step: "},
                "steps": [
                    {
                        "label": str(i),
                        "method": "animate",
                        "args": [[str(i)], {
                            "frame": {"duration": 0, "redraw": True},
                            "mode": "immediate",
                        }],
                    }
                    for i in range(frame_count)
                ],
            }],
        )

    def _add_edge_trace(self, fig: go.Figure, graph_state: GraphState, edge: Any) -> None:
        """Draw one aisle, widened by traffic and highlighted when full."""
        x0, y0 = self.positions[edge.from_node]
        x1, y1 = self.positions[edge.to_node]

        occupancy = graph_state.edge_occupancy(edge.from_node, edge.to_node)
        congested = edge.capacity is not None and occupancy >= edge.capacity

        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(
                width=1.5 + 1.5 * occupancy,
                color=EDGE_CONGESTED_COLOR if congested else EDGE_COLOR,
            ),
            hoverinfo="text",
            text=f"weight {edge.weight}"
                 + (f", capacity {edge.capacity}" if edge.capacity is not None else "")
                 + f", {occupancy} unit(s) on aisle",
        ))

    def _add_node_trace(self, fig: go.Figure, graph_state: GraphState) -> None:
        """Draw all nodes with type-specific markers and labels."""
        xs, ys, colors, symbols, labels, hovers = [], [], [], [], [], []
        for node in graph_state.nodes:
            x, y = self.positions[node.id]
            xs.append(x)
            ys.append(y)
            colors.append(NODE_COLORS.get(node.node_type, NODE_COLORS["travel"]))
            symbols.append(NODE_SYMBOLS.get(node.node_type, "circle"))
            label = node.name
            if node.capacity is not None:
                label += f" (cap {node.capacity})"
            labels.append(label)
            hovers.append(f"node {node.id}: {node.node_type}"
                          + (f", occupancy {graph_state.node_occupancy(node.id)}/{node.capacity}"
                             if node.capacity is not None else ""))

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            marker=dict(size=22, color=colors, symbol=symbols,
                        line=dict(width=1, color="#444444")),
            text=labels,
            textposition="bottom center",
            textfont=dict(size=10),
            hoverinfo="text",
            hovertext=hovers,
        ))

    def _add_edge_label_trace(self, fig: go.Figure, graph_state: GraphState) -> None:
        """Draw weight (and capacity) labels at aisle midpoints."""
        xs, ys, labels = [], [], []
        for edge in graph_state.edges:
            x0, y0 = self.positions[edge.from_node]
            x1, y1 = self.positions[edge.to_node]
            xs.append((x0 + x1) / 2)
            ys.append((y0 + y1) / 2)
            label = f"{edge.weight:g}"
            if edge.capacity is not None:
                label += f" (cap {edge.capacity})"
            labels.append(label)

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="text",
            text=labels,
            textfont=dict(size=9, color="#888888"),
            hoverinfo="skip",
        ))

    def _add_pod_count_trace(self, fig: go.Figure, graph_state: GraphState) -> None:
        """Show how many pods are waiting at each node."""
        counts: Dict[int, int] = {}
        for pod in graph_state.active_pods:
            if pod.carried_by is None and pod.current_node is not None:
                counts[pod.current_node] = counts.get(pod.current_node, 0) + 1

        xs, ys, labels = [], [], []
        for node_id, count in counts.items():
            x, y = self.positions[node_id]
            xs.append(x)
            ys.append(y + 0.09)
            labels.append(f"{count} pod{'s' if count > 1 else ''}")

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="text",
            text=labels,
            textfont=dict(size=10, color=POD_LABEL_COLOR),
            hoverinfo="skip",
        ))

    def _add_drive_unit_trace(self, fig: go.Figure, graph_state: GraphState) -> None:
        """
        Draw all drive units: parked units fan out around their node, units
        in transit are placed proportionally along their aisle.
        """
        at_node: Dict[int, List[Any]] = {}
        for unit in graph_state.drive_units:
            if not unit.in_transit:
                at_node.setdefault(unit.current_node, []).append(unit)

        xs, ys, colors, labels = [], [], [], []
        for unit in sorted(graph_state.drive_units, key=lambda u: u.id):
            if unit.in_transit:
                x0, y0 = self.positions[unit.current_node]
                x1, y1 = self.positions[unit.transit_destination]
                edge = graph_state.get_edge(unit.current_node, unit.transit_destination)
                weight = edge.weight if edge is not None else 1
                progress = min(max(1 - unit.transit_remaining_time / weight, 0.0), 1.0)
                x = x0 + (x1 - x0) * progress
                y = y0 + (y1 - y0) * progress
            else:
                x, y = self.positions[unit.current_node]
                peers = at_node[unit.current_node]
                if len(peers) > 1:
                    angle = 2 * math.pi * peers.index(unit) / len(peers)
                    x += 0.06 * math.cos(angle)
                    y += 0.06 * math.sin(angle)

            xs.append(x)
            ys.append(y)
            colors.append(DU_CARRYING_COLOR if unit.carrying else DU_EMPTY_COLOR)
            label = f"DU{unit.id}"
            if unit.carrying:
                label += ":" + ",".join(unit.carrying)
            labels.append(label)

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="markers+text",
            marker=dict(size=13, color=colors, symbol="circle",
                        line=dict(width=1, color="#FFFFFF")),
            text=labels,
            textposition="top center",
            textfont=dict(size=9),
            hoverinfo="text",
            hovertext=labels,
        ))

    def _add_stats_trace(self, fig: go.Figure, graph_state: GraphState) -> None:
        """Pin a live stats readout to the top-left corner."""
        carried = sum(1 for pod in graph_state.active_pods if pod.carried_by is not None)
        stats = (f"t = {graph_state.current_time_step}   "
                 f"active pods: {len(graph_state.active_pods)} ({carried} on robots)   "
                 f"delivered: {len(graph_state.delivered_pods)}")

        fig.add_trace(go.Scatter(
            x=[self.x_range[0] + 0.05],
            y=[self.y_range[1] - 0.05],
            mode="text",
            text=[stats],
            textposition="bottom right",
            textfont=dict(size=12, color="#333333"),
            hoverinfo="skip",
        ))
