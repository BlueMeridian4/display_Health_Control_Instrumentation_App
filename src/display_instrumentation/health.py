from typing import Optional

def compute_health(
    connected: bool,
    cmd_success: bool,
    latency_ms: Optional[float],
    brightness: Optional[float],
    refresh_rate: Optional[float],
) -> str:
    if not connected:
        return "FAILED"

    if brightness is not None or refresh_rate is not None:
        # Display is alive
        if not cmd_success:
            return "DEGRADED"

        if latency_ms is not None and latency_ms > 1500:
            return "DEGRADED"

        return "OK"

    return "UNKNOWN"