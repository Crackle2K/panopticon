"""
graph/analyzer.py — Graph construction and anomaly detection.

Pipeline
--------
  list[LogEntry]  →  build_graph()       →  nx.DiGraph
  nx.DiGraph      →  detect_anomalies()  →  AnomalyMap + centrality dict

Anomaly detection uses two orthogonal signals:

  1. PORT SCAN (per-edge)
     ─────────────────────
     For each directed edge (src → dst) we count the cardinality of the
     set of observed destination ports.  If a source hits one target on
     ≥ PORT_SCAN_THRESHOLD distinct ports it is flagged as a scanner.
     This catches SCANNER_IP → 10.0.0.2 (1030+ unique ports) precisely.

  2. HIGH OUT-DEGREE (per-node)
     ───────────────────────────
     A node that initiates connections to many unique destinations is a
     lateral-movement indicator — normal machines talk to a small, stable
     peer set.  We flag nodes whose out-degree falls in the top
     (1 - HIGH_DEGREE_PERCENTILE) tail of the distribution, subject to a
     hard floor (MIN_OUT_DEGREE_TO_FLAG) to suppress false positives on
     sparse graphs.

     Raw out-degree is used rather than the normalised centrality value
     because the threshold needs a real lower bound independent of graph
     size; normalised values compress everything toward zero on large graphs.

Degree Centrality (NetworkX, O(V+E)) is computed separately and attached
to every node.  It normalises degree by (N-1) for cross-graph comparability
and is used only for node sizing in the visualiser — it is not a detection
signal itself.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

import networkx as nx

from data.generate_logs import LogEntry


# ---------------------------------------------------------------------------
# Tuneable thresholds
# ---------------------------------------------------------------------------

PORT_SCAN_THRESHOLD:    int   = 15    # unique ports on a single src→dst edge
HIGH_DEGREE_PERCENTILE: float = 0.90  # flag nodes in the top 10 % by out-degree
MIN_OUT_DEGREE_TO_FLAG: int   = 3     # never flag a node that hits < 3 destinations


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

AnomalyMap = dict[str, list[str]]   # node_id → [signal_string, ...]


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(logs: list[LogEntry]) -> nx.DiGraph:
    """
    Convert a flat list of log entries into a weighted directed graph.

    Each unique (src_ip, dst_ip) pair collapses into one directed edge.
    Edge attributes accumulated in a single O(E) pass:
      connection_count  — total log events on this edge
      unique_ports      — cardinality of distinct dst_ports observed
      ports             — sorted port list (kept for the sidebar display)
    """
    G: nx.DiGraph = nx.DiGraph()

    # Use a plain dict accumulator so we touch each log entry exactly once.
    acc: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "ports": set()}
    )

    for entry in logs:
        src  = entry["src_ip"]
        dst  = entry["dst_ip"]
        port = entry["dst_port"]
        if src not in G:
            G.add_node(src)
        if dst not in G:
            G.add_node(dst)
        acc[(src, dst)]["count"] += 1
        acc[(src, dst)]["ports"].add(port)

    for (src, dst), data in acc.items():
        G.add_edge(
            src, dst,
            connection_count=data["count"],
            unique_ports=len(data["ports"]),
            ports=sorted(data["ports"]),
        )

    return G


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(G: nx.DiGraph) -> tuple[AnomalyMap, dict[str, float]]:
    """
    Apply both detection signals and return the anomaly map plus degree
    centrality for all nodes.

    Returns
    -------
    anomalies
        node_id → list of human-readable signal strings.
        Nodes absent from this dict are considered normal.
    degree_centrality
        Normalised degree centrality (undirected view) for every node.
        Used by the visualiser to scale node size — not a detection metric.
    """
    anomalies: AnomalyMap = defaultdict(list)

    # Undirected degree centrality: nodes that both send AND receive a lot
    # of traffic appear large in the visualiser, making hubs easy to spot.
    degree_centrality: dict[str, float] = nx.degree_centrality(G)

    # Raw out-degree for the lateral-movement threshold calculation
    out_degrees: dict[str, int] = dict(G.out_degree())

    # Percentile cut-off: sort values and slice at the percentile index.
    # We skip flagging on trivially small graphs (< 3 nodes) to avoid
    # marking every node on a toy dataset.
    sorted_out = sorted(out_degrees.values())
    if len(sorted_out) >= 3:
        idx           = int(len(sorted_out) * HIGH_DEGREE_PERCENTILE)
        out_threshold = sorted_out[min(idx, len(sorted_out) - 1)]
    else:
        out_threshold = float("inf")

    for node in G.nodes():
        # ── Signal 1: per-edge port scan ─────────────────────────────────
        for _, dst, edata in G.out_edges(node, data=True):
            if edata.get("unique_ports", 0) >= PORT_SCAN_THRESHOLD:
                anomalies[node].append(
                    f"port_scan → {dst}: {edata['unique_ports']} unique ports"
                )

        # ── Signal 2: high out-degree (lateral movement) ──────────────────
        node_out = out_degrees.get(node, 0)
        if node_out >= MIN_OUT_DEGREE_TO_FLAG and node_out >= out_threshold:
            anomalies[node].append(
                f"high_out_degree: {node_out} unique destinations"
            )

    return dict(anomalies), degree_centrality
