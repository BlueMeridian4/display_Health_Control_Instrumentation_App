import time

from .xrandr import parse_xrandr, update_display
from .acquisition import collect_samples
from .sink import NominalSink

def run(sample_period_s: float = 2.0):
    displays = parse_xrandr()
    sink = NominalSink()

    while True:
        for d in displays:
            update_display(d, sample_period_s)

        samples = collect_samples(displays)
        sink.push(samples)

        time.sleep(sample_period_s)