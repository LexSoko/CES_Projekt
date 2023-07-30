import os
from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.fft import fft, fftfreq

graphicsdir="Gesamtdoku/graphics/"
filename = "winder_measurements/auswertung/abriss.csv"

# simple dataframe row filter
def filter_df(df:pd.DataFrame, key:str, min_val:float=None, max_val:float=None) -> pd.DataFrame:
    if min is not None and max is not None:
        return df.drop(df[np.logical_or(df[key] < min_val , df[key] > max_val)].index, inplace = False)
    else:
        return None

df = filter_df(pd.read_csv(filename,sep=";",dtype={"m":str,"millis":int,"step_ha":float,"step_la":float,"load":float}),"millis",100000,120000)

fig = plt.figure(figsize=(9,9))

ax_step_HA = fig.add_subplot(311)
ax_step_HA.scatter(df["millis"], df["step_ha"], s = 1)
ax_step_HA.set_ylabel("stepcount HA")
ax_step_HA.set_xlabel("t / ms")

ax_step_NA = fig.add_subplot(312,sharex=ax_step_HA)
ax_step_NA.scatter(df["millis"], df["step_la"],label="stepcount NA", s = 1)
ax_step_NA.set_ylabel("stepcount NA")

ax_load = fig.add_subplot(313,sharex=ax_step_HA)
ax_load.scatter(df["millis"], df["load"], s = 1)
ax_load.set_ylabel("rohwerte Wägezelle")



fig.savefig(graphicsdir+"roh.pdf",dpi="figure")