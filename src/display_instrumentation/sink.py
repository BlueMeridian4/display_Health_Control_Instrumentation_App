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


class NominalSink:
    DATASET_REFNAME = "Linux Display Telemetry"

    def __init__(self):
        self.stream = None

        if NominalClient is None:
            self.client = None
            return

        token = os.environ.get("NOMINAL_API_KEY")
        api_url = os.environ.get("NOMINAL_API_URL")
        workspace_rid = os.environ.get("NOMINAL_WORKSPACE_RID")

        if not all([token, api_url, workspace_rid]):
            self.client = None
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

    def push(self, samples: Iterable[DisplaySample]) -> None:
        if self.stream is None:
            return

        for s in samples:
            ts = s.timestamp
            tags = {"display": s.display_name}

            self.stream.enqueue("display.connected", ts, float(s.connected), tags=tags)
            self.stream.enqueue("display.uptime_s", ts, s.uptime_s, tags=tags)
            self.stream.enqueue("display.cmd_success", ts, float(s.cmd_success), tags=tags)
            self.stream.enqueue("display.health", ts, s.health, tags=tags)

            if s.brightness_percent is not None:
                self.stream.enqueue(
                    "display.brightness_percent", ts, s.brightness_percent, tags=tags
                )

            if s.refresh_rate_hz is not None:
                self.stream.enqueue(
                    "display.refresh_rate_hz", ts, s.refresh_rate_hz, tags=tags
                )

            if s.cmd_latency_ms is not None:
                self.stream.enqueue(
                    "display.cmd_latency_ms", ts, s.cmd_latency_ms, tags=tags
                )

        self.stream.flush()

    def close(self):
        if self.stream:
            self.stream.__exit__(None, None, None)
