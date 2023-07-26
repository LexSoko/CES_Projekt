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
seg1 = 0
seg1s = []
seg2 = 0
seg2s = []


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
    
    ticks = ticks - curr_ticks
    
    stepss.append(steps)
    curr_tickss.append(curr_ticks)
    
    seg2s.append(seg+seg1)

    while (ticks > 0):
      seg1 = seg1 + 1
      seg2 = seg + seg1
      if (ticks > MAX_TICKS):
        curr_ticks = 32768
      else:
        curr_ticks = ticks

      ticks = ticks - curr_ticks
      
      segs.append(seg)                     # -> k min = 250
      ks.append(k)
      tickss.append(ticks)
      stepss.append(0)
      curr_tickss.append(curr_ticks)
      seg2s.append(seg2)
    

plt.plot(np.array(segs),np.array(ks),label="k")
plt.plot(np.array(segs),np.array(tickss)/400,label="ticks")
plt.plot(np.array(segs),np.array(stepss),label="steps")
plt.plot(np.array(segs),np.array(curr_tickss)/400,label="curr_ticks")
plt.legend()
plt.show()

plt.plot(np.array(seg2s),np.array(ks),label="k")
plt.plot(np.array(seg2s),np.array(segs),label="seg")
plt.plot(np.array(seg2s),np.array(tickss)/400,label="ticks")
plt.plot(np.array(seg2s),np.array(stepss),label="steps")
plt.plot(np.array(seg2s),np.array(curr_tickss)/400,label="curr_ticks")
plt.legend()
plt.show()