# src/generator/generate_telemetry.py
import json
import random
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict


@dataclass
class TelemetryEvent:
    asset_id: str
    event_ts: str
    site_id: str
    sensor_temp: float
    sensor_vibration: float
    sensor_pressure: float
    rpm: int
    status_code: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def make_assets(n_assets: int, n_sites: int) -> List[Dict[str, str]]:
    assets = []
    for i in range(1, n_assets + 1):
        assets.append(
            {
                "asset_id": f"ASSET-{i:04d}",
                "site_id": f"SITE-{random.randint(1, n_sites):02d}",
            }
        )
    return assets


def generate_event(asset_id: str, site_id: str, failure_rate: float) -> TelemetryEvent:
    # Base signals (normal operating range)
    temp = random.gauss(75, 6)          # Fahrenheit-ish
    vib = abs(random.gauss(0.010, 0.006))
    pressure = random.gauss(45, 5)
    rpm = int(random.gauss(1500, 120))

    # Inject occasional anomalies (to mimic degradation)
    if random.random() < 0.08:
        temp += random.uniform(8, 18)
        vib += random.uniform(0.015, 0.030)

    # Status logic
    status = "OK"
    if temp > 90 or vib > 0.030:
        status = "WARN"
    if random.random() < failure_rate or (temp > 100 and vib > 0.040):
        status = "FAIL"

    # Clamp values to realistic bounds
    temp = round(clamp(temp, 40, 120), 2)
    vib = round(clamp(vib, 0.000, 0.080), 5)
    pressure = round(clamp(pressure, 20, 70), 2)
    rpm = int(clamp(rpm, 800, 2200))

    return TelemetryEvent(
        asset_id=asset_id,
        event_ts=utc_now_iso(),
        site_id=site_id,
        sensor_temp=temp,
        sensor_vibration=vib,
        sensor_pressure=pressure,
        rpm=rpm,
        status_code=status,
    )


def write_jsonl(events: List[TelemetryEvent], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(asdict(e)) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic IoT telemetry as JSONL.")
    parser.add_argument("--n-assets", type=int, default=50, help="Number of assets to simulate")
    parser.add_argument("--n-sites", type=int, default=3, help="Number of sites/plants")
    parser.add_argument("--rows", type=int, default=5000, help="Number of telemetry rows to generate")
    parser.add_argument("--failure-rate", type=float, default=0.01, help="Base failure probability per event")
    parser.add_argument("--out", type=str, default="data/telemetry.jsonl", help="Output JSONL path")
    args = parser.parse_args()

    assets = make_assets(args.n_assets, args.n_sites)

    events: List[TelemetryEvent] = []
    for _ in range(args.rows):
        a = random.choice(assets)
        events.append(generate_event(a["asset_id"], a["site_id"], args.failure_rate))

    out_path = Path(args.out)
    write_jsonl(events, out_path)

    # Print a few sample lines for quick verification
    print(f"✅ Wrote {len(events)} telemetry events to: {out_path}")
    print("Sample events:")
    for e in events[:3]:
        print(json.dumps(asdict(e), indent=2))


if __name__ == "__main__":
    main()
