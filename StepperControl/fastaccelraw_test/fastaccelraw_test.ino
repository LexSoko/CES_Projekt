#include <HardwareSerial.h>
#include <TMCStepper.h>
#include <FastAccelStepper.h>

#define EN_PIN              2          // Enable
#define STEPPER_SERIAL      Serial2    // TMC2208/TMC2224 HardwareSerial port
#define R_SENSE             0.11f      // E_SENSE for current calc.

#define DRIVER_ADDRESS_1    0b00       // TMC2209 Driver address according to MS1 and MS2
#define DIR_PIN_1           4          // Direction
#define STEP_PIN_1          5          // Step

#define DRIVER_ADDRESS_2    0b10       // TMC2209 Driver address according to MS1 and MS2
#define DIR_PIN_2           18          // Direction
#define STEP_PIN_2          19          // Step

// FAS calculation stuff
#define MAX_TICKS 65535
#define MAX_STEPS 255


// fastaccelstepper objects
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper1 = NULL;
//FastAccelStepper *stepper2 = NULL;

//TMC driver objects
TMC2209Stepper driver1(&STEPPER_SERIAL, R_SENSE , DRIVER_ADDRESS_1);
//TMC2209Stepper driver2(&STEPPER_SERIAL, R_SENSE , DRIVER_ADDRESS_2);

/*
  Adds a Stepper command to the FAS queue and waits until the queue has place
*/
void addCmd1(uint16_t ticks, uint8_t steps,bool dir) {
  //TODO: add idle when the queue is full
  struct stepper_command_s cmd = {
        .ticks = ticks, .steps = steps, .count_up = dir};
  while (true) {
    int rc = stepper1->addQueueEntry(&cmd);
    if (rc == AQE_OK) {
      break;
    }
    // adding a delay(1) causes problems
    delayMicroseconds(1000);
  }
}

/*
  Adds a Stepper Block with constant speed to the FAS library queue
  This function has to generate multiple Stepper Commands for one Block if
  the Block includes more then 255 Steps (bc library takes steps as uint8_t)
  and if the block has more than 65535 ticks per Step (bc lib takes ticks as uint16_t)
*/
void addBlock1(uint32_t ticks, uint32_t steps, bool dir){
  //TODO: Test this function extensively
  //TODO: check if a command can handle more than MAX_TICKS/2

  uint32_t myTicks = ticks;
  uint32_t mySteps = steps;

  if(myTicks <= MAX_TICKS){

    while(mySteps > MAX_STEPS){
      addCmd1((uint16_t)ticks, (uint8_t)MAX_STEPS,dir);
      mySteps -= MAX_STEPS;
    }

    if(mySteps >0){
      addCmd1((uint16_t)ticks, (uint8_t)mySteps,dir);
    }

  } else {
    while(mySteps > 0){

      addCmd1((uint16_t)(MAX_TICKS/2),(uint8_t)1,dir);
      myTicks -= (MAX_TICKS/2);
      mySteps -= 1;

      while(myTicks > MAX_TICKS){
        addCmd1((uint16_t)(MAX_TICKS/2), (uint8_t)0,dir);
        myTicks -= (MAX_TICKS/2);
      }

      if(myTicks >0){
        addCmd1((uint16_t)myTicks, (uint8_t)0,dir);
      }

    }
  }
}


void setup() {
  // PC connection
  Serial.begin(250000);         // Init serial port and set baudrate
  while(!Serial);               // Wait for serial port to connect
  Serial.println("\nStart...");

  // stepper driver serial connection
  STEPPER_SERIAL.begin(9600);

  // Stepper 1 Driver settings
  driver1.begin();
  driver1.toff(4);
  driver1.rms_current(500);
  driver1.microsteps(64);
  driver1.en_spreadCycle(false);
  driver1.pwm_autoscale(true);

    // Stepper 1 Driver settings
  //driver2.begin();
  //driver2.toff(4);
  //driver2.rms_current(500);
  //driver2.microsteps(0);
  //driver2.en_spreadCycle(false);
  //driver2.pwm_autoscale(true);

  // fastaccelstepper stuff
  engine.init();
  stepper1 = engine.stepperConnectToPin(STEP_PIN_1);
  //stepper2 = engine.stepperConnectToPin(STEP_PIN_2);

  if (stepper1) {
    stepper1->setDirectionPin(DIR_PIN_1);
    stepper1->setEnablePin(EN_PIN);
    stepper1->setAutoEnable(true);
    Serial.println("Stepper1 configuration finished succesfully");
  }
  //if (stepper2) {
  //  stepper2->setDirectionPin(DIR_PIN_2);
  //  stepper2->setEnablePin(EN_PIN);
  //  stepper2->setAutoEnable(true);
  //  Serial.println("Stepper2 configuration finished succesfully");
  //}
}


#define SEGMENTS 500
bool direction = false;
void loop() {
  if (!stepper1) return;

  Serial.println("Start");
  for (uint32_t seg = 1; seg < SEGMENTS; seg++) {
    // Ticks at start/end: 10ms
    // @step = STEPS/2: it is 10ms/STEPS for STEPS=500 => 20us
    uint32_t k = max(seg, SEGMENTS - seg);
    uint32_t ticks = TICKS_PER_S / 100 / (SEGMENTS - k);
    uint16_t curr_ticks;
    uint8_t steps;
    if (ticks > MAX_TICKS) {
      curr_ticks = 32768;
      steps = 1;
    } else {
      steps = MAX_TICKS / ticks;
      curr_ticks = ticks;
    }
    ticks -= curr_ticks;

    addCmd1(curr_ticks, steps, direction);

    // this part is for the waiting commands, when speed is to low for library
    // this adds waiting commands with Length MAX_TICKS/2 until step time for current speed is reached
    while (ticks > 0) {
      uint16_t curr_ticks;
      if (ticks > MAX_TICKS) {
        curr_ticks = 32768;
      } else {
        curr_ticks = ticks;
      }
      ticks -= curr_ticks;
      addCmd1(curr_ticks, 0, direction);
    }
  }

  Serial.println("no more commands to be created");
  while (!stepper1->isQueueEmpty()) {
  }
  Serial.println("queue is empty");

  while (stepper1->isRunning()) {
  }

  Serial.println("stepper has stopped");

  delay(1000);
  direction = !direction;


}
