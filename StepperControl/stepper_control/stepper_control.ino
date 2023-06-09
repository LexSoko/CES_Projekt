#include <AccelStepper.h>

const int x_stp_pin = 2;
const int x_dir_pin = 5;

const int y_stp_pin = 3;
const int y_dir_pin = 6;

const int enable_stp = 8;

AccelStepper step_x(AccelStepper::DRIVER, x_stp_pin,x_dir_pin);

void setup() {
  // put your setup code here, to run once:
  step_x.setPinsInverted(false,false,true);
  step_x.setEnablePin(enable_stp);
  step_x.enableOutputs();

  
  Serial.begin(57600);
  step_x.setMaxSpeed(1000);

  //pinMode(x_stp_pin,OUTPUT);
  //pinMode(x_dir_pin,OUTPUT);
  //pinMode(enable_stp,OUTPUT);

  //digitalWrite(enable_stp, LOW);
  //Serial.println("start");
  //digitalWrite(x_dir_pin,HIGH);
}

void loop() {
  step_x.setSpeed(200.0);
  step_x.runSpeed();
  //digitalWrite(x_stp_pin,HIGH);
  //delayMicroseconds(500);
  //digitalWrite(x_stp_pin,LOW);
  //delayMicroseconds(500);
}
