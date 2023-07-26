#include "HX711.h"

#define PIN_DT 2
#define PIN_SCK 3 
#define BTN_CAL 8

float weight = 500;
bool btn_bool;
long offset;
long calibration_factor = -460;
unsigned long time_now = 0;
long loadcell_read;
//variable scale datentyp HX711
HX711 loadcell;

void setup() {

  
  Serial.begin(57600);
 
 
  loadcell.begin(PIN_DT,PIN_SCK,64);
  //loadcell.set_scale(calibration_factor);
  
  pinMode(BTN_CAL,INPUT_PULLUP);
  
  
  // put your setup code here, to run once:

}

void loop() {
    btn_bool = digitalRead(BTN_CAL);
  if (btn_bool == LOW) {
     
      // measuring the offset
      long r1 = loadcell.read_average(50);
      
      time_now = millis();
      delay(10000);
    
      long r2 = loadcell.read_average(50);
     
  
      r1 = r1 | 0x80000000;
      Serial.write((byte*) &r1, sizeof(r1));
      Serial.write((byte*) &r2, sizeof(r2));
      Serial.println();
      
      
    }
    loadcell_read = loadcell.read();
    time_now = micros();
    
    Serial.write((byte*) &loadcell_read, sizeof(loadcell_read));
    Serial.write((byte*) &time_now, sizeof(time_now));
    Serial.println();
    
    
    
}
