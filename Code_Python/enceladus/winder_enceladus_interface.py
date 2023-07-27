from __future__ import annotations
import os

# imports for asyncronous task
import asyncio
from asyncio import Queue, QueueEmpty
import aiofiles
from aiofiles.base import AiofilesContextManager
from datetime import datetime

# TEXTUAL TUI imports
from rich.align import Align
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import Footer, Header, TextLog, Input, Static
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.message import Message
from textual.events import Ready

# serial connection
import serial
import re

# Important constants for Serial comm
COM_PORT = "COM3"
BAUD_RATE = 57600

#TODO extract static functions into utils class

#TODO #scripting move machine script to a widget
#TODO #scripting use new easier command tracking to advance script
#TODO #scripting create initialization\calibration scripts
#TODO #scripting write the simple coil winding script
#TODO #scripting #measurementFiles add script phase logging
#TODO #serial remove old cmd_handler if its safe

########### Command Line User Interface stuff ##############

class EnceladusSerialWidget(Widget):
    """
    This widget is only used to get a asyncdronous background task for
    handling serial interface to enceladus and autonomos controll of
    the coilwinder
    """
    #TODO #serial finish serial interface
    
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
    
    #TODO #serial #scripting make command tracking easier
    #TODO #serial add missing calibration, settings, control commands and measurement packets
    
    """ the currently active command"""
    active_command = {
        "name":None,
        "finished":True,
        "error":False,
        "response":None
    }
    
    """ allowed commands"""
    allowed_commands = [
        "whoareyou","gotorelrev","gotorel","abort","disableidlecurrent",
        "getpos","loadcellav","loadcellraw","loadcellstart","loadcellstop"
        ]
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
        "getpos":"Current position:",
        "loadcellav":"loadcellAverage:",
        "loadcellraw":"loadcellRaw:",
        "loadcellstart":"measurement start!",
        "loadcellstop":"measurement end!"
        
    }
    
    # queues
    #_measurement_file_queue:Queue[str]
    #
    #@property
    #def measurement_file_queue(self):
    #    return self._measurement_file_queue
    #
    #@measurement_file_queue.setter
    #def measurement_file_queue(self, new_queue:Queue):
    #    self._measurement_file_queue = new_queue
    
    
    # stuff 
    
    counter = 0
    
    script_handler = None
    coilwinder_script = False
    com_port_exists:bool = False
    
    
    def __init__(self, parent:CMDInterface,send_cmd_queue:Queue,meas_filequeue:Queue,*args, **kwargs):
        self._cmd_interface = parent
        self._send_cmd_queue = send_cmd_queue
        self._measurement_file_queue = meas_filequeue
        self.com_port_exists = False
        super().__init__(*args, **kwargs)
    
    async def async_functionality(self):
        while True:
            """
            async runtime code read from serial buffer
            """
            await self._read_next_line_()   # check for new messages from serial 
            
            try:
                cmd = self._send_cmd_queue.get_nowait() # check for new commands from ui
                
                print("really got command")
                print(cmd)
                #TODO: #Martin zum testen kannst du messdaten nachrichten aus ui queue nehmen und in measurements queue schreiben
                # somit kannst du aus dem ui fake serial responses schreiben
                
                self.post_message(CMDInterface.UILog(self.try_enceladus_command(cmd)))
            except QueueEmpty:
                pass
                
            #if self.coilwinder_script and self.script_handler is not None:
            #    await self.script_handler.run_script()
            
            await asyncio.sleep(0.001)  # Mock async functionality
            
            self.counter += 1
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.

    def render(self) -> Align:
        
        text = """datarate: in={}, out={}
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
            
            
        return Align.left(text, vertical="top")
    
    
    async def on_mount(self):
        # get backend instance
        try:
            self._conn = serial.Serial(port=self.port, baudrate=self.baudrate)
            self.com_port_exists = True
            await self._reset_arduino_and_input_buffer_()
        except serial.SerialException:
            # manage no COM port
            self.com_port_exists = False
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
        #print("try command")
        
        if((name is not None) and (name in self.allowed_commands)): #check if command allowed
            self.active_command["name"] = name
            self.active_command["finished"] = False
            self.active_command["error"] = False
            self.active_command["response"] = None
            if self.com_port_exists:
                self._send_cmd_(cmd)
            return "sent successfully"
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
        while (self.com_port_exists and self._conn.in_waiting != 0):
            line = str(self._conn.readline())
            #print("here baby")
            #print(line)
            data = line.replace("\\r\\n\'","").replace("b\'","")
            
            #TODO: #Martin nur messdaten nachricht in _measurement_file_queue schreiben und nicht alle

            #await self._cmd_interface.add_ext_line_to_log(data)
            self.post_message(CMDInterface.UILog(data))
            await self._measurement_file_queue.put(data)
            print("put data in queue")

            if(not self.active_command["finished"]):
                if(self.cmd_finished_responses[self.active_command["name"]] in data):
                    # we got response from a currently active command

                    self.active_command["finished"] = True
                    self.active_command["response"] = data
                    #await self._cmd_interface.add_ext_line_to_log("cmd: \""+self.active_command["name"]+"\" finished")
                    self.post_message(CMDInterface.UILog("cmd: \""+self.active_command["name"]+"\" finished"))
    
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
    #TODO #measurementFiles refactor for more structure
    #TODO #measurementFiles finish parameter file
    #TODO #measurementFiles #scripting add script phase logging
    
    write_queue_fulliness = reactive(float)
    #directory_name = reactive(str)
    filenames = reactive(list[str])
    writespeeds = reactive(list[int])
    
    _measurements_queue:Queue #infinite sizes for now
    @property
    def measurements_queue(self):
        return self._measurements_queue
    
    params_queue:Queue
    
    dirname:str = "./winder_measurements/xxx/"
    
    measurement_file_handle:AiofilesContextManager
    meas_filename:str = "meas_xxx.csv"
    
    params_file_handle:AiofilesContextManager
    params_filename:str = "para_xxx.csv"
    
    def __init__(self, parent:CMDInterface,meas_filequeue:Queue,*args, **kwargs):
        self._cmd_interface = parent
        
        self._measurements_queue = meas_filequeue
        self.params_queue = Queue(0)
        
        datestring = FileIOTaskWidget.return_date()
        self.dirname = self.dirname.replace("xxx",datestring)
        
        timestring = FileIOTaskWidget.return_time()
        self.meas_filename = self.meas_filename.replace("xxx",timestring)
        self.params_filename = self.params_filename.replace("xxx",timestring)
        print("dirname "+self.dirname)
        #self.directory_name = self.dirname
        self.filenames.append(self.meas_filename)
        self.filenames.append(self.params_filename)
        
        self.writespeeds.append(0)
        
        super().__init__(*args, **kwargs)
    
    
    async def on_mount(self):
        asyncio.create_task(self.filewrite_worker())
        
        #self.measurement_file_handle = await self.open_measurements_file()
    
    def render(self) -> Align:
        
        text = """filenames: {}\nwritespeeds: {}""".format(
                self.filenames,
                self.writespeeds
        )
            
            
        return Align.left(text, vertical="top")
    
    async def filewrite_worker(self):
        while True:
            newline = await self._measurements_queue.get()
            #TODO #Martin messdaten nachrichten umbauen in csv zeilen bevor sie ins file hinzugefügt werden
            print("got data from queue")
            await self.write_to_measurements_file(newline)
            print("written data to file")
            self.writespeeds[0] += 1
        
    async def open_measurements_file(self):
        self.measurement_file_handle = await aiofiles.open(self.meas_filename)
    
        
    async def write_to_measurements_file(self,csvline:str):
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)
            
        # open the file
        async with aiofiles.open(self.dirname+self.meas_filename, mode='a') as handle:
            # write to the file
            await handle.write(csvline+"\n")
    
    def return_datetime()->str:
        return datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    
    def return_date()->str:
        return datetime.now().strftime("%m-%d-%Y")
    
    def return_time()->str:
        return datetime.now().strftime("%H-%M-%S")
        
    
    
class MachineScriptsWidget(Widget):
    
    script_mode = reactive(False)
    script_name = reactive(str)
    script_state = reactive("unconnected")
    
    allowed_scripts = ["script simple winding"]
    
    
    def __init__(self,
                 parent:CMDInterface,
                 ui_cmd_queue:Queue,
                 command_responses_queue:Queue,
                 command_send_queue:Queue,
                 *args, **kwargs):
        self._cmd_interface = parent
        self._ui_cmd_queue = ui_cmd_queue
        self._command_responses_queue = command_responses_queue
        self._command_send_queue = command_send_queue
        
        self._serial_widget:EnceladusSerialWidget = None
        
        # state variables #TODO: move to script container class
        ## positional variables
        self.current_pos = [0,0]
        ## unconnected state
        self.sent_whoareyou = False
        self.received_name = False
        ## position request state
        self.sent_pos_req = False
        self.received_pos_resp = False
        ## limit setting
        self.limits_set = False
        
        super().__init__(*args, **kwargs)
        
    
    async def set_serial_widget(self, serial:EnceladusSerialWidget):
        self._serial_widget = serial
        
    def render(self) -> Align:
        text = """script mode: {}, name: {}, state: {}""".format(
                self.script_mode,
                self.script_name,
                self.script_state)
        return Align.left(text, vertical="top")
    
    async def on_mount(self):
        asyncio.create_task(self.command_executor())
    
    async def command_executor(self):
        while True:
            await asyncio.sleep(1) #placeholder code
            if self.script_mode:
                match self.script_name:
                    case "script simple winding":
                        await self.simple_winding() # TODO: use script container class instead
            else:
                cmd = await self._ui_cmd_queue.get()
                if (cmd is not None) and (cmd in self.allowed_scripts):
                    self.script_mode = True
                    self.script_name = cmd
                else:
                    await self._command_send_queue.put(cmd)
                
    async def simple_winding(self): # move this to script container classes
        match self.script_state:
            case "unconnected":
                # check if machine is responsive
                if not self.sent_whoareyou:
                    await self._command_send_queue.put("whoareyou")
                    self.sent_whoareyou = True
                    self.post_message(CMDInterface.UILog("script: connection test started"))
                
                else:
                    if self._serial_widget.active_command["finished"]:
                        self.received_name = True
                        self.post_message(CMDInterface.UILog("script:"+"connection test successfull, enter position request"))
                        self.script_state = "position_request"


            case "position_request":
                # get current position
                if not self.sent_pos_req:
                    await self._command_send_queue.put("getpos")
                    self.sent_pos_req = True
                    self.post_message(CMDInterface.UILog("script:"+"sent position request"))
                
                else:
                    if self._serial_widget.active_command["finished"]:
                        self.received_pos_resp = True
                        (self.current_pos[0],self.current_pos[1]) = self.parse_pos_resp(self._serial_widget.active_command["response"])
                        self.post_message(CMDInterface.UILog("script:"+"pos received as "+str(self.current_pos)+ ", enter limit setting"))
                        self.script_state = "limit_setting"


            case "limit_setting":
                # set speed, acceleration and position limits
                if not self.limits_set:
                    self.post_message(CMDInterface.UILog("script:"+"entered limit setting"))
                    self.limits_set = True
                    self.script_state = "finished"

            #case "not_on_start_pos":
                # drive to starting position
            case "finished":
                #status = self.serial_handler.exit_script_mode("finished")
                self.post_message(CMDInterface.UILog("script:"+self.script_state))
                self.script_mode = False
                self.script_name = ""
                self.script_state = "unconnected"

            case _:
                self.post_message(CMDInterface.UILog("script:"+"unknown status: "+self.script_state))
    
    def parse_pos_resp(self,response:str)->tuple:
        words = response.split(' ')
        pos1 = int(words[2].strip(" \r\n"))
        pos2 = int(words[3].strip(" \r\n"))
        return (pos1,pos2)



class CMDInterface(App):
    CSS = """
    Static {
        border: solid green;
        content-align: center middle;
        height: 1fr;
        width: 1fr;
    }

    .horizontal {
        height: 9fr;
    }
    
    .box {
        border: solid green;
        content-align: left top;
        height: 1fr;
        width: 1fr;
    }

    .input {
        height: 1fr;
        border: solid green;
    }
    """
    
    BINDINGS = [
        Binding(key="q",action="quit",description="Quit the App"),
        Binding(key="enter",action="submit",description="submit cmd")
    ]
    
    #queues
    #TODO: move queue generation to another place
    _measurements_filewrite_queue:  Queue = None
    _ui_cmd_queue:                  Queue = None
    _command_responses_queue:       Queue = None
    _command_send_queue:            Queue = None
    
    def __init__(self, *args, **kwargs):
        """constructor is only used to instantiate the queue
        this must be changed later
        """
        self._measurements_filewrite_queue  = Queue(0)
        self._ui_cmd_queue                  = Queue(0)
        self._command_responses_queue       = Queue(0)
        self._command_send_queue            = Queue(0)
        
        super().__init__(*args, **kwargs)
    
    def compose(self) -> ComposeResult:
        """creates graphical structure of the CMDInterface and instantiates the Widgets"""
        yield Header(show_clock=True, name="Enceladus interface Coilwinder")
        yield Footer()
        yield Vertical(
            Horizontal(
                TextLog(id="output",highlight=True,markup=True,classes = "box"),
                ScrollableContainer(
                    EnceladusSerialWidget(parent=self,send_cmd_queue=self._command_send_queue, meas_filequeue=self._measurements_filewrite_queue,classes = "box"),
                    FileIOTaskWidget(parent=self,meas_filequeue=self._measurements_filewrite_queue,classes = "box"),
                    MachineScriptsWidget(parent=self,ui_cmd_queue=self._ui_cmd_queue,command_responses_queue=self._command_responses_queue,command_send_queue=self._command_send_queue,classes="box"),
                    id="right-vert"
                ),
                classes="horizontal"
            ),
            Input(id="input",placeholder="Enter cmd...",classes = "box"),
        )
    
    @on(Input.Submitted)
    async def handle_cmd_input(self, event: Input.Submitted) -> None:
        """called when text was typed into cmd input and then enter was pressed"""
        self.post_message(CMDInterface.UILog(event.value))
        event.input.value = ""
        
        #enc_ser_widget = self.query_one(EnceladusSerialWidget)
            
        #ret = enc_ser_widget.try_enceladus_command(event.value)
        await self._ui_cmd_queue.put(event.value)
        #self.post_message(CMDInterface.UILog(ret))
    
    @on(Ready)
    async def handle_ready(self, event:Ready)->None:
        print("on ready event")
        serial_widget = self.query_one(EnceladusSerialWidget)
        script_widget = self.query_one(MachineScriptsWidget)
        await script_widget.set_serial_widget(serial_widget)
    
    class UILog(Message):
        """Message Class for messages which need to be displayed in
        User interface TextLog widget
        
        call (from anywhere):
        self.post_message(CMDInterface.UILog(message:str))
        """
        def __init__(self, msg:str) -> None:
            self.msg = msg
            super().__init__()
    
    def on_cmdinterface_uilog(self, message: CMDInterface.UILog)-> None:
        """gets called when a UILog Message is postet
        """
        print("got message")
        self.query_one(TextLog).write(message.msg)



if __name__ == "__main__":
    app = CMDInterface()
    app.run()