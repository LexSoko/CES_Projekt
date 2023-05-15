###############################################################################
#
# Organization: University of Graz
# Department Institute of Physics
# Group: OPNAQ - 
# Programmer: Jan Enenkel
# Date: 21.3.2023
# 
# Program Description 
# Raspberry Pi 4 HQ Camera - Simple Sampling with FFT
#
# Simple Sample code to take some image data and perform an FFT
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
camera = PiCamera();
camera.resolution=(640, 480);
camera.framerate = 30;
time.sleep(1.0);
print("Camera Initialized:",camera);
fig, (ax1,ax2) = plt.subplots(1,2);
image = np.empty((640, 480, 3), dtype=np.uint8);
grey_image = np.empty((640, 480), dtype=np.uint8);
image_fft = np.empty((640, 480), dtype=np.uint8);

while True:
    camera.capture( image , format = 'rgb' );
    image =  image.reshape( (480,640,3) );
    grey_image = rgb2gray(image);                                                   # convert RGB Image to greyscale
    image_fft = np.log(abs((np.fft.fftshift( np.fft.fft2( grey_image )))));         # perform FFT of image
    
    ax1.imshow(grey_image , cmap='gray');                                           # load grey image (with grey colormap)
    ax1.set_title("Original Image");

    ax2.imshow( image_fft, cmap='gray');                                            # load FFT image (with grey colormap)
    ax2.set_title("FFT Image");

    plt.draw();                                                                     # draw
    plt.pause(0.001);                                                               # short delay
    gc.collect();                                                                   # garbage collect
    ax1.cla();                                                                      # clear memory of plt to avoid getting slower
    ax2.cla();                                                                      # clear memory of plt to avoid getting slower

print("Closing camera:",camera);
camera.close();
plt.close();