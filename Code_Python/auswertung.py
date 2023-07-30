import os
from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from scipy.fft import rfft, rfftfreq
from scipy.fft import fft, fftfreq

graphicsdir="Gesamtdoku/graphics/"
dirname = "winder_measurements/auswertung/"
filename = {
    "mess1":"zyl_50_25_no_spring.csv",
    "mess2":"zyl_50_25_yes_spring.csv",
    "mess3":"quad_50_no_spring_strong_tens.csv",
    "mess4":"quad_50_yes_spring_strong_tens.csv",
    "mess5":"quad_50_yes_spring_weak_tens.csv",
}

df_dict = {key:pd.read_csv(dirname+filen,sep=";",dtype={"m":str,"millis":int,"step_ha":float,"step_la":float,"load":float}
    ) for (key,filen) in filename.items()}

##### functions #######

# maps values like the arduino standard lib function map()
map_arduino = lambda x, in_min, in_max, out_min, out_max:(x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

# calculates numerical derivative
def calc_deriv(y_arr,x_arr,di_x):
    #di_x must be integer and half of the dx index shift
    dy = np.roll(y_arr,2*di_x) - y_arr
    dx = np.roll(x_arr,2*di_x) - x_arr
    return np.roll((dy / dx),-di_x)

# simple dataframe row filter
def filter_df(df:pd.DataFrame, key:str, min_val:float=None, max_val:float=None) -> pd.DataFrame:
    if min is not None and max is not None:
        return df.drop(df[np.logical_or(df[key] < min_val , df[key] > max_val)].index, inplace = False)
    else:
        return None

# standard error of mean
def calc_unsicherheit(data):
    data.sem()


# dateninterpolation auf constante Zeit für fft
def interpol(df, time_intervall):
    d = df.set_index('millis')
    t = d.index
    r = pd.Index(np.arange(df["millis"].min(),df["millis"].max(),time_intervall), name=t.name)
    return df.set_index('millis') \
            .reindex(t.union(r))\
                .interpolate('index')\
                    .loc[r]\
                        .reset_index()


##### allgemeine berechnungen  #####
latex_dict = {
    "F_WZ":r"$F_{WZ}$ / mN",    #N
    "phi_HA":r"$\varphi_{HA}$ / °",   #degrees
    "phi_NA":r"$\varphi_{NA}$ / °",
    "omeg_HA":r"$\omega_{HA}$ / ° s$^{-1}$",   #degrees / millis
    "omeg_NA":r"$\omega_{NA}$ / ° s$^{-1}$",
    "alph_HA":r"$\alpha_{HA}$ / ° s$^{-2}$",   #degrees / (millis)^2
    "alph_NA":r"$\alpha_{NA}$ / ° s$^{-2}$",
    "amp":r"Amplitude $F_{WZ}(f)$ / willkürliche Einheiten",
    "freq":r"$f$ / Hz",
}

for meas in df_dict.values():
    meas["F_WZ"] = map_arduino(meas["load"],11439.0,330913.0,0.0,177.0) *  9.81 # scale values where 11439 at no load
                                                                            # and 330913 at the wheight of a one plus 6 phone (177 g)
                                                                            # weight acuraccy of the phone is estimated with pm 0.5 g

    meas["phi_HA"] = meas["step_ha"] * (360.0/1600.0)                       # one stepper revolution is 1600 steps (200 * 8)
    meas["phi_NA"] = meas["step_la"] * (360.0/1600.0) 

    meas["omeg_HA"] = calc_deriv(meas["phi_HA"],meas["millis"],1)           # winkelgeschwindigkeit
    meas["omeg_NA"] = calc_deriv(meas["phi_NA"],meas["millis"],1)

    meas["alph_HA"] = calc_deriv(meas["omeg_HA"],meas["millis"],1)          # winkelbeschleunigung
    meas["alph_NA"] = calc_deriv(meas["omeg_NA"],meas["millis"],1)


# zeiten konstanter geschwindigkeit 
t_intervals_const_speed = {
    "50_no_spring":[47000,75500],
    "25_no_spring":[133500,173000],
    "50_yes_spring":[57500,87000],
    "25_yes_spring":[203000,242000],
    "quad_no_spring":[135000,199000],
    "quad_yes_spring":[90000,140000],
}

df_const_speed_no_spring_50 = filter_df(df_dict["mess1"],"millis",t_intervals_const_speed["50_no_spring"][0],t_intervals_const_speed["50_no_spring"][1])
df_const_speed_no_spring_25 = filter_df(df_dict["mess1"],"millis",t_intervals_const_speed["25_no_spring"][0],t_intervals_const_speed["25_no_spring"][1])
df_const_speed_yes_spring_50 = filter_df(df_dict["mess2"],"millis",t_intervals_const_speed["50_yes_spring"][0],t_intervals_const_speed["50_yes_spring"][1])
df_const_speed_yes_spring_25 = filter_df(df_dict["mess2"],"millis",t_intervals_const_speed["25_yes_spring"][0],t_intervals_const_speed["25_yes_spring"][1])
df_const_speed_no_spring_50_quad = filter_df(df_dict["mess3"],"millis",t_intervals_const_speed["quad_no_spring"][0],t_intervals_const_speed["quad_no_spring"][1])
df_const_speed_yes_spring_50_quad = filter_df(df_dict["mess4"],"millis",t_intervals_const_speed["quad_yes_spring"][0],t_intervals_const_speed["quad_yes_spring"][1])



##### auswertung 1 const speed zylinderspule für 25 und 50 speed und für mit und ohne feder
# calc mean Fs
F_m_50_no = df_const_speed_no_spring_50["F_WZ"].mean()
F_m_25_no = df_const_speed_no_spring_25["F_WZ"].mean()
F_m_50_yes = df_const_speed_yes_spring_50["F_WZ"].mean()
F_m_25_yes = df_const_speed_yes_spring_25["F_WZ"].mean()

F_u_50_no = df_const_speed_no_spring_50["F_WZ"].std()
F_u_25_no = df_const_speed_no_spring_25["F_WZ"].std()
F_u_50_yes =df_const_speed_yes_spring_50["F_WZ"].std()
F_u_25_yes =df_const_speed_yes_spring_25["F_WZ"].std()

# calc mean phis
omeg_m_50_no = df_const_speed_no_spring_50["omeg_HA"].mean()
omeg_m_25_no = df_const_speed_no_spring_25["omeg_HA"].mean()
omeg_m_50_yes = df_const_speed_yes_spring_50["omeg_HA"].mean()
omeg_m_25_yes = df_const_speed_yes_spring_25["omeg_HA"].mean()

omeg_u_50_no =  df_const_speed_no_spring_50["omeg_HA"].std()
omeg_u_25_no =  df_const_speed_no_spring_25["omeg_HA"].std()
omeg_u_50_yes = df_const_speed_yes_spring_50["omeg_HA"].std()
omeg_u_25_yes = df_const_speed_yes_spring_25["omeg_HA"].std()


#fig_const = plt.figure(figsize=(9,9))
#ax_const = fig_const.add_subplot()
#
#ax_const.scatter(df_const_speed_no_spring_50["omeg_HA"],df_const_speed_no_spring_50["F_WZ"],c="red",alpha=0.05)
#ax_const.scatter(df_const_speed_no_spring_25["omeg_HA"],df_const_speed_no_spring_25["F_WZ"],c="red",alpha=0.05)
#ax_const.scatter(df_const_speed_yes_spring_50["omeg_HA"],df_const_speed_yes_spring_50["F_WZ"],c="green",alpha=0.05)
#ax_const.scatter(df_const_speed_yes_spring_25["omeg_HA"],df_const_speed_yes_spring_25["F_WZ"],c="green",alpha=0.05)
#
#ax_const.errorbar(omeg_m_50_no, F_m_50_no, xerr=omeg_u_50_no, yerr =F_u_50_no, label="no spring", c="red")
#ax_const.errorbar(omeg_m_25_no, F_m_25_no, xerr=omeg_u_25_no, yerr =F_u_25_no, label="no spring", c="red")
#ax_const.errorbar(omeg_m_50_yes, F_m_50_yes, xerr=omeg_u_50_yes, yerr =F_u_50_yes, label="with spring" ,c="green")
#ax_const.errorbar(omeg_m_25_yes, F_m_25_yes, xerr=omeg_u_25_yes, yerr =F_u_25_yes, label="with spring" ,c="green")
#
#ax_const.set_xlabel(latex_dict["omeg_HA"])
#ax_const.set_ylabel(latex_dict["F_WZ"])
#ax_const.legend()
#ax_const.grid()
#
#
#fig_const.savefig(graphicsdir+"const_speed.pdf",dpi="figure")


##### auswertung 2 ffts für auswirkungen feder
# datensätze:
#  mess1 und 2 mit speed 50
TIME_INTERVAL_INTERPOL = 12.5           #ms
zyl_no__fed = interpol(df_const_speed_no_spring_50,TIME_INTERVAL_INTERPOL)
zyl_yes_fed = interpol(df_const_speed_yes_spring_50,TIME_INTERVAL_INTERPOL)
quad_no__fed = interpol(df_const_speed_no_spring_50_quad,TIME_INTERVAL_INTERPOL)
quad_yes_fed = interpol(df_const_speed_yes_spring_50_quad,TIME_INTERVAL_INTERPOL)


fig_ffts = plt.figure(figsize=(9,9))
legenden = ["zyl. ohne Feder","zyl. mit Feder","quad. ohne Feder","quad. mit Feder"]

for i,df in enumerate([zyl_no__fed, zyl_yes_fed, quad_no__fed, quad_yes_fed]):
    N = len(df.index)
    df["amp"] = abs(fft(df["F_WZ"].values))
    df["amp"] = df["amp"] / df["amp"].max()

    df["freq"] = fftfreq(N, TIME_INTERVAL_INTERPOL/1000)

    ax_ffts = fig_ffts.add_subplot(221+i)
    ax_ffts.plot(df["freq"],df["amp"],label=legenden[i])


    ax_ffts.set_xlabel(latex_dict["freq"])
    ax_ffts.set_ylabel(latex_dict["amp"])
    ax_ffts.set_xlim(0,10)
    ax_ffts.set_ylim(0,0.1)
    ax_ffts.legend()


fig_ffts.savefig(graphicsdir+"ffts.pdf",dpi="figure")


#ax_ffts.set_xlabel(latex_dict["omeg_HA"])
#ax_ffts.set_ylabel(latex_dict["F_WZ"])
#ax_ffts.set_xlimit(0,10)
#ax_ffts.legend()
#ax_ffts.grid()






#  mess3 und 4 mit speed 50 


# daten interpolieren

#plt.show()