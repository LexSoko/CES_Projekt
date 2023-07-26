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
#define HALF_MAX_TICKS 32768
#define MAX_STEPS 255


// fastaccelstepper objects
FastAccelStepperEngine engine = FastAccelStepperEngine();
FastAccelStepper *stepper1 = NULL;
FastAccelStepper *stepper2 = NULL;

//TMC driver objects
TMC2209Stepper driver1(&STEPPER_SERIAL, R_SENSE , DRIVER_ADDRESS_1);
TMC2209Stepper driver2(&STEPPER_SERIAL, R_SENSE , DRIVER_ADDRESS_2);

/*
  Adds a Stepper command to the FAS queue and waits until the queue has place
  returns true if command was command was enqueued succesfully
*/
bool addCmd1(uint16_t ticks, uint8_t steps,bool dir) {
  struct stepper_command_s cmd = {
        .ticks = ticks, .steps = steps, .count_up = dir};
  while (true) {
    int rc = stepper1->addQueueEntry(&cmd);
    //TODO: add further info returns from queue
    if (rc == AQE_OK) {
      return true;
    }
    // adding a delay(1) causes problems
    delayMicroseconds(1000);
  }
  return false;
}

/*
  Adds a Stepper command to the FAS queue and waits until the queue has place
  returns true if command was command was enqueued succesfully
*/
bool addCmd2(uint16_t ticks, uint8_t steps,bool dir) {
  struct stepper_command_s cmd = {
        .ticks = ticks, .steps = steps, .count_up = dir};
  while (true) {
    int rc = stepper2->addQueueEntry(&cmd);
    //TODO: add further info returns from queue
    if (rc == AQE_OK) {
      return true;
    }
    // adding a delay(1) causes problems
    delayMicroseconds(1000);
  }
  return false;
}

void idle(){
  //do fast checks
  //TODO: add stuff to do
}

