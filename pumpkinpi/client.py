#!/usr/bin/python3

import sys
import math

argv = sys.argv

if '--help' in argv:
    print(
        'Usage: client.py [--host HOST | -h HOST] [--port PORT | -p PORT] COMMAND [COMMAND ...]\n'
        '\n'
        'Send one or more commands to the PumpkinPi server.\n'
        '\n'
        'Options:\n'
        '  --host HOST, -h HOST  Server address (default: config file or 127.0.0.1)\n'
        '  --port PORT, -p PORT  Server port (default: config file or 9001)\n'
        '  --help                Show this help message and exit\n'
        '\n'
        'Commands include blink, cycle, monitor, sides.left.0, sides.right.4,\n'
        'blink.eyes, eyes.left, eyes.right, and pause SECONDS (for example: pause 10).\n'
        'Separate commands with spaces. monitor must be sent by itself.'
    )
    sys.exit(0)

import socket as sock
from pumpkinpi.config import resolve_network_options

sock.setdefaulttimeout(2)

# Common error messages specific to sockets.
err_msg_timeout = 'Connection Error:\tConnection timeout error occurred with server at \'{0}\' listening on port {1:d}.'

# Create client socket, denoted as 's'.
s = sock.socket()

# Resolve command-line options first, then use config-file defaults.
HOST, PORT = resolve_network_options(argv[1:])

ADDR = (HOST, PORT)

# Read commands from the command line, skipping connection options.
command_args = []
i = 1
while i < len(argv):
    if argv[i] in ('-h', '--host', '-p', '--port'):
        i += 2
    elif argv[i].startswith('--host=') or argv[i].startswith('--port='):
        i += 1
    else:
        command_args.append(argv[i])
        i += 1

if not command_args:
    print('ERROR:\tAt least one command is required.')
    exit(2)

# Convert the CLI pause syntax to the TCP request syntax.
command_sequence = []
i = 0
while i < len(command_args):
    command = command_args[i]
    if command == 'pause':
        if i + 1 >= len(command_args):
            print('ERROR:\tpause requires a non-negative number of seconds.')
            exit(2)
        duration = command_args[i + 1]
        try:
            seconds = float(duration)
        except ValueError:
            print('ERROR:\tpause requires a non-negative number of seconds.')
            exit(2)
        if not math.isfinite(seconds) or seconds < 0:
            print('ERROR:\tpause requires a non-negative number of seconds.')
            exit(2)
        command_sequence.append(f'pause({duration})')
        i += 2
    else:
        command_sequence.append(command)
        i += 1

if 'monitor' in command_sequence and command_sequence != ['monitor']:
    print('ERROR:\tThe monitor command must be sent by itself.')
    exit(2)

cmd = ' '.join(command_sequence)

# Connect to server at HOST listening on port PORT.
try:
    s.connect(ADDR)
except sock.timeout:
    print(err_msg_timeout.format(*ADDR))
    exit(1)

encoded_cmd = cmd.encode(encoding='utf-8')
s.sendall(encoded_cmd)
s.shutdown(sock.SHUT_WR)

code = 0
s.settimeout(None)
response = bytearray()
while True:
    chunk = s.recv(1024)
    if not chunk:
        break
    response.extend(chunk)

response_text = response.decode(encoding='utf-8')
if response_text.startswith('ERROR:'):
    print(response_text)
    code = 1
elif response_text.startswith('WARNING:'):
    print(response_text)
elif command_sequence == ['monitor']:
    print(response_text)

print(f'Client sent {len(encoded_cmd):d} bytes of data to \'s://{HOST}:{PORT:d}/\'.')

# Close and disconnect.
s.close()

exit(code)
