import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import time

from display_instrumentation.xrandr import parse_xrandr, update_display
from display_instrumentation.acquisition import collect_samples
from display_instrumentation.sink import NominalSink

SAMPLE_PERIOD_S = 2.0

def main():
    displays = parse_xrandr()
    sink = NominalSink()

    print("Starting display telemetry → Nominal Connect")

    try:
        while True:
            for d in displays:
                update_display(d, SAMPLE_PERIOD_S)

            samples = collect_samples(displays)
            sink.push(samples)

            for s in samples:
                print(
                    f"{s.timestamp.isoformat()} "
                    f"{s.display_name} "
                    f"connected={s.connected} "
                    f"brightness={s.brightness_percent} "
                    f"refresh={s.refresh_rate_hz} "
                    f"latency={s.cmd_latency_ms} "
                    f"health={s.health}"
                )


            time.sleep(SAMPLE_PERIOD_S)

    except KeyboardInterrupt:
        print("Stopping acquisition")
    finally:
        sink.close()

if __name__ == "__main__":
    main()
