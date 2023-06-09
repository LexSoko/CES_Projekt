# Importing Libraries
import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import struct

#arduino = serial.Serial(port='COM9', baudrate=115200)
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

class serial_mma_data_stream:

    def __init__(self, port:str, baudrate:int,  rx_size: int,calibration_weight:float, len:int=10):
        self.port = port
        self.baudrate = baudrate
        self.rx_size = rx_size
        self.conn = serial.Serial(port=self.port, baudrate=self.baudrate)
        self.start = True
        self.len = 10
        self.calibration_weight = calibration_weight
        self.calibration_factor = 1
        self.offset = 0
        self.conn.setDTR(False)
        time.sleep(1)
        self.conn.flushInput()
        self.conn.set_buffer_size(rx_size = self.rx_size)
        self.conn.setDTR(True)

    def get_next_meas(self) -> bytes:
        numbytes = self.conn.in_waiting
        if(numbytes <=10):
            return None


        return self.conn.read(self.len)
    
    def get_next_rot_enc(self) -> tuple():
        meas_data = self.get_next_meas()
        if meas_data is None:
            return None

        rot_pos = int.from_bytes(meas_data[0:4], byteorder='little')
        rot_timeVal = int.from_bytes(meas_data[4:8], byteorder='little')

        return (rot_timeVal,rot_pos,meas_data)
    def get_next_loadcell(self) -> tuple():
        meas_loadcell = self.get_next_meas()
        if meas_loadcell is None: 
            return None
        
        call_byte = meas_loadcell[0]
        if call_byte == 128:
            self.calibration_factor = (float(int.from_bytes(meas_loadcell[1:4]), byteorder = "little"))/self.calibration_weight
            self.offset = int.from_bytes(meas_loadcell[4:8])
        else:
            loadcell_raw = int.from_bytes(meas_loadcell[0:4], byteorder= "little")
            loadcell_timeVal = int.from_bytes(meas_loadcell[4:8], byteorder= "little")
            return (loadcell_raw,loadcell_timeVal,meas_loadcell)
    



#ädef readRotaryEncoder():
#ä    if(start == 1):
#ä        data = arduino.readline()
#ä        start = 0
#ä    data = arduino.read(10) 
#ä    return data


arduino = serial_mma_data_stream("COM9", 57600,16384,500)
rotPosition_ls = []
timeVal_ls = []
#bytes_ls = []
timeVal = 0
rot_pos = 0
databyt = bytes()
#debug_flag = False
loadcell_raw_ls= []
loadcell_converted_ls = []
loadcell_timeVal_ls = []
i = 0
for i in range(0,200):
    

    data = arduino.get_next_loadcell()
    if(data is not None):
        (loadcell_raw,loadcell_timeVal,val3) = data 
        print("raw data loadcell:",loadcell_raw,"time_val micros:", loadcell_timeVal, "bytestring:", val3)


        loadcell_raw_ls.append(loadcell_raw)
        loadcell_timeVal_ls.append(loadcell_timeVal)
        loadcell_converted_ls.append(loadcell_raw/(arduino.calibration_factor) - arduino.offset)
       
for i in loadcell_converted_ls:
    print(i)   

plt.scatter(loadcell_timeVal_ls,loadcell_converted_ls )
plt.show()



#i = 0
#while i < 20:
#    #numbytes = arduino.in_waiting
#    #if numbytes <= 10:
#    #    continue
#    retVal = arduino.get_next_rot_enc()
#
#    if(retVal is not None):
#        (timeVal,rot_pos,databyt) = retVal
#        i = i + 1
#
#
#    #bytes_ls.append(numbytes)
#    #while not (numbytes > 10):
#    #    time.sleep(.001)
#
#    #databyt = readRotaryEncoder()
#    
#    #print(databyt) # printing the value
#    
#    #value = int.from_bytes(databyt, byteorder='little')
#    
#    #rot_pos = int.from_bytes(databyt[0:4], byteorder='big')
#    #timeVal = int.from_bytes(databyt[4:8], byteorder='big')
#    
#    #rot_pos = value >> (32 + 16)
#    #if rot_pos != 0:
#    rotPosition_ls.append(rot_pos)
#    #timeVal = (value >> 16) & 0xFFFFFFFF
#    timeVal_ls.append(timeVal)
#    #print(value.bit_length())
#    #print(timeVal,"\t",rot_pos)
#    
#    #print("Databytes: ",''.join(format(x, '02x') for x in databyt))
#    #print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
#    print(rot_pos,";",timeVal,";",''.join(format(x, '02x') for x in databyt))
#    #if(rot_pos >= 2555 and rot_pos <=2565):
#    #    print("Databytes: ",''.join(format(x, '02x') for x in databyt))
#    #    print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
#    #    debug_flag = True
#    #elif(debug_flag and rot_pos<=50 and rot_pos != 0):
#    #    print("Databytes: ",''.join(format(x, '02x') for x in databyt))
#    #    print("rot_pos:   ",rot_pos," time_pos:    ",timeVal, "numbytes:    ",numbytes)
#    #elif(debug_flag and rot_pos >= 10):
#    #    debug_flag = False
#        
#    


# Oachkatzlscjowaf 082

    
# rotaryEncoder_arr = np.array(timeVal_ls, rotPosition_ls)

#print(rotaryEncoder_arr)
#plt.scatter(timeVal_ls,rotPosition_ls)
##plt.scatter(np.asarray(timeVal_ls), np.asarray(bytes_ls)*100)
#plt.show()