/*
  Prepare calculated movement block into stepper commands for the two axis.
  stepper commands are prepared to meet the FAS library limitations:
  ticks <= MAX_TICKS = 2^16 -1 (uint16_t)
  steps <= MAX_STEPS = 2^8 -1  (uint8_t)
*/
void addBlock(uint32_t ticks1, uint32_t steps1, bool dir1, uint32_t ticks2, uint32_t steps2, bool dir2){
  uint32_t  myTicks1 = ticks1,
            mySteps1 = steps1;
  bool      cmdsToEnqueue1 = (steps1 != 0),
            tickStepActive1 = false;

  uint32_t  myTicks2 = ticks2,
            mySteps2 = steps2;
  bool      cmdsToEnqueue2 = (steps2 != 0),
            tickStepActive2 = false;
  
  do{
    idle();

    // try to enqueue a command for stepper 1
    if(cmdsToEnqueue1 && !stepper1->isQueueFull()){
      if(ticks1 <= MAX_TICKS){
        // ticks are legal for stepper queue
        // only steps have to be seperated if there are too many
        if(mySteps1 <= MAX_STEPS){
          // no step seperation needed 
          if(addCmd1((uint16_t)ticks1,(uint8_t)mySteps1,dir1)){
            mySteps1 = 0;
          }
        } else {
          // step seperation needed
          if(addCmd1((uint16_t)ticks1,(uint8_t)MAX_STEPS,dir1)){
            mySteps1 -= MAX_STEPS;
          }
        }

      } else {
        // to many ticks -> multiple cmds needed for 1 step
        if(!tickStepActive1){
          // first cmd for step
          myTicks1 = ticks1;
          if(addCmd1((uint16_t) HALF_MAX_TICKS, (uint8_t)1, dir1)){
            tickStepActive1 = true;
            myTicks1 -= HALF_MAX_TICKS;
            mySteps1 --;
          }
        } else if(myTicks1 > MAX_TICKS) {
          // intermediate wait commands for step
          if(addCmd1((uint16_t) HALF_MAX_TICKS, (uint8_t)0, dir1)){
            tickStepActive1 = true;
            myTicks1 -= HALF_MAX_TICKS;
          }
        } else {
          // last wait command for step
          if(addCmd1((uint16_t) myTicks1, (uint8_t)0, dir1)){
            tickStepActive1 = false;
            myTicks1 = 0;
          }
        }
      }

      if((mySteps1 == 0) && !tickStepActive1){
        // block enqueuement is finished for stepper 1
        cmdsToEnqueue1 = false;
      }
    } // stepper 1 cmd enqueuement attempt finished


    // try to enqueue a command for stepper 2
    if(cmdsToEnqueue2 && !stepper2->isQueueFull()){
      if(ticks2 <= MAX_TICKS){
        // ticks are legal for stepper queue
        // only steps have to be seperated if there are too many
        if(mySteps2 <= MAX_STEPS){
          // no step seperation needed 
          if(addCmd2((uint16_t)ticks2,(uint8_t)mySteps2,dir2)){
            mySteps2 = 0;
          }
        } else {
          // step seperation needed
          if(addCmd2((uint16_t)ticks2,(uint8_t)MAX_STEPS,dir2)){
            mySteps2 -= MAX_STEPS;
          }
        }

      } else {
        // to many ticks -> multiple cmds needed for 1 step
        if(!tickStepActive2){
          // first cmd for step
          myTicks2 = ticks2;
          if(addCmd2((uint16_t) HALF_MAX_TICKS, (uint8_t)1, dir2)){
            tickStepActive2 = true;
            myTicks2 -= HALF_MAX_TICKS;
            mySteps2 --;
          }
        } else if(myTicks2 > MAX_TICKS) {
          // intermediate wait commands for step
          if(addCmd2((uint16_t) HALF_MAX_TICKS, (uint8_t)0, dir2)){
            tickStepActive2 = true;
            myTicks2 -= HALF_MAX_TICKS;
          }
        } else {
          // last wait command for step
          if(addCmd2((uint16_t) myTicks2, (uint8_t)0, dir2)){
            tickStepActive2 = false;
            myTicks2 = 0;
          }
        }
      }

      if((mySteps2 == 0) && !tickStepActive2){
        // block enqueuement is finished for stepper 2
        cmdsToEnqueue2 = false;
      }
    } // stepper 2 cmd enqueuement attempt finished

  }while(cmdsToEnqueue1 || cmdsToEnqueue2);

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
  driver1.microsteps(0);
  driver1.en_spreadCycle(false);
  driver1.pwm_autoscale(true);

  // Stepper 1 Driver settings
  driver2.begin();
  driver2.toff(4);
  driver2.rms_current(500);
  driver2.microsteps(0);
  driver2.en_spreadCycle(false);
  driver2.pwm_autoscale(true);

  // fastaccelstepper stuff
  engine.init();
  stepper1 = engine.stepperConnectToPin(STEP_PIN_1);
  stepper2 = engine.stepperConnectToPin(STEP_PIN_2);

  if (stepper1) {
    stepper1->setDirectionPin(DIR_PIN_1);
    stepper1->setEnablePin(EN_PIN);
    stepper1->setAutoEnable(true);
    Serial.println("Stepper1 configuration finished succesfully");
  }
  if (stepper2) {
    stepper2->setDirectionPin(DIR_PIN_2);
    stepper2->setEnablePin(EN_PIN);
    stepper2->setAutoEnable(true);
    Serial.println("Stepper2 configuration finished succesfully");
  }
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
    uint32_t ticks = TICKS_PER_S / 2 / (SEGMENTS - k);

    uint32_t steps = MAX_TICKS / ticks;
    if(steps == 0) steps = 1;
    addBlock(ticks,steps*2,direction,ticks*2,steps,!direction);
  }

  Serial.println("no more commands to be created");
  while ((!stepper1->isQueueEmpty()) && (!stepper2->isQueueEmpty())) {
  }
  Serial.println("queue is empty");

  while ((stepper1->isRunning()) && (stepper2->isRunning())) {
  }

  Serial.println("stepper has stopped");

  delay(1000);
  direction = !direction;


}
