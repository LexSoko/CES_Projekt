from __future__ import annotations

from typing import TYPE_CHECKING

# imports for asyncronous task
import asyncio
from datetime import datetime

# TEXTUAL TUI imports
from rich.align import Align
from textual import on
from textual.app import App, ComposeResult
from textual.validation import ValidationResult, Validator
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Footer, Header, TextLog, Input, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
if TYPE_CHECKING:
    from textual.message import Message

# serial connection
import serial
import time
from time import time
import re

# data structures
import queue

# Important constants for Serial comm
COM_PORT = "COM3"
BAUD_RATE = 57600


###################### Coulwinder Interface stuff ######################

class enceladus_serial_cmd_handler:
    """enceladus command handler should check if commands are valid and keep track of active commands
    enceladus commands should pass responsed on to UI and notify callers when commands are finished

    all runtimecode is executed through run function
    responses are passed on to cmd line handler log function and to command callers"""
    
    #################  attribute types  #####################
    # reactive variables
    _datarate_in:        int
    def _set_datarate(self, rate:int):
        self._datarate_in = rate
        self.w
    _datarate_out:       int
    _send_queue_level:   float
    _port:               str
    _baudrate:           int
    _port_open:          bool
    
    
    
    """ the currently active command"""
    active_command = {
        "name":None,
        "finished":True,
        "error":False,
        "response":None
    }
    
    """ allowed commands"""
    allowed_commands = ["whoareyou","gotorelrev","gotorel","abort","disableidlecurrent","getpos"]
    allowed_scripts = ["script simple winding"]
    
    """ command responses which indicate that a command is finished

    Returns:
        _type_: string
    """
    cmd_finished_responses = {
        "whoareyou":"FrankensteinsGemueseGarten_0v0",
        "gotorelrev":"DONE",
        "gotorel":"DONE",
        "abort":"Aborting movement!",
        "disableidlecurrent":"Idle Current Disabled!",
        "getpos":"Current position:"
    }

    script_handler = None
    script_mode = False

    def __init__(self,widget:EnceladusSerialWidget, ui: cmd_interface, com_port:str, baudrate:int = 57600):
        """Creates new instance of the Enceladus command handler

        Args:
            gui (cmd_interface): the user interface class implementing .add_ext_line_to_log(line)
            port (str): COM Port descriptive name (eg. COM3)
            baudrate (int): Baudrate of serial connection
        """
        # ui widget
        
        # reactive variables
        self._datarate_in = 0
        self._datarate_out = 0
        self._send_queue_level = 0.0
        self._port = com_port
        self._baudrate = baudrate
        self._port_open = False
        
        # Serial port stuff
        self._conn = serial.Serial(port=self._port, baudrate=self._baudrate)

        # gui related stuff
        self._ui = ui

        # last preperations
        #self._reset_arduino_and_input_buffer_()
    








