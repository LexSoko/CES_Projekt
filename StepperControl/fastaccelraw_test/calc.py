import matplotlib.pyplot as plt
import numpy as np

SEGMENTS = 500
TICKS_PER_S = 16000000
MAX_TICKS = 65535
segs = []
ks = []
tickss = []
stepss = []
curr_tickss = []
ticks2s = []


for seg in range(1,SEGMENTS):
    segs.append(seg)
    k = max(seg,SEGMENTS-seg)                       # -> k min = 250
    ks.append(k)
    ticks = TICKS_PER_S / 100 / (SEGMENTS-k)
    tickss.append(ticks)
    
    if (ticks > MAX_TICKS):
      curr_ticks = 32768
      steps = 1
    else:
      steps = MAX_TICKS / ticks
      curr_ticks = ticks
    
    ticks2 = ticks - curr_ticks
    
    stepss.append(steps)
    curr_tickss.append(curr_ticks)
    ticks2s.append(ticks2)

plt.plot()