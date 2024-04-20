import time
import random
import tkinter as tk
import board
import adafruit_dotstar as dotstar
import bluetooth 

# server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM) 
# port = 22
# server_sock.bind(("",port)) 
# server_sock.listen(1) 
# client_sock,address = server_sock.accept() 
# print ("Connection made with: ", address) 
# while True: 
#     recvdata = client_sock.recv(1024) 
#     print ("Information Received: %s" % recvdata)
#     if (recvdata == "Q"): 
#         print ("Finished.") 
#         break
         
# client_sock.close() 
# server_sock.close()

recvdata = 1

# MAIN LOOP

# Initialize LED strip
# Need to change LED strip colors here for warnings
# dots = dotstar.DotStar(board.SCK, board.MOSI, 40, brightness=0.2)
# white_brightness = 100
# red_vec = (white_brightness, 0, 0)
# left_list = [19, 20, 21]

def do_stuff():
    s = 'DANGER!'
    l.config(text=s, fg='red')
    root.after(100, do_stuff)

root = tk.Tk()
root.attributes("-alpha", 0.1)
root.wm_overrideredirect(True)
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.bind("<Button-1>", lambda evt: root.destroy())

l = tk.Label(text='', font=("Helvetica", 80))
l.pack(expand=True)

do_stuff()
root.mainloop()
