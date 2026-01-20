from datetime import datetime, timezone
from typing import List

from .models import Display, DisplaySample
from .health import compute_health


def collect_samples(displays: List[Display]) -> List[DisplaySample]:
    now = datetime.now(timezone.utc)
    samples: List[DisplaySample] = []

    for d in displays:
        health = compute_health(
            connected=d.connected,
            cmd_success=d.last_cmd_success,
            latency_ms=d.last_cmd_latency_ms,
            brightness=d.brightness_percent,
            refresh_rate=d.refresh_rate_hz,
        )

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