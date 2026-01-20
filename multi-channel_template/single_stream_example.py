import time
from datetime import datetime, timezone
import numpy as np
import connect_python


@connect_python.main
def stream_data(client: connect_python.Client):
    print("Starting single_stream_example.py", flush=True)

    # Initialize state variables from initial app state
    frequency = client.get_value("frequency", 1.0)
    y_offset = client.get_value("y_axis_offset", 0.0)

    print(f"Initial values - frequency: {frequency}, y_offset: {y_offset}", flush=True)

    try:
        client.clear_stream("sine_wave")
        client.clear_stream("incrementing_value")

        start = datetime.now(timezone.utc)
        while True:
            t = datetime.now(timezone.utc)
            delta = (t - start).total_seconds()
            value = np.sin(delta * frequency) + y_offset

            client.stream("sine_wave", t, value)
            client.stream("incrementing_value", t, delta)

            time.sleep(0.01)  # Add a small delay
    except Exception as e:
        print(f"Error in stream_data: {e}", flush=True)


if __name__ == "__main__":
    stream_data()
