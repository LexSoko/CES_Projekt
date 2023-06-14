import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt
import os 

path = os.getcwd()

data = pd.read_csv(path + "\\Rotary Encoder\\loadcell_csv_data\\resolution_test.csv",delimiter=";")

time = data["time"]/1e6
weight = data["weight"]
plt.plot(time[269:],weight[269:], "b-", label="weight")
plt.legend()
plt.show()
