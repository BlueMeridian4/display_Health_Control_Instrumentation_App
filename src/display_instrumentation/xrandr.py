from __future__ import annotations

import subprocess
import time
import re
from typing import List, Optional

# Map physical display names to ddcutil display numbers
ddc_map = {
    "DP-0": 1,
    "HDMI-0": 2,
}

class Display:
    def __init__(self, name: str, is_internal: bool):
        self.name = name
        self.is_internal = is_internal
        self.connected = False
        self.brightness_percent: Optional[int] = None
        self.refresh_rate_hz: Optional[float] = None
        self.uptime_s: float = 0.0
        self.last_cmd_latency_ms: Optional[float] = None
        self.last_cmd_success: bool = False

    def __repr__(self) -> str:
        return (
            f"<Display {self.name} connected={self.connected} "
            f"brightness={self.brightness_percent} "
            f"refresh={self.refresh_rate_hz}Hz>"
        )


def parse_xrandr() -> List[Display]:
    result = subprocess.run(
        ["xrandr", "--query"],
        capture_output=True,
        text=True,
        check=False,
    )

    displays: List[Display] = []
    current_display: Optional[Display] = None

    for line in result.stdout.splitlines():
        if " connected" in line:
            name = line.split()[0]
            is_internal = name.startswith("eDP")
            current_display = Display(name, is_internal)
            current_display.connected = True
            displays.append(current_display)

        elif current_display and re.match(r"^\s+\d", line):
            match = re.search(r"(\d+(?:\.\d+)?)\*", line)
            if match:
                current_display.refresh_rate_hz = float(match.group(1))
                current_display = None

    return displays


def read_brightness(display: Display) -> Optional[int]:
    if display.is_internal:
        return None

    display_number = ddc_map.get(display.name)
    if display_number is None:
        return None

    start_time = time.time()
    result = subprocess.run(
        ["ddcutil", "--display", str(display_number), "getvcp", "10"],
        capture_output=True,
        text=True,
        check=False,
    )
    latency = (time.time() - start_time) * 1000.0
    display.last_cmd_latency_ms = latency

    if result.returncode != 0:
        display.last_cmd_success = False
        return None

    display.last_cmd_success = True

    for line in result.stdout.splitlines():
        if "current value" in line:
            value_str = (
                line.split("current value =")[1]
                .split(",")[0]
                .strip()
            )
            display.brightness_percent = int(value_str)
            return display.brightness_percent

    return None


def update_displays(displays: List[Display], sample_period_s: float = 2.0) -> None:
    for display in displays:
        read_brightness(display)
        display.uptime_s += sample_period_s
