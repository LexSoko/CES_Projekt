import sys
import time

from telemetrix import telemetrix

"""
Monitor a digital input pin
https://mryslab.github.io/telemetrix/
"""

"""
Setup a pin for digital input and monitor its changes
"""

# Setup a pin for analog input and monitor its changes
DIGITAL_PIN = 12  # arduino pin number

A_JOYSTICK_X = 0
A_JOYSTICK_Y = 1

# Callback data indices
CB_PIN_MODE = 0
CB_PIN = 1
CB_VALUE = 2
CB_TIME = 3


temp_dat = [0 , 0 , 0 , 0]
TEMP_STAT = 0
TEMP_TIME = 1
TEMP_X = 2
TEMP_Y = 3


def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the change occurred

    :param data: [pin, current reported value, pin_mode, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    print(f'Pin Mode: {data[CB_PIN_MODE]} Pin: {data[CB_PIN]} Value: {data[CB_VALUE]} Time Stamp: {date}')

def log_dat_callback(data):
    pin_num = data[CB_PIN]
    value = data[CB_VALUE]
    temp_dat[TEMP_TIME] = data[CB_TIME]

    



def digital_in(my_board : telemetrix.Telemetrix, pin):
    """
     This function establishes the pin as a
     digital input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a pymata4 instance
     :param pin: Arduino pin number
     """

    # set the pin mode
    my_board.set_pin_mode_digital_input(pin, callback=the_callback)



def analog_in(my_board, pin):
    """
     This function establishes the pin as a
     digital input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a pymata4 instance
     :param pin: Arduino pin number
     """

    # set the pin mode
    my_board.set_pin_mode_analog_input(pin, callback=the_callback)

    print('Enter Control-C to quit.')
    # my_board.enable_digital_reporting(12)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        board.shutdown()
        sys.exit(0)


board = telemetrix.Telemetrix()
char_list = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N']
start_times = {'A':0 ,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0}
time_list = {'A':0 ,'B':0,'C':0,'D':0,'E':0,'F':0,'G':0,'H':0,'I':0,'J':0,'K':0,'L':0,'M':0,'N':0}

def pingCall(data):
    time_list[chr(data[0])] = time.time() - start_times[chr(data[0])]
    print(f'Looped back: {chr(data[0])}')

def ping(my_board: telemetrix.Telemetrix, loop_back_data):
    try:
        for data in loop_back_data:
            start_times[data] = time.time()
            my_board.loop_back(data,callback=pingCall)
            print(f'sending: {data}')
    except KeyboardInterrupt:
        board.shutdown()
        sys.exit(0)


    print('Enter Control-C to quit.')
    # my_board.enable_digital_reporting(12)
    try:
        while True:
            time.sleep(.0001)
    except KeyboardInterrupt:
        board.shutdown()
        #sys.exit(0)


try:
    #analog_in(board, A_JOYSTICK_X)
    ping(board,char_list)
    print(time_list)
    time.sleep(1)
except KeyboardInterrupt:
    board.shutdown()
    sys.exit(0)