# Importing Libraries
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import struct

arduino = serial.Serial(
    port='COM3',
    baudrate=57600,
    bytesize=serial.EIGHTBITS,
    
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    xonxoff=0,
    rtscts=0
    )

"""
Bug2:
 -  Description:
    Python program stopped right at startup and gave completely wrong data

 -  Problem:
    arduino propably sends data from already running programm which has to big timestamps
    so python programm stopps immediately

 -  Solution:
    reset arduino from python side
    following code
"""
# Toggle DTR to reset Arduino
arduino.setDTR(False)
time.sleep(1)

# toss any data already received, see
# link
arduino.flushInput()

arduino.set_buffer_size(rx_size=16384)

arduino.setDTR(True)


"""
Limitation Problem1:
 -  Limitation source:
    Craptop (Max)

 -  Issue:
    Craptop can't handle baud rate 115200. Highest possible baud rate is 57600

 -  Workaround:
    run program with max baud rate 57600 on arduino and in python
"""

"""
Bug1:
 -  Description:
    in python, the rotary encoder value switched from 2559 to zero, then countet up
    normaly starting from zero and then after around 500 CNTs back to the expected
    value.
    Additionally some rotary encoder values at random times where also 0.
    
 -  Problem:
    most likely the Serial buffer on PC site didn't have the full 10 required bytes
    already read in, when a newline character entered the buffer,
    and so not all 10 bytes of one measurement value where read out from the buffer

 -  Solution:
    wait until at least 10 bytes are in the buffer and always read out
    excactly 10 bytes
"""

#def write_read(x):
#    arduino.write(bytes(x, 'utf-8'))
#    time.sleep(0.05)
#    data = arduino.readline()
#    return data

def readRotaryEncoder():
    data = arduino.read(10) 
    return data


rotPosition_ls = []
timeVal_ls = []
bytes_ls = []
timeVal = 0
debug_flag = False
while timeVal <= 1e7:
    numbytes = arduino.in_waiting
    if numbytes <= 10:
        continue
    
    bytes_ls.append(numbytes)
    #while not (numbytes > 10):
    #    time.sleep(.001)

    databyt = readRotaryEncoder()
    
    #print(databyt) # printing the value
    
    value = int.from_bytes(databyt, byteorder='little')
    
    rot_pos = int.from_bytes(databyt[0:4], byteorder='little')
    timeVal = int.from_bytes(databyt[4:8], byteorder='little')
    
    #rot_pos = value >> (32 + 16)
    #if rot_pos != 0:
    rotPosition_ls.append(rot_pos)
    #timeVal = (value >> 16) & 0xFFFFFFFF
    timeVal_ls.append(timeVal)
    #print(value.bit_length())
    #print(timeVal,"\t",rot_pos)
    
    #print("Databytes: ",''.join(format(x, '02x') for x in databyt))
    #print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
    print(rot_pos,";",timeVal,";",''.join(format(x, '02x') for x in databyt),";",numbytes)
    #if(rot_pos >= 2555 and rot_pos <=2565):
    #    print("Databytes: ",''.join(format(x, '02x') for x in databyt))
    #    print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
    #    debug_flag = True
    #elif(debug_flag and rot_pos<=50 and rot_pos != 0):
    #    print("Databytes: ",''.join(format(x, '02x') for x in databyt))
    #    print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
    #elif(debug_flag and rot_pos >= 10):
    #    debug_flag = False
        
    
    
# rotaryEncoder_arr = np.array(timeVal_ls, rotPosition_ls)

#print(rotaryEncoder_arr)
print(np.asarray(bytes_ls).max())
plt.scatter(timeVal_ls,rotPosition_ls)
plt.scatter(np.asarray(timeVal_ls), np.asarray(bytes_ls)*100)
plt.show()