import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import board
import adafruit_lis2mdl
import adafruit_lsm303_accel
import math
import time
import busio
import numpy as np
import os
import csv
import adafruit_dotstar as dotstar
import atexit
"""
Notes:
 - GPS is accurate
 - Magnetometer works significntly better outside
 - Need to find if bearing angle calculation is accurate
 - Need to change distance in moveMark function
"""

# Control variables
is_display = True  # Determines if one gets rid of bar for tkinter screen
# For display
coord_idx = 0
coord_list = 0
# Calibrate Compass
# Note that I will use GPIO zero code, but just replace with the LED strip code
# Use other python library  for screen measurement



#hardiron_cal = compass.calibrate(mag)
#hardiron_cal = [[-79.05, 10.65], [-51.75, 33.9], [-13.95, 35.4]]
hardiron_cal = [[-70.8, -1.5], [-55.05, 15.6], [-20.4, 5.3999999999999995]]
# Set screen metrics
distance = 112
if is_display:
   x_boundary = 1920 # +10 to eliminate any white areas on screen (SOLVED)
   y_boundary = 1080
else:
   x_boundary = 1200
   y_boundary = 800

x_start = x_boundary/2
y_start = y_boundary/2
marker_x = x_start
marker_y = y_start
right_toggle = 0
overflow = 4 * x_boundary
speed_var = 2.25
refresh_rate = 15

# Initialize LED strip
# Need to change LED strip colors here for warnings
dots = dotstar.DotStar(board.SCK, board.MOSI, 40, brightness=0.2)
white_brightness = 100
white_vec = (white_brightness, white_brightness, white_brightness)
red_vec = (white_brightness, 0, 0)
blue_vec = (0, 0, white_brightness)
green_vec = (0, white_brightness, 0)
yellow_vec = (white_brightness, white_brightness, 0)
while True:
   left_list = [19, 20, 21]
   for dot in left_list:
      dots[dot] = red_vec


light_dict = {'path': white_vec, 'good': blue_vec, 'danger': red_vec, 'path_end': green_vec, 'investigate': yellow_vec}
#Values are received from angle given by magnetometer
look_x = []
look_y = []
mark_bound = 80
text_x = mark_bound / 2 - 5
text_y = mark_bound / 10
#change speed to depend on ratio between look_x and look_y
xspeeds = []
yspeeds = []

num = 0
guidance = []
dist = []

edge_margin = 20
x_values = []
y_values = []



def light_left(dots, color_vec):

   left_list = [19, 20, 21]
   for dot in left_list:
      dots[dot] = color_vec
   return None

def light_right(dot, color_vec):

   right_list = [0, 1, 2]
   for dot in right_list:
      dots[dot] = color_vec
   return None

def light_top(dots, turn_on=True):
   if turn_on:
      dots.fill((0,0,0))
      turn_on = False

   top_list = [10, 11, 12]
   for dot in top_list:
      dots[dot] = white_vec
   return None

def exit_func():
   dots.fill((0,0,0))

# In order to read csv output from gps, use filename and function below
filename = 'gps_info.csv'

def read_csv(fname):
   data = None
   with open(fname, mode='r') as file:
      csvFile = csv.reader(file)
      data = next(csvFile)
   return data

obs_filename = 'gps_obs_info.csv'
display_filename = 'Object_Label.csv'
def read_csv_obs(fname):
    # Note that the order for this should be angles, distances, markers for each line
    data = []
    with open(fname, mode='r') as file:
        csvFile = csv.reader(file)
        for line in csvFile:
            data.append(line)
    return data

def find_sign(number):
   s = 0
   if number > 0:
      s = 1
   else:
      s = -1
   return s


def find_marker_shift(target_angle, mag_angle):
   ang_diff = target_angle - mag_angle
   res = 0

   if abs(ang_diff) < 180:
      ang_sign = find_sign(ang_diff)
      res = ang_sign * abs(ang_diff)
   else:
      ang_sign = -1 * find_sign(ang_diff)
      res = ang_sign * (360 - abs(ang_diff))

   return res


