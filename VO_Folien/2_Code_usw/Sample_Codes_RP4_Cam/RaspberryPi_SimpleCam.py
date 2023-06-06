###############################################################################
#
# Organization: University of Graz
# Department Institute of Physics
# Group: OPNAQ - 
# Programmer: Jan Enenkel
# Date: 21.3.2023
# 
# Program Description 
# Raspberry Pi 4 HQ Camera - Simple Sampling
#
# Simple Sample code to take some image data and show it onto the screen.
###############################################################################

#Imports 
from picamera import PiCamera
import gc
import time
import numpy as np
import matplotlib.pyplot as plt

from skimage.io import imread, imshow
from skimage.color import rgb2hsv, rgb2gray, rgb2yuv
from skimage import color, exposure, transform

print("Initalizing Camera!");

camera = PiCamera();                            # generate instance of Camera
camera.resolution=(640, 480);                   # set camera resolution to 640x480 (mainly because its faster)
camera.framerate = 30;                          # camera set to 30FPS
time.sleep(1.0);                                # give camera some time to adjust to settings
print("Camera Initialized:",camera);

plt.figure(num=None, figsize=(8, 6), dpi=80)
image = np.empty((640, 480, 3), dtype=np.uint8);        # reserve some memory 

while True:                                             # infinite loop
    camera.capture( image , format = 'rgb' );           # sample an image
    image =  image.reshape( (480,640,3) );              # reshape to 480x640 because of plt data arrangement
    plt.imshow( image );                                # load data (in color)
    plt.draw();                                         # draw plt
    plt.pause(0.001);                                   # short wait
    gc.collect();                                       # perform garbage collection
    plt.clf();                                          # clear plot to avoid overloading memory
    image =  image.reshape( (640,480,3) );              # reshape for next sample (not sure if needed)

print("Closing camera:",camera);
camera.close();
plt.close();