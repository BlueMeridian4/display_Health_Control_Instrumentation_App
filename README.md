# Display Health Control Instrumentation App

This project provides a **Linux-based display telemetry agent** that can:

- Monitor multiple local monitors in real time.
- Collect display metrics such as **brightness**, **refresh rate**, **uptime**, **health**, and **command success**.
- Stream telemetry data live to a **Nominal Connect client** either through **Nominal Core** or **Nominal App**.

It is designed for **multi-monitor setups** and allows simultaneous streaming to the **Nominal web app** and **local Nominal Connect app**.

## Features

- Automatic detection of connected displays using `xrandr`.
- Brightness readings via `ddcutil` for external monitors.
- Health scoring for each display (`OK`, `DEGRADED`, `FAILED`, `UNKNOWN`).
- Continuous uptime tracking and refresh rate monitoring.
- Configurable sample period (default 2 seconds).
- Optional persistent disk logging to `telemetry.log`.
- Real-time streaming to Nominal Connect datasets and assets.

## Project Structure

```text
display_Health_Control_Instrumentation_App/
├── multi-channel_template/       # Example templates and prebuilt Connect app
│   ├── app.connect               # Connect app configuration
│   ├── multi_stream_example.py   # Example of multi-stream telemetry
│   ├── single_stream_example.py  # Example of single-stream telemetry
│   └── preview.png               # Screenshot preview
├── scripts/
│   └── run_acquisition.py        # Main agent entrypoint
├── src/
│   └── display_instrumentation/
│       ├── acquisition.py        # Sample collection logic
│       ├── health.py             # Health computation
│       ├── models.py             # Display and sample models
│       ├── sink.py               # Nominal Connect streaming sink
│       └── xrandr.py             # Monitor detection & brightness updates
├── telemetry.log                 # Optional persistent log file
└── pyproject.toml                # Project metadata and dependencies
```

## Requirements

- Linux with **X11** (supports XSHM screen capture)
- Python 3.12+
- `ddcutil` installed and accessible in `$PATH`
- Optional: `python-dotenv` for environment variable management
- Nominal Connect SDK:
  ```bash
  pip install nominal
  ```

## Environment variables for streaming:

```bash
export NOMINAL_API_KEY="your_api_token"
export NOMINAL_API_URL="https://api.nominal.com"
export NOMINAL_WORKSPACE_RID="workspace_rid_here"
```

## Usage

### Running the Agent (Nominal Core)

```
cd display_Health_Control_Instrumentation_App
pip install -e .
python scripts/run_acquisition.py
```

- By default, the agent:
  - Streams telemetry to Nominal Core
  - Samples every 2 seconds (configurable via sample_period_s)

### Running the Agent (Nominal App)

1. Launch `connect-app` from nominal-connect folder
2. Click `OPEN APP` in top left corner of application
3. Navigate to `~/display_Health_Control_Instrumentation_App/multi-channel_template/app.connect`
4. Click `Run All` in bottom left corner to begin live stream of telemetry data

- By default, the agent:
  - Streams telemetry to Nominal Connect
  - Logs to telemetry.log (can be disabled via disk_logging in Connect app)
  - Samples every 2 seconds (configurable via sample_period_s)

### Example Multi-Stream Template

Inside multi-channel_template:
`python3 multi_stream_example.py`

This example demonstrates streaming telemetry from multiple displays simultaneously.

## Display Metrics

Each display is tracked with the following channels:

| Channel               | Description                                                           |
| --------------------- | --------------------------------------------------------------------- |
| `.connected`          | 1.0 if connected, 0.0 if disconnected                                 |
| `.brightness_percent` | Current brightness (0–100)                                            |
| `.refresh_rate_hz`    | Current refresh rate in Hz                                            |
| `.uptime_s`           | Accumulated uptime in seconds                                         |
| `.cmd_latency_ms`     | Latency of last command in milliseconds                               |
| `.cmd_success`        | 1.0 if last command succeeded, 0.0 otherwise                          |
| `.health`             | Health score (1.0 = OK, 0.5 = DEGRADED, 0.0 = FAILED, -1.0 = UNKNOWN) |

## Development Notes

- The agent uses threaded acquisition with a queue for efficient logging.
- Displays are automatically labeled (Display_1, Display_2, ...) based on left-to-right X position.
- Internal laptop panels (eDP, LVDS) are detected but brightness cannot be modified.