obs_angs = []
obs_dists = []
obs_labels = []
disp_name = ''
obs_progress = ''
on_flag = True
def_flag = False
description_dict = {'Person': 'Civilian, with military CV algorithm\n can distinguish between hostile and friendly',
                    'Chair': 'Chair meant for sitting',
                    'Monitor': 'Computer monitor, with military camera\n can determine what is on screen',
                    'Plant': 'Potted plant with green leaves'}

warning_flag = False
warning_text = '!!!TOO CLOSE TO DANGER!!!'
warning_visible = False
def moveMark():
   global xspeed, yspeed, look_x, look_y, marker_x, marker_y, coord_list, coord_idx, \
      prev_target_angle, target_angle, obs_angs, obs_dists, obs_labels, dist, guidance, num, warning_flag, warning_visible
   # get bounding box of the image
   # may want to remove averaging
   # Overflow will be used to determine FOV
   # Make overflow proportional to fov
   # look_x is where you want to look, not where you are actively looking

  # Updates GPS if there is a fix, doesn't if there isn't, initializes to right outside valhalla (can change)
   print(num)
   try:
    #  tmp = read_csv(filename)
      obs_tmp = read_csv_obs(obs_filename)
      disp_tmp = read_csv_obs(display_filename)
      """
      if tmp != None:
         distance = tmp[0]
         target_angle = tmp[1]
         coord_idx = tmp[2]
         coord_list = tmp[3]
         #canvas.itemconfigure(obj_dist, text = f'{distance} m')
         #canvas.itemconfigure(coord_progress, text = f'{coord_idx} / {coord_list} Points Reached')
         prev_target_angle = target_angle
      """
      if obs_tmp != None and len(obs_tmp) == 5:
         obs_angs = obs_tmp[0]
         print(f'Obs angs1 = {obs_angs}')
         obs_dists = obs_tmp[1]
         obs_labels = obs_tmp[2]
         obs_progress = obs_tmp[3]
         obs_complete = obs_tmp[4]
         warning_visible = False
         tmp_warning_flag = False
         display_string = f'Distance: {obs_dists[0]}\n{obs_progress[0]}'
         # Conditional for if final point is reached
         if obs_complete[0] == 'True':
            canvas.tab[0]['image'] = ImageTk.PhotoImage(icons['path'])
            #guidance[0] = (canvas.create_image(-mark_bound,y_boundary/2, image=canvas.tab[0]['image'], anchor='center'))
            canvas.itemconfigure(guidance[0], image=canvas.tab[0]['image'])
            canvas.itemconfigure(object_name, text='Route Finished', font='SegoeUI 24', fill='white')
         else:
            canvas.itemconfigure(object_name, text=display_string, font='SegoeUI 24', fill='white')

         for i in range(num):
            #canvas.itemconfigure(dist[i], text=obs_dists[i] + ' m')
            if obs_labels[i] == 'danger' and float(obs_dists[i]) < 1:
               tmp_warning_flag = True

            if obs_labels[i] == 'danger' and float(obs_dists[i]) > 100:
               canvas.tab[i]['image'] = ImageTk.PhotoImage(icons['black'])
               canvas.itemconfigure(guidance[i], image=canvas.tab[i]['image'])
               canvas.itemconfigure(dist[i], text='')
            elif obs_labels[i] == 'danger' and float(obs_dists[i]) <= 100:
               canvas.tab[i]['image'] = ImageTk.PhotoImage(icons['danger'])
               canvas.itemconfigure(guidance[i], image=canvas.tab[i]['image'])
               canvas.itemconfigure(dist[i], text=obs_dists[i] + ' m')
               warning_visible = True
            else:
               canvas.itemconfigure(dist[i], text=obs_dists[i] + ' m')   
         warning_flag = tmp_warning_flag
         print(f'Warning is visible: {warning_visible}')
      if disp_tmp != None:
         print(disp_tmp)
         on_flag = disp_tmp[2][0] == '1'
         print(on_flag)
         def_flag = disp_tmp[1][0] == '1'
         disp_name = disp_tmp[0][0]
         #canvas.itemconfigure(object_name, text=disp_name)
         if def_flag and disp_name in description_dict.keys() and not warning_flag:
            canvas.itemconfigure(object_description, text=description_dict[disp_name])
         elif warning_flag:
            canvas.itemconfigure(object_name, text=warning_text, font='SegoeUI 40', fill='red')
            canvas.itemconfigure(object_description, text='')
         else:
            canvas.itemconfigure(object_description, text='')
   except StopIteration:
      #target_angle = prev_target_angle
      pass

   if on_flag:
      print(f'Obs_ang: {obs_angs}')
      mag_pitch_vec = compass.run_compass_tilt(mag, accel, hardiron_cal)
      mag_angle = mag_pitch_vec[0]
      #offset_angle = find_marker_shift(float(target_angle), mag_angle)
      ang2pixel_arr = []
      #ang2pixel_arr.append(offset_angle / 360 * 9 * x_boundary)
      right_lit = False
      left_lit = False
      for i in range(num):
         ang2pixel_arr.append(find_marker_shift(float(obs_angs[i]), mag_angle) / 360 * 9 * x_boundary)
      # (leftPos, topPos, rightPos, bottomPos) = canvas.bbox(guidance)
      # ang2pixel = offset_angle / 360 * 9 * x_boundary
      pitch_angle = mag_pitch_vec[2] / 360 * 16.5 * y_boundary  # Keep all in same y value

      #print(f"Angle: {compass.run_compass_tilt(mag, accel, hardiron_cal)}")
      print(f'Angle: {mag_angle}')
      #print(f'Offset angle is: {offset_angle}')
      #print(f'Bearing angle is: {target_angle}')
      print(f'Pitch Angle: {mag_pitch_vec[2]}')
      #look_x = float(x_boundary / 2 - ang2pixel)
      look_y = [float(y_boundary / 2 - pitch_angle) for i in range(len(ang2pixel_arr))]
      look_x = [float(x_boundary / 2 - ang2pixel_arr[i]) for i in range(len(ang2pixel_arr))]
      #eye_x_pos.configure(text = f'current look x value:  {look_x}')
      #boundaries of the canvas to swap sides of display
      # Adjust for edge cases, add/subtract from overflow to set

      for i in range(num):
         # Right side overflow
         if look_x[i] >= x_boundary + overflow:
            canvas.moveto(guidance[i], mark_bound / 2, y_values[i] - mark_bound / 2)
            canvas.moveto(dist[i], mark_bound + text_x, y_values[i] + text_y)
            look_x[i] = look_x[i] - (x_boundary + (2 * overflow))

         # Left side overflow
         if look_x[i] <= -(overflow):
            canvas.moveto(guidance[i], x_boundary - 1.5 * mark_bound, y_values[i] - mark_bound / 2)
            canvas.moveto(dist[i], x_boundary + text_x, y_values[i] + text_y)
            look_x[i] = look_x[i] + (x_boundary + (2 * overflow))

         # Bottom overflow
         if look_y[i] >= y_boundary + overflow:
            canvas.moveto(guidance[i], x_values[i] - mark_bound / 2, mark_bound / 2)
            canvas.moveto(dist[i], x_values[i] + text_x, mark_bound + text_y)
            look_y[i] = look_y[i] - (y_boundary + (2 * overflow))

         # Top overflow
         if look_y[i] <= -(overflow):
            canvas.moveto(guidance[i], x_values[i] - mark_bound / 2, y_boundary - 1.5 * mark_bound)
            canvas.moveto(dist[i], x_values[i] + text_x, y_boundary + text_y)
            look_y[i] = look_y[i] + (y_boundary + (2 * overflow))

         ## Modifiyng the speed at which the marker travels
         ## if the point to get to is outside of horizontal boundaries then marker will
         ## stop moving in out of bounds direction

         if (x_values[i] <= mark_bound and look_x[i] <= mark_bound) or (
                 x_values[i] >= x_boundary - mark_bound and look_x[i] >= x_boundary - mark_bound):
            xspeeds[i] = 0
            if (x_values[i] <= mark_bound and look_x[i] <= mark_bound):
               canvas.moveto(guidance[i], -mark_bound / 2, y_values[i] - mark_bound / 2)
               canvas.moveto(dist[i], text_x, y_values[i] + text_y)
               if (not right_lit and obs_labels[i] == 'danger' and warning_visible) or (not right_lit and obs_labels[i] != 'danger'):
                  light_right(dots, light_dict[obs_labels[i]])
                  right_lit = True
            else:
               canvas.moveto(guidance[i], x_boundary - mark_bound / 2, y_values[i] - mark_bound / 2)
               canvas.moveto(dist[i], x_boundary + text_x, y_values[i] + text_y)
               if (not left_lit and obs_labels[i] == 'danger' and warning_visible) or (not left_lit and obs_labels[i] != 'danger'):
                  light_left(dots, light_dict[obs_labels[i]])
                  left_lit = True
                          ## Otherwise it will gradually speed up and slow down with distance
         else:
            xspeeds[i] = (look_x[i] - x_values[i]) / 50
            if not right_lit and not left_lit: 
               dots.fill((0,0,0))
            elif right_lit:
                light_left(dots, (0,0,0))
            elif left_lit:
                light_right(dots, (0,0,0))
         ## if the point to get to is outside of vertical boundaries then marker will
         ## stop moving in out of bounds direciton
         if (y_values[i] <= mark_bound and look_y[i] <= mark_bound) or (
                 y_values[i] >= y_boundary - mark_bound and look_y[i] >= y_boundary - mark_bound):
            yspeeds[i] = 0
            if (y_values[i] <= mark_bound and look_y[i] <= mark_bound):
               canvas.moveto(guidance[i], x_values[i] - mark_bound / 2, -mark_bound / 2)
               canvas.moveto(dist[i], x_values[i] + text_x, text_y)
            else:
               canvas.moveto(guidance[i], x_values[i] - mark_bound / 2, y_boundary - mark_bound / 2)
               canvas.moveto(dist[i], x_values[i] + text_x, y_boundary + text_y)
         ## Otherwise it will gradually speed up and slow down with distance
         else:
            yspeeds[i] = (look_y[i] - y_values[i]) / 50

         ## Old code that had issues with bounding and would not move once hitting
         ## the boundary wall

         # if (((100 < marker_x < x_boundary - 100) and not (look_x -3 < marker_x < look_x + 3)) or
         #    ((100 < marker_y < y_boundary - 100) and not (look_y -3 < marker_y < look_y + 3))):
         #       # move the image
         #       canvas.move(guidance, xspeed, yspeed)
         #       canvas.move(obj_dist, xspeed, yspeed)
         #       marker_x = marker_x + xspeed
         #       marker_y = marker_y + yspeed
         #       # if marker_x > x_boundary - 100:
         #       #    marker_x = x_boundary - 100
         #       # elif marker_x < 100:
         #       #    marker_x = 100
         #       # if marker_y > y_boundary - 100:
         #       #    marker_y = y_boundary - 100
         #       # elif marker_y < 100:
         #       #    marker_y = 100

         #       x_pos.configure(text = f'current x value: {marker_x}')
         #       y_pos.configure(text = f'current y value: {marker_y}')

         if ((mark_bound - edge_margin <= x_values[i] <= x_boundary - mark_bound + edge_margin) and not (
                 look_x[i] - 5 < x_values[i] < look_x[i] + 5)):
            # move image in x direction
            canvas.move(guidance[i], xspeeds[i], 0)
            canvas.move(dist[i], xspeeds[i], 0)
            (leftPos, topPos, rightPos, bottomPos) = canvas.bbox(guidance[i])
            x_values[i] = (leftPos + rightPos) / 2
         elif x_values[i] > x_boundary - mark_bound:
            x_values[i] = x_boundary - mark_bound
         elif x_values[i] < mark_bound:
            x_values[i] = mark_bound

         if ((mark_bound <= y_values[i] <= y_boundary - mark_bound) and not (look_y[i] - 5 < y_values[i] < look_y[i] + 5)):
            # move image in x direction
            canvas.move(guidance[i], 0, yspeeds[i])
            canvas.move(dist[i], 0, yspeeds[i])
            (leftPos, topPos, rightPos, bottomPos) = canvas.bbox(guidance[i])
            y_values[i] = (topPos + bottomPos) / 2
         elif y_values[i] > y_boundary - mark_bound:
            y_values[i] = y_boundary - mark_bound
         elif y_values[i] < mark_bound:
            y_values[i] = mark_bound

       #  canvas.after(refresh_rate, moveMark)
   else:
      for i in range(len(guidance)):
         canvas.moveto(guidance[i], -2*mark_bound, y_boundary/2)
            #canvas.moveto(obj_dist, -marker_size, y_boundary/2)
        #    canvas.after(5, moveMark)
      canvas.itemconfigure(object_name, text='')
      canvas.itemconfigure(object_description, text='')
   canvas.after(refresh_rate, moveMark)


