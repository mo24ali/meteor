import json
from datetime import datetime

import pytest

from src.bronze.fetch_weather import (
    fetch_weather_for_city,
    run_bronze_ingestion,
    snapshot_path,
    validate_payload,
)

FIXED_NOW = datetime(2026, 9, 15, 12, 0, 0)


class _AdvancingNow:
    def __init__(self, start):
        self._t = start

    def __call__(self):
        self._t = self._t.replace(second=self._t.second + 1)
        return self._t


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            from requests.exceptions import HTTPError

            raise HTTPError(f"HTTP {self.status_code}", response=self)

    def json(self):
        return self._payload


def test_validate_payload_accepts_valid_shape():
    validate_payload({"daily": {"time": ["2026-09-15"], "temperature_2m_max": [30.0]}})


def test_validate_payload_rejects_missing_daily():
    with pytest.raises(ValueError, match="daily.time"):
        validate_payload({"hourly": {}})


def test_validate_payload_rejects_non_list_time():
    with pytest.raises(ValueError, match="must be a list"):
        validate_payload({"daily": {"time": "2026-09-15"}})


def test_fetch_weather_for_city_success(monkeypatch):
    import requests

    sent = {}

    def fake_get(url, params, timeout):
        sent["url"] = url
        sent["params"] = params
        return FakeResponse({"daily": {"time": ["2026-09-15"], "temperature_2m_max": [30.0]}})

    monkeypatch.setattr(requests, "get", fake_get)

    payload = fetch_weather_for_city(33.6, -7.6)
    assert payload["daily"]["time"] == ["2026-09-15"]
    assert sent["params"]["latitude"] == 33.6


def test_fetch_weather_for_city_retries_then_raises(monkeypatch):
    import requests

    attempts = {"count": 0}

    def fake_get(url, params, timeout):
        attempts["count"] += 1
        return FakeResponse({"error": True}, status_code=500)

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(Exception):
        fetch_weather_for_city(33.6, -7.6, retries=2, backoff_factor=0.1)
    assert attempts["count"] == 2


def test_snapshot_path_creates_day_dir(tmp_path):
    path = snapshot_path(str(tmp_path), "2026-09-15", datetime(2026, 9, 15, 10, 30, 0))
    assert path == str(tmp_path / "2026-09-15" / "raw_weather_snapshot_20260915_103000.json")
    assert (tmp_path / "2026-09-15").is_dir()


def test_run_bronze_ingestion_writes_snapshot(tmp_path, monkeypatch):
    cities_csv = tmp_path / "cities.csv"
    cities_csv.write_text("city,lat,lng\nCasablanca,33.5992,-7.62\nRabat,34.0209,-6.8416\n")

    monkeypatch.setattr(
        "src.bronze.fetch_weather.fetch_weather_for_city",
        lambda lat, lng, **kwargs: {"daily": {"time": ["2026-09-15"]}},
    )
    monkeypatch.setattr("src.bronze.fetch_weather.datetime_now", _AdvancingNow(FIXED_NOW))

    output_dir = tmp_path / "bronze"
    failed = run_bronze_ingestion(cities_csv=str(cities_csv), output_dir=str(output_dir))

    assert failed == 0
    snapshots = list((output_dir / "2026-09-15").glob("raw_weather_snapshot_*.json"))
    assert len(snapshots) == 1

    with open(snapshots[0], encoding="utf-8") as f:
        snapshot = json.load(f)
    assert snapshot["ingested"] == 2
    assert {entry["city"] for entry in snapshot["results"]} == {"Casablanca", "Rabat"}


def test_run_bronze_ingestion_resume_skips_existing(tmp_path, monkeypatch):
    cities_csv = tmp_path / "cities.csv"
    cities_csv.write_text("city,lat,lng\nCasablanca,33.5992,-7.62\nRabat,34.0209,-6.8416\n")

    monkeypatch.setattr(
        "src.bronze.fetch_weather.fetch_weather_for_city",
        lambda lat, lng, **kwargs: {"daily": {"time": ["2026-09-15"]}},
    )
    monkeypatch.setattr("src.bronze.fetch_weather.datetime_now", _AdvancingNow(FIXED_NOW))

    output_dir = tmp_path / "bronze"
    run_bronze_ingestion(cities_csv=str(cities_csv), output_dir=str(output_dir))

    failed = run_bronze_ingestion(cities_csv=str(cities_csv), output_dir=str(output_dir), resume=True)

    assert failed == 0
    snapshots = sorted((output_dir / "2026-09-15").glob("raw_weather_snapshot_*.json"))
    assert len(snapshots) == 2

    with open(snapshots[1], encoding="utf-8") as f:
        snapshot = json.load(f)
    assert snapshot["ingested"] == 0
    assert snapshot["skipped"] == 2