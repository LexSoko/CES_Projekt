import data_acquisition as daq
import pandas as pd 
import os 
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
import numpy as np
#returns current directory
path = os.getcwd()
loadcell_raw_ls = []
loadcell_timeVal_ls = []
loadcell_converted_ls = []
doit = True
max_data_points = 1000
WORK_COMMAND = 0x80
CALIBRATION_COMMAND = 0xC0
SYNC_COMMAND = 0xE0

arduino = daq.serial_mma_data_stream("COM6", 57600,16384,177)  

def work():
    arduino.send_command(WORK_COMMAND)
def calibrate():
    arduino.send_command(CALIBRATION_COMMAND)
def sync():
    arduino.send_command(SYNC_COMMAND)
#root = tk.Tk()
#root.geometry('600x400')
#root.resizable(False, False)
#root.title('Button Demo')
#button_work = tk.Button(root,text="work", command= work)
#button_calibrate = tk.Button(root,text="calibrate", command= calibrate)
#button_sync = tk.Button(root,text="sync", command= sync)

    
if doit == True:
    i=0
    while i<max_data_points:


        #data = arduino.get_next_loadcell()
        #if(data is not None):
        #    (loadcell_raw,loadcell_timeVal,val3,bool) = data 
        #    if bool:
    #   # print(rot_pos,";",timeVal,";",''.join(format(x, '02x') for x in databyt))
        #        print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:", ''.join(format(x, '02x') for x in val3))


        data = arduino.get_next_loadcell()
        if (data is None):
            print("Data is None")
        if(data is not None):
            print("Data is not None")
            (loadcell_raw,loadcell_timeVal,val3,bool) = data 
            if bool:
    
                print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:", ''.join(format(x, '02x') for x in val3))


            else:
                loadcell_raw_ls.append(loadcell_raw)
                loadcell_timeVal_ls.append(loadcell_timeVal)
                if ((i%100)==0):
                    print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:",  ''.join(format(x, '02x') for x in val3),"i",i)
                print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:",  ''.join(format(x, '02x') for x in val3),"i",i)

                i += 1
       

       






for r in loadcell_raw_ls:
    loadcell_converted_ls.append((r - arduino.offset)*arduino.calibration_factor)
save_data = False
if save_data == True:
    loadcell_csv = pd.DataFrame([loadcell_timeVal_ls,loadcell_converted_ls]).T
    loadcell_csv.to_csv(path + "\\Rotary Encoder\\loadcell_csv_data\\resolution_test_300s.csv", sep= ";")


plot = True
if plot ==True:    
    plt.scatter(np.array(loadcell_timeVal_ls)/1e6,loadcell_raw_ls)

    plt.show()
    plt.cla()
    plt.plot(np.array(loadcell_timeVal_ls)/1e6,loadcell_converted_ls, "b-",label= f"calibration_factor={arduino.calibration_factor},offset={arduino.offset}" )
    plt.legend(loc="best")
    plt.show()
