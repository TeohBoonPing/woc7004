import json
import os
from pathlib import Path


RESULTS_DIR = Path('/usr/src/app/k6/results')
OUT_CSV = RESULTS_DIR / 'energy_comparison.csv'
OUT_JSON = RESULTS_DIR / 'energy_comparison.json'


def load_json(path: Path):
    if not path.exists():
        return None
    with path.open() as f:
        return json.load(f)


def fmt(value, unit, digits=3):
    if value is None:
        return "n/a"
    return f"{round(value, digits)} {unit}"

def fmt_energy_kwh(value, digits=3):
    if value is None:
        return "n/a"
    if value < 0.01:
        return f"{round(value * 1000, digits)} Wh"
    return f"{round(value, digits)} kWh"

def fmt_per_req_kwh(value, digits=6):
    if value is None:
        return "n/a"
    return f"{round(value * 1_000_000, 1)} µWh/req"


def main():
    baseline = load_json(RESULTS_DIR / 'baseline_energy.json') or {}
    db_only = load_json(RESULTS_DIR / 'energy_result_k6_db.json') or {}
    redis_only = load_json(RESULTS_DIR / 'energy_result_k6_redis.json') or {}

    b_kwh = baseline.get('baseline_energy_kwh')
    b_secs = baseline.get('baseline_duration_seconds') or 0
    db_kwh = db_only.get('total_energy_kwh')
    r_kwh = redis_only.get('total_energy_kwh')
    db_reqs = db_only.get('total_requests') or 0
    r_reqs = redis_only.get('total_requests') or 0
    db_secs = db_only.get('duration_seconds') or 0
    r_secs = redis_only.get('duration_seconds') or 0

    # Adjust by subtracting proportional baseline energy (scaled by scenario duration)
    def adjusted_kwh(total, scenario_secs):
        if total is None:
            return None
        if b_kwh and b_secs:
            baseline_rate_kwh_per_s = b_kwh / b_secs
            return max(total - baseline_rate_kwh_per_s * scenario_secs, 0)
        return total

    db_adj = adjusted_kwh(db_kwh, db_secs)
    r_adj = adjusted_kwh(r_kwh, r_secs)

    def per_req(kwh, reqs):
        if kwh is None or not reqs:
            return None
        return kwh / reqs

    db_per_kwh = per_req(db_kwh, db_reqs)
    r_per_kwh = per_req(r_kwh, r_reqs)
    db_per_adj = per_req(db_adj, db_reqs)
    r_per_adj = per_req(r_adj, r_reqs)

    # Differences (DB vs Redis)
    def diff(a, b):
        if a is None or b is None:
            return None
        return a - b

    diff_total_kwh = diff(db_kwh, r_kwh)
    diff_total_adj = diff(db_adj, r_adj)
    diff_per_kwh = diff(db_per_kwh, r_per_kwh)
    diff_per_adj = diff(db_per_adj, r_per_adj)

    # Build a human-readable table (CSV)
    rows = [
        ["Metric", "DB-only", "Redis-only", "Difference (DB-Redis)", "Notes"],
        ["Total Requests", str(db_reqs), str(r_reqs), "-", "Requests processed in scenario"],
        ["Total Energy", fmt_energy_kwh(db_kwh, 6), fmt_energy_kwh(r_kwh, 6), fmt_energy_kwh(diff_total_kwh, 6), "Raw energy during scenario"],
        ["Baseline Energy", fmt_energy_kwh(b_kwh, 6), "-", "-", f"Measured over {b_secs}s; proportional subtraction for adjusted values"],
        ["Adjusted Energy", fmt_energy_kwh(db_adj, 6), fmt_energy_kwh(r_adj, 6), fmt_energy_kwh(diff_total_adj, 6), "Adjusted = total - (baseline_rate × scenario_duration)"],
        ["Energy/Request (kWh/req)", fmt(db_per_kwh, "kWh/req", 9), fmt(r_per_kwh, "kWh/req", 9), fmt(diff_per_kwh, "kWh/req", 9), "Raw per-request energy"],
        ["Adjusted Energy/Request (kWh/req)", fmt(db_per_adj, "kWh/req", 9), fmt(r_per_adj, "kWh/req", 9), fmt(diff_per_adj, "kWh/req", 9), "Adjusted per-request energy"],
        ["Energy/Request", fmt_per_req_kwh(db_per_kwh), fmt_per_req_kwh(r_per_kwh), fmt_per_req_kwh(diff_per_kwh), "Same as above, in µWh for readability"],
        ["Adjusted Energy/Request", fmt_per_req_kwh(db_per_adj), fmt_per_req_kwh(r_per_adj), fmt_per_req_kwh(diff_per_adj), "Adjusted per-request, in µWh"],
    ]

    # Write CSV
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w') as f:
        for row in rows:
            f.write(",".join(row) + "\n")

    # Write JSON summary
    out = {
        "inputs": {
            "baseline_json": str(RESULTS_DIR / 'baseline_energy.json'),
            "db_json": str(RESULTS_DIR / 'energy_result_k6_db.json'),
            "redis_json": str(RESULTS_DIR / 'energy_result_k6_redis.json'),
        },
        "values": {
            "baseline_energy_kwh": b_kwh,
            "baseline_duration_seconds": b_secs,
            "db_total_energy_kwh": db_kwh,
            "redis_total_energy_kwh": r_kwh,
            "db_total_requests": db_reqs,
            "redis_total_requests": r_reqs,
            "db_duration_seconds": db_secs,
            "redis_duration_seconds": r_secs,
            "db_adjusted_energy_kwh": db_adj,
            "redis_adjusted_energy_kwh": r_adj,
            "db_energy_per_request_kwh": db_per_kwh,
            "redis_energy_per_request_kwh": r_per_kwh,
            "db_adjusted_energy_per_request_kwh": db_per_adj,
            "redis_adjusted_energy_per_request_kwh": r_per_adj,
            "diff_total_energy_kwh": diff_total_kwh,
            "diff_adjusted_energy_kwh": diff_total_adj,
            "diff_per_request_kwh": diff_per_kwh,
            "diff_adjusted_per_request_kwh": diff_per_adj,
        },
        "readable": {
            "db_total_energy": fmt(db_kwh, "kWh", 6),
            "redis_total_energy": fmt(r_kwh, "kWh", 6),
            "baseline_energy": fmt(b_kwh, "kWh", 6),
            "db_adjusted_total_energy": fmt(db_adj, "kWh", 6),
            "redis_adjusted_total_energy": fmt(r_adj, "kWh", 6),
            "db_per_request_uwh": fmt((db_per_kwh or 0) * 1_000_000 if db_per_kwh is not None else None, "µWh/req", 1),
            "redis_per_request_uwh": fmt((r_per_kwh or 0) * 1_000_000 if r_per_kwh is not None else None, "µWh/req", 1),
            "db_adjusted_per_request_uwh": fmt((db_per_adj or 0) * 1_000_000 if db_per_adj is not None else None, "µWh/req", 1),
            "redis_adjusted_per_request_uwh": fmt((r_per_adj or 0) * 1_000_000 if r_per_adj is not None else None, "µWh/req", 1),
        },
        "outputs": {
            "csv": str(OUT_CSV),
        },
    }
    with OUT_JSON.open('w') as f:
        json.dump(out, f, indent=2)

    # Console summary
    print("[compare] Energy comparison:")
    print(f"  Baseline: {fmt_energy_kwh(b_kwh, 6)} over {b_secs}s")
    print(f"  DB-only:  {fmt_energy_kwh(db_kwh, 6)} (adjusted: {fmt_energy_kwh(db_adj, 6)})")
    print(f"  Redis:    {fmt_energy_kwh(r_kwh, 6)} (adjusted: {fmt_energy_kwh(r_adj, 6)})")
    print(f"  Diff (DB-Redis): total={fmt_energy_kwh(diff_total_kwh, 6)}, adjusted={fmt_energy_kwh(diff_total_adj, 6)}")
    print(f"  Per-request adjusted: DB={fmt_per_req_kwh(db_per_adj)}, Redis={fmt_per_req_kwh(r_per_adj)}")
    print(f"[compare] Written {OUT_CSV} and {OUT_JSON}")


if __name__ == "__main__":
    main()


