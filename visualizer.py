"""
visualizer.py — Matplotlib desktop window for Panopticon.

Opens a single figure split into two panels:

  LEFT (72 %)  — force-directed network graph (Fruchterman-Reingold layout)
  RIGHT (26 %) — stats overview + node inspector

Node encoding
─────────────
  colour  blue  (#3b82f6) = normal
          red   (#ef4444) = anomaly signal fired
          amber (#f59e0b) = currently selected (click to change)
  size    proportional to degree centrality — hubs appear larger
  edges   width log-scaled on connection_count; curved directed arrows

Interaction
───────────
  Click any node → right panel populates with:
    • IP address + anomaly badge (if flagged)
    • Degree centrality, out-degree, in-degree
    • Per-signal anomaly reasons
    • Up to 8 adjacent connections
"""

from __future__ import annotations

import textwrap
from typing import Any

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from graph.analyzer import AnomalyMap


# ---------------------------------------------------------------------------
# Colour palette  (matches the original design intent)
# ---------------------------------------------------------------------------

BG_DARK     = "#0f172a"   # slate-900 — canvas background
BG_SURFACE  = "#1e293b"   # slate-800 — info panel background
BG_BORDER   = "#334155"   # slate-700 — spine / divider colour
TEXT_MAIN   = "#e2e8f0"   # slate-200
TEXT_MUTED  = "#94a3b8"   # slate-400
C_NORMAL    = "#3b82f6"   # blue-500
C_ANOMALOUS = "#ef4444"   # red-500
C_SELECTED  = "#f59e0b"   # amber-500
C_EDGE      = "#475569"   # slate-600


# ---------------------------------------------------------------------------
# Info panel renderer
# ---------------------------------------------------------------------------

