from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Display:
    name: str
    is_internal: bool
    connected: bool = False
    brightness_percent: Optional[int] = None
    refresh_rate_hz: Optional[float] = None
    uptime_s: float = 0.0
    last_cmd_latency_ms: Optional[float] = None
    last_cmd_success: bool = False


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