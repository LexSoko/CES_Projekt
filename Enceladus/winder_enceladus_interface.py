from __future__ import annotations

from typing import TYPE_CHECKING

# imports for asyncronous task
import asyncio
from asyncio import Queue
import aiofiles
from aiofiles.base import AiofilesContextManager
from datetime import datetime

# TEXTUAL TUI imports
from rich.align import Align
from textual import events, on
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

    def __init__(self,widget:EnceladusSerialWidget, ui: CMD_Interface, com_port:str, baudrate:int = 57600):
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
    
    def __init__(self, enceladus:enceladus_serial_cmd_handler,ui: CMD_Interface):

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
    #scripty : coilwinder_machine_script | None=None
    #coilwinder_machine_script(scripty).
    
    # reactives
    datarate_in = reactive(0)
    datarate_out = reactive(0)
    send_queue_level = reactive(0.0)
    port = reactive(COM_PORT)
    baudrate = reactive(BAUD_RATE)
    port_open = reactive(False)
    coilwinder_script = reactive(bool | None)
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
    
    # queues
    _measurement_file_queue:Queue[str]
    
    @property
    def measurement_file_queue(self):
        return self._measurement_file_queue
    
    @measurement_file_queue.setter
    def measurement_file_queue(self, new_queue:Queue):
        self._measurement_file_queue = new_queue
    
    
    # stuff 
    
    counter = 0
    
    script_handler = None
    coilwinder_script = False
    
    async def async_functionality(self):
        while True:
            """
            async runtime code read from serial buffer
            """
            await self._read_next_line_()
            if self.coilwinder_script and self.script_handler is not None:
                await self.script_handler.run_script()
            
            await asyncio.sleep(0.001)  # Mock async functionality
            
            self.counter += 1
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.

    def render(self) -> Align:
        
        text = """
datarate: in={}, out={}
port open: {},
send queue lvl: {}
port: {}, baud rate: {}
Counter: {},
script_mode: {}
            """.format(
                self.datarate_in,
                self.datarate_out,
                self.port_open,
                self.send_queue_level,
                self.port,self.baudrate,
                self.counter,
                self.coilwinder_script
        )
            
            
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
        self.coilwinder_script = True
        return "entered scriptmode"
    
    def exit_script_mode(self,exit_status:str):
        self.script_handler = None
        self.coilwinder_script = False
        return exit_status

    async def _read_next_line_(self):
        """read next line from serial buffer
        """
        while (self._conn.in_waiting != 0):
            line = str(self._conn.readline())
            print("here baby")
            print(line)
            data = line.replace("\\r\\n\'","").replace("b\'","")

            await CMD_Interface(self.app).add_ext_line_to_log("hello")
            self._measurement_file_queue.put(data)

            if(not self.active_command["finished"]):
                if(self.cmd_finished_responses[self.active_command["name"]] in data):
                    # we got response from a currently active command

                    self.active_command["finished"] = True
                    self.active_command["response"] = data
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



