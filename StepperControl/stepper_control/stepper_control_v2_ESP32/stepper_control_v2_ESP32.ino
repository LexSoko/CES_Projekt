#include <HardwareSerial.h>
#include <TMCStepper.h>
#include <FastAccelStepper.h>

/*
Note:
Select "ESP32 Dev Module" as board

when uploading to esp32, hold boot button when text with
loading points appears in the upload terminal!
*/


#define DIAG_PIN_2         19          // STALL motor 2
#define EN_PIN_2           18          // Enable
#define DIR_PIN_2          4          // Direction
#define STEP_PIN_2         5          // Step
#define SERIAL_PORT_2      Serial2    // TMC2208/TMC2224 HardwareSerial port
#define DRIVER_ADDRESS_2   0b00       // TMC2209 Driver address according to MS1 and MS2
#define R_SENSE_2          0.11f      // E_SENSE for current calc.  
#define STALL_VALUE_2      2          // [0..255]

FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper = NULL;

//hw_timer_t * timer1 = NULL;
TMC2209Stepper driver2(&SERIAL_PORT_2, R_SENSE_2 , DRIVER_ADDRESS_2 );


//void IRAM_ATTR onTimer() {
//
//  digitalWrite(STEP_PIN_2, !digitalRead(STEP_PIN_2));
//} 

void setup() {
  Serial.begin(250000);         // Init serial port and set baudrate
  while(!Serial);               // Wait for serial port to connect
  Serial.println("\nStart...");
  SERIAL_PORT_2.begin(115200);
  
  pinMode(DIAG_PIN_2 ,INPUT);
//  pinMode(EN_PIN_2 ,OUTPUT);
//  pinMode(STEP_PIN_2 ,OUTPUT);
//  pinMode(DIR_PIN_2 ,OUTPUT);

//  digitalWrite(EN_PIN_2 ,LOW);
//  digitalWrite(DIR_PIN_2 ,LOW);

  driver2.begin();
  /*
  Research(numbers are chapters of TMC2209 datasheet):
    TOFF is mentioned in:
     - 5.1.1 (Registry Map-OTP_READ (for power up defaults)) pg.23/24
     - 5.5.1 (Registry Map-CHOPCONF (Chopper Configuration)) pg.31:
        size: 4 bits (toff0-3)
        func: TOFF off time and driver enable
        comm: Off time setting controls duration of slow decay phase
     - 5.5.3 (Registry Map-DRV_STATUS (Driver Status Flags)) pg.34:
        just a comment on low side shorting flag for motor phases
     - 6 (StealthChop-Parameters related to Stealth Chop) pg.44:
        desc: TOFF = General enable for the motor driver, the actual value
                      does not influence StealthChop.
        vals: 0-> Driver OFF;  1...15-> Driver Enabled
     - 7.1 (SpreadCycle Chopper-Settings) pg.45/46:
        desc: TOFF value controls the slow decay phase time t_off which idk
              what that helps at all.
  
  Conclusion:
    TOFF consists of 4 bits [5.5.1]. By writing a value other than 0
    on TOFF, the StealthChop mode is activated [6]. If SpreadCycle is
    used, the value of TOFF controls the slow decay phase time t_off
    of the Chopper-SpreadCycle [7.1].
  */
  driver2.toff(4);
  /*
  Research(numbers are chapters of TMC2209 datasheet):
    blank time is mentioned in:
     - 5.5.1 (Registry Map-CHOPCONF (Chopper Configuration)) pg.30:
        size: 2 bits (tbl0-1)
        func: TBL blank time select
        comm: Set comparator blank time to 16, 24, 32 or 40 clocks (24 recommended)
     - 6 (StealthChop-Parameters related to Stealth Chop) pg.44:
        desc: TBL = Comparator blank time. This time needs to safely
                    cover the switching event and the duration of the
                    ringing on the sense resistor. Choose a setting of
                    24 or 32 for typical applications. For higher
                    capacitive loads, 40 may be required. Lower
                    settings allow StealthChop to regulate down to
                    lower coil current values. 
  
  Conclusion:
    its some timing which for normal applications should be 24
  */
  driver2.blank_time(24);

  /*
    sets the RMS current Limit in mA
  */
  driver2.rms_current(500);

  /*
  sets the microstepping resolution
  */
  driver2.microsteps(4);
  driver2.TCOOLTHRS(0xFFFFF); // 20bit max
  driver2.semin(0);
  driver2.semax(2);
  driver2.shaft(false);
  driver2.sedn(0b01);
  driver2.SGTHRS(STALL_VALUE_2);
  
  Serial.print(driver2.GCONF(), HEX);
  Serial.print(" ");
  Serial.print(driver2.GSTAT(), HEX);
  Serial.print(" ");
  Serial.print(driver2.OTP_READ(), HEX);
  Serial.print(" ");
  Serial.print(driver2.IOIN(), HEX);
  Serial.print(" ");

  engine.init();
  stepper = engine.stepperConnectToPin(STEP_PIN_2);
  if (stepper) {
    stepper->setDirectionPin(DIR_PIN_2);
    stepper->setEnablePin(EN_PIN_2);
    stepper->setAutoEnable(true);

    // If auto enable/disable need delays, just add (one or both):
    // stepper->setDelayToEnable(50);
    // stepper->setDelayToDisable(1000);

    stepper->setSpeedInUs(10000);  // the parameter is us/step !!!
    stepper->setAcceleration(1000);
    stepper->move(800);
  }

  //activate_interrupt();
}

void loop() {
 static uint32_t last_time=0;
 uint32_t ms = millis();
 if((ms-last_time) > 100) { //run every 0.1s
    last_time = ms;

    //Serial.print("0 ");
    //Serial.print(driver2.GCONF(), HEX);
    //Serial.print(" ");
    //Serial.println(driver2.cs2rms(driver2.cs_actual()), DEC);
  }
}

//void activate_interrupt(){
//  {
//    cli();//stop interrupts
//    timer1 = timerBegin(3, 8,true); // Initialize timer 4. Se configura el timer,  ESP(0,1,2,3)
//                                 // prescaler of 8, y true es una bandera que indica si la interrupcion se realiza en borde o en nivel
//    timerAttachInterrupt(timer1, &onTimer, true); //link interrupt with function onTimer
//    timerAlarmWrite(timer1, 8000, true); //En esta funcion se define el valor del contador en el cual se genera la interrupción del timer
//    timerAlarmEnable(timer1);    //Enable timer        
//    sei();//allow interrupts
//  }
//}