#include "HX711.h"

#define PIN_DT 2
#define PIN_SCK 3 
#define BTN_CAL 8
#define SYNC_PIN 7

// serial command types
#define WORK_COMMAND 0x80
#define CALIBRATION_COMMAND 0xC0
#define SYNC_COMMAND 0xE0
#define TARE_COMMAND  116
#define RAW_CALL_COMMAND 114

// exit flag definitions

#define EF_SYNC

long raw_offset;  //value that determines the offset in the calibration (tare)
long raw_calibration; //value with applied force to determine the calibration factor
unsigned long time_now = 0; // timestamp to send
long loadcell_read; //value send to python in the work loop


byte controll_byte;
byte exitFlag = 0xF0;
unsigned long previous_time = 0;
const unsigned long wait_time = 5000;


//variable scale datentyp HX711
HX711 loadcell;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(57600);
  loadcell.begin(PIN_DT,PIN_SCK,64);
  attachInterrupt(digitalPinToInterrupt(SYNC_PIN), syncInterrupt, FALLING);
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available()) {
    controll_byte = Serial.read();
    //controll_byte = strtol(controll_byte, NULL, 16);
    //Serial.print("Command: ");
    //Serial.println(controll_byte);

  }
  
  switch (controll_byte)
  {
  case WORK_COMMAND:
    //as long the exitFlag command is not read the work loop continiuos
    exitFlag = 0x00;
    //Serial.println("work commandbyte read");
    while (exitFlag != 0xF0) {
      //Serial.println("workloop");
      work(); 
      if (Serial.available()){
          // sets exitFlag to incoming byte
          // only if exitFlag is 1111 0000 the loop will be left
          exitFlag = Serial.read();
          //Serial.println("exit commandbyte read");
      }
      // checks every five seconds if data is in buffer
      if (time_now - previous_time >= wait_time) {
        if (Serial.available()){
          // sets exitFlag to incoming byte
          // only if exitFlag is 1111 0000 the loop will be left
          exitFlag = Serial.read();
          //Serial.println("exit commandbyte read");
        }
      }
    }
    controll_byte = 0x00;
    break;
  case CALIBRATION_COMMAND:
    // controll sequence is initiated using 1100 0000
    calibration();
    controll_byte = 0x00;
    break;
  case SYNC_COMMAND:
    //sync sequence is initiated using 1110 0000
    sync();
    controll_byte = 0x00;
    break;
  }



}

void work() {
  loadcell_read = loadcell.read();
  time_now = millis();
  
  Serial.write((byte*) &loadcell_read, sizeof(loadcell_read));
  Serial.write((byte*) &time_now, sizeof(time_now));
  Serial.println();
    
}
void syncInterrupt(){
  time_now = micros();
  exitFlag = 0xF0;
}
void sync() {
  exitFlag = 0x00;
  //Serial.println("syncfunction initiated");
  while(exitFlag != 0xF0){
    //Serial.println("syncloop");
    //just waits for interrupt
  }
  Serial.write((byte*) &time_now, sizeof(time_now));
  Serial.println();
}
void calibration() {
  // stays in loop as long the commands are not given
  exitFlag = 0x00;
  Serial.println("calibration function initiated");
  while (exitFlag != 0xF0) {
    //Serial.println("tareloop");
    //only triggers if tare command is given 0000 1010
    if (Serial.read() == TARE_COMMAND){
      //Serial.println("raw tare commandbyte read");
      // measuring the offset
      raw_offset = loadcell.read_average(50);
      exitFlag = 0xF0;
    }
  }

  exitFlag = 0x00;
  while (exitFlag != 0xF0) {
    //Serial.println("raw cal value loop");
     //only triggers if calibration raw value command is given 0000 1011
    if (Serial.read() == RAW_CALL_COMMAND ){
      //Serial.println("raw cal commandbyte read");
      //measuring the raw value after the calibration weight is placed
      raw_calibration = loadcell.read_average(50);
      exitFlag = 0xF0;
    }
  }
  //Serial.println("sending calibration values");
  //when both values are read the arduino sends them as 10 byte strings
  raw_offset = raw_offset | 0x80000000;
  Serial.write((byte*) &raw_offset, sizeof(raw_offset));
  Serial.write((byte*) &raw_calibration, sizeof(raw_calibration));
  Serial.println();
}