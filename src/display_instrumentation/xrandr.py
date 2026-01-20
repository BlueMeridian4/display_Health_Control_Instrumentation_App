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

XRANDR_HEADER_RE = re.compile(
    r'^(?P<name>\S+)\s+connected'
    r'(?:\s+primary)?'
    r'(?:\s+(?P<mode>\d+x\d+)\+(?P<x>\d+)\+(?P<y>\d+))?'
)

XRANDR_MODE_RE = re.compile(r'^\s+\d+x\d+.*\*')

def parse_xrandr() -> List[Display]:
    result = subprocess.run(
        ["xrandr", "--query"],
        capture_output=True,
        text=True,
        check=False,
    )

    displays: List[tuple[int, Display]] = []
    current: Optional[Display] = None
    current_x = 0

    for line in result.stdout.splitlines():
        header = XRANDR_HEADER_RE.match(line)
        if header:
            name = header.group("name")
            is_internal = name.startswith(("eDP", "LVDS"))
            current_x = int(header.group("x") or 0)

            current = Display(
                name=name,
                is_internal=is_internal,
                connected=True,
            )
            displays.append((current_x, current))
            continue

        # ---- Active mode line (contains refresh rate) ----
        if current and XRANDR_MODE_RE.match(line):
            rate_match = re.search(r'(\d+(?:\.\d+)?)\*', line)
            if rate_match:
                current.refresh_rate_hz = float(rate_match.group(1))
            current = None  # done with this display

    # ---- Stable left → right ordering ----
    displays.sort(key=lambda item: item[0])

    final: List[Display] = []
    for idx, (_, d) in enumerate(displays, start=1):
        d.label = f"Display_{idx}"
        final.append(d)

    return final


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
