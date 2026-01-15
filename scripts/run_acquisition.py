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

            time.sleep(SAMPLE_PERIOD_S)

    except KeyboardInterrupt:
        print("Stopping acquisition")
    finally:
        sink.close()

if __name__ == "__main__":
    main()