class coilwinder_machine_script:
    """
    this handler should block manual commands in script mode
    this handler should be a hardware firewall by keeping track of machine bounds
    and blocking physically unsafe commands

    Returns:
        _type_: _description_

    Yields:
        _type_: _description_
    """
    
    # interface handler
    serial_handler = None
    
    # machine bounds:
    lim_pos_up = None
    lim_pos_low = None
    lim_vel_up = 200
    lim_vel_down = 0
    lim_accel_up = 100
    lim_accel_down = 0
    K_xy = 15
    
    # current Machine parameters (vectors for both axis)
    current_pos = [None,None]
    target_pos = [0,0]
    paused_pos = [0,0]
    currentOn = False
    measurementOn = False

    # Coil parameters
    coil_limit_sec_up = 80000
    coil_limit_sec_low = 0

    # behavioral stuff
    script_mode = False
    script_state = "unconnected"
    
    def __init__(self, enceladus:enceladus_serial_cmd_handler,ui: cmd_interface):

        # importatant class references
        self.serial_handler = enceladus
        self.ui = ui

        # state variables
        ## unconnected state
        self.sent_whoareyou = False
        self.received_name = False
        ## position request state
        self.sent_pos_req = False
        self.received_pos_resp = False
        ## limit setting
        self.limits_set = False

    async def run_script(self):
        #print("run script")
        await self.simple_winding()
    
    async def simple_winding(self):
        match self.script_state:
            case "unconnected":
                # check if machine is responsive
                if not self.sent_whoareyou:
                    succ = self.serial_handler.try_enceladus_command("whoareyou")
                    if succ == "sent successfully":
                        self.sent_whoareyou = True
                        await self._script_log_("connection test started")
                
                else:
                    if self.serial_handler.active_command["finished"]:
                        self.received_name = True
                        await self._script_log_("connection test successfull, enter position request")
                        self.script_state = "position_request"



            case "position_request":
                # get current position
                if not self.sent_pos_req:
                    succ = self.serial_handler.try_enceladus_command("getpos")
                    if succ == "sent successfully":
                        self.sent_pos_req = True
                        await self._script_log_("sent position request")
                
                else:
                    if self.serial_handler.active_command["finished"]:
                        self.received_pos_resp = True
                        (self.current_pos[0],self.current_pos[1]) = self.parse_pos_resp(self.serial_handler.active_command["response"])
                        await self._script_log_("pos received as "+str(self.current_pos)+ ", enter limit setting")
                        self.script_state = "limit_setting"

            case "limit_setting":
                # set speed, acceleration and position limits
                if not self.limits_set:
                    await self._script_log_("entered limit setting")
                    self.limits_set = True
                    self.script_state = "finished"

            #case "not_on_start_pos":
                # drive to starting position
            case "finished":
                status = self.serial_handler.exit_script_mode("finished")
                await self._script_log_(status)

            case _:
                print("default")
    
    def parse_pos_resp(self,response:str)->tuple:
        words = response.split(' ')
        pos1 = int(words[2].strip(" \r\n"))
        pos2 = int(words[3].strip(" \r\n"))
        return (pos1,pos2)

    async def _script_log_(self, log:str):
        await self.ui.add_ext_line_to_log("script: "+log)



        


    
    
    

########### Command Line User Interface stuff ##############
#class EnceldausAutomationScriptWidget(Widget):
    

class EnceladusSerialWidget(Widget):
    """
    This widget is only used to get a asyncdronous background task for
    handling serial interface to enceladus and autonomos controll of
    the coilwinder
    """
    
    # reactives
    datarate_in = reactive(0)
    datarate_out = reactive(0)
    send_queue_level = reactive(0.0)
    port = reactive(COM_PORT)
    baudrate = reactive(BAUD_RATE)
    port_open = reactive(False)
    
    # serial port stuff
    _conn: serial.Serial
    
    # command tracking stuff
    """ the currently active command"""
    active_command = {
        "name":None,
        "finished":True,
        "error":False,
        "response":None
    }
    
    """ allowed commands"""
    allowed_commands = ["whoareyou","gotorelrev","gotorel","abort","disableidlecurrent","getpos"]
    allowed_scripts = ["script simple winding"]
    
    """ command responses which indicate that a command is finished

    Returns:
        _type_: string
    """
    cmd_finished_responses = {
        "whoareyou":"FrankensteinsGemueseGarten_0v0",
        "gotorelrev":"DONE",
        "gotorel":"DONE",
        "abort":"Aborting movement!",
        "disableidlecurrent":"Idle Current Disabled!",
        "getpos":"Current position:"
    }
    
    # stuff 
    
    counter = 0
    
    script_handler = None
    script_mode = False
    
    async def async_functionality(self):
        while True:
            """
            async runtime code read from serial buffer
            """
            await self._read_next_line_()
            if self.script_mode and self.script_handler is not None:
                await self.script_handler.run_script()
            
            await asyncio.sleep(0.001)  # Mock async functionality
            
            self.counter += 1
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.

    def render(self) -> Align:
        text = """
datarate: in={}, out={}
port open: {}, send queue lvl: {}
port: {}, baud rate: {}
Counter: {}
            """.format(self.datarate_in,self.datarate_out,self.port_open,self.send_queue_level,self.port,self.baudrate,self.counter)
        return Align.center(text, vertical="middle")
    
    
    async def on_mount(self):
        # get backend instance
        self._conn = serial.Serial(port=self.port, baudrate=self.baudrate)
        await self._reset_arduino_and_input_buffer_()
        
        # start the async repetitive serial handler
        asyncio.create_task(self.async_functionality())

    def try_enceladus_command(self,cmd:str) -> str:
        """checks command for validity and passed it to serial buffer
        

        Args:
            cmd (str): command to send

        Returns:
            str: validity response
        """
        name = self._extract_cmd_name_(cmd)
        print("try command")
        
        if((name == "abort") or ((name is not None) and (name in self.allowed_commands))): #check if command allowed
            self.active_command["name"] = name
            self.active_command["finished"] = False
            self.active_command["error"] = False
            self.active_command["response"] = None
            self._send_cmd_(cmd)
            return "sent successfully"
        elif (name is not None and cmd in self.allowed_scripts):
            return self.enter_script_mode(cmd)
        else:
            return "command not allowed"
    
    def enter_script_mode(self,cmd:str)->str:
        self.script_handler = coilwinder_machine_script(self,self.app)
        self.script_mode = True
        return "entered scriptmode"
    
    def exit_script_mode(self,exit_status:str):
        self.script_handler = None
        self.script_mode = False
        return exit_status

    async def _read_next_line_(self):
        """read next line from serial buffer
        """
        while (self._conn.in_waiting != 0):
            line = str(self._conn.readline()).replace("\\r\\n\'","").replace("b\'","")

            await self.app.add_ext_line_to_log(line)

            if(not self.active_command["finished"]):
                if(self.cmd_finished_responses[self.active_command["name"]] in line):
                    # we got response from a currently active command

                    self.active_command["finished"] = True
                    self.active_command["response"] = line
                    await self.app.add_ext_line_to_log("cmd: \""+self.active_command["name"]+"\" finished")
    
    def _send_cmd_(self, cmd:str):
        """actually sending the command

        Args:
            cmd (str): validated command
        """
        self._conn.write((cmd+"\n").encode())
    
    def _extract_cmd_name_(self,cmd:str) -> str:
        """gets first word out of cmd string

        Args:
            cmd (str): command

        Returns:
            str: first word or None
        """
        return re.search("^([\w\-]+)",cmd)[0]
        
    async def _reset_arduino_and_input_buffer_(self):
        """resets the arduino and the serial buffer
        """
        self._conn.setDTR(False)
        await asyncio.sleep(1)
        self._conn.flushInput()
        self._conn.setDTR(True)
        
