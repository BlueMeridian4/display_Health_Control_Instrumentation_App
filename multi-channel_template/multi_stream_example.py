import numpy as np
import sys
from datetime import datetime, timezone
import time
import connect_python


log = connect_python.get_logger("multi-stream")


@connect_python.main
def stream_data(client: connect_python.Client):
    log.info("Starting multi_stream_example.py")

    # Initialize state variables from initial app state
    frequency = client.get_value("frequency", 1.0)
    y_offset = client.get_value("y_axis_offset", 0.0)
    debug_logging = client.get_value("debug_logging", False)

    try:
        stream_count = int(client.get_value("stream_count", "40"))
    except (ValueError, TypeError):
        stream_count = 40

    try:
        delay = float(client.get_value("delay", "0.015"))
    except (ValueError, TypeError):
        delay = 0.015

    log.info(f"Initial values - frequency: {frequency}, y_offset: {y_offset}")

    def shutdown_handler():
        log.info("Example shutdown handler called")

    client.add_shutdown_callback(shutdown_handler)

    try:
        client.clear_stream("sensors")

        start = datetime.now(timezone.utc)

        # Generate channel names once before the loop
        channel_names = [
            f"{['Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta', 'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Omicron', 'Pi', 'Rho', 'Sigma', 'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega'][i % 24]}_{np.random.randint(1, 99999)}"
            for i in range(stream_count)
        ]

        while True:
            t = datetime.now(timezone.utc)
            delta = (t - start).total_seconds()
            floats = [
                np.sin(delta * frequency * i) + y_offset for i in range(stream_count)
            ]

            client.stream_from_dict(
                "sensors", timestamp=t, channel_map=dict(zip(channel_names, floats))
            )

            if debug_logging:
                print(f"Data size: {len(floats)}", flush=True)
                print(f"\x1b[31mTimestamp: {t}\x1b[0m", flush=True, file=sys.stderr)

            time.sleep(delay)

    except Exception as e:
        print(f"Error in stream_data: {e}", flush=True)


if __name__ == "__main__":
    stream_data()
