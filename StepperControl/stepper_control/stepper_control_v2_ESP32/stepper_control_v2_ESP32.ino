#include <HardwareSerial.h>
#include <TMCStepper.h>
#include <FastAccelStepper.h>

/*
Note:
Select "ESP32 Dev Module" as board

when uploading to esp32, hold boot button when text with
loading points appears in the upload terminal!
*/

/*
  Problem1:
  StepperDriver doesn't react to Serial Commands and no meaningfull values can be read out from the driver

  Possible Causes:
   -  Driver Serial port not initialized correctly -> test driver.beginSerial line
   -  TMC driver object not initialized correctly -> test commented line at initialization
   -  Hardware wiring is faulty -> check signals with oszi
   -  Driver must be enabled for Serial communication -> Do fastStepper stuff before TMC2209 Driver stuff
      workaround -> set enable to HIGH manually with 4 commented lines after DIAG Pin initialization

  Testobservations:
   -  UART Schnittstelle funzt es war TX RX auf ESP32 Seite vertauscht
*/


//#define DIAG_PIN_2          19          // STALL motor 2
#define EN_PIN              2          // Enable
#define SERIAL_PORT_2       Serial2    // TMC2208/TMC2224 HardwareSerial port
#define DRIVER_ADDRESS_1    0b00       // TMC2209 Driver address according to MS1 and MS2

#define DIR_PIN_1           4          // Direction
#define STEP_PIN_1          5          // Step

//#define DIR_PIN_2           18          // Direction
//#define STEP_PIN_2          19          // Step

#define R_SENSE_2            0.11f      // E_SENSE for current calc.  
#define STALL_VALUE_2        2          // [0..255]

FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper1 = NULL;

TMC2209Stepper driver1(&SERIAL_PORT_2, R_SENSE_2 , DRIVER_ADDRESS_1);

void setup() {
  Serial.begin(250000);         // Init serial port and set baudrate
  while(!Serial);               // Wait for serial port to connect
  Serial.println("\nStart...");

  // init driver serial port
  SERIAL_PORT_2.begin(9600);
  //SERIAL_PORT_2.write("Hello");

  driver1.begin();

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
  driver1.toff(4);
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
  driver1.blank_time(24);
  /*
    sets the RMS current Limit in mA
  */
  driver1.rms_current(500);
  /*
  sets the microstepping resolution
  */
  driver1.microsteps(0);

  /*
    TODO: research functions
  */
  driver1.TCOOLTHRS(0xFFFFF); // 20bit max
  driver1.semin(0);
  driver1.semax(2);
  driver1.shaft(false);
  driver1.sedn(0b01);
  driver1.SGTHRS(STALL_VALUE_2);
  
  Serial.print(driver1.GCONF(), HEX);
  Serial.print(" ");
  Serial.print(driver1.GSTAT(), HEX);
  Serial.print(" ");
  Serial.print(driver1.OTP_READ(), HEX);
  Serial.print(" ");
  Serial.print(driver1.IOIN(), HEX);
  Serial.print(" ");


  engine.init();
  stepper1 = engine.stepperConnectToPin(STEP_PIN_1);
  if (stepper1) {
    stepper1->setDirectionPin(DIR_PIN_1);
    stepper1->setEnablePin(EN_PIN);
    stepper1->setAutoEnable(true);

    // If auto enable/disable need delays, just add (one or both):
    // stepper->setDelayToEnable(50);
    // stepper->setDelayToDisable(1000);

    stepper1->setSpeedInUs(1250);  // the parameter is us/step !!!
    stepper1->setAcceleration(1000);
    stepper1->move(8000);
  }

  //activate_interrupt();
}

void loop() {
 static uint32_t last_time=0;
 uint32_t ms = millis();
 if((ms-last_time) > 100) { //run every 0.1s
    last_time = ms;

    Serial.print("0 ");
    Serial.print(driver1.GCONF(), HEX);
    Serial.print(" ");
    Serial.println(driver1.cs2rms(driver1.cs_actual()), DEC);
  }
}
