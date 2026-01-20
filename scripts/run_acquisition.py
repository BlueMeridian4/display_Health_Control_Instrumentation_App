import os
import sys
import time
import json
import queue
import threading
from datetime import datetime, date, timezone

import connect_python  # MUST be first

# ---- Path setup AFTER connect import ----
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from display_instrumentation.xrandr import parse_xrandr, update_display
from display_instrumentation.acquisition import collect_samples
from display_instrumentation.sink import NominalSink

_loop_started = False

# ======================
# Logging Infrastructure
# ======================

log_queue = queue.Queue(maxsize=10_000)
stop_event = threading.Event()

def json_safe(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def log_worker(path="telemetry.log"):
    with open(path, "a", buffering=1) as f:
        while not stop_event.is_set():
            try:
                item = log_queue.get(timeout=0.5)
                f.write(json.dumps(item, default=json_safe) + "\n")
            except queue.Empty:
                continue

# ======================
# Helpers
# ======================

def sanitize(v, default=0.0):
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def health_to_float(health):
    return {
        "OK": 1.0,
        "DEGRADED": 0.5,
        "FAILED": 0.0,
        "ERROR": 0.0,
        "UNKNOWN": -1.0,
    }.get(health, -1.0)

CONNECTOR_TO_LABEL = {
    "DP-0": "Built-In_Display",
    "HDMI-0": "External_Display_1",
    "DP-4": "External_Display_2",
}

# ======================
# Acquisition Worker
# ======================

def acquisition_loop(client, sink, sample_period_s, disk_logging):
    logger = connect_python.get_logger("display-agent")
    STREAM_NAME = "display"

    logger.info("Acquisition loop started")

    while not stop_event.is_set():
        try:
            loop_start = time.time()
            logger.info("Acquisition tick")

            # ---- Discover displays (ONCE per tick) ----
            displays = parse_xrandr()

            if not displays:
                logger.warning("No displays detected")
                time.sleep(sample_period_s)
                continue

            # ---- Assign stable labels ----
            for d in displays:
                d.label = CONNECTOR_TO_LABEL.get(d.name, f"Unknown_{d.name}")

            # ---- Update + sample ----
            for d in displays:
                update_display(d, sample_period_s)

            samples = collect_samples(displays)
            logger.info(f"Collected {len(samples)} samples")

            # ---- Optional disk sink ----
            sink.push(samples)

            # ---- Build channel map ----
            channel_map = {}
            for d, s in zip(displays, samples):
                label = d.label
                channel_map.update({
                    f"{label}.connected": sanitize(s.connected),
                    f"{label}.brightness_percent": sanitize(s.brightness_percent),
                    f"{label}.refresh_rate_hz": sanitize(s.refresh_rate_hz),
                    f"{label}.uptime_s": sanitize(s.uptime_s),
                    f"{label}.cmd_latency_ms": sanitize(getattr(s, "cmd_latency_ms", 0.0)),
                    f"{label}.cmd_success": sanitize(getattr(s, "cmd_success", 0.0)),
                    f"{label}.health": health_to_float(getattr(s, "health", "UNKNOWN")),
                })

            logger.info(channel_map)

            # ---- Stream ----
            client.stream_from_dict(
                STREAM_NAME,
                timestamp=datetime.now(timezone.utc),
                channel_map=channel_map,
            )

            # ---- Sleep remaining period ----
            elapsed = time.time() - loop_start
            time.sleep(max(0.0, sample_period_s - elapsed))

        except Exception:
            logger.exception("Acquisition loop crashed")
            time.sleep(1.0)

# ======================
# CONNECT ENTRYPOINT
# ======================

@connect_python.main
def run(client: connect_python.Client):
    global _loop_started

    logger = connect_python.get_logger("display-agent")

    sample_period_s = float(client.get_value("sample_period_s", 2.0))
    disk_logging = bool(client.get_value("disk_logging", True))

    logger.info("Display agent started")

    sink = NominalSink()

    if disk_logging:
        threading.Thread(target=log_worker, daemon=True).start()

    def shutdown_handler():
        logger.info("Shutdown requested")
        stop_event.set()
        sink.close()

    client.add_shutdown_callback(shutdown_handler)

    if "CONNECT_RUNNER" not in os.environ and not _loop_started:
        _loop_started = True
        threading.Thread(
            target=acquisition_loop,
            args=(client, sink, sample_period_s, disk_logging),
            daemon=True,
        ).start()

    # ---- Keep client alive ----
    while not stop_event.is_set():
        time.sleep(0.5)

if __name__ == "__main__":
    run()