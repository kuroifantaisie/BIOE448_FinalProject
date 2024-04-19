import time
import random
import board
import adafruit_dotstar as dotstar

print(dir(board))
dots = dotstar.DotStar(board.SCLK, board.SDA, 30, brightness=0.2)

def random_color():
    return random.randrange(0, 7) * 32


# MAIN LOOP
n_dots = len(dots)
while True:
    # Fill each dot with a random color
    for dot in range(n_dots):
        dots[dot] = (random_color(), random_color(), random_color())

    time.sleep(0.25)