#define DATA_PIN_A 2
#define DATA_PIN_B 3

#include <Encoder.h>
#include <util/atomic.h>


Encoder rotaryEncoder(DATA_PIN_A, DATA_PIN_B);


void setup() {
  Serial.begin(57600);
  // Serial.println("Rotary Encoder Test:");
}

long oldPosition  = -999;
unsigned long newPosition = 0;
unsigned long time = 0;

void loop() {
  newPosition = rotaryEncoder.read();
  time = micros();

  //Serial.write(newPosition>>24);
  //Serial.write(newPosition>>16);
  //Serial.write(newPosition>>8);

  Serial.write((byte*) &newPosition, sizeof(newPosition));
  //Serial.print(newPosition);
  //Serial.print(";");

  //Serial.write(time>>24);
  //Serial.write(time>>16);
  //Serial.write(time>>8);

  Serial.write((byte*)&time, sizeof(time));
  
  //Serial.print(time);
  Serial.println();
}