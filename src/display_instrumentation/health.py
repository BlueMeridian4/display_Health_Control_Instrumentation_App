from __future__ import annotations

def compute_health(cmd_success: bool, latency_ms: Optional[float]) -> str:
    if not cmd_success:
        return "ERROR"
    if latency_ms and latency_ms > 200:
        return "DEGRADED"
    return "OK"