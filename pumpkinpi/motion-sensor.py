from gpiozero import MotionSensor
from signal import pause
from sys import argv
import subprocess as sp


""" The arguments passed to this script are passed to the 'client.py' script that is run when motion is 
detected by the motion sensor.  Note that this includes optional network arguments as well as the 
mandatory argument that describes the command to be executed by the PumpkinPi 'server.py' script 
(e.g. 'blink', which says the PumpkinPi LEDs shall blink the specified number of times,  or 
'eyes.right', which says the PumpkinPi's right eye LED shall be toggled). """


def send_msg():
    # Initialize the list of arguments to be passed to 'sp.run', denoted as 'args'.
    args = ['python3', 'client.py']

    # Extend 'args' with the appropriate arguments passed to this script.
    if len(argv) > 1:
        args.extend(argv[1:])
    else:
        args.append('blink')

    cp = sp.run(args, capture_output=True, encoding='utf-8')
    if cp.stdout is not None:
        print(args[0] + ' ' + args[1] + ' ' + args[2] + ':\t' + cp.stdout)


pir = MotionSensor(pin=4, pull_up=True, queue_len=5)
pir.when_activated = send_msg

try:
    pause()
except KeyboardInterrupt:
    print("\nKeyboard interrupt received.  Stopping script.")
