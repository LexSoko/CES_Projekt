#include "HX711.h"

#define PIN_DT 2
#define PIN_SCK 3 
#define BTN_CAL 8

float weight = 177.0;
bool btn_bool;
int val = 0;
float calibration_factor = -460;
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
   
    
      loadcell.set_scale();
      Serial.print("remove any weight");
      
      loadcell.tare(50);
      Serial.println("Tare done");
      Serial.print("Place Calibration weight \t");
      time_now = millis();
      while(millis() < time_now + 10000){
        
      }
    
      long reading = loadcell.get_units(50);
      Serial.println("reading: \t");
      Serial.println(reading);
      calibration_factor = float(reading)/float(weight);
      Serial.print("calibration factor: \t");
      Serial.print(calibration_factor);
      loadcell.set_scale(calibration_factor);
      }
      
    
    loadcell_read = loadcell.get_units();
    
    Serial.println(loadcell_read);
    
    
    
}
