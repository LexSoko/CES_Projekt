import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# boundary parameters
f_max = 16                                              #Hz   Maximalfrequenz (also am start des Wickelprozesses)

# machine parameters
h_well  = 0.4                                           #m  länge Welle
r_well  = 0.005                                         #m  Wellenradius

rho_well = 7874.0                                       #kg/m**3 Dichte Wellenmaterial
I_0_Well = 0.5* rho_well* h_well*np.pi*r_well**4        #kgm^2 Trägheitsmoment Welle

# coil body/winding parameters  (Zylinderspule)
r_min = 0.075                                           #m Radius Spulenkern
h_Sp = 0.02                                             #m Spulenhöhe in Drehachsenrichtung
d_Dr = 0.0001                                           #m Drahtdurchmesser

sig = 0.00007                                           #kg/m längen Dichte Draht only copper for 0.1 mm wire
rho_Sp = 7874.0                                         #kg/m**3 Volumsdichte Spulenkörper
m_0_Sp = rho_Sp * h_Sp * np.pi * r_min**2               #kg Masse Spulenkörper
I_0_sp = 0.5* m_0_Sp * r_min**2                         #kgm^2 Trägheitsmoment Spulenkörper

N_Wind = 5000                                           #1 Anzahl an Wicklungen
N_Wk_L = int(np.floor(h_Sp / d_Dr))                     #1 Anzahl an Wicklungen pro Lage
N_lines = int(np.ceil(N_Wind/N_Wk_L))                   #1 Anzahl Lagen gesamt

# Wire parameters
v_Dr = f_max * ( r_min + d_Dr/2) * 2 * np.pi            #m/s konstante Drahtflussgeschwindigkeit
F_T = 15                                                #N Drahttension

# Winding functions
def r_n(n):                                             #m Wickelradius nter Lage
    return r_min + d_Dr/2 + n*d_Dr

def tau_n(n):                                           #s Wickeldauer nte Lage
    return N_Wk_L * 2 * np.pi * r_n(n) / v_Dr

def tau_n_Wk(n):                                        #s Wickeldauer wicklung in nter Lage
    return 2 * np.pi * r_n(n) / v_Dr

def I_Wk(r):                                            #kgm^2 Trägheitsmoment Wicklung abh. von Wickelradius r
    return sig*2*np.pi* r *(6 * d_Dr**2 + r**2)


### calculation procedure
"""#############        Coil dependend         #############"""
# calc n dependencies
n_arr = np.arange(N_lines)                              #1 Lagen
n_Wk_arr = np.arange(N_lines * N_Wk_L)                  #1 Wicklungen

r_n_arr = r_n(n_arr)                                    #m Wickelradien
Tau_n_arr = tau_n(n_arr)                                #s Lagenwickeldauern
Tau_n_Wk_arr = tau_n_Wk(n_arr)                          #s Wicklungswickeldauern
I_Wk_n = I_Wk(r_n_arr)                                  #kgm^2 Trägheitsmomente

# calc time dependencies
timesteps = N_Wind *2                                   #1 anzahl zeitpunkte mind 2 pro Wicklung
Tau_ges = np.sum(Tau_n_arr)                             #s gesamtwickeldauer 
t_arr = np.linspace(0,Tau_ges,timesteps)                #s Zeit array
t_step = t_arr[1]-t_arr[0]                              #s Zeitintervall

#                                                       Laufvariablen:
n_curr = 0                                              #1 Lage
n_Wk_curr = 0                                           #1 Wicklung
n_Wk_L_curr = 0                                         #1 Wicklung in akt. Lage
I_Wk_Line = 0                                           #kgm^2 Trägheitsmoment von schon fertigen Lagen
I_Wk_curr = 0                                           #kgm^2 Trägheitsmoment von letzter Wicklung
Tau_prev = 0.0                                          #s Zeitpunkt letzter Lagenwechsel

#                                                       dem entsprechend aufzufüllende listen:
n_t = []
n_Wk_t = []
n_Wk_L_t = []
r_t = []
I_Sp_t = []

for (i_t,t_curr) in enumerate(t_arr):                   # schleife über Zeitpunkte

    #Zeitpunkt nächster Lagenwechsel
    Tau_next = np.sum(Tau_n_arr[0:n_curr+1])

    #Ist Lagenwechsel jetzt?
    if(t_curr > Tau_next):
        # Trägheitsmoment von schon gewickelten Lagen
        # achtung is ein pfusch hack muss vor n_curr++ passieren
        # weil immer vorherige line betrachtet wird
        I_Wk_Line = I_Wk_Line + (I_Wk(r_n_arr[n_curr])*N_Wk_L)

        #Lagen und Wicklung-akt.-Lage counter anpassen 
        n_curr = n_curr + 1
        n_Wk_L_curr = 0

        # Zeitpunkt vorheriger Lagenwechsel
        Tau_prev = Tau_next
    
    #Zeitpunkt nächster Wicklungswechsel
    Tau_Wk_L_next = Tau_prev + (n_Wk_L_curr + 1)*Tau_n_Wk_arr[n_curr]

    #Ist nächste Wicklung jetzt?
    if(t_curr > Tau_Wk_L_next):
        # Trägheitsmoment von schon gewickelten Lagen + Wicklungen
        # achtung is ein pfusch hack muss vor n_Wk_L_curr++ passieren
        # weil immer vorherige Wicklung betrachtet wird
        I_Wk_curr = I_Wk_Line + (I_Wk(r_n_arr[n_curr])*n_Wk_L_curr)

        #ges.-Wicklungs und Wicklung-akt.-Lage counter anpassen
        n_Wk_curr = n_Wk_curr + 1
        n_Wk_L_curr = n_Wk_L_curr + 1

    #Listen befüllen
    n_t.append(n_curr)
    n_Wk_t.append(n_Wk_curr)
    n_Wk_L_t.append(n_Wk_L_curr)
    r_t.append(r_n(n_curr))
    I_Sp_t.append(I_Wk_curr)

