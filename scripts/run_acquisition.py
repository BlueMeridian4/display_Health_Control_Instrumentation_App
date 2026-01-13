from display_instrumentation.xrandr import parse_xrandr, update_displays
from display_instrumentation.nominal_sink import NominalSink
import time

def main():
    displays = parse_xrandr()
    sink = NominalSink()

    print("Starting display telemetry acquisition...")

    try:
        while True:
            update_displays(displays)  # updates brightness, latency, uptime
            sink.push_samples(displays)  # automatically upload to Nominal
            time.sleep(2)  # sampling period
    except KeyboardInterrupt:
        print("Stopping acquisition.")
