"""
generate_logs.py — Synthetic network log generator for Panopticon.

Produces a realistic mix of benign baseline traffic and two injected
attack scenarios so every test run uses purely simulated, legal data:

  BASELINE         — Normal internal east-west traffic plus DNS/HTTP egress.
  PORT SCAN        — External host probing a single target across hundreds of
                     ports in a narrow time window (classic nmap-style sweep).
  LATERAL MOVEMENT — A compromised internal host ("patient zero") making
                     sequential SMB / RDP / SSH connections to every peer,
                     the canonical post-exploitation indicator.

Run standalone to dump a logs.json file for offline inspection:
    python -m data.generate_logs
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import TypedDict


# ---------------------------------------------------------------------------
# Log schema
# ---------------------------------------------------------------------------

class LogEntry(TypedDict):
    timestamp:         str   # ISO-8601
    src_ip:            str
    dst_ip:            str
    dst_port:          int
    protocol:          str   # "TCP" | "UDP"
    bytes_transferred: int
    label:             str   # "normal" | "port_scan" | "lateral_movement"


# ---------------------------------------------------------------------------
# Network topology constants
# ---------------------------------------------------------------------------

INTERNAL_HOSTS: list[str] = [f"10.0.0.{i}" for i in range(1, 11)]

HOST_ROLES: dict[str, str] = {
    "10.0.0.1":  "gateway",
    "10.0.0.2":  "web-server",
    "10.0.0.3":  "db-server",
    "10.0.0.4":  "file-server",
    "10.0.0.5":  "mail-server",
    "10.0.0.6":  "workstation-A",
    "10.0.0.7":  "workstation-B",
    "10.0.0.8":  "workstation-C",
    "10.0.0.9":  "workstation-D",
    "10.0.0.10": "workstation-E",
}

TRUSTED_EXTERNAL: list[str] = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]

# Ports that appear during normal daily operations
BASELINE_PORTS: list[int] = [80, 443, 53, 22, 25, 587, 3306, 5432, 8080]

# Attack IPs — kept outside the 10.0.0.x internal subnet
SCANNER_IP   = "192.168.99.10"  # external recon actor
PATIENT_ZERO = "10.0.0.11"      # compromised internal host doing lateral spread

# Admin protocols favoured by attackers during lateral movement
LATERAL_PORTS: list[int] = [22, 445, 3389, 5985]

SIM_START = datetime(2024, 6, 15, 9, 0, 0)
SIM_END   = datetime(2024, 6, 15, 10, 0, 0)


# ---------------------------------------------------------------------------
# Traffic generators
# ---------------------------------------------------------------------------

def _rand_ts(start: datetime, end: datetime, rng: random.Random) -> str:
    """Return a uniformly random ISO timestamp in [start, end]."""
    delta = int((end - start).total_seconds())
    return (start + timedelta(seconds=rng.randint(0, delta))).isoformat()


def _baseline(n: int, rng: random.Random) -> list[LogEntry]:
    """
    Generate n benign log entries.

    Byte counts are drawn from a log-normal distribution so they replicate
    the heavy-tailed shape of real HTTP/file-transfer traffic rather than
    a suspicious uniform distribution.
    """
    entries: list[LogEntry] = []
    for _ in range(n):
        src      = rng.choice(INTERNAL_HOSTS)
        # 80 % of traffic stays internal; 20 % goes to trusted resolvers/CDN
        dst      = rng.choice(INTERNAL_HOSTS + TRUSTED_EXTERNAL * 2)
        port     = rng.choice(BASELINE_PORTS)
        protocol = "UDP" if port == 53 else "TCP"
        nbytes   = max(64, int(rng.lognormvariate(8, 2)))
        entries.append(LogEntry(
            timestamp=_rand_ts(SIM_START, SIM_END, rng),
            src_ip=src, dst_ip=dst, dst_port=port,
            protocol=protocol, bytes_transferred=nbytes, label="normal",
        ))
    return entries


def _port_scan(rng: random.Random) -> list[LogEntry]:
    """
    Simulate a TCP SYN sweep from SCANNER_IP against the web server.

    Covers ports 1–1024 plus high-interest service ports, mimicking what
    nmap -sS -T4 produces.  Each probe is ~60 bytes (just the SYN) and
    all arrive within a two-minute burst — both hallmarks of automation.
    """
    target = "10.0.0.2"
    ports  = list(range(1, 1025)) + [3389, 5432, 5900, 6379, 8443, 27017]
    t0     = SIM_START + timedelta(minutes=10)
    t1     = t0 + timedelta(seconds=120)  # 2-minute burst window

    return [
        LogEntry(
            timestamp=_rand_ts(t0, t1, rng),
            src_ip=SCANNER_IP, dst_ip=target, dst_port=port,
            protocol="TCP", bytes_transferred=60, label="port_scan",
        )
        for port in ports
    ]


def _lateral_movement(rng: random.Random) -> list[LogEntry]:
    """
    Simulate PATIENT_ZERO pivoting across the internal subnet.

    Pattern: compromised host authenticates / probes every peer over admin
    protocols (SSH, SMB, RDP, WinRM).  Byte counts are larger than SYN
    probes because real auth handshakes and small data transfers occur.
    """
    targets = [h for h in INTERNAL_HOSTS if h != PATIENT_ZERO]
    t0      = SIM_START + timedelta(minutes=30)
    t1      = SIM_START + timedelta(minutes=55)

    entries: list[LogEntry] = []
    for target in targets:
        for port in LATERAL_PORTS:
            entries.append(LogEntry(
                timestamp=_rand_ts(t0, t1, rng),
                src_ip=PATIENT_ZERO, dst_ip=target, dst_port=port,
                protocol="TCP",
                bytes_transferred=rng.randint(1_024, 32_768),
                label="lateral_movement",
            ))
    return entries


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_logs(baseline_count: int = 300, seed: int = 42) -> list[LogEntry]:
    """
    Build and return the full synthetic log dataset.

    Parameters
    ----------
    baseline_count:
        Normal traffic entries to include.  Keeping this ≥ 200 ensures the
        attack IPs don't dominate the degree distribution, which makes the
        anomaly detection metrics more meaningful.
    seed:
        RNG seed for reproducibility.  Pass None for a fresh random dataset.
    """
    rng  = random.Random(seed)
    logs = _baseline(baseline_count, rng) + _port_scan(rng) + _lateral_movement(rng)
    rng.shuffle(logs)
    return logs


# ---------------------------------------------------------------------------
# Standalone — write logs.json next to this file
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out = Path(__file__).parent / "logs.json"
    data = generate_logs()
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[generate_logs] wrote {len(data)} entries → {out}")
