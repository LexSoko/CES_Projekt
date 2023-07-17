#include "HX711.h"

#define PIN_DT 2
#define PIN_SCK 3 
#define BTN_CAL 8
#define SYNC_PIN 7


long raw_offset;  //value that determines the offset in the calibration (tare)
long raw_calibration; //value with applied force to determine the calibration factor
unsigned long time_now = 0; // timestamp to send
long loadcell_read; //value send to python in the work loop
char commandbuffer[256]; 

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

  
  
  
  pinMode(BTN_CAL,INPUT_PULLUP);
  
  
  // put your setup code here, to run once:
}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available()) {
    controll_byte = Serial.read();
  }
  
// Work function is initiated using the first bit of the read byte (1000 0000)
  if (controll_byte == 0x80) {
    //as long the exitFlag command is not read the work loop continiuos
    while (exitFlag != 0xF0) {
      work(); 
      // checks every five seconds if data is in buffer
      if (time_now - previous_time >= wait_time) {
        if (Serial.available()){
          // sets exitFlag to incoming byte
          // only if exitFlag is 1111 0000 the loop will be left
          exitFlag = Serial.read();
        }
      }
    }
  }
  // controll sequence is initiated using 1100 0000
  if (controll_byte == 0xC0) {
    calibration();
  }
  //sync sequence is initiated using 1110 0000
  if (controll_byte == 0xE0) {
    sync();
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
  while(exitFlag != 0xF0){
    //just waits for interrupt
  }
}
void calibration() {
  // stays in loop as long the commands are not given
  exitFlag = 0x00;
  while (exitFlag != 0xF0) {
    //only triggers if tare command is given 0000 1010
    if (Serial.read() == 0x0A){
      // measuring the offset
      raw_offset = loadcell.read_average(50);
      exitFlag = 0xF0;
    }
  }

  exitFlag = 0x00;
  while (exitFlag != 0xF0) {
     //only triggers if calibration raw value command is given 0000 1011
    if (Serial.read() == 0x0B){
      //measuring the raw value after the calibration weight is placed
      raw_calibration = loadcell.read_average(50);
      exitFlag = 0xF0;
    }
  }
  //when both values are read the arduino sends them as 10 byte strings
  raw_offset = raw_offset | 0x80000000;
  Serial.write((byte*) &raw_offset, sizeof(raw_offset));
  Serial.write((byte*) &raw_calibration, sizeof(raw_calibration));
  Serial.println();
}