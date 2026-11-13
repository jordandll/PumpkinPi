# PumpkinPi

PumpkinPi is a small Python package for controlling a PumpkinPi GPIO board and its connected LEDs/eyes through simple command-driven scripts. It includes a CLI wrapper, a socket-based server/client pattern, and a built-in animation script for demonstration and testing.

## What is included

This package contains the following modules:

- `server.py` — listens for client commands and toggles the PumpkinPi outputs.
- `client.py` — sends a command string to the server over a socket.
- `cycle.py` — runs a short cycle animation across the PumpkinPi sides and eyes.
- `pumpkinpi` — exposes package scripts as CLI subcommands.
- `pumpkinpi` — package entry point for running the CLI.
- `motion-sensor.py` — motion-sensor-related logic for GPIO interaction.

## Installation

From the project root, install the package in editable mode if you are working in this repository:

```bash
pip install -e .
```

Once installed, the package exposes a `pumpkinpi` command.

## CLI usage

```bash
pumpkinpi --help
```

This will list the available subcommands, which correspond to the Python scripts in this package.

Example:

```bash
pumpkinpi server --host 127.0.0.1 --port 9001
pumpkinpi client --host 127.0.0.1 --port 9001 blink
pumpkinpi cycle
```

The CLI runs the matching script with Python automatically, so each file acts like a command.

## Network defaults

The `server` and `client` commands read default network settings from an INI
configuration file. On Linux, the preferred location is
`~/.config/pumpkinpi/config.ini` (or `$XDG_CONFIG_HOME/pumpkinpi/config.ini`
when `XDG_CONFIG_HOME` is set). The suggested legacy location
`~/.local/etc/pumpkinpi_config.d` is also supported; it can be either a config
file or a directory containing `config.ini`. On macOS, the default is
`~/Library/Application Support/pumpkinpi/config.ini`; on Windows, it is
`%APPDATA%\pumpkinpi\config.ini`.

Create the config file with a `[network]` section and set either or both values:

```ini
[network]
host = 192.168.1.20
port = 9001
```

These settings are used by both `pumpkinpi server` and `pumpkinpi client` when
their corresponding options are omitted. Command-line options take precedence:

```bash
pumpkinpi client --host 127.0.0.1 --port 9002 blink
```

## Example server/client flow

Start the server:

```bash
python server.py --host 127.0.0.1 --port 9001
```

Then send a command from another terminal:

```bash
python client.py --host 127.0.0.1 --port 9001 blink
```

The client accepts multiple space-separated commands in one request. The server
validates the full batch before running any of it, then executes commands in
order:

```bash
python client.py blink pause 10 sides.left.0
```

The client-side syntax for a pause is `pause SECONDS`; the client converts it to
the TCP request form `pause(SECONDS)`. For example, `pause 10` pauses execution
for ten seconds. Pause durations must be non-negative numbers.

Common commands include:

- `blink`
- `cycle`
- `sides.left.0`
- `sides.right.4`
- `eyes.left`
- `eyes.right`
- `monitor`
- `pause 10` (client syntax; sent over the network as `pause(10)`)

These commands are sent as UTF-8 text over a socket and interpreted by the server logic.
The `monitor` command returns the currently lit LED paths, one per line, using the same
notation as toggle commands (for example, `eyes.left` or `sides.left.0`). It returns
`none` when all LEDs are off. `monitor` must be the only command in a request.
The server continues accepting `monitor` requests while a command batch is running.
Other command batches received during execution are queued in order, and their clients
receive a warning that the server is busy.

## Mock testing

The project supports GPIO Zero mock mode for local testing without a physical Raspberry Pi:

```bash
GPIOZERO_PIN_FACTORY=mock python server.py
```

This lets the scripts run in a simulated hardware environment. The server prints the full name of each executed command in both mock and hardware modes.

## Notes

This package is intended for Raspberry Pi experimentation and simple hardware control workflows. It is best used with a PumpkinPi board or a GPIO Zero mock factory during development or testing.
