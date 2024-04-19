from gpiozero import LED
import time

led_right = LED(10)
led_left = LED(9)

led_right.on()
led_left.on()
