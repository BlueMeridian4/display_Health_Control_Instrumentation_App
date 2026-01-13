from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class DisplaySample:
    timestamp: datetime
    display_name: str
    is_internal: bool
    connected: bool
    brightness_percent: Optional[int]
    refresh_rate_hz: Optional[float]
    uptime_s: float
    cmd_latency_ms: Optional[float]
    cmd_success: bool
    health: str
