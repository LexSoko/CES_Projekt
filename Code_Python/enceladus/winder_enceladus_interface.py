from __future__ import annotations
from abc import ABC, abstractmethod
import os

# imports for asyncronous task
import asyncio
from asyncio import Queue, QueueEmpty
from typing import Any, Callable, Dict, List
import aiofiles
from aiofiles.base import AiofilesContextManager
import aiofiles.os, aiofiles.ospath
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

# other imports
from dataclasses import dataclass,field

#class Machine():
#    def __init__(self):
        # Loadcell parameters
#        self.calibrated:bool = False
#        self.tara_weight:int = None
#        self.scale_weight:int = None

    # coil parameters

    # machinebounds

# Important constants for Serial comm
COM_PORT = "COM9"
BAUD_RATE = 57600
machine = {
    "calibrated"  :False,
    "tara_weight" :None,
    "scale_weight":None,
    "coilheight"  :-237322,
    "motorspeed"  :50,
    "acceleration":10
}

#TODO extract static functions into utils class

#TODO #scripting create initialization\calibration scripts
#TODO #scripting write the simple coil winding script
#TODO #scripting #measurementFiles add script phase logging

########### datastructures and object factories ############
class Singleton(object):
    """Singleton base class.
    
    A Singleton is a Object existing only once in programm memory
    and is statically accessible from anywhere in the code
    (this is like a global object but cooler)
    """
    _instances = {}
    def __new__(class_, *args, **kwargs):
        if class_ not in class_._instances:
            class_._instances[class_] = super(Singleton, class_).__new__(class_, *args, **kwargs)
        return class_._instances[class_]

class Command(ABC):
    name:str = ""
    full_cmd:str = ""
    params:list = []
    response_keys:list[str] = []
    response_msg:str = ""
    state:str = "None"
    
    _possible_states:list[str] = ["created","sent","resp_received","error","finished","novalidator"]
    
    def __init__(self,name:list,full_cmd:list,params:list,response_keys:list[str]) -> None:
        self.name = name
        self.full_cmd = full_cmd
        self.params = params
        self.response_keys = response_keys
        
        self.response_msg = ""
        self.state = "created"
    
    def got_sent(self) -> None:
        #print(self.name+" got sent")
        self.state = "sent"
    
    def got_received(self, response_msg:str) -> None:
        #print(self.name+" got received")
        self.response_msg = response_msg
        self.state = "resp_received"
    
    @abstractmethod
    def validate_cmd(self)->str:
        return "novalidator"
    
    async def wait_on_response(self) -> str:
        while not self.state == "resp_received":
            await asyncio.sleep(1)
        
        return self.validate_cmd()
        
    def __str__(self):
        return "{name:"+self.name+" params:"+str(self.params)+" state:"+self.state+"}"
        
class CommandFactory(Singleton):
    """used to check and create Command objects
    """
    
    #allowed commands
    allowed_commands:list[str] = [
        "whoareyou","gotorelrev","gotorel","abort","disableidlecurrent",
        "getpos","loadcellav","loadcellraw","loadcellstart","loadcellstop",
        "goto", "acceleration"
        ]
    
    #allowed command responses
    cmd_response_keys:Dict[str,list[str]] = {
        "whoareyou"         :["FrankensteinsGemueseGarten_0v0"],
        "gotorelrev"        :["DONE"],
        "gotorel"           :["DONE"],
        "goto"              :["DONE"],
        "abort"             :["Aborting movement!"],
        "disableidlecurrent":["Idle Current Disabled!"],
        "getpos"            :["Current position:"],
        "loadcellav"        :["loadcellAverage:"],
        "loadcellraw"       :["loadcellRaw:"],
        "loadcellstart"     :["measurement start!"],
        "loadcellstop"      :["measurement end!"],
        "acceleration"      :["Setting Acceleration to :"],
        "motorspeed"        :["Setting motorspeed:"]
    }
    
    class StandardCommand(Command):
        def validate_cmd(self) -> str:
            if any([resp in self.response_msg for resp in self.response_keys]):
                self.state = "finished"
                #print(self.name+" validates finished")
                #return "finished"
            else:
                self.state = "error"
                #print(self.name+" validates error")
                #return "error"
            
            return self.state
        
    
    def createStandardCommand(self,cmd:str) -> StandardCommand:
        # check if cmd contains valid cmd key:
        keys_in_cmd = [key for key in CommandFactory.cmd_response_keys.keys() if key in cmd]
        
        if len(keys_in_cmd) == 0:
            return None
        
        # get right cmd key which is the longest matched command key
        cmd_key = max(keys_in_cmd)
        
        #create and return the command
        
        return CommandFactory.StandardCommand(
            name=cmd_key,
            full_cmd=cmd,
            params = cmd.replace(cmd_key,"").strip().split(" "),
            response_keys=CommandFactory.cmd_response_keys[cmd_key]
        )
            
            
    
    
