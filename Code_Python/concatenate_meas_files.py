import os
from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np

def concat_to_new_file(dir:str, new_filename:str):
    #dirname = "winder_measurements/07-29-2023/"
    directory_name = dir
    filenames = [name for name in os.listdir(directory_name)]
    filtered_names = [n for n in filenames if re.search("meas", n) ]
    #new_filename = directory_name+"first_coil_concat.csv"
    new_filename = directory_name + new_filename
    
    df = pd.concat((pd.read_csv(directory_name+filename) for filename in filtered_names))

    df.to_csv(Path(new_filename),index=False)

concat_to_new_file("winder_measurements/07-29-2023/","test_name.csv")

df = pd.read_csv("winder_measurements/07-29-2023/"+"test_name.csv",sep=";",dtype={
    "m":str,
    "millis":int,
    "step_ha":float,
    "step_la":float,
    "load":int})
print(df)
df["deg_HA"] = 2 * np.pi * (df["step_ha"] % 1600) / 1600.0      # 1600 steps per full rotation
df["mm_LA"] = df["step_ha"] / 1600.0                        # 1 mm per rotation spindle

def map_arduino(x, in_min, in_max, out_min, out_max):
    """ map like in the arduino standard library"""
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min
df["mN_load"] = map_arduino(df["load"],11439,330913,0.0,177.0) *  9.81  # scale values where 11439 at no load
                                                                        # and 330913 at the wheight of a one plus 6 phone (177 g)
                                                                        # weight acuraccy of the phone is estimated with pm 0.5 g

# derivation function / Inertia functions
def calc_deriv(y_arr,x_arr,di_x):
    #di_x must be integer and half of the dx index shift
    dy = np.roll(y_arr,2*di_x) - y_arr
    dx = np.roll(x_arr,2*di_x) - x_arr
    return np.roll((dy / dx),-di_x)


df["deg_s_HA"] = calc_deriv(df["deg_HA"],df["millis"],3)  *1000    # 1600 steps per full rotation
df["mm_s_LA"] = calc_deriv(df["mm_LA"],df["millis"],3) *1000                        # 1 mm per rotation spindle

df["s"] = df["millis"] / 1000

r = 5
df["x"] = r * np.cos(df["deg_HA"])
df["z"] = r * np.sin(df["deg_HA"])

#df.plot.scatter(x="s",y="deg_s_HA")
#df.plot.scatter(x="s",y="mm_s_LA")
#df.plot.scatter(x="s",y="deg_HA")
#df.plot.scatter(x="s",y="mm_LA")
#df.plot.scatter(x="s",y="mN_load")

df.plot.scatter(x = "deg_s_HA",y="mm_s_LA",s=map_arduino(df["mN_load"],df["mN_load"].min(),df["mN_load"].max(), 1, 10),c=df["mN_load"],cmap="viridis_r")

fig1= plt.figure()
ax1 = fig1.add_subplot(projection='3d')
ax1.scatter(df["s"],df["mm_s_LA"],df["mN_load"],s=map_arduino(df["mN_load"],df["mN_load"].min(),df["mN_load"].max(), 1, 10),c=df["mN_load"],cmap="viridis_r")
ax1.set_xlabel("s")
ax1.set_ylabel("mm/s")
ax1.set_zlabel("mN")

fig2= plt.figure()
ax2 = fig2.add_subplot(projection='3d')
ax2.scatter(df["x"],df["mm_LA"],df["z"],s=map_arduino(df["mN_load"],df["mN_load"].min(),df["mN_load"].max(), 1, 10),c=df["mN_load"],cmap="viridis_r")
ax2.set_xlabel("mm x")
ax2.set_ylabel("mm y")
ax2.set_zlabel("mm z")
plt.show()