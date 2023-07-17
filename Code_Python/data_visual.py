import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import os 
import tkinter as tk

path = os.getcwd()

window_coilwinder = tk.Tk()
window_coilwinder.title("Coilwinder Serial Monitor")
window_coilwinder.mainloop()


















matplot = False
if matplot == True:    
    data = pd.read_csv(path + "\\Rotary Encoder\\loadcell_csv_data\\resolution_test_300s.csv",delimiter=";")

    time = data["time"][1079:]/1e6
    weight = data["weight"][1079:]
    weight_avg = np.mean(weight)
    weight_std = np.std(weight)
    print("weight_avg:",weight_avg, "weight_std:", weight_std)
    plt.hist(weight, 200)
    plt.show()
    plt.cla()

    plt.plot(time[1079:],weight[1079:], "b-", label="weight")
    plt.legend()
    plt.show()
