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
            display_tag = {"display_id": s.display_name}

            self.stream.enqueue(
                channel_name="display.connected",
                timestamp=ts,
                value=float(s.connected),
                tags=display_tag,
            )

            if s.brightness_percent is not None:
                self.stream.enqueue(
                    channel_name="display.brightness_percent",
                    timestamp=ts,
                    value=float(s.brightness_percent),
                    tags=display_tag,
                )

            if s.refresh_rate_hz is not None:
                self.stream.enqueue(
                    channel_name="display.refresh_rate_hz",
                    timestamp=ts,
                    value=s.refresh_rate_hz,
                    tags=display_tag,
                )

            self.stream.enqueue(
                channel_name="display.uptime_s",
                timestamp=ts,
                value=s.uptime_s,
                tags=display_tag,
            )

            if s.cmd_latency_ms is not None:
                self.stream.enqueue(
                    channel_name="display.cmd_latency_ms",
                    timestamp=ts,
                    value=s.cmd_latency_ms,
                    tags=display_tag,
                )

            self.stream.enqueue(
                channel_name="display.cmd_success",
                timestamp=ts,
                value=float(s.cmd_success),
                tags=display_tag,
            )

            # String channel
            self.stream.enqueue(
                channel_name="display.health",
                timestamp=ts,
                value=s.health,
                tags=display_tag,
            )

    # ---------- Shutdown ----------

    def close(self):
        self.stream.__exit__(None, None, None)