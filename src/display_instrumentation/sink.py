from __future__ import annotations

import os
import tempfile
from typing import List

import pandas as pd
from dotenv import load_dotenv
from nominal.core import NominalClient

from .models import DisplaySample

load_dotenv()


class NominalSink:
    """
    Uploads display telemetry directly to Nominal Connect
    using a persistent Asset + Dataset.
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
            )
            self.asset.add_dataset(self.DATASET_REFNAME, dataset)
            return dataset

    # ---------- Upload ----------

    def push(self, samples: List[DisplaySample]) -> None:
        if not samples:
            return

        df = pd.DataFrame([s.__dict__ for s in samples])

        # Nominal requires string or float columns only
        df["timestamp"] = df["timestamp"].astype(str)

        with tempfile.NamedTemporaryFile(
            suffix=".csv", delete=False
        ) as tmp:
            df.to_csv(tmp.name, index=False)

            self.dataset.add_tabular_data(
                path=tmp.name,
                timestamp_column="timestamp",
                timestamp_type="iso_8601",
            )
