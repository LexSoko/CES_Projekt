import serial

# Important constants for Serial comm
COM_PORT = "COM9"

def initialization():
    """
    setup of class objects
    """

def application_loop():
    """
    main application loop

    here serial port should be checked with high priority for
    response messages

    prepared enceladus commands should be checked with medium priority

    commandline input should be checked with low priority
    """




# TODO: write serial enceladus command handler class
class enceladus_cmd_handler:
    """
    enceladus command handler should prepare commands for serial write and add them to buffer
    enceladus commands should read responses and add them to commandline print buffer
    enceladus command handler should check new enceladus commands for validity
    this handler should block manual commands in script mode
    this handler should be a hardware firewall by keeping track of machine bounds
    and blocking physically unsafe commands

    all runtimecode is executed through run function
    responses are passed on to cmd line handler enqueue function
    manual cmds are received through the manual cmd queue
    script commands through the script cmd queue
    Machinebounds:
    2 Linear axis limits
    speed limits (top and bottom)
    acceleration limits (top and bottom)
    """

    def __init__(self, com_port:str, baudrate:int = 57600):
        """Creates new instance of the Enceladus command handler

        Args:
            port (str): COM Port descriptive name (eg. COM3)
            baudrate (int): Baudrate of serial connection
        """

        # Serial port stuff
        self.port = port
        self.baudrate = baudrate
        self.conn = serial.Serial(port=self.port, baudrate=self.baudrate)

        # public datastructures

        # private datastructures


        # last preperations
        self._reset_arduino_and_input_buffer_()
    
    def run():
        """runtime code

        1. read out enceladus responses and pass them to cmd line handler
        2. check, prepare and send enceladus commands if there are any and scripting mode is off
        3. execute script routine if any is active
        """

    def _reset_arduino_and_input_buffer_():
        self.conn.setDTR(False)
        time.sleep(1)
        self.conn.flushInput()
        self.conn.setDTR(True)


# TODO: write command line Interface handler class
# TODO: test controlling enceladus manually over commandline Interface
# TODO: test execution of small enceladus movement scripts