########### Command Line User Interface stuff ##############

class EnceladusSerialWidget(Widget):
    """
    This widget is only used to get a asyncdronous background task for
    handling serial interface to enceladus and autonomos controll of
    the coilwinder
    """
    #TODO #serial finish serial interface
    #TODO #serial add missing calibration, settings, control commands and measurement packets
    
    # reactives
    datarate_in = reactive(0)
    datarate_out = reactive(0)
    send_queue_level = reactive(0)
    port = reactive(COM_PORT)
    baudrate = reactive(BAUD_RATE)
    counter = reactive(0)

    # serial port stuff
    _conn: serial.Serial
    com_port_exists:bool = False
    active_cmds:list[Command] = []
    
    
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
            self.action_page_downdatarate_in = self._conn.in_waiting
            await self._read_next_line_()   # check for new messages from serial 
            
            try:
                cmd = self._send_cmd_queue.get_nowait() # check for new commands from ui

                if(not await self.check_if_cmd_and_handle(cmd)):
                    #print("really got command")
                    #print(cmd)
                    pass
                
            #Only for Testing begin
            #     match_obj = re.search("(^m [-]?[0-9]+ [-]?[0-9]+ [-]?[0-9]+ [-]?[0-9]+)[\s]*$", cmd.full_cmd)
            #     if(match_obj != None):
            #        match_obj_str = match_obj.group()
            #        await self._measurement_file_queue.put(match_obj_str)
            #        print("put data in queue:"+match_obj_str)
            #     else:
            #         self.post_message(CMDInterface.UILog(cmd.full_cmd)) #TODO: Max ich hoff des stimmt das Messdaten nicht als message gesendet werden?
            # Only for Teting end
                
            except QueueEmpty:
                pass
                
            
            await asyncio.sleep(0.001)  # Mock async functionality
            
            self.counter += 1
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.

    def render(self) -> Align:
        
        text = """datarate: in={}, out={}\nsend queue lvl: {}\nport: {}, baud rate: {}\nCounter: {},""".format(
                self.datarate_in,
                self.datarate_out,
                self.send_queue_level,
                self.port,self.baudrate,
                self.counter
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

    async def _read_next_line_(self):
        """read next line from serial buffer
        """
        while (self.com_port_exists and self._conn.in_waiting != 0):
            line = str(self._conn.readline())
            #print("here baby")
            #print(line)
            data = line.replace("\\r\\n\'","").replace("b\'","")
            #print("ser: got msg: "+data)
            #MSH begin
            match_obj = re.search("(^m [-]?[0-9]+ [-]?[0-9]+ [-]?[0-9]+ [-]?[0-9]+)[\s]*$", data)
            if(match_obj != None and match_obj.group() != ""):
                match_obj_str = match_obj.group()
                await self._measurement_file_queue.put(match_obj_str)
            elif("Aborting movement!" in data):
                # abort command was triggered -> mark every command as finished
                #print("caught abort response")
                for cmd in self.active_cmds:
                    #print("ckill cmd:"+cmd.name)
                    cmd.got_received(data)
                    self.active_cmds.remove(cmd)
            elif(not await self.check_if_cmd_resp_and_handle(data)):
                # common error is for loadcellstop "no valid command"
                if( any(c.name == "loadcellstop" for c in self.active_cmds)):
                    self.post_message(CMDInterface.UILog("resend loadcellstop: "+str(data)))
                    # get right loadcellstop cmd and resend it
                    for c in self.active_cmds:
                        if c.name == "loadcellstop":
                            self._send_cmd_(c.name)


                else:
                    #ok this must be an error
                    self.post_message(CMDInterface.UILog("ser: got: "+str(data)))
                    
    
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
    
    async def check_if_cmd_resp_and_handle(self, data)->bool:
        for cmd in self.active_cmds:
            if any([key in data for key in cmd.response_keys]):
                #print("sereadline: commandresponse received:"+str(cmd))
                cmd.got_received(data)
                self.active_cmds.remove(cmd)
                return True
        
        return False
    
    async def check_if_cmd_and_handle(self,cmd)->bool:
        if (type(cmd) is CommandFactory.StandardCommand):
            #print("ser: got command with right type:"+cmd.full_cmd)
            self.active_cmds.append(cmd)
            self._send_cmd_(cmd.full_cmd)
            self.post_message(CMDInterface.UILog("ser:sent:"+cmd.full_cmd))
            cmd.got_sent()
            return True
        
        return False



class FileIOTaskWidget(Widget):
    #TODO #measurementFiles finish parameter file
    #TODO #measurementFiles #scripting add script phase logging
    
    write_queue_fulliness = reactive(int)
    #directory_name = reactive(str)
    filenames = reactive(list[str])
    writespeeds = reactive(list[int])
    
    filesize = reactive(int)

    
    _measurements_queue:Queue #infinite sizes for now
    @property
    def measurements_queue(self):
        return self._measurements_queue
    
    params_queue:Queue
    
    
    max_filesize:int = 10000 #  10kbyte
    
    dirname_pattern:str = "./winder_measurements/xxx/"
    meas_filename_pattern:str = "meas_xxx.csv"
    
    measurement_file_handle:AiofilesContextManager
    meas_filename:str = "meas_xxx.csv"
    
    params_file_handle:AiofilesContextManager
    params_filename:str = "para_xxx.csv"
    
    def __init__(self, parent:CMDInterface,meas_filequeue:Queue,*args, **kwargs):
        self._cmd_interface = parent
        
        self._measurements_queue = meas_filequeue
        self.params_queue = Queue(0)
        
        self.dirname = self.dirname_pattern
        
        timestring = FileIOTaskWidget.return_time()
        self.meas_filename = self.meas_filename_pattern.replace("xxx",timestring)
        self.params_filename = self.params_filename.replace("xxx",timestring)
        #print("dirname "+self.dirname)
        #self.directory_name = self.dirname
        self.filenames.append(self.meas_filename)
        self.filenames.append(self.params_filename)
        
        self.writespeeds.append(0)
        
        super().__init__(*args, **kwargs)
    
    
    async def on_mount(self):
        asyncio.create_task(self.filewrite_worker())
        
        #self.measurement_file_handle = await self.open_measurements_file()
    
    def render(self) -> Align:
                
        text = """queuesize: {}\nfilenames: {}\nwritespeeds: {}\nfilesize:  {}""".format(
            self.write_queue_fulliness,
            self.filenames,
            self.writespeeds,
            self.filesize
        )
            
            
        return Align.left(text, vertical="top")
    
    async def filewrite_worker(self):
        datestring = FileIOTaskWidget.return_date()
        self.dirname = self.dirname_pattern.replace("xxx",datestring)
        # print("open file")
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)
        
        
        # async with aiofiles.open(self.dirname+self.meas_filename, mode='a') as handle:
        
        # MSH begin
        while True:
            #TODO: #Martin update the filenames reactive with new filenames
            #TODO: #Martin close and open same file after data block of size blocksize is written
            timestring = FileIOTaskWidget.return_time()
            self.meas_filename = self.meas_filename_pattern.replace("xxx",timestring)
            self.filesize = 0   # byte
            async with aiofiles.open(self.dirname+self.meas_filename, mode='a') as handle:
                while self.filesize < self.max_filesize:
                    self.write_queue_fulliness = self._measurements_queue.qsize()
                    
                    data = await self._measurements_queue.get()
                    #print("got data from queue")
                    
                                    
                    
                    newline = data.rstrip().replace(' ' , ';')
                    #print(newline)
                    await handle.write(newline+"\n")

                    self.writespeeds[0] += 1
                    self.refresh()
                    self.app.refresh()
                    
                    self.filesize += len(newline)   # byte
                    #print("filesize:"+str(self.filesize))
                    #
                    # P.S.: Like a STM operator esoterically places aluminum Foil on it's
                    #       big microscopic device, I myself esoterically place critical
                    #       code in the quiet neighbourhood of loop iteration begendings.
                    #       LG Jax Most                                                                     sadly no aluminium was found :(
                    #
        
    async def open_measurements_file(self):
        self.measurement_file_handle = await aiofiles.open(self.meas_filename)
    
        
    async def write_to_measurements_file(self,csvline:str):
        async with aiofiles.open(self.dirname+self.meas_filename, mode='a') as handle:
            # open the file
            # write to the file
            await handle.write(csvline+"\n")
    
    def return_datetime()->str:
        return datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    
    def return_date()->str:
        return datetime.now().strftime("%m-%d-%Y")
    
    def return_time()->str:
        return datetime.now().strftime("%H-%M-%S")
        