#schöne np arrays machen aus listen
n_t_arr  = np.array(n_t)
n_Wk_t_arr   = np.array(n_Wk_t)
n_Wk_L_t_arr = np.array(n_Wk_L_t)
r_t_arr = np.array(r_t)
I_Sp_t_arr = np.array(I_Sp_t)

# derivation function / Inertia functions
def calc_deriv(y_arr,x_arr,di_x):
    #di_x must be integer and half of the dx index shift
    dy = np.roll(y_arr,2*di_x) - y_arr
    dx = np.roll(x_arr,2*di_x) - x_arr
    return np.roll((dy / dx),-di_x)

# Ableitungen aus den erhaltenen arrays bilden
f_t_arr = calc_deriv(n_Wk_t_arr,t_arr,1)    # Hz
w_t_arr = f_t_arr * 2* np.pi
dot_w_t_arr = calc_deriv(w_t_arr,t_arr,1)
# moment calculations
M_T_t_arr = F_T * r_t_arr

M_0_Sp_arr = I_0_sp * dot_w_t_arr
M_0_well_arr = I_0_Well * dot_w_t_arr

L_Sp = I_Sp_t_arr * w_t_arr
M_Sp = calc_deriv(L_Sp,t_arr,1)

M_ges = M_T_t_arr + M_0_Sp_arr + M_0_well_arr + M_Sp

### output
print("v_Dr = ",v_Dr,)
print("lines=",N_lines,", windings=",N_Wk_L,", timesteps=",timesteps,", t_step=",t_step)
print("Tau_winding=",Tau_n_Wk_arr[0],", Tau_line=",Tau_n_arr[0],", Tau_ges=",Tau_ges)

def window_rms(a, window_size):
  a2 = np.power(a,2)
  window = np.ones(window_size)/float(window_size)
  return np.sqrt(np.convolve(a2, window, 'valid'))

f_t_RMS_arr = window_rms(f_t_arr,N_Wk_L*2)
t_RMS_arr = t_arr[int(N_Wk_L):N_Wind*2-int(N_Wk_L)+1]

print(t_RMS_arr.size,f_t_RMS_arr.size)
print(int(N_Wk_L/2),N_Wind*2-int(N_Wk_L/2))

# counter plotten
fig_log_t = plt.figure(figsize=(6,6))
ax_log_t = fig_log_t.add_subplot(1,1,1)
ax_log_t.scatter(t_arr,n_t_arr,label=r"n_Lines / s")
ax_log_t.scatter(t_arr,n_Wk_t_arr/1000,label=r"n_Wk/1000 / s")
ax_log_t.scatter(t_arr,n_Wk_L_t_arr/100,label=r"n_Wk/100 / s")
ax_log_t.set_ylabel(r"t / s")
ax_log_t.set_xlabel(r"n / Number Lines,timesteps")
ax_log_t.legend()

# plot n(t) and r(t)
fig_nr_t = plt.figure(figsize=(6,6))
ax_nr_t = fig_nr_t.add_subplot(1,1,1)
ax_nr_t.plot(t_arr,n_t_arr,label=r"n(t)")
ax_nr_t.plot(t_arr,r_t_arr*100,label=r"r(t) / cm")
ax_nr_t.plot(t_arr,I_Sp_t_arr*1e5,label=r"I_Sp(t) / gdm$^2$")
ax_nr_t.plot(t_arr,f_t_arr*10,label=r"f(t) / 0.1Hz")
ax_nr_t.plot(t_RMS_arr,f_t_RMS_arr*10,label=r"f(t) / 0.1Hz")
ax_nr_t.set_xlabel(r"t / s")
ax_nr_t.legend()

# Momente plotten
fig_mom = plt.figure(figsize=(6,6))
ax_mom = fig_mom.add_subplot(1,1,1)
ax_mom.plot(t_arr,M_ges,label=r"M_ges(t)")
ax_mom.plot(t_arr,M_Sp,label=r"M_Sp(t)")
ax_mom.plot(t_arr,M_0_well_arr,label=r"M_0_well_arr(t)")
ax_mom.plot(t_arr,M_0_Sp_arr,label=r"M_0_Sp_arr(t)")
ax_mom.plot(t_arr,M_T_t_arr,label=r"M_T_t_arr(t)")
ax_mom.set_xlabel(r"t / s")
ax_mom.set_ylabel(r"M / Nm")
ax_mom.legend()


