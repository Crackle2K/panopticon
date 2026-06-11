"""
main.py — Panopticon entry point.

Run:
    python main.py

A desktop window will open showing the simulated network topology.
Click any node to inspect its metrics and anomaly signals in the right panel.
"""

from data.generate_logs import generate_logs
from graph.analyzer import build_graph, detect_anomalies
from visualizer import show_topology


def main() -> None:
    print("[panopticon] Generating simulated network logs...")
    logs = generate_logs(baseline_count=300, seed=42)
    print(f"[panopticon] {len(logs)} log entries generated.")

    print("[panopticon] Building network graph...")
    G = build_graph(logs)
    print(f"[panopticon] Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges.")

    print("[panopticon] Running anomaly detection...")
    anomalies, degree_centrality = detect_anomalies(G)
    flagged = list(anomalies.keys())
    print(f"[panopticon] {len(flagged)} anomalous node(s) flagged: {flagged}")

    print("[panopticon] Opening topology window...")
    show_topology(G, anomalies, degree_centrality)


if __name__ == "__main__":
    main()