class MachineWidget(Widget):
    myMachine = reactive(dict)
    
    def __init__(self,parent:CMDInterface):
        global machine
        self.myMachine = machine
        self.parentApp = parent

    def render(self) -> Align:
        text = str(self.myMachine)
        return Align.left(text, vertical="top")
    
    async def on_mount(self):
        asyncio.create_task(self.updateMachine())
    
    async def updateMachine(self):
        while True:
            global machine
            self.myMachine = machine
            self.refresh()  # This is required for ongoing refresh
            self.app.refresh()  # Also required for ongoing refresh, unclear why, but commenting-out breaks live refresh.
            print("update machine widget")
            await asyncio.sleep(1)


class MachineScriptsWidget(Widget):
    
    script_mode = reactive(False)
    script_name = reactive(str)
    script_state = reactive("unconnected")
    
    allowed_scripts = ["script simple winding", "script calibration"]


    allowed_script_inputs:list[str] = []  #this will be filled by scripts to enable user input commands
    ui_script_inputs:list[str] = []
    
    cmd_fact = CommandFactory()
    
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
        
        #self._serial_widget:EnceladusSerialWidget = None
        
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
        
    
    #async def set_serial_widget(self, serial:EnceladusSerialWidget):
    #    self._serial_widget = serial
        
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
            await asyncio.sleep(0.01) #placeholder code
            #if self.script_mode:
            #    match self.script_name:
            #        case "script simple winding":
            #            await self.simple_winding() # TODO: use script container class instead
            #else:
            
            cmd = await self._ui_cmd_queue.get()
            #print("cmd_ex got command: "+cmd)
            if(not cmd in self.allowed_scripts and
               not cmd in self.allowed_script_inputs):
                cmd_obj = await self.create_cmd_await_response(cmd)
                self.whennoerror(cmd_obj,lambda sel,cmd_o: sel.post_message(
                    CMDInterface.UILog("cmd_exe cmd:"+cmd_o.state +"\n->resp:"+cmd_o.response_msg)))
                
            elif(not self.script_mode):
                match cmd:
                    case "script calibration":
                        # create calibration script
                        self.create_script_task(self.calibration_script)
                    case "script simple winding":
                        # create simple winding script
                        self.create_script_task(self.simple_winding)
                        
            elif(cmd in self.allowed_script_inputs):
                self.forward_to_script(cmd)
                
            else:
                #script was called but already one acitve
                self.post_message(CMDInterface.UILog("cmd_exe: script already running"))

            #
            # TODO #scripting think how paralell scripts during scripting phase could be implemented
            #
            # TODO #scripting make calibration script as first machinescript
            # and with learned lessons the coil winding script
            # don't waste your time on Endstops and automatic coil finding
            # RESULTS ARE MORE TIMECRITICAL!!
            #
            # Calibration:
            # -> promp User to "empty the loadcell"
            # -> tara command from UI leads to averaged measurement
            # -> promp User to put "calibration weight" on loadcell
            # -> scale command for another avrg. meas.
            # -> save these properties somwhere safe
            # -> log tara and scale values in UI
            # 
            # First Winding:
            # -> drive to one coil ending manually (with prompt)
            # -> UI cmd SetPos2
            # -> drive to other coil ending manually (with prompt)
            # -> UI cmd SetPos1
            # -> prompt user for coil_diameter, coil_height, cable_diameter
            #                   winding number, spannsystemparameters, phases to log
            # -> calculate winding speeds, for constant cable throughput
            # -> prompt user if the calculated speed is ok and can be driven safely
            # -> start the buisiness:
            # -> loop over all required goto commands
            # 
            

    def forward_to_script(self, cmd):
        self.ui_script_inputs.append(cmd)
    
    async def create_cmd_await_response(self, cmd:str)->Command:
        cmd_obj = CommandFactory().createStandardCommand(cmd)
                #print("cmd_ex built cmd_obj: "+str(cmd_obj))
        if cmd_obj is not None:
            await self._command_send_queue.put(cmd_obj)
                    #print("cmd_ex sent cmd_obj")
            status = await cmd_obj.wait_on_response()
                    #print("cmd_ex got response:"+status)
            #self.post_message(CMDInterface.UILog("command_executor: "+str(cmd)+"-response: "+cmd_obj.response_msg))
                    #print("cmd_ex got response end:")
        #else:
            #self.post_message(CMDInterface.UILog("command_executor: "+cmd+" not a command"))
        
        return cmd_obj
    
    def whennoerror(self,cmd_obj:Command,func:Callable[[MachineScriptsWidget,Command],Any])->Any:
        if cmd_obj is None:
            self.post_message(CMDInterface.UILog("cmd_exe cmd is None"))
            return False
        elif cmd_obj.state == "error":
            cmd_obj.response_msg
            self.post_message(CMDInterface.UILog("cmd_exe cmd:"+cmd_obj.name+" "+ ("is None" if (cmd_obj is None) else "has error:"+cmd_obj.response_msg)))
            return False
        
        return func(self,cmd_obj)
        
    def create_script_task(self, script_routine:Callable[[...],None]):
        asyncio.create_task(script_routine())
    
    async def calibration_script(self) -> None:
        # Calibration:
        # -> promp User to "empty the loadcell"
        # -> tara command from UI leads to averaged measurement
        # -> promp User to put "calibration weight" on loadcell
        # -> scale command for another avrg. meas.
        # -> save these properties somwhere safe
        # -> log tara and scale values in UI

        ####################################################### setup variables
        self.post_message(CMDInterface.UILog("calibration start:"))
        self.script_state = "setup"
        self.script_mode = True
        self.script_name = "calibration"
        global machine


        
        ####################################################### tara parameter
        # -> promp User to "empty the loadcell"
        # -> tara command from UI leads to averaged measurement
        self.script_state = "tara"
        self.allowed_script_inputs.append("tara") #tara start
        self.post_message(CMDInterface.UILog("please empty loadcell and then type \"tara\""))

        while("tara" not in self.ui_script_inputs): # wait for user input
            await asyncio.sleep(1)
            #print("wait for tara cmd")
        self.ui_script_inputs.remove("tara")
        
        def setTara(cmd_o:Command):    # function to set machine value
            global machine
            machine["tara_weight"] = int(cmd_o.response_msg.split(" ")[1])
            print("written Tara")

        cmd_obj = await self.create_cmd_await_response("loadcellav 50") #handle enceladus command
        self.whennoerror(cmd_obj,lambda sel,cmd_o: setTara(cmd_o))

        self.post_message(CMDInterface.UILog("script got tara:"+str(machine["tara_weight"])))
        self.allowed_script_inputs.remove("tara") #tara end

        ####################################################### scale parameter
        # -> promp User to put "calibration weight" on loadcell
        # -> scale command for another avrg. meas.
        self.script_state = "scale"
        self.allowed_script_inputs.append("scale") #scale start
        self.post_message(CMDInterface.UILog("put calibration weight on and then type \"scale\""))

        while("scale" not in self.ui_script_inputs): # wait for user input
            await asyncio.sleep(1)
            #print("wait for scale cmd")
        self.ui_script_inputs.remove("scale")
        
        def setScale(cmd_o:Command):    # function to set machine value
            global machine
            machine["scale_weight"] = int(cmd_o.response_msg.split(" ")[1])
        
        cmd_obj = await self.create_cmd_await_response("loadcellav 50") #handle enceladus command
        self.whennoerror(cmd_obj,lambda sel,cmd_o: setScale( cmd_o))

        self.post_message(CMDInterface.UILog("script got scale:"+str(machine["scale_weight"])))
        self.allowed_script_inputs.remove("scale") #scale end

        ####################################################### close down variables
        self.post_message(CMDInterface.UILog("calibration finished:"))
        self.script_state = "finished"
        self.script_name = "None"
        self.script_mode = False
    
    async def simple_winding(self) -> None:
        # simple_winding:
        # -> set speed and acc
        # -> start loadcell measurement
        # -> loop 4 times:
        # ->    run motor forward gotorel -237322
        # ->    run motor backward gotorelrev -237322
        # -> stop loadcell measurement


        self.post_message(CMDInterface.UILog("simple winding start:"))
        self.script_state = "setup"
        self.script_mode = True
        self.script_name = "simple winding"
        global machine
        
        stepdistance = machine["coilheight"]
        max_speed = machine["motorspeed"]
        acc = machine["acceleration"]

        ####################################################### set speed
        self.script_state = "set speed"
        self.post_message(CMDInterface.UILog("set speed:"+str(max_speed)))
        success = False
        while(not success):
            cmd_obj = await self.create_cmd_await_response("motorspeed "+str(max_speed)) #handle enceladus command
            success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)


        ####################################################### set acc
        self.script_state = "set accel"
        self.post_message(CMDInterface.UILog("set accel:"+str(acc)))
        success = False
        while(not success):
            cmd_obj = await self.create_cmd_await_response("acceleration "+str(acc)) #handle enceladus command
            success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)



        ####################################################### start loadcell
        self.script_state = "start loadcell"
        self.post_message(CMDInterface.UILog("start loadcell meas"))
        success = False
        while(not success):
            cmd_obj = await self.create_cmd_await_response("loadcellstart") #handle enceladus command
            success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)

        k = 0
        for i in range(2):
            # ->    run motor forward gotorel -237322
            k += 1
            self.post_message(CMDInterface.UILog("winding nr:"+str(k)))
            success = False
            while(not success):
                cmd_obj = await self.create_cmd_await_response("gotorel "+str(-237322)) #handle enceladus command
                success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)

            # ->    run motor backward gotorelrev -237322
            k += 1
            self.post_message(CMDInterface.UILog("winding nr:"+str(k)))
            success = False
            while(not success):
                cmd_obj = await self.create_cmd_await_response("gotorelrev "+str(-237322)) #handle enceladus command
                success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)

        
    
        ####################################################### stop loadcell
        self.script_state = "stop loadcell"
        self.post_message(CMDInterface.UILog("stop loadcell meas"))
        success = False
        while(not success):
            cmd_obj = await self.create_cmd_await_response("loadcellstop") #handle enceladus command
            success = self.whennoerror(cmd_obj,lambda sel,cmd_o: True)


        self.post_message(CMDInterface.UILog("simple winding end:"))
        self.script_state = "finished"
        self.script_mode = False
        self.script_name = "None"


    
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
    #Machine().tara_weight = 69
    

    def __init__(self, *args, **kwargs):
        """constructor is only used to instantiate the queue
        this must be changed later
        """
        self._measurements_filewrite_queue  = Queue(0)
        self._ui_cmd_queue                  = Queue(0)
        self._command_responses_queue       = Queue(0)
        self._command_send_queue            = Queue(0)
        self.notauscommand = CommandFactory().createStandardCommand("abort")
        
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
                    MachineWidget(classes = "box"),
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
        
        if event.value == "abort":
            self.post_message(CMDInterface.UILog("not abort"))
            await self._command_send_queue.put(self.notauscommand)
            # do not wait for command responses here
            # i had to search for an error for ca. 2h but only solution was to comment out following two lines
            #resp = await self.notauscommand.wait_on_response()
            #self.post_message(CMDInterface.UILog("not abort ausgeführt"))
        else:
            await self._ui_cmd_queue.put(event.value)
            #self.post_message(CMDInterface.UILog(ret))
    
    #@on(Ready)
    #async def handle_ready(self, event:Ready)->None:
    #    #print("on ready event")
    #    serial_widget = self.query_one(EnceladusSerialWidget)
    #    script_widget = self.query_one(MachineScriptsWidget)
    #    await script_widget.set_serial_widget(serial_widget)
    
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
        #print("got message")
        self.query_one(TextLog).write(message.msg)


if __name__ == "__main__":
    app = CMDInterface()
    app.run()