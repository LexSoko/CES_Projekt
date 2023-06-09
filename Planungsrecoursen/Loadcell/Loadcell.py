import serial as sl
import matplotlib.pyplot as plt
import numpy as np 


Serial_Port = sl.Serial("COM9",57600)
i = 0
while i < 200:
    
    line = Serial_Port.readline()
    Loadcell = int.from_bytes(line[0:4], 'little')
    time = int.from_bytes(line[4:8], 'little')
    print(Loadcell,";",time,";",''.join(format(x,'02x') for x in line))
    #print(line)
    
    i += 1
    