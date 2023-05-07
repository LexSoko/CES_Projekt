import numpy as np
import matplotlib.pyplot as plt

g = 9.81                        # m/s**2    erdbeschleunigung


###########  Hauptachsenberechnung  #######
f_max = 1000 / 60               # U/s       maximale hauptachsendrehzahl
b_Spu_ges = 0.02                # m         Spulenbreite

# für ärgste wickelart (sinuscoil)
"""linearführungs verschub m"""
z_D = lambda t : (b_Spu_ges/2) * np.sin(2*np.pi*f_max * t)
"""linearführungs beschleunigung m/s**2"""
a_z_D_t = lambda t : (b_Spu_ges/2) * (2*np.pi*f_max)**2 * np.sin(2*np.pi*f_max * t)

###########  Linearführungstisch  #########
m_T = 1                         # kg        masse tisch
µ_LF = 0.1                      # N/N       reibung linearführung

"""Reibungskraft linearführung N"""
F_R_Tg = µ_LF * m_T * g

"""Tischbeschleunigungskraft N"""
F_T_t = lambda t: m_T * a_z_D_t(t)

###############     Spindel      ###########
µ_Sp = 0.1                      # N/N       reibung spindel
alpha_Sp = 6                    # °         steigungswinkel spindel
R_Sp = 0.004                    # m/°       steigung Spindel

                                # N/N       wirkungsgrad Spindel
eta_Sp = (1 - µ_Sp * np.tan(alpha_Sp)) / (1 + (µ_Sp / np.tan(alpha_Sp)))

"""gesamtkraft auf spindel N"""
F_T_ges_t = lambda t: F_T_t(t) + F_R_Tg

"""gesamtdrehmoment auf Spindel Nm"""
M_Sp_t = lambda t: (F_T_ges_t(t) / eta_Sp) * (R_Sp/2*np.pi)


############## Calculations ###############
N_data = 100
period = 1/f_max

# calc momentum function from time
t_arr = np.linspace(0,period,N_data)
M_Sp_arr = M_Sp_t(t_arr)

# calc RMS of Momentum signal: simply a convolution over one period
#M_Sp_RMS = np.sqrt(np.convolve(np.power(M_Sp_arr,2), np.ones(N_data)/float(N_data), 'valid'))  # works only for continious RMS calculation
M_Sp_RMS = np.sqrt(np.sum(np.power(M_Sp_arr,2))/float(N_data))
M_Sp_Amp = np.max(np.abs(M_Sp_arr))

fig_t = plt.figure(figsize=(6,4))
ax_M_t = fig_t.add_subplot(1,1,1)
ax_M_t.plot(t_arr,M_Sp_arr,
            label=r"$M_{Sp}(t)$"+"\n"+
            r"$M_{Sp,RMS}$ ="+"{:.2f}".format(M_Sp_RMS*100)+" Ncm\n"+
            r"$M_{Sp,Amp}$ ="+"{:.2f}".format(M_Sp_Amp*100)+" Ncm"
            )
ax_M_t.set_xlabel(r"$t$ / s")
ax_M_t.set_ylabel(r"$M$ / Nm")
ax_M_t.legend()



# calc frequency dependence
f_arr = np.linspace(0,f_max,100)
N_data = 100
M_list_RMS = []
M_list_Amp = []
for f in f_arr:
    f_max = f
    period = 1/f_max
    
    t_arr = np.linspace(0,period,N_data)
    M_Sp_arr = M_Sp_t(t_arr)
    
    M_Sp_RMS = np.sqrt(np.sum(np.power(M_Sp_arr,2))/float(N_data))
    M_Sp_Amp = np.max(np.abs(M_Sp_arr))
    
    M_list_RMS.append(M_Sp_RMS)
    M_list_Amp.append(M_Sp_Amp)

M_Sp_f_RMS_arr = np.array(M_list_RMS)
M_Sp_f_Amp_arr = np.array(M_list_Amp)

fig_f = plt.figure(figsize=(6,4))
ax_M_f = fig_f.add_subplot(1,1,1)
ax_M_f.plot(f_arr*60,M_Sp_f_RMS_arr,label=r"$M_{Sp,RMS}(f)$")
ax_M_f.plot(f_arr*60,M_Sp_f_Amp_arr,label=r"$M_{Sp,Amp}(f)$")
ax_M_f.set_xlabel(r"$f$ / U/min")
ax_M_f.set_ylabel(r"$M$ / Nm")
ax_M_f.legend()
plt.show()
