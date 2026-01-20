from __future__ import annotations

import subprocess
import time
import re
from typing import Optional, List

from .models import Display


# Map physical display names to ddcutil display numbers
ddc_map = {
    "DP-0": 1,
    "HDMI-0": 2,
    "DP-4": 3,
}


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

            current_display = Display(
                name=name,
                is_internal=is_internal,
                connected=True,
            )
            displays.append(current_display)

        elif current_display and re.match(r"^\s+\d", line):
            match = re.search(r"(\d+(?:\.\d+)?)\*", line)
            if match:
                current_display.refresh_rate_hz = float(match.group(1))
                current_display = None

    return displays


def read_brightness(display: Display) -> Optional[int]:
    if display.is_internal:
        display.last_cmd_success = True
        return None

    display_number = ddc_map.get(display.name)
    if display_number is None:
        display.last_cmd_success = False
        return None

    start = time.time()
    result = subprocess.run(
        ["ddcutil", "--display", str(display_number), "getvcp", "10"],
        capture_output=True,
        text=True,
        check=False,
    )
    display.last_cmd_latency_ms = (time.time() - start) * 1000.0

    if result.returncode != 0:
        display.last_cmd_success = False
        return None

    display.last_cmd_success = True

    for line in result.stdout.splitlines():
        if "current value" in line:
            value = line.split("current value =")[1].split(",")[0].strip()
            display.brightness_percent = int(value)
            return display.brightness_percent

    return None


def update_display(display: Display, sample_period_s: float) -> None:
    read_brightness(display)
    display.uptime_s += sample_period_s