""" Beschleunigungsmomentberechnungen für eliptischen Spulenkörper mit 15x1,5 cm"""
# functions to map angles into a intervall [-pi,+pi]
map_theta = lambda theta: np.fmod(theta, 2 * np.pi)

# coil parameters
r_g = 0.075                                             #m große Halbachse
r_k = 0.0075                                            #m kleine Halbachse
U = 0.304784                                            #m Umfang nummerisch ermittelt mit https://planetcalc.com/5494/
v_0 = f_max*U                                           #m/s mittlere Drahtgeschwindigkeit
f_0 = f_max                                             #Hz mittlere Hauptachsenfrequenz
w_0 = f_0 * 2 * np.pi                                   #1/s mittlere HA-Winkelgechwindigkeit
print("f_max=",f_max,", v_0=",v_0,", Tau_Wk=",1/f_0)

def v_thet(thet,omeg):
    return np.sqrt((r_g*np.sin(thet)*omeg)**2 + (r_k*np.cos(thet)*omeg)**2 + (( (r_k**2-r_g**2)*np.sin(2*thet)*omeg )**2 / (4*( (r_g*np.cos(thet))**2 + (r_k*np.sin(thet))**2 ))))
"""
Wolfram Alpha Prompt (vorher v_0 einsetzen und daten in HA_thet_t.csv kopieren)
Runge-Kutta method, dy/dx = v_0 / sqrt( (.075*sin(y))^2 + (.0075*cos(y))^2 + ((.0075^2-0.075^2)*sin(2*y))^2/(4*((.075*cos(y))^2 + (.0075*sin(y))^2)) ), y(0) = 0, from 0 to 1, h = .0125
Runge-Kutta method, dy/dx = .3048 / sqrt( (0.075*sin(y))^2 + (0.0075*cos(y))^2 + ((0.0075^2-0.075^2)*sin(2*y))^2/(4*((0.075*cos(y))^2 + (0.0075*sin(y))^2)) ), y(0) = 0, from 0 to 1, h = .0125
"""
# theta(t) Funktion wird über Wolfram Alpha aus DGL berechnet
df_thet = pd.read_csv(".//Planungsrecoursen//Hauptachse_Momentberechnung//HA_thet_t.csv",delimiter=";")

#t = np.linspace(0,3/f_0,5000)
t = df_thet["t"]

thet_t_arr = df_thet["thet"]
omeg_t_arr = calc_deriv(thet_t_arr,t,1)
alph_t_arr = calc_deriv(omeg_t_arr,t,1)

r_t_arr = np.sqrt((r_g*np.cos(thet_t_arr))**2 + (r_k*np.sin(thet_t_arr))**2)

#v_t_arr = [v_thet(thet_t_arr[i],omeg_t_arr[i]) for i in range(3)]
v_t_arr = v_thet(thet_t_arr,omeg_t_arr)

I_0_calc = I_0_sp + I_0_Well
I_start = I_0_calc + I_Sp_t_arr[0]
I_end = I_0_calc + I_Sp_t_arr[len(I_Sp_t_arr)-1]

M_alpha_start = I_start*alph_t_arr
M_alpha_end = I_end*alph_t_arr

fig_test_thet = plt.figure(figsize=(6,6))
ax_test_thet = fig_test_thet.add_subplot(3,1,1)
ax_test_v = fig_test_thet.add_subplot(3,1,2)
ax_test_I = fig_test_thet.add_subplot(3,1,3)

ax_test_v.set_xlabel(r"$t$ / s")
ax_test_v.set_ylabel(r"$v$ / m/s")
ax_test_thet.set_xlabel(r"$t$ / s")
ax_test_thet.set_ylabel(r"$\theta$ / $\pi$ / $\pi / s$ / $\pi / s^2$")
ax_test_I.set_xlabel(r"$t$ / s")
ax_test_I.set_ylabel(r"$M$ / Nm")

ax_test_v.plot(t,v_t_arr,label=r"$v_{Dr}(t)$")
ax_test_v.hlines(v_0,np.min(t),np.max(t),color="red",label=r"$v_{Dr,0}(t)$")
ax_test_v.plot(t,r_t_arr,label=r"$r_(t)$")
ax_test_thet.plot(t,map_theta(thet_t_arr)/np.pi,label=r"$\theta_{HA}(t)$")
ax_test_thet.plot(t,omeg_t_arr/(100*np.pi),label=r"$\omega_{HA}(t)/100$")
ax_test_thet.plot(t,alph_t_arr/(100000*np.pi),label=r"$\alpha_{HA}(t)$/100000")
ax_test_I.plot(t,M_alpha_start,label=r"$M_{alpha,start}(t)$")
ax_test_I.plot(t,M_alpha_end,  label=r"$M_{alpha,end}(t)$")

ax_test_thet.legend()
ax_test_v.legend()
ax_test_I.legend()

plt.show()