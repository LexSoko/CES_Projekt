# intro
# This file acts as a program development skript
# scope of this code is:
# - first rotary encoder and hx711 weight cell serial communication handler
# - simple visualization by plotting received values
# - bug, limitation and problem documentation

# Importing Libraries
import serial
import time
import numpy as np
import matplotlib.pyplot as plt

# documentation stuff
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

class serial_mma_data_stream:
    """Serial Data reading class for weight cell and rotary encoder
    """

    def __init__(self, port:str, baudrate:int,  rx_size: int,calibration_weight:float, len:int=10):
        """Creates new instance of the Serial Data reading class

        Args:
            port (str): COM Port descriptive name (eg. COM3)
            baudrate (int): Baudrate of serial connection 
            rx_size (int): Recommendation value for OS serial buffer size
            calibration_weight (float): Mass of the calibration weight in Gramms
            len (int, optional): Length of one data packet. Defaults to 10 (4 byte value, 4 byte time(mus),2 byte delimiter).
        """
        # Serial port stuff
        self.port = port
        self.baudrate = baudrate
        self.conn = serial.Serial(port=self.port, baudrate=self.baudrate)
        self.rx_size = rx_size
        
        # data protocol stuff
        self.len = 10
        
        # weigth cell stuff
        self.start = True
        self.calibration_weight = calibration_weight
        self.calibration_factor = 1
        self.offset = 0
        
        # reseting arduino and serial input buffer to start with clean data
        self.conn.setDTR(False)
        time.sleep(1)
        self.conn.flushInput()
        self.conn.set_buffer_size(rx_size = self.rx_size)
        self.conn.setDTR(True)
        
        

    def get_next_meas(self, len:int = None) -> bytes:
        """Reads out predefined (self.len) or passed (len:int =None) number of bytes out of COM buffer if available

        Args:
            len (int, optional): custom number of bytes to read out. Defaults to None.

        Returns:
            bytes: byte array read out from the buffer. None if not enough bytes available.
        """
        numbytes = self.conn.in_waiting

        if(len is not None):
            if(numbytes <=len):
                return None
            return self.conn.read(len)
        else:
            if(numbytes <=self.len):
                return None
            return self.conn.read(self.len)
    
    
    def get_next_rot_enc(self) -> tuple():
        """Reads out new rotary encoder data if available.

        Args:
            self (_type_): instance

        Returns:
            tuple(rot_timeVal,rot_pos,meas_data): rotary encoder data plus raw bytes
        """
        meas_data = self.get_next_meas()
        if meas_data is None:
            return None

        rot_pos = int.from_bytes(meas_data[0:4], byteorder='little')
        rot_timeVal = int.from_bytes(meas_data[4:8], byteorder='little')

        return (rot_timeVal,rot_pos,meas_data)
    
    
    def get_next_loadcell(self) -> tuple():
        """Reads out new weight cell data if available. Additionally detects calibration value and offset out of data.

        Args:
            self (_type_): instance

        Returns:
            tuple(loadcell_raw,loadcell_timeVal,meas_loadcell): load cell data plus raw bytes
        """
        meas_loadcell = self.get_next_meas()
        if meas_loadcell is None: 
            return None
        
        call_byte = meas_loadcell[0]
        # if cal then data bytes have flag : 0b1000 0000 xxxx xxxx .. xxxx xxxx 
        if call_byte == 128:
            cal_raw = int.from_bytes(meas_loadcell[1:4], byteorder = "little")
            self.calibration_factor = float(cal_raw)/self.calibration_weight
            self.offset = int.from_bytes(meas_loadcell[4:8], byteorder = "little")
            return (self.calibration_factor,self.offset,meas_loadcell,True)
        else:
            loadcell_raw = int.from_bytes(meas_loadcell[0:4], byteorder= "little")
            loadcell_timeVal = int.from_bytes(meas_loadcell[4:8], byteorder= "little")
            return (loadcell_raw,loadcell_timeVal,meas_loadcell,False)
    



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