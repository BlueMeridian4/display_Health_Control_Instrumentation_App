from __future__ import annotations

import os
from datetime import timedelta
from typing import Iterable

from dotenv import load_dotenv
from nominal.core import NominalClient

from .models import DisplaySample

load_dotenv()


class NominalSink:
    """
    Streams display telemetry to Nominal using a persistent Asset + Dataset.
    """

    DATASET_REFNAME = "display_telemetry"

    def __init__(self):
        token = os.environ.get("NOMINAL_API_KEY")
        api_url = os.environ.get("NOMINAL_API_URL")
        workspace_rid = os.environ.get("NOMINAL_WORKSPACE_RID")

        if not all([token, api_url, workspace_rid]):
            raise RuntimeError("Nominal environment variables not set")

        self.client = NominalClient.from_token(
            token,
            api_url,
            workspace_rid=workspace_rid,
        )

        self.asset = self._get_or_create_asset()
        self.dataset = self._get_or_create_dataset()

        # Keep a persistent write stream (important for streaming workloads)
        self.stream = self.dataset.get_write_stream(
            max_wait=timedelta(seconds=1)
        )
        self.stream.__enter__()

    # ---------- Asset ----------

    def _get_or_create_asset(self):
        name = "Linux Display Workstation"

        assets = self.client.search_assets(properties={"device": "display_host"})
        if assets:
            return assets[0]

        return self.client.create_asset(
            name=name,
            description="Continuous display telemetry from Linux workstation",
            properties={
                "device": "display_host",
                "os": "linux",
            },
            labels=["display", "instrumentation"],
        )

    # ---------- Dataset ----------

    def _get_or_create_dataset(self):
        try:
            return self.asset.get_dataset(self.DATASET_REFNAME)
        except ValueError:
            dataset = self.client.create_dataset(
                name="Display Telemetry",
                description="Brightness, refresh rate, health, command latency",
                labels=["display", "telemetry", "streaming"],
                properties={"source": "xrandr + ddcutil"},
                prefix_tree_delimiter=".",
            )
            self.asset.add_dataset(self.DATASET_REFNAME, dataset)
            return dataset

    # ---------- Streaming Upload ----------

    def push(self, samples: Iterable[DisplaySample]) -> None:
        """
        Stream samples to Nominal.
        """
        for s in samples:
            ts = s.timestamp

            # Tag by display so multiple monitors coexist cleanly
            tags = {"display": s.display_name}

            self.stream.enqueue(
                "display.connected",
                ts,
                float(s.connected),
                tags=tags,
            )

            if s.brightness_percent is not None:
                self.stream.enqueue(
                    "display.brightness_percent",
                    ts,
                    float(s.brightness_percent),
                    tags=tags,
                )

            if s.refresh_rate_hz is not None:
                self.stream.enqueue(
                    "display.refresh_rate_hz",
                    ts,
                    s.refresh_rate_hz,
                    tags=tags,
                )

            self.stream.enqueue(
                "display.uptime_s",
                ts,
                s.uptime_s,
                tags=tags,
            )

            if s.cmd_latency_ms is not None:
                self.stream.enqueue(
                    "display.cmd_latency_ms",
                    ts,
                    s.cmd_latency_ms,
                    tags=tags,
                )

            self.stream.enqueue(
                "display.cmd_success",
                ts,
                float(s.cmd_success),
                tags=tags,
            )

            # String channel
            self.stream.enqueue(
                "display.health",
                ts,
                s.health,
                tags=tags,
            )

    # ---------- Shutdown ----------

    def close(self):
        self.stream.__exit__(None, None, None)