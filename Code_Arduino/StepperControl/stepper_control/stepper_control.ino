#include <AccelStepper.h>
#include <SoftwareSerial.h>
#include <TMCStepper.h>


const int x_stp_pin = 2;
const int x_dir_pin = 5;

const int y_stp_pin = 3;
const int y_dir_pin = 6;

const int enable_stp = 8;

const int rx_sw_pin = 12;
const int tx_sw_pin = 13;
const float r_sense = 0.11f;

AccelStepper step_x(AccelStepper::DRIVER, x_stp_pin,x_dir_pin);
SoftwareSerial tmc2209(rx_sw_pin,tx_sw_pin);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for Native USB only
  }

  Serial.println("Goodnight moon!");
  tmc2209.begin(38400);

  step_x.setPinsInverted(false,false,true);
  step_x.setEnablePin(enable_stp);
  step_x.enableOutputs();

  
  //Serial.begin(57600);
  step_x.setMaxSpeed(8000);

  //pinMode(x_stp_pin,OUTPUT);
  //pinMode(x_dir_pin,OUTPUT);
  //pinMode(enable_stp,OUTPUT);

  //digitalWrite(enable_stp, LOW);
  //Serial.println("start");
  //digitalWrite(x_dir_pin,HIGH);
}

void loop() {

  if (tmc2209.available())
    Serial.write(tmc2209.read());


  //if (Serial.available())
  //  mySerial.write(Serial.read());
    
  step_x.setSpeed(8000.0);
  step_x.runSpeed();
  //digitalWrite(x_stp_pin,HIGH);
  //delayMicroseconds(500);
  //digitalWrite(x_stp_pin,LOW);
  //delayMicroseconds(500);
}
