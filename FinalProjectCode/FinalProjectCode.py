import time
import random
import board
import adafruit_dotstar as dotstar
import bluetooth 

server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
port = 22
server_sock.bind(("",port)) 
server_sock.listen(1) 
client_sock,address = server_sock.accept() 
print ("Connection made with: ", address) 
while True: 
    recvdata = client_sock.recv(1024) 
    print ("Information Received: %s" % recvdata)
    if (recvdata == "Q"): 
        print ("Finished.") 
        break
         
client_sock.close() 
server_sock.close()

print(dir(board))
dots = dotstar.DotStar(board.SCK, board.MOSI, 30, brightness=0.2)

def random_color():
    return random.randrange(0, 7) * 32


# MAIN LOOP
n_dots = len(dots)
while True:
    # Fill each dot with a random color
    for dot in range(n_dots):
        dots[dot] = (random_color(), random_color(), random_color())

    time.sleep(0.25)