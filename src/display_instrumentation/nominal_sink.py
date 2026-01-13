from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
from dotenv import load_dotenv
from nominal.core import NominalClient

from display_instrumentation.xrandr import Display # your Display class

load_dotenv()


class NominalSink:
    """Handles uploading display telemetry to Nominal."""

    def __init__(self):
        # Initialize Nominal client
        token = os.environ.get("NOMINAL_API_KEY")
        api_url = os.environ.get("NOMINAL_API_URL")
        workspace_rid = os.environ.get("NOMINAL_WORKSPACE_RID")

        if not all([token, api_url, workspace_rid]):
            raise ValueError("Nominal environment variables not set!")

        self.client = NominalClient.from_token(token, api_url, workspace_rid=workspace_rid)

        # Create asset representing the workstation
        self.asset = self.client.create_asset(
            "Linux Display Instrumentation",
            description="Display telemetry from Ubuntu workstation",
            labels=["Display", "Instrumentation", "Linux"],
        )

        # Create dataset for telemetry
        self.dataset = self.client.create_dataset(
            name="Display Telemetry",
            description="Brightness, refresh, health, latency",
        )

        # Link dataset to asset
        self.asset.add_dataset("Display Data", self.dataset)

        # Local folder to stage CSVs before upload
        self.buffer_dir = Path(".nominal_buffer")
        self.buffer_dir.mkdir(exist_ok=True)

    def push_samples(self, displays: List[Display]):
        """Convert Display objects to CSV and upload to Nominal."""
        if not displays:
            return

        # Convert to DataFrame
        df = pd.DataFrame([d.__dict__ for d in displays])

        # Use UTC timestamp in filename
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        csv_path = self.buffer_dir / f"display_samples_{ts}.csv"

        # Save to CSV
        df.to_csv(csv_path, index=False)

        # Upload to Nominal
        self.dataset.add_tabular_data(
            str(csv_path),
            timestamp_column="timestamp",
            timestamp_type="iso_8601",
        )

        print(f"Uploaded {len(displays)} samples to Nominal from {csv_path.name}")
