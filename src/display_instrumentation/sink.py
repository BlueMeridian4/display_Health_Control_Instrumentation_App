from __future__ import annotations

import os
from datetime import timedelta
from typing import Iterable

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from nominal.core import NominalClient
except Exception:
    NominalClient = None

from .models import DisplaySample

# ======================
# Display Label Mapping
# ======================
def sanitize(value, default=0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def health_to_float(health: str) -> float:
    return {
        "OK": 1.0,
        "DEGRADED": 0.5,
        "FAILED": 0.0,
        "ERROR": 0.0,
        "UNKNOWN": -1.0,
    }.get(health, -1.0)


class NominalSink:
    DATASET_REFNAME = "Linux Display Telemetry"

    def __init__(self):
        self.client = None
        self.stream = None

        if NominalClient is None:
            return

        token = os.environ.get("NOMINAL_API_KEY")
        api_url = os.environ.get("NOMINAL_API_URL")
        workspace_rid = os.environ.get("NOMINAL_WORKSPACE_RID")

        if not all([token, api_url, workspace_rid]):
            return

        self.client = NominalClient.from_token(
            token,
            api_url,
            workspace_rid=workspace_rid,
        )

        self.asset = self._get_or_create_asset()
        self.dataset = self._get_or_create_dataset()

        self.stream = self.dataset.get_write_stream(
            max_wait=timedelta(seconds=1)
        )
        self.stream.__enter__()

    # ======================
    # Nominal Setup Helpers
    # ======================

    def _get_or_create_asset(self):
        assets = self.client.search_assets(properties={"device": "display_host"})
        if assets:
            return assets[0]

        return self.client.create_asset(
            name="Linux Display Workstation",
            description="Continuous display telemetry",
            properties={"device": "display_host"},
            labels=["display"],
        )

    def _get_or_create_dataset(self):
        try:
            return self.asset.get_dataset(self.DATASET_REFNAME)
        except ValueError:
            dataset = self.client.create_dataset(
                name=self.DATASET_REFNAME,
                description="Display telemetry",
                prefix_tree_delimiter=".",
            )
            self.asset.add_dataset(self.DATASET_REFNAME, dataset)
            return dataset

    # ======================
    # Streaming
    # ======================

    def push(self, samples: Iterable[DisplaySample]) -> None:
        if self.stream is None:
            return

        for s in samples:
            ts = s.timestamp
            label = s.label
            base = label  # channel prefix

            self.stream.enqueue(
                f"{base}.connected",
                ts,
                sanitize(s.connected),
            )

            self.stream.enqueue(
                f"{base}.uptime_s",
                ts,
                sanitize(s.uptime_s),
            )

            self.stream.enqueue(
                f"{base}.cmd_success",
                ts,
                sanitize(s.cmd_success),
            )

            self.stream.enqueue(
                f"{base}.health",
                ts,
                health_to_float(s.health),
            )

            if s.brightness_percent is not None:
                self.stream.enqueue(
                    f"{base}.brightness_percent",
                    ts,
                    sanitize(s.brightness_percent),
                )

            if s.refresh_rate_hz is not None:
                self.stream.enqueue(
                    f"{base}.refresh_rate_hz",
                    ts,
                    sanitize(s.refresh_rate_hz),
                )

            if s.cmd_latency_ms is not None:
                self.stream.enqueue(
                    f"{base}.cmd_latency_ms",
                    ts,
                    sanitize(s.cmd_latency_ms),
                )

        self.stream.flush()

    def close(self):
        if self.stream:
            self.stream.__exit__(None, None, None)
            self.stream = None
