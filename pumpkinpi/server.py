import sys

argv = sys.argv

if '--help' in argv:
    print(
        'Usage: server.py [--host HOST | -h HOST] [--port PORT | -p PORT]\n'
        '\n'
        'Start the PumpkinPi command server.\n'
        '\n'
        'Options:\n'
        '  --host HOST, -h HOST  Address to bind to (default: 127.0.0.1)\n'
        '  --port PORT, -p PORT  Port to listen on (default: 9001)\n'
        '  --help                Show this help message and exit'
    )
    sys.exit(0)

from gpiozero import PumpkinPi
from gpiozero.pins.mock import MockFactory
import socket as sock
import subprocess as sp
import queue
import threading
import math
import time

# Common error messages specific to sockets.
err_msg_timeout = 'Connection Error:\tConnection timeout error occurred with client at \'{0}\' on port {1:d}.'


def parse_commands(message):
    command_tokens = message.split()
    if not command_tokens:
        raise ValueError('No commands were provided.')
    if 'monitor' in command_tokens and command_tokens != ['monitor']:
        raise ValueError('The monitor command must be sent by itself.')

    parsed = []
    for command in command_tokens:
        if command == 'blink':
            parsed.append(('blink', None))
        elif command == 'blink.eyes':
            parsed.append(('blink', 'eyes'))
        elif command in ('cycle', 'monitor'):
            parsed.append((command, None))
        elif command.startswith('pause(') and command.endswith(')'):
            duration_text = command[6:-1]
            try:
                duration = float(duration_text)
            except ValueError as parse_error:
                raise ValueError('pause requires a non-negative number of seconds.') from parse_error
            if not math.isfinite(duration) or duration < 0:
                raise ValueError('pause requires a non-negative number of seconds.')
            parsed.append(('pause', duration))
        elif command.startswith('sides.'):
            parts = command.split('.')
            if len(parts) != 3 or parts[1] not in ('left', 'right'):
                raise ValueError(f'Invalid command: {command}')
            try:
                led_index = int(parts[2])
            except ValueError as parse_error:
                raise ValueError(f'Invalid command: {command}') from parse_error
            parsed.append(('side', (parts[1], led_index)))
        elif command in ('eyes.left', 'eyes.right'):
            parsed.append(('eye', command.split('.')[1]))
        else:
            raise ValueError(f'Invalid command: {command}')
    return parsed


# Parse the command line for address info.
if '-h' in argv:
    HOST = argv[argv.index('-h') + 1]
elif '--host' in argv:
    HOST = argv[argv.index('--host') + 1]
else:
    HOST = '127.0.0.1'

if '-p' in argv:
    PORT = int(argv[argv.index('-p') + 1])
elif '--port' in argv:
    PORT = int(argv[argv.index('--port') + 1])
else:
    PORT = 9001

ADDR = (HOST, PORT)

# Create server socket bound to HOST listening on port PORT.
ss = sock.socket()
ss.bind(ADDR)
ss.listen()

# Instantiate PumpkinPi class.
pumpkin = PumpkinPi()

command_queue = queue.Queue()
queue_state_lock = threading.Lock()
pending_batches = 0


def execute_commands(parsed_commands):
    for kind, value in parsed_commands:
        if kind == 'side':
            command_name = f'sides.{value[0]}.{value[1]}'
        elif kind == 'eye':
            command_name = f'eyes.{value}'
        elif kind == 'blink':
            command_name = 'blink.eyes' if value == 'eyes' else 'blink'
        elif kind == 'pause':
            command_name = f'pause({value})'
        else:
            command_name = kind

        if kind == 'side':
            side, index = value
            getattr(pumpkin.sides, side)[index].toggle()  # type: ignore[attr-defined]
        elif kind == 'eye':
            getattr(pumpkin.eyes, value).toggle()  # type: ignore[attr-defined]
        elif kind == 'blink':
            if value == 'eyes':
                if isinstance(pumpkin.pin_factory, MockFactory):
                    print("PumpkinPi is blinking...")
                pumpkin.eyes.blink(n=5, background=False)  # type: ignore[attr-defined]
                if isinstance(pumpkin.pin_factory, MockFactory):
                    print("PumpkinPi is done blinking.")
            else:
                if isinstance(pumpkin.pin_factory, MockFactory):
                    print("PumpkinPi is blinking...")
                pumpkin.blink(n=5, background=False)  # type: ignore[attr-defined]
                if isinstance(pumpkin.pin_factory, MockFactory):
                    print("PumpkinPi is done blinking.")
        elif kind == 'cycle':
            sp.run(['python3', 'cycle.py'])
        elif kind == 'pause':
            time.sleep(value)  # type: ignore

        print(f'{command_name} was executed')


def process_command_queue():
    global pending_batches
    while True:
        parsed_commands, client_socket = command_queue.get()
        response = b'ERROR: Command batch did not complete.'
        try:
            execute_commands(parsed_commands)
            response = b'OK'
        except Exception as command_error:
            response = f'ERROR: {command_error}'.encode(encoding='utf-8')
            print(f'Command batch failed: {command_error}')
        finally:
            if client_socket is not None:
                try:
                    client_socket.sendall(response)
                except OSError as send_error:
                    print(f'Unable to send command response: {send_error}')
                finally:
                    client_socket.close()
            with queue_state_lock:
                pending_batches -= 1
            command_queue.task_done()


threading.Thread(target=process_command_queue, daemon=True).start()

while True:
    # Accept incoming connection by listening on port 9001.
    try:
        s, addr = ss.accept()
    except KeyboardInterrupt:
        print('\nServer was stopped by a keyboard interrupt before a connection was accepted.')
        exit(0)

    s.settimeout(2)

    # Read the complete request; the client closes its write side when done.
    try:
        request = bytearray()
        while True:
            chunk = s.recv(1024)
            if not chunk:
                break
            request.extend(chunk)
    except sock.timeout:
        print(err_msg_timeout.format(*addr))
        s.close()
        continue

    try:
        cmd = request.decode(encoding='utf-8')
        parsed_commands = parse_commands(cmd)
        for kind, value in parsed_commands:
            if kind == 'side':
                side, index = value
                leds = getattr(pumpkin.sides, side)  # type: ignore[attr-defined]
                if not -len(leds) <= index < len(leds):
                    raise ValueError(f'Invalid side LED index: {index}')
    except (UnicodeDecodeError, ValueError) as request_error:
        s.sendall(f'ERROR: {request_error}'.encode(encoding='utf-8'))
        s.close()
        continue

    if parsed_commands[0][0] == 'monitor':
        active_leds = [
            f'eyes.{side}'
            for side in ('left', 'right')
            if getattr(pumpkin.eyes, side).is_active  # type: ignore[attr-defined]
        ]
        active_leds.extend(
            f'sides.{side}.{index}'
            for side in ('left', 'right')
            for index, led in enumerate(getattr(pumpkin.sides, side))  # type: ignore[attr-defined]
            if led.is_active
        )
        response = '\n'.join(active_leds) if active_leds else 'none'
        try:
            s.sendall(response.encode(encoding='utf-8'))
        except OSError as send_error:
            print(f'Unable to send monitor response: {send_error}')
        finally:
            s.close()
        continue

    with queue_state_lock:
        server_busy = pending_batches > 0
        pending_batches += 1
    command_queue.put((parsed_commands, None if server_busy else s))
    if server_busy:
        try:
            s.sendall(b'WARNING: Server is busy; commands have been queued.')
        except OSError as send_error:
            print(f'Unable to send busy warning: {send_error}')
        finally:
            s.close()
