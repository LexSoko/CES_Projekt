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
if TYPE_CHECKING:
    from textual.message import Message

# serial connection
import serial
import time
import re

# data structures
import queue

# Important constants for Serial comm
COM_PORT = "COM4"
BAUD_RATE = 115200


###################### Coulwinder Interface stuff ######################

class enceladus_serial_cmd_handler:
    """enceladus command handler should check if commands are valid and keep track of active commands
    enceladus commands should pass responsed on to UI and notify callers when commands are finished

    all runtimecode is executed through run function
    responses are passed on to cmd line handler log function and to command callers"""
    
    
    """ the currently active command"""
    active_command = {
        "name":None,
        "finished":True,
        "error":False
    }
    
    """ allowed commands"""
    allowed_commands = ["whoareyou","gotorelrev","gotorel","abort"]
    
    """ command responses which indicate that a command is finished

    Returns:
        _type_: string
    """
    cmd_finished_responses = {
        "whoareyou":"FrankensteinsGemueseGarten_0v0",
        "gotorelrev":"DONE",
        "gotorel":"DONE",
        "abort":"Aborting movement!"
    }

    def __init__(self, ui: cmd_interface, com_port:str, baudrate:int = 57600):
        """Creates new instance of the Enceladus command handler

        Args:
            gui (cmd_interface): the user interface class implementing .add_ext_line_to_log(line)
            port (str): COM Port descriptive name (eg. COM3)
            baudrate (int): Baudrate of serial connection
        """

        # Serial port stuff
        self.port = com_port
        self.baudrate = baudrate
        self.conn = serial.Serial(port=self.port, baudrate=self.baudrate)

        # gui related stuff
        self.ui = ui

        # last preperations
        self._reset_arduino_and_input_buffer_()
    
    async def run(self):
        """
        async runtime code read from serial buffer
        """
        await self._read_next_line_()
        
    def try_enceladus_command(self,cmd:str) -> str:
        """checks command for validity and passed it to serial buffer
        

        Args:
            cmd (str): command to send

        Returns:
            str: validity response
        """
        name = self._extract_cmd_name_(cmd)
        
        if(name is not None and name in self.allowed_commands): #check if command allowed
            self.active_command["name"] = name
            self.active_command["finished"] = False
            self._send_cmd_(cmd)
            return "sent successfully"
        else:
            return "command not allowed"
        
    async def _read_next_line_(self):
        """read next line from serial buffer
        """
        while (self.conn.in_waiting != 0):
            line = str(self.conn.readline())

            await self.ui.add_ext_line_to_log(line)

            if(not self.active_command["finished"]):
                if(self.cmd_finished_responses[self.active_command["name"]] in line):
                    # active command was finished successfully
                    self.active_command["finished"] = True
                    await self.ui.add_ext_line_to_log("cmd: \""+self.active_command["name"]+"\" finished")
    
    def _send_cmd_(self, cmd:str):
        """actually sending the command

        Args:
            cmd (str): validated command
        """
        self.conn.write((cmd+"\n").encode())
    
    def _extract_cmd_name_(self,cmd:str) -> str:
        """gets first word out of cmd string

        Args:
            cmd (str): command

        Returns:
            str: first word or None
        """
        return re.search("^([\w\-]+)",cmd)[0]
        
    
    def _reset_arduino_and_input_buffer_(self):
        """resets the arduino and the serial buffer
        """
        self.conn.setDTR(False)
        time.sleep(1)
        self.conn.flushInput()
        self.conn.setDTR(True)


class coilwinder_machine:
    """
    this handler should block manual commands in script mode
    this handler should be a hardware firewall by keeping track of machine bounds
    and blocking physically unsafe commands

    Returns:
        _type_: _description_

    Yields:
        _type_: _description_
    """
    
    #interface handler
    serial_handler = None
    
    #machine bounds:
    lim_pos_up = None
    lim_pos_low = None
    lim_vel_up = 200
    lim_vel_down = 0
    lim_accel_up = 100
    lim_accel_down = 0
    
    # behavioral stuff
    script_mode = False
    
    
    
    

########### Command Line User Interface stuff ##############

class MachineInterfaceWidget(Widget):
    """
    This widget is only used to get a asyncdronous background task for
    handling serial interface to enceladus and autonomos controll of
    the coilwinder
    """
    
    #serial handler stuff
    enceladus_handler = 0
    connection_active = False
    command_active = False
    script_active = False
    
    counter = 0
    
    async def async_functionality(self):
        print("add ENCELADUS")
        self.enceladus_handler = enceladus_serial_cmd_handler(ui = self.app, com_port = COM_PORT,baudrate = BAUD_RATE)
        
        print("add ENCELADUS FINISHED")
        while True:
            await asyncio.sleep(0.2)  # Mock async functionality
            await self.enceladus_handler.run()
            self.counter += 1
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.

    def render(self) -> Align:
        now = datetime.strftime(datetime.now(), "%H:%M:%S.%f")[:-5]
        text = f"{now}\nCounter: {self.counter}"
        return Align.center(text, vertical="middle")
    
    
    async def on_mount(self):
        asyncio.create_task(self.async_functionality())


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
        yield Header(show_clock=True, name="Enceladus interface Coilwinder")
        yield Footer()
        #yield Input(placeholder="Enter Command..")
        yield Vertical(
            Horizontal(
                TextLog(id="output",highlight=True,markup=True,classes = "box"),
                ScrollableContainer(
                    MachineInterfaceWidget(classes = "box"),
                    Static("Two",classes = "box"),
                    Static("Three",classes = "box"),
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
        
        
        encel_cmd = self.query_one(MachineInterfaceWidget).enceladus_handler
        ret = encel_cmd.try_enceladus_command(event.value)
        await self._add_line_to_log_(ret)
    
    async def action_focus_input(self)->None:
        text_input = self.query_one(Input)
        text_input.focus()
        return
    
    async def action_focus_log(self)->None:
        text_log = self.query_one(TextLog)
        text_log.focus()
        return
    
    async def action_reset_focus(self) -> None:
        header = self.query_one(Header)
        header.focus()
        return
    
    async def action_submit(self) -> None:
        #do submit
        return

    async def _add_line_to_log_(self,new_line:str) -> None:
        text_log = self.query_one(TextLog)
        text_log.write(new_line)

    async def add_ext_line_to_log(self,new_line:str) -> None:
        text_log = self.query_one(TextLog)
        text_log.write(new_line)



if __name__ == "__main__":
    app = cmd_interface()
    app.run()