def move_app(event):
    window.geometry(f'+{event.x_root}+{event.y_root}')


window = tk.Tk()
canvas = tk.Canvas(window,width=x_boundary,height=y_boundary, bg='black', bd=0, highlightthickness=0)
canvas.pack()
canvas.tab = [{} for q in range(50)]
canvas.focus_set()

#Load an image in the script
img = (Image.open("destiny_marker.png"))
blue = (Image.open("marker_blue.png"))
green = (Image.open("marker_green.png"))
red = (Image.open("marker_red.png"))
yellow = (Image.open("marker_yellow.png"))
black = (Image.open("clear.png"))
#Resize the Image using resize method
marker_img = img.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)
marker_blue = blue.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)
marker_green = green.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)
marker_red = red.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)
marker_yellow = yellow.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)
marker_black = black.resize((mark_bound,mark_bound), Image.Resampling.LANCZOS)

icons = {'path' : marker_img, 'good' : marker_blue, 'danger' : marker_red, 'investigate': marker_yellow, 'path_end' : marker_green, 'black': marker_black}
#icon_value = 0
icons1 = {'path': img, 'good': blue, 'danger': red, 'investigate': yellow, 'path_end': green}
icon_meanings = {'good': 'Blue = Supply Drop', 'danger': 'Red = Possible bomb', 'investigate': 'Yellow = Enemy Camp'}
tmp = read_csv_obs(obs_filename)
icon_values = tmp[2]
icon_start = 130
print(icon_values)

