#include <Encoder.h>


/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Global Variables                              */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
#define DATA_PIN_A 2
#define DATA_PIN_B 3

volatile bool syncState = false;
volatile unsigned long syncTime;

long oldPosition = -999;
long newPosition = 0;
unsigned long time = 0;

Encoder rotaryEncoder(DATA_PIN_A, DATA_PIN_B);


/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    IRS                                           */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
void syncISR() {
  syncTime = micros();  // ist so 128 microsekunden schneller als wenn nach der ISR
  syncState = true;

}

/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Functions                                     */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
void syncController(bool sendflag = false, int INTERRUPT_PIN_SYNC = 2, int SYNC_SEND = 4 ) {
  
  delay(50);

  if(sendflag == true){
    pinMode(SYNC_SEND, OUTPUT);
    digitalWrite(SYNC_SEND, HIGH);
  }

  pinMode(INTERRUPT_PIN_SYNC, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN_SYNC), syncISR, LOW);

  while (syncState == false){
    if(sendflag == true){
      digitalWrite(SYNC_SEND, LOW);
    }
  }

  Serial.println(syncTime);
  // Serial.write((byte*)&syncTime, sizeof(syncTime));
  // Serial.write((byte*)&syncTime, sizeof(syncTime));
  // Serial.println();

  delay(1000);
}



/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Setup                                         */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
void setup() {
  Serial.begin(57600);
  syncController(true);
}


// Loop
void loop() {



  newPosition = rotaryEncoder.read();
  time = micros();

  // Serial.write((byte*)&newPosition, sizeof(newPosition));

  // Serial.write((byte*)&time, sizeof(time));
  Serial.println(newPosition);
  Serial.println();
}