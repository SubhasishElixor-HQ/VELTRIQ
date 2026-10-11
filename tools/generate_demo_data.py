from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "generated" / "demo.jsonl"
GROUND_TRUTH = ROOT / "data" / "ground_truth" / "demo_ground_truth.json"


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_records() -> tuple[list[dict], dict]:
    anchor = datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    scenarios = [
        {"name": "normal_city", "day": 0, "distance": 18.4, "energy": 16.2, "ambient": 22.0, "hvac": 1.2, "battery": [27.5, 28.1, 28.8, 29.2, 29.0, 28.7], "warning": None},
        {"name": "range_drop", "day": 4, "distance": 31.2, "energy": 25.1, "ambient": 4.5, "hvac": 4.8, "battery": [24.2, 24.5, 25.0, 25.4, 25.1, 24.8], "warning": None},
        {"name": "battery_warning", "day": 9, "distance": 22.7, "energy": 19.4, "ambient": 18.0, "hvac": 1.8, "battery": [32.0, 34.1, 36.7, 39.3, 42.0, 42.5], "warning": "battery_temperature_warning"},
        {"name": "adas_disengagement", "day": 14, "distance": 40.3, "energy": 18.6, "ambient": 20.0, "hvac": 1.4, "battery": [27.3, 27.6, 28.0, 28.4, 28.2, 28.1], "warning": "adas_disengagement"},
        {"name": "battery_warning_recurrence", "day": 17, "distance": 25.1, "energy": 20.1, "ambient": 26.0, "hvac": 2.1, "battery": [31.7, 33.2, 35.4, 38.6, 41.1, 42.2], "warning": "battery_temperature_warning"},
        {"name": "missing_sensor", "day": 20, "distance": 12.6, "energy": 20.2, "ambient": 9.0, "hvac": 2.6, "battery": [26.0, 26.5, None, 27.8, 28.2, 28.5], "warning": "sensor_data_unavailable"},
    ]
    records: list[dict] = []
    truth: dict = {"dataset": "VehicleGPT synthetic demo v1", "scenarios": []}
    for index, scenario in enumerate(scenarios, 1):
        trip_id = f"SIM-{index:03d}"
        start = anchor + timedelta(days=scenario["day"])
        finish = start + timedelta(minutes=10)
        scenario_id = scenario["name"]
        records.append({"schema_version": 1, "record_type": "trip", "trip_id": trip_id, "vehicle_alias": "Demo EV 01", "started_at": iso(start), "ended_at": iso(finish), "scenario": scenario_id, "distance_km": scenario["distance"], "data_origin": "simulated"})
        event_ids = []
        for minute in range(6):
            ts = start + timedelta(minutes=minute * 2)
            values = {
                "vehicle_speed": (0, 28, 42, 36, 15, 0)[minute],
                "battery_soc": round(82 - minute * (0.45 + scenario["energy"] / 100), 1),
                "battery_temperature": scenario["battery"][minute],
                "energy_consumption": round(scenario["energy"] + (minute - 2.5) * 0.35, 1),
                "ambient_temperature": scenario["ambient"],
                "hvac_power": scenario["hvac"],
            }
            units = {"vehicle_speed": "km/h", "battery_soc": "%", "battery_temperature": "C", "energy_consumption": "kWh/100km", "ambient_temperature": "C", "hvac_power": "kW"}
            for signal_id, value in values.items():
                quality = "valid"
                if value is None:
                    quality = "missing"
                if scenario_id == "missing_sensor" and signal_id == "battery_temperature" and minute == 4:
                    quality = "delayed"
                record_id = f"{trip_id}-S-{minute:02d}-{signal_id}"
                records.append({"schema_version": 1, "record_type": "signal", "record_id": record_id, "timestamp_utc": iso(ts), "trip_id": trip_id, "source": "simulated_can", "signal_id": signal_id, "value": value, "unit": units[signal_id], "quality": quality, "scenario_id": scenario_id})
        if scenario["warning"] == "battery_temperature_warning":
            event_id = f"{trip_id}-E-BATT-01"
            event_ids.append(event_id)
            records.append({"schema_version": 1, "record_type": "event", "event_id": event_id, "timestamp_utc": iso(start + timedelta(minutes=10)), "trip_id": trip_id, "source": "diagnostics", "event_type": scenario["warning"], "severity": "warning", "description": "Battery temperature reached the warning threshold", "scenario_id": scenario_id})
            records.append({"schema_version": 1, "record_type": "log", "log_id": f"{trip_id}-L-01", "timestamp_utc": iso(start + timedelta(minutes=10)), "trip_id": trip_id, "source": "thermal_controller", "level": "warning", "text": "Battery temperature warning recorded; cooling status not included in this demo trace.", "scenario_id": scenario_id})
        elif scenario["warning"] == "adas_disengagement":
            event_id = f"{trip_id}-E-ADAS-01"
            event_ids.append(event_id)
            records.append({"schema_version": 1, "record_type": "event", "event_id": event_id, "timestamp_utc": iso(start + timedelta(minutes=8)), "trip_id": trip_id, "source": "adas", "event_type": scenario["warning"], "severity": "info", "description": "Driver assistance disengaged; driver takeover recorded", "scenario_id": scenario_id})
        elif scenario["name"] == "range_drop":
            event_id = f"{trip_id}-E-RANGE-01"
            event_ids.append(event_id)
            records.append({"schema_version": 1, "record_type": "event", "event_id": event_id, "timestamp_utc": iso(start + timedelta(minutes=10)), "trip_id": trip_id, "source": "range_estimator", "event_type": "range_drop", "severity": "warning", "description": "Estimated range decreased during the trip", "scenario_id": scenario_id})
        elif scenario["warning"] == "sensor_data_unavailable":
            event_id = f"{trip_id}-E-SENSOR-01"
            event_ids.append(event_id)
            records.append({"schema_version": 1, "record_type": "event", "event_id": event_id, "timestamp_utc": iso(start + timedelta(minutes=6)), "trip_id": trip_id, "source": "diagnostics", "event_type": scenario["warning"], "severity": "warning", "description": "Battery temperature sample missing or delayed", "scenario_id": scenario_id})
        truth["scenarios"].append({"scenario_id": scenario_id, "trip_id": trip_id, "expected_event_ids": event_ids, "expected_signal": "energy_consumption", "expected_energy_kwh_per_100km": scenario["energy"]})
    return records, truth


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic VehicleGPT synthetic vehicle traces.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    records, truth = build_records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    GROUND_TRUTH.parent.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH.write_text(json.dumps(truth, indent=2), encoding="utf-8")
    print(f"Generated {len(records)} records at {args.output}")
    print(f"Ground truth written to {GROUND_TRUTH}")


if __name__ == "__main__":
    main()