def _render_info_panel(
    ax: Axes,
    G: nx.DiGraph,
    anomalies: AnomalyMap,
    degree_centrality: dict[str, float],
    selected: str | None,
) -> None:
    """
    Completely redraws the right-hand info panel.

    Called once on startup (selected=None) and again on every node click.
    The full-clear-and-redraw approach is simpler than trying to update
    individual text artists in place.
    """
    ax.clear()
    ax.set_facecolor(BG_SURFACE)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(BG_BORDER)

    # We lay text out by tracking a y-cursor that decrements per line.
    # transAxes means (0,0)=bottom-left, (1,1)=top-right of this axes.
    y       = 0.97
    LINE_H  = 0.034   # vertical step per text line
    INDENT  = 0.06    # left margin

    def write(
        text:  str,
        color: str  = TEXT_MAIN,
        size:  int  = 9,
        bold:  bool = False,
        wrap:  bool = False,
    ) -> None:
        nonlocal y
        lines = textwrap.wrap(text, 30) if wrap and len(text) > 30 else [text]
        for line in lines:
            ax.text(
                INDENT, y, line,
                transform=ax.transAxes,
                color=color, fontsize=size,
                fontweight="bold" if bold else "normal",
                fontfamily="monospace", va="top",
            )
            y -= LINE_H

    def gap(n: float = 1.0) -> None:
        nonlocal y
        y -= LINE_H * n

    def divider(label: str) -> None:
        write(f"── {label} ──", color=BG_BORDER, size=7)

    # ── Title ────────────────────────────────────────────────────────────
    write("PANOPTICON", color=C_NORMAL, size=13, bold=True)
    write("Network Topology Analyzer", color=TEXT_MUTED, size=8)
    gap()

    # ── Summary stats ────────────────────────────────────────────────────
    divider("SUMMARY")
    write(f"Nodes     {G.number_of_nodes()}", color=TEXT_MUTED, size=8)
    write(f"Edges     {G.number_of_edges()}", color=TEXT_MUTED, size=8)
    n_anom = len(anomalies)
    write(
        f"Anomalies {n_anom}",
        color=C_ANOMALOUS if n_anom else TEXT_MUTED,
        size=8, bold=bool(n_anom),
    )
    gap()

    # ── Legend (coloured patches + labels) ───────────────────────────────
    divider("LEGEND")
    for color, label in [(C_NORMAL, "Normal"), (C_ANOMALOUS, "Anomalous"), (C_SELECTED, "Selected")]:
        # Draw a small filled rectangle as the colour swatch
        ax.add_patch(mpatches.FancyBboxPatch(
            (INDENT, y - 0.012), 0.06, 0.022,
            boxstyle="round,pad=0.004",
            facecolor=color, edgecolor="none",
            transform=ax.transAxes, zorder=3,
        ))
        ax.text(
            INDENT + 0.10, y, label,
            transform=ax.transAxes,
            color=TEXT_MUTED, fontsize=8,
            fontfamily="monospace", va="top",
        )
        y -= LINE_H
    gap()

    # ── Node inspector ────────────────────────────────────────────────────
    divider("NODE INSPECTOR")

    if selected is None:
        write("Click any node", color=TEXT_MUTED, size=8)
        write("to inspect details.", color=TEXT_MUTED, size=8)
        return

    is_anom = selected in anomalies
    write(selected, color=C_ANOMALOUS if is_anom else C_SELECTED, size=9, bold=True)
    if is_anom:
        write("⚠  ANOMALOUS", color=C_ANOMALOUS, size=8, bold=True)
    gap(0.5)

    dc  = degree_centrality.get(selected, 0.0)
    out = G.out_degree(selected)
    ins = G.in_degree(selected)
    write(f"Deg. Centrality  {dc:.4f}", color=TEXT_MUTED, size=8)
    write(f"Out-Degree       {out}",    color=TEXT_MUTED, size=8)
    write(f"In-Degree        {ins}",    color=TEXT_MUTED, size=8)

    # Anomaly signal details
    reasons = anomalies.get(selected, [])
    if reasons:
        gap(0.5)
        write("Signals:", color=C_ANOMALOUS, size=8, bold=True)
        for reason in reasons:
            write(f"• {reason}", color=TEXT_MAIN, size=7, wrap=True)

    # Adjacent connections (capped at 8 to avoid overflow)
    conns = [
        (u, v, d)
        for u, v, d in G.edges(data=True)
        if u == selected or v == selected
    ]
    if conns:
        gap(0.5)
        write("Connections:", color=TEXT_MUTED, size=8, bold=True)
        for u, v, d in conns[:8]:
            cnt   = d.get("connection_count", "?")
            ports = d.get("unique_ports", "?")
            write(f"{u} → {v}", color=TEXT_MAIN, size=7, wrap=True)
            write(f"  {cnt} conns · {ports} ports", color=TEXT_MUTED, size=7)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def show_topology(
    G: nx.DiGraph,
    anomalies: AnomalyMap,
    degree_centrality: dict[str, float],
) -> None:
    """
    Open a full-screen-ish matplotlib window and block until it is closed.

    The force-directed layout (Fruchterman-Reingold via nx.spring_layout)
    models edges as springs and applies repulsion between all node pairs.
    k controls the ideal spring length — larger values spread the graph out,
    which improves legibility when nodes have long IP-address labels.
    """
    fig: Figure = plt.figure(figsize=(18, 10), facecolor=BG_DARK)
    try:
        fig.canvas.manager.set_window_title("Panopticon — Network Topology Analyzer")
    except AttributeError:
        pass  # not all matplotlib backends expose a window title

    # Two axes: graph on the left, info panel on the right.
    # add_axes([left, bottom, width, height]) in figure-fraction coordinates.
    ax_graph: Axes = fig.add_axes([0.01, 0.04, 0.70, 0.92], facecolor=BG_DARK)
    ax_info:  Axes = fig.add_axes([0.73, 0.04, 0.26, 0.92], facecolor=BG_SURFACE)

    for ax in (ax_graph, ax_info):
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(BG_BORDER)

    # ── Layout ──────────────────────────────────────────────────────────────
    # spring_layout uses the Fruchterman-Reingold algorithm.
    # k=2.0 → nodes spread further apart than the default (k=1/√N),
    # which keeps the IP labels readable on a dense graph.
    # iterations=100 is enough to reach a stable arrangement.
    pos: dict[str, np.ndarray] = nx.spring_layout(G, seed=42, k=2.0, iterations=100)

    # ── Edges ────────────────────────────────────────────────────────────────
    edges     = list(G.edges(data=True))
    # Log-scale width so the port-scan edge (1000+ events) doesn't visually
    # dwarf every other edge; normal traffic edges remain clearly visible.
    widths    = [
        max(0.4, float(np.log2(d.get("connection_count", 1) + 1)) * 0.6)
        for _, _, d in edges
    ]

    nx.draw_networkx_edges(
        G, pos, ax=ax_graph,
        edgelist=[(u, v) for u, v, _ in edges],
        width=widths,
        edge_color=C_EDGE,
        alpha=0.65,
        arrows=True,
        arrowsize=12,
        connectionstyle="arc3,rad=0.08",   # gentle curve separates parallel edges
        min_source_margin=14,
        min_target_margin=14,
    )

    # ── Nodes ────────────────────────────────────────────────────────────────
    nodes_list: list[str] = list(G.nodes())
    colors = [
        C_ANOMALOUS if n in anomalies else C_NORMAL
        for n in nodes_list
    ]
    # Area-based sizing: degree_centrality in [0,1], mapped to [150, 2650]
    sizes = [
        150 + degree_centrality.get(n, 0.0) * 2500
        for n in nodes_list
    ]

    # draw_networkx_nodes returns a PathCollection (scatter) that we can
    # make pickable — this is the hook for the click-to-inspect interaction.
    scatter = nx.draw_networkx_nodes(
        G, pos, ax=ax_graph,
        nodelist=nodes_list,
        node_color=colors,
        node_size=sizes,
        alpha=0.92,
        linewidths=1.2,
        edgecolors=BG_BORDER,
    )
    scatter.set_picker(True)
    scatter.set_pickradius(8)   # pixel tolerance for click hit-test

    # ── Labels ───────────────────────────────────────────────────────────────
    nx.draw_networkx_labels(
        G, pos, ax=ax_graph,
        font_size=6.5,
        font_color=TEXT_MAIN,
        font_family="monospace",
    )

    ax_graph.set_title(
        "Click any node to inspect  ·  Anomalous nodes in red",
        color=TEXT_MUTED, fontsize=9, pad=8, fontfamily="monospace",
    )

    # ── Info panel — initial (empty inspector) render ────────────────────────
    _render_info_panel(ax_info, G, anomalies, degree_centrality, selected=None)

    # ── Pick event handler ────────────────────────────────────────────────────
    # mpl_connect returns a connection ID (cid) that could be used to
    # disconnect the handler later; we don't need it here.
    def on_pick(event: Any) -> None:
        # Guard: only react to clicks on our node scatter, not edge artists
        if event.artist is not scatter:
            return
        if not len(event.ind):
            return

        # event.ind is an array of hit node indices (multiple if overlapping).
        # We take the first (topmost) hit.
        node_id = nodes_list[event.ind[0]]

        # Re-colour all nodes: selected = amber, others unchanged
        new_colors = [
            C_SELECTED  if n == node_id  else
            C_ANOMALOUS if n in anomalies else
            C_NORMAL
            for n in nodes_list
        ]
        scatter.set_facecolors(new_colors)

        # Redraw the info panel with this node's data
        _render_info_panel(ax_info, G, anomalies, degree_centrality, selected=node_id)

        # draw_idle() queues a redraw without blocking the event loop
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("pick_event", on_pick)

    plt.tight_layout(pad=0)
    plt.show()