class InputValidator(Validator):  
    def validate(self, value: str) -> ValidationResult:
        """Check a string is equal to its reverse."""
        if self.is_valid(value):
            return self.success()
        else:
            return self.failure("Not valid :/")

    @staticmethod
    def is_valid(value: str) -> bool:
        return value != "not valid"
    
class cmd_interface(App):
    CSS = """
    Static {
    content-align: center middle;

    height: 1fr;
    }

    .box {
        border: solid green;
    }

    .input {
        height: 1fr;
        border: solid green;
    }
    """
    
    BINDINGS = [
        Binding(key="q",action="quit",description="Quit the App"),
        Binding(key="i",action="focus_input",description="focus cmd input"),
        Binding(key="enter",action="submit",description="submit cmd"),
        Binding(key="l",action="focus_log",description="focus textlog"),
        Binding(key="tab",action="reset_focus",description="unfocus")
    ]
    
    def compose(self) -> ComposeResult:
        self.header = Header(show_clock=True, name="Enceladus interface Coilwinder")
        
        self.textlog = TextLog(id="output",highlight=True,markup=True,classes = "box")
        self.enc_ser_widget = EnceladusSerialWidget(classes = "box")
        self.cmd_input = Input(id="input",placeholder="Enter cmd...",classes = "box",validators=[InputValidator()])
        
        self.footer = Footer()
        yield self.header
        yield self.footer
        yield Vertical(
            Horizontal(
                self.textlog,
                ScrollableContainer(
                    self.enc_ser_widget,
                    Static("Two",classes = "box"),
                    Static("Three",classes = "box"),
                    id="right-vert"
                )
            ),
            self.cmd_input,
        )
    
    @on(Input.Submitted)
    async def handle_cmd_input(self, event: Input.Submitted) -> None:
        """called when text was typed into cmd input and then enter was pressed"""
        text_input = event.input
        await self._add_line_to_log_(event.value)
        text_input.value = ""
        
        ret = self.enc_ser_widget.try_enceladus_command(event.value)
        await self._add_line_to_log_(ret)
    
    async def action_focus_input(self)->None:
        self.cmd_input.focus()
        return
    
    async def action_focus_log(self)->None:
        self.textlog.focus()
        return
    
    async def action_reset_focus(self) -> None:
        self.header.focus()
        return
    
    async def action_submit(self) -> None:
        #do submit
        return

    async def _add_line_to_log_(self,new_line:str) -> None:
        self.textlog.write(new_line)

    async def add_ext_line_to_log(self,new_line:str) -> None:
        self.textlog.write(new_line)



if __name__ == "__main__":
    app = cmd_interface()
    app.run()