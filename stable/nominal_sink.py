from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from nominal.core import NominalClient  # ← THIS WAS MISSING

load_dotenv()

class NominalSink:
    def __init__(self):
        self.client = NominalClient.from_token(
            os.environ["NOMINAL_API_KEY"],
            os.environ["NOMINAL_API_URL"],
            workspace_rid=os.environ["NOMINAL_WORKSPACE_RID"],
        )

        self.asset = self.client.create_asset(
            "Linux Display Instrumentation",
            description="Display telemetry from Ubuntu workstation",
            labels=["Display", "Instrumentation", "Linux"],
        )

        self.dataset = self.client.create_dataset(
            name="Display Telemetry",
            description="Brightness, refresh, health, latency",
        )

        self.asset.add_dataset("Display Data", self.dataset)

        # Where we stage CSVs
        self.buffer_dir = Path(".nominal_buffer")
        self.buffer_dir.mkdir(exist_ok=True)

    def push_samples(self, samples):
        if not samples:
            return

        df = pd.DataFrame([s.__dict__ for s in samples])

        # Create a unique CSV per push
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        csv_path = self.buffer_dir / f"display_samples_{ts}.csv"

        df.to_csv(csv_path, index=False)

        self.dataset.add_tabular_data(
            str(csv_path),
            timestamp_column="timestamp",
            timestamp_type="iso_8601",
        )