class FileIOTaskWidget(Widget):
    write_queue_fulliness = reactive(float)
    filenames = reactive(list[str])
    writespeeds = reactive(list[int])
    
    _measurements_queue:Queue #infinite sizes for now
    @property
    def measurements_queue(self):
        return self._measurements_queue
    
    params_queue:Queue
    
    measurement_file_handle:AiofilesContextManager
    meas_filename:str = "meas_xxx.csv"
    
    params_file_handle:AiofilesContextManager
    params_filename:str = "para_xxx.csv"
    
    def __init__(self, *children: Widget, name: str | None = None, id: str | None = None, classes: str | None = None, disabled: bool = False) -> None:
        
        self._measurements_queue = Queue(0)
        self.params_queue = Queue(0)
        
        datestring = FileIOTaskWidget.return_datetime()
        self.meas_filename = self.meas_filename.replace("xxx",datestring)
        self.params_filename = self.params_filename.replace("xxx",datestring)
        self.filenames.append(self.meas_filename)
        self.filenames.append(self.params_filename)
        
        self.writespeeds.append(0)
        
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled)
    
    
    async def on_mount(self):
        asyncio.create_task(self.filewrite_worker())
        
        #self.measurement_file_handle = await self.open_measurements_file()
    
    def render(self) -> Align:
        
        text = """
filenames: {}

writespeeds: {}
            """.format(
                self.filenames,
                self.writespeeds
        )
            
            
        return Align.center(text, vertical="middle")
    
    async def filewrite_worker(self):
        while True:
            newline = await self._measurements_queue.get()
            await self.write_queue_fulliness(newline)
            self.writespeeds[0] += 1
        
    async def open_measurements_file(self):
        self.measurement_file_handle = await aiofiles.open(self.meas_filename)
    
        
    async def write_to_measurements_file(self,csvline:str):
        # open the file
        async with aiofiles.open(self.meas_filename, mode='w') as handle:
            # write to the file
            await handle.write(csvline)
    
    def return_datetime()->str:
        return datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
        
    
    
            
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


    
class CMD_Interface(App):
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
    
    
    def __init__(self):
        self._textlog = None
        self._cmd_input = None
        self._enc_ser_widget = None
        self._header = None
        self._files_wi = None
        super().__init__()
        
    #important widgets
    _textlog:TextLog
    @property
    def textlog(self)->TextLog:
        return self._textlog
    
    _cmd_input:Input
    @property
    def cmd_input(self)->Input:
        return self._cmd_input
    
    _enc_ser_widget:EnceladusSerialWidget
    @property
    def enc_ser_widget(self)->EnceladusSerialWidget:
        return self._enc_ser_widget
    
    _header:Header
    @property
    def header(self)->Header:
        return self._header
    
    _files_wi:FileIOTaskWidget
    @property
    def files_wi(self)->FileIOTaskWidget:
        return self._files_wi
    
    
    _measurements_filewrite_queue:Queue = None
    @property
    def _measurements_filewrite_queue(self):
        if self._measurements_filewrite_queue is None:
            filewi = self.query_one(FileIOTaskWidget)
            if filewi is None:
                return None
            
            self._measurements_filewrite_queue = filewi.measurements_queue
        
        return self._measurements_filewrite_queue
    
    def _push_measurement_filewrite_queue_reference(self,queue:Queue):
        serwi = self.query_one(EnceladusSerialWidget)
        if serwi is not None:
            serwi.measurement_file_queue = queue
    
    def compose(self) -> ComposeResult:
        #generating widged instances
        yield Header(show_clock=True, name="Enceladus interface Coilwinder")
        yield Footer()
        yield Vertical(
            Horizontal(
                TextLog(id="output",highlight=True,markup=True,classes = "box"),
                ScrollableContainer(
                    EnceladusSerialWidget(classes = "box"),
                    FileIOTaskWidget(classes = "box"),
                    id="right-vert"
                )
            ),
            Input(id="input",placeholder="Enter cmd...",classes = "box",validators=[InputValidator()]),
        )
    
    @on(Input.Submitted)
    async def handle_cmd_input(self, event: Input.Submitted) -> None:
        """called when text was typed into cmd input and then enter was pressed"""
        text_input = event.input
        await self._add_line_to_log_(event.value)
        text_input.value = ""
        
        if self._enc_ser_widget is None:
            self._enc_ser_widget = self.query_one(EnceladusSerialWidget)
            
        ret = self._enc_ser_widget.try_enceladus_command(event.value)
        await self._add_line_to_log_(ret)
    
    async def action_focus_input(self)->None:
        
        if self._cmd_input is None:
            self._cmd_input = self.query_one(Input)
            
        self._cmd_input.focus()
        return
    
    async def action_focus_log(self)->None:
        if self._textlog is None:
            self._textlog = self.query_one(TextLog)
        self._textlog.focus()
        return
    
    async def action_reset_focus(self) -> None:
        if self._header is None:
            self._header = self.query_one(Header)
        self._header.focus()
        return
    
    async def action_submit(self) -> None:
        #do submit
        return

    async def _add_line_to_log_(self,new_line:str) -> None:
        if self.textlog is None:
            self._textlog = self.query_one(TextLog)
        #await self.log(new_line)
        self._textlog.write(new_line)

    async def add_ext_line_to_log(self,new_line:str) -> None:
        if self.textlog is None:
            self._textlog = self.query_one(TextLog)
        #await self.log(new_line)
        print("needed textlog")
        self.textlog.write(new_line)



if __name__ == "__main__":
    app = CMD_Interface()
    app.run()