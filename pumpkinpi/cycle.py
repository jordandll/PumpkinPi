from gpiozero import PumpkinPi
from time import sleep

pumpkin = PumpkinPi()

for i in range(5):
    pumpkin.sides.left[i].toggle() # type: ignore
    sleep(0.2)

pumpkin.eyes.left.toggle() # type: ignore
sleep(0.2)
pumpkin.eyes.right.toggle() # type: ignore
sleep(0.2)

for i in range(5):
    pumpkin.sides.right[4-i].toggle() # type: ignore
    sleep(0.2)
