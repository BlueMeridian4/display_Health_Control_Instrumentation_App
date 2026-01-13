from __future__ import annotations
from datetime import datetime
from typing import List
from .models import DisplaySample
from .health import compute_health

SAMPLE_PERIOD_S = 2

def collect_samples(displays) -> List[DisplaySample]:
    samples = []
    now = datetime.utcnow()

    for d in displays:
        health = compute_health(d.last_cmd_success, d.last_cmd_latency_ms)

        samples.append(
            DisplaySample(
                timestamp=now,
                display_name=d.name,
                is_internal=d.is_internal,
                connected=d.connected,
                brightness_percent=d.brightness_percent,
                refresh_rate_hz=d.refresh_rate_hz,
                uptime_s=d.uptime_s,
                cmd_latency_ms=d.last_cmd_latency_ms,
                cmd_success=d.last_cmd_success,
                health=health,
            )
        )

    return samples
