from __future__ import annotations

import csv
import sys
from pathlib import Path


def summarize_jtl(path: Path) -> dict[str, float]:
    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(row)

    if not rows:
        raise ValueError("No JTL rows found.")

    durations = [int(row["elapsed"]) for row in rows if row.get("elapsed")]
    success_count = sum(1 for row in rows if str(row.get("success", "")).lower() == "true")
    error_count = len(rows) - success_count
    timestamps = [int(row["timeStamp"]) for row in rows if row.get("timeStamp")]

    min_ts = min(timestamps)
    max_ts = max(timestamps)
    wall_seconds = max((max_ts - min_ts) / 1000, 1.0)

    avg_response_ms = round(sum(durations) / len(durations), 2)
    throughput_rps = round(len(rows) / wall_seconds, 2)
    error_rate_pct = round((error_count / len(rows)) * 100, 2)

    return {
        "samples": len(rows),
        "avg_response_ms": avg_response_ms,
        "throughput_rps": throughput_rps,
        "error_rate_pct": error_rate_pct,
        "success_count": success_count,
        "error_count": error_count,
        "wall_seconds": round(wall_seconds, 2),
    }


def main() -> None:
    if len(sys.argv) != 2:
      raise SystemExit("Usage: python jmeter/scripts/summarize_jtl.py <path-to-jtl>")

    jtl_path = Path(sys.argv[1]).resolve()
    if not jtl_path.exists():
      raise SystemExit(f"JTL file not found: {jtl_path}")

    summary = summarize_jtl(jtl_path)
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