for i in range(len(icon_values)):
   canvas.tab[num]['image'] = ImageTk.PhotoImage(icons[icon_values[i]])
   guidance.append(canvas.create_image(-mark_bound,y_boundary/2, image=canvas.tab[num]['image'], anchor='center'))
   dist.append(canvas.create_text(-mark_bound+text_x, y_boundary/2+text_y, text=f'{tmp[1][i]} m', font='SegoeUI 16',fill='white', anchor='nw'))
   if icon_values[i] != 'path':
      canvas.create_text(50, 130+(i-1)*20, text=icon_meanings[icon_values[i]], font='SegoeUI 20', fill='white', anchor='nw')
   x_values.append(0)
   y_values.append(0)
   look_x.append(0)
   look_y.append(0)
   xspeeds.append(0)
   yspeeds.append(0)
   num += 1

# photoimage = ImageTk.PhotoImage(marker_img)
# guidance = canvas.create_image(x_start,y_start,image=photoimage,anchor='center')

#canvas.create_text(3, 120, text=f'test skull: {distance}', font='SegoeUI 13',fill='black', anchor='nw')

if is_display:
   window.overrideredirect(True)
   title_bar = tk.Frame(window, bg='green', bd=0)
   title_bar.pack(expand=1, fill=tk.X)
   title_bar.bind("<B1-Motion>", move_app)
   title_label = tk.Label(title_bar, text="hello", bg='black')
   title_label.pack(side=tk.LEFT)
   close_button = tk.Button(window, text="x", font="Helvetica, 8", command=window.quit)
   close_button.pack(pady=10)


object_name = canvas.create_text(50, 50, text=disp_name, font='SegoeUI 24',fill='white', anchor='nw')
object_description = canvas.create_text(50, 90, text='',
                                        font='SegoeUI 24',fill='white', anchor='nw')
canvas.after(refresh_rate, moveMark)
window.mainloop()

atexit.register(exit_func)
