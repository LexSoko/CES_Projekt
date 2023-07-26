/*
 *****************************************************************************
 * Project: Encedalus 2v0
 * Description: Stepper Motor Controller
 * Usage for: Monochromators, Stepper Motors or Filterwheel
 * Board: Arduino Nano                                                                         
 * Hardware: A4988 Power Stage, 4x20 Character Display, Joystick, Sub-D15 Interface
 * Date: 29.7.2020 - 12.1.2021 - 26.05.2021
 * 
 * Revision History:
 * 18.5.2021: Added Better homing Position
 * 20.5.2021: Adding Ramping
 * 22.5.2021: Adding Statemachine
 * 24.5.2021: Testing Sequence
 * 11.6.2021: New Speed calculation
 * 17.7.2021: adding LSF polynomial
 * 27.10.2021: adding y-axis for Microscope
 * 25.11.2021: changing motor direction
 * 12.04.2022: removed setPolynomials
 * 13.05.2022: removed delay for 200ms -> might cause trouble for display version --> Add Delay into Display Code
 * 26.02.2023: improved Display & more Joystick Tolerances due to Joystick Tolerances around the middle position.
 * Programmmer: Jan Enenkel / Part of Jan's Masters Thesis                                                         
 ******************************************************************************
*/

/*
 *****************************************************************************
 * Copyright by Jan Enenkel  - JankeyTec GmbH                                *
 * All rights are reserved.                                                  *
 *                                                                           *
 * IMPORTANT - PLEASE READ CAREFULLY BEFORE COPYING, INSTALLING OR USING     *
 * THE SOFTWARE.                                                             *
 *                                                                           *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS       *
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT         *
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS         *
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT  *
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,     *
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT          *
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,     *
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY     *
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT       *
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE     *
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.      *
 *****************************************************************************
 */

#include <LiquidCrystal.h>
#include "HX711.h"

// DEFINTION OF DIGITAL PINS for Display
#define DISP_RS 4
#define DISP_E 5
#define DISP_D4 6
#define DISP_D5 7
#define DISP_D6 8
#define DISP_D7 9

#define JOYSTICKVERSION false
#define DISPLAYVERSION false

//#define MY_IDENTITY "MotorControl_KLD4"
//#define MY_IDENTITY "Monochromator1"
//#define MY_IDENTITY "Monochromator2"
//#define MY_IDENTITY "Filterwheel_2v0"
//#define MY_IDENTITY "Enceladus_2v0_UC2"

#define MY_IDENTITY "FrankensteinsGemueseGarten_0v0"

//#define MY_IDENTITY "BottomObjectiveMotor"

// I/O DEFINITIONS for the Joystick
int ACD_X_PIN = A6;
int ACD_Y_PIN = A7;
#define JOYSTICK_BUTTON 14 // placeholder pins where nothing is connected
#define MOTOR_POSITION 15  // ->^
#define WORM_POSITION 16   // ->|

// I/O DEFINITONS for the Motors

#define SECOND_AXIS
#define MOTOR_ENABLE 11

// motor 1 is main motor and also gets faster step impulses
#define MOTOR_DIRECTION1 12  //only active one
#define MOTOR_STEP1 13

// motor 2 is secondary axis motor and gets slower step impulses by factor K_xy
#define MOTOR_DIRECTION2 9
#define MOTOR_STEP2 10

#define LOADCELL
#define PIN_DT 19
#define PIN_SCK 18
byte loadcell_gain = 64;
long loadcell_read = 0; // raw loadcell value
bool loadcell_active = false;
unsigned long time_meas = 0;
HX711 loadcell;     // loadcell instance

// Create a Display
LiquidCrystal lcd(DISP_RS, DISP_E, DISP_D4, DISP_D5, DISP_D6, DISP_D7);


///////////////////////////////////////////////////////////////
//////////////////// GLOBAL VARIABLES /////////////////////////
///////////////////////////////////////////////////////////////

// General Usecase String for UART Feedback
char string[100];

// 4x20 Character Display Strings
char TopString[20];           // Display Top String
char JoyString[20];           // Joystick Parameters
char PositionString[20];
char StateString[20];

// Joystick Position & Button State
int joystick_x_pos = 0;
int joystick_y_pos = 0;
int joystick_value = 0;           // Absolut Intensitiy how much the joystick to 

// Inputs from the Motorposition
int MotorPositionZeroState = 0;
int WormPositionZeroState = 0;       // This is Turret 0 Position!
int LastWormPosition = 0;
int Timer1DelayRegisterPreloadValue = 65000;              //

/////////////////////////////////////////// Positioning Variables ///////////////////////////////////////
int MotorDirection = 0;               // Motordirection = 0 --> Motor to the Left (CCW), Motordirection = 1 --> Motor to the right (clockwise)
int MaxMotorSpeed = 200;                 // Motorspeed can be between 0 and 1000 --> setting the timer value

// secondary axis variables
const char K_xy = 15;
int K_xy_count = 0;
int second_axis_dir_rev = 0; // 0 is same as main axis 1 is reversed of main axis
long CurrentPosition2=0;

long TargetPosition=0;                // Always Absolute
long CurrentPosition=0;               // set to 0 by home!
long LastHome=0;                      // set to 0 by home!
long Rampsteps = 0;

long lastTimeStamp = 0;

long Oversteps = 0;                // 1000 by default
long StateMachineSwitchpoint1 = 0;
long StateMachineSwitchpoint2 = 0;
char Signum = 0;
long Delta = 0;

int AccelerationCounter = 0;
int ActualMotorSpeed = 0;
int Acceleration = 1;                // Middle by default
int CruiseBackSpeed = 150;             // Default very slow

unsigned long StopWatch_BeginTime = 0;

/////////////////////////////////////////// Positioning Variables ///////////////////////////////////////

// System Relevant Bools
bool isHomecoming = false;                    // When Homcoming Command was triggered
bool MovementEnabled = false;                // true during any kind of movement
bool OverSteppingHome = false;

// Wavelengthcalculation Polynomials
double polynomial_a[3];
double polynomial_b[3];
double polynomial_c[3];
long   motor_offset[3];

int ActiveGrating = 0;

unsigned long t_begin = 0;

bool DisableIdleCurrent = false;            // Disable Idle Current when True
unsigned long DisableIdleCurrentDelayTime = 200;
unsigned long DirectionChangeDelayTime = 500;

#define STATEMACHINESTATE_IDLE         -1
#define STATEMACHINESTATE_RAMPUP        0
#define STATEMACHINESTATE_CRUISE        1
#define STATEMACHINESTATE_RAMPDOWN      2
#define STATEMACHINESTATE_DELAY         3
#define STATEMACHINESTATE_CRUISEBACK    4
#define STATEMACHINESTATE_IDLECURRENT   5

char StateMachineState = STATEMACHINESTATE_IDLE;




// UART Interface Variables
const byte numChars = 96;
char receivedChars[numChars];   // an array to store the received data
char tempChars[numChars];
bool newData = false;

////////////////////////////
// DATA PROCESSING FUNCTIONS
////////////////////////////
// from the JankeyTec Conversions.Lib
////////////////////////////
bool hasStringInside( const char *line , const char *str )
{
        if(line == NULL)
                return false;
        if( str == NULL)
                return false;

        int i = 0;
        int j = 0;
        int LineLenght = strlen( line );
        int strLen = strlen(str );
        int countcorrect = 0;

        for(  i = 0; i < LineLenght ; i++ )
        {
                countcorrect = 0;
                if( line[i] == str[0] )       // if the first char of the searching word is correct
                        {
                                for( j = 0; j < strLen ; j++ )
                                {
                                  if( line[i+j] == str[j] )
                                  {
                                    countcorrect ++;
                                  }
                                }
                                 if( countcorrect == strLen )
                                        return true;
                        }
        }

return false;
}

bool isNum( char c )
{
  if( (c >= '0') && (c <= '9') )
    return true;
return false;
}

long getLongElementFromString( char *string , int element_count , char seperator )
{
        char *p = string;
        char *p_start = NULL;
        long counter = 0;
        int i = 0;

        if( string == NULL )
                return 0;

        // Loop to start position
        while( (*(p)!= 0) && (element_count != 0) )
        {
                if( (*p)=='\n' || (*p)==0 )
                        return 0;
                if( (*p) == seperator )
                        element_count--;
                p++;
        }

        // save start of desired text
        p_start = p;

        // count text!
        while( (*(p)!= 0) && (*(p)!= seperator) && ((*p)!='\n') )
        {
                counter++;
                p++;
        }

        // allocate
        p = (char *)malloc( (counter+1) * sizeof( char ) );
        // check
        if( p == NULL )
                return 0;
        // copy
        for( i = 0; i < counter ; i++ )
            p[i] = *p_start++;

        p[i] = 0;
        counter = String(p).toInt();
        free(p);
        // return integer
        return counter;
}

char *getCharElementFromString( char *string , int element_count , char seperator )
{
        char *p = string;
        char *p_start = NULL;
        int counter = 0;
        int i = 0;

        if( string == NULL )
                return 0;

        // Loop to start position
        while( (*(p)!= 0) && (element_count != 0) )
        {
                if( (*p)=='\n' || (*p)==0 )
                        return 0;

                if( (*p) == seperator )
                        element_count--;
                p++;
        }

        // save start of desired text
        p_start = p;

        // count text!
        while( (*(p)!= 0) && (*(p)!= seperator) && ((*p)!='\n') )
        {
                counter++;
                p++;
        }

        // allocate - has to be deleted by calling function!!!
        p = (char *)malloc( (counter+1) * sizeof( char ) );
        // check
        if( p == NULL )
                return 0;
        // copy
        for( i = 0; i < counter ; i++ )
            p[i] = *p_start++;

        p[i] = 0;
        return p;
}


// END FROM THE JankeyTec CONVERSIONS.Lib // Monochromator#1 Polynomials
/*
void SetupPolynomials()
{
  polynomial_a[0] = -6.76184874e-09;
  polynomial_b[0] = 5.13927890e-03;
  polynomial_c[0] = -2.50561125e+01;
  motor_offset[0] = 0;

  polynomial_a[1] = -1.07175780e-08;
  polynomial_b[1] = 2.63719837e-02;
  polynomial_c[1] = -8.55259198e+03;
  motor_offset[1] = 0;

  polynomial_a[2] = -5.77937E-08;
  polynomial_b[2] = 0.161206429;
  polynomial_c[2] = -89717.7;
  motor_offset[2] = 0;
}*/

// Polynomials for Monochromator#2

void SetupPolynomials()
{
  polynomial_a[0] = -4.85771122214617451277e-09;//-8.45557183662918267145e-09;
  polynomial_b[0] = 9.07603084716582589331e-03;//9.49116795085348796679e-03;
  polynomial_c[0] = 1.48631947049889912016e+00;//-1.08080451342870986764e+01;
  motor_offset[0] = 0;

  polynomial_a[1] = -8.00790849468289982050e-09;
  polynomial_b[1] = 1.55348170145891122801e-02;
  polynomial_c[1] = -4.77528237836225980573e+03;
  motor_offset[1] = 0;

  polynomial_a[2] = -5.77937E-08;
  polynomial_b[2] = 0.161206429;
  polynomial_c[2] = -89717.7;
  motor_offset[2] = 0;
}

///////////////////////////////////////////
// Initialize the IC
///////////////////////////////////////////
void setup() {
  // I/Os
  // Display
  pinMode(DISP_RS, OUTPUT);
  pinMode(DISP_E, OUTPUT);
  pinMode(DISP_D4, OUTPUT);
  pinMode(DISP_D5, OUTPUT);
  pinMode(DISP_D6, OUTPUT);
  pinMode(DISP_D7, OUTPUT);  
  pinMode(MOTOR_DIRECTION1, OUTPUT);
  pinMode(MOTOR_STEP1, OUTPUT);
  pinMode(MOTOR_ENABLE, OUTPUT);
  digitalWrite(MOTOR_ENABLE, HIGH);
  digitalWrite(MOTOR_STEP1, LOW);

#ifdef SECOND_AXIS
  pinMode(MOTOR_DIRECTION2, OUTPUT);
  pinMode(MOTOR_STEP2, OUTPUT);
  digitalWrite(MOTOR_STEP2, LOW);
#endif

#ifdef LOADCELL
  loadcell.begin(PIN_DT,PIN_SCK,loadcell_gain);
#endif

  // Joystick
  if(JOYSTICKVERSION)
  {
    //pinMode(JOYSTICK_BUTTON, INPUT_PULLUP);
    pinMode(MOTOR_POSITION, INPUT_PULLUP);
    pinMode(WORM_POSITION, INPUT_PULLUP);
  }
  
  // Initialize Serial Interface
  // 1.3.2022 --> setting to 57600 Baud!!!
  Serial.begin(57600);

  // Initialize the Display
  if(DISPLAYVERSION)
  {
    lcd.begin(20, 4);
    lcd.clear();
  }

  // Configure Timer!
  noInterrupts();           // disable all interrupts
  TCCR1A = 0;
  TCCR1B = 0;

//  TCNT1 = 34286;            // preload timer 65536-16MHz/256/2Hz
  SetMotorSpeed(0);
  TCCR1B |= (1 << CS11);    // no 8 prescaler --> 0.5 us per clock
  TIMSK1 |= (1 << TOIE1);   // enable timer overflow interrupt
  interrupts();             // enable all interrupts          // enable all interrupts

  SetupPolynomials();
  
  Serial.println(MY_IDENTITY);
  Serial.println("#Partytime");
  strcpy(TopString,"#Partytime");

  lastTimeStamp = millis();
}

/////////////////////////////////////////////////////////////////////////////////////
// Processing of the USB/UART Interface
// Important Note: Strings are Terminated with '\0' not with CR or LF
/////////////////////////////////////////////////////////////////////////////////////
void ProcessUART()
{
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
   
    while (Serial.available() > 0 && newData == false)
    {
        rc = Serial.read();

        if (rc != endMarker)
        {
            receivedChars[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else
        {
            receivedChars[ndx] = '\0'; // terminate the string - 
            ndx = 0;
            newData = true;
        }
    }
}

///////////////////////////////////////////////////////////////////////////////////
// MotorCommands!!!
//////////////////////////////////////////////////////////////////////////////////

void SetMotorSpeed(int Speed)
{
  // 1000 Speed = 50us pulse time
  // 0 Speed = 1050us pulse time
  //int Timervalue = 1050 - Speed;
  int Timervalue = (int)(50.0+1000.0*exp(-Speed/120.0));
  setTimer1Time(Timervalue);
}

/////////////////////////////////////
// setTimer1Time
// Sets the Delaytime for Timer1
// 
/////////////////////////////////////
void setTimer1Time(int microseconds)
{
  Timer1DelayRegisterPreloadValue = 65535-(microseconds-2)*2;
}

/////////////////////////////////////
// MoveH
// Moving always in Absolute
/////////////////////////////////////


void MotorTurnOffCurrent()
{
        digitalWrite(MOTOR_ENABLE, HIGH);   // Turn off Motor Current
}

void MotorTurnOnCurrent()
{
          digitalWrite(MOTOR_ENABLE, LOW);   // Turn on Motor Current 
}

void Abort()
{
  StateMachineState = STATEMACHINESTATE_IDLE;
  isHomecoming = false;
  MovementEnabled = false;     // In case
  OverSteppingHome = false;
  if(DisableIdleCurrent==true)
    MotorTurnOffCurrent();
}

void StopWatch_Start()
{
  StopWatch_BeginTime = millis();
}

unsigned long StopWatch_Time()
{
  return (millis()-StopWatch_BeginTime);      // No timer overflow considered in this function, in case you need -> take it from the Hyperion project 
}

int getWormSignal()
{
  unsigned char i = 0;
  unsigned char counter = 0;
  unsigned char wormpos;
  //for( i=0;i<10;i++)
  //{
      wormpos = digitalRead(WORM_POSITION);
  /*counter += wormpos;
  }
  if(counter>5)
    return 1;
  else
    return 0;*/
    return wormpos;
}

bool DetectHomePositionFromRight()
{
            unsigned char Wormpos = 0;
            Wormpos = getWormSignal();
            if( (Wormpos==0)  && (LastWormPosition==1) )
            {
              //Serial.println("HomeFromRight");
              return true;              
            }
            LastWormPosition = Wormpos;                         // 3.4.2022 -->  Trying to fix the "missing home big"
return false;
}

bool DetectHomePositionFromLeft()
{
            unsigned char Wormpos = 0;
            Wormpos = getWormSignal();
            if( (Wormpos==1)  && (LastWormPosition==0) )
            {
              //Serial.println("HomeFromLeft");
              return true;              
            }
            LastWormPosition = Wormpos;                         // 3.4.2022 -->   Trying to fix the "missing home big"
return false;}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////
//////////      Setup State Machine
//////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void SetupStateMachine()
{
  if(StateMachineState != STATEMACHINESTATE_IDLE)
  {
    Serial.println("Ongoing Movement!");  
    return;
  }

  if(isHomecoming)                          // Homing!
  {
    LastWormPosition = getWormSignal();
    
    OverSteppingHome = false;
    MotorDirection = 0;      // LEFT
    if(Acceleration==0)      // no Acceleration, starting with cruise!
      {
        ActualMotorSpeed = MaxMotorSpeed;
        SetMotorSpeed(ActualMotorSpeed);
        StateMachineState = STATEMACHINESTATE_CRUISE;
      }
    else                      // with Acceleration, starting with Ramp
    {
        Rampsteps = Acceleration * MaxMotorSpeed *(-1);
        StateMachineSwitchpoint1 = Rampsteps + CurrentPosition;
        StateMachineState = STATEMACHINESTATE_RAMPUP;
    }
    //Serial.println("Starting Homing proecdure!");
    MovementEnabled = true;
  }
  else                                      // Regular Movement
  {
    if(TargetPosition == CurrentPosition)
    {
      Serial.println("DONE");
      return; 
    }
    
    if(TargetPosition<CurrentPosition)  // Is the target left or right from the current Position
    {
        MotorDirection = 0;      // to LEFT
        TargetPosition -= Oversteps;
    }
    else
    {
        MotorDirection = 1;      // to RIGHT
    }

    Delta = TargetPosition - CurrentPosition;
    if(Delta>0)
      Signum = 1;
    else
      Signum = -1;

    if(Acceleration!=0)   // a is ramp needed
        {
           if( (MaxMotorSpeed*Acceleration*2) > abs(Delta) )       // We are in Scenario#1 --> To short to achieve cruise altitude
           {
              StateMachineSwitchpoint2 =  Delta/2 + CurrentPosition;
              //sprintf(string, "Scenario#1 - no cruise  - decellerate at: %s",String(StateMachineSwitchpoint2, DEC).c_str());
              //Serial.println(string);
           }
           else                                                       // We are in Scenario#2 --> Cruide Altitude can be achieved
           {
              Rampsteps = Acceleration * MaxMotorSpeed;
              StateMachineSwitchpoint1 = Rampsteps*Signum      + CurrentPosition;
              StateMachineSwitchpoint2 = TargetPosition - Rampsteps*Signum;
              //sprintf(string, "Scenario#2 - with cruise  SW1: %s SW2:%s"
              //,String(StateMachineSwitchpoint1, DEC).c_str()
              //,String(StateMachineSwitchpoint2, DEC).c_str());
              //Serial.println(string);
           }
          
          AccelerationCounter = 0;
          ActualMotorSpeed =0 ;
          SetMotorSpeed(ActualMotorSpeed);
          MovementEnabled = true;
          StateMachineState = STATEMACHINESTATE_RAMPUP;
          //Serial.println("Starting Rampup!");  
        }
    else     // No acceleration needed, we are in cruising mode.
    {
      SetMotorSpeed(MaxMotorSpeed);
      MovementEnabled = true;
      StateMachineState = STATEMACHINESTATE_CRUISE;
    }
  }
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////
//////////      Process State Machine
//////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


void ProcessStateMachine()
{
  switch (StateMachineState)
  {
    case STATEMACHINESTATE_IDLE:
    // Do nothing    
    break;

    ////////////////////////////////////////////////////////
    ///////// RAMPUP 
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_RAMPUP:
    
          if(isHomecoming)
          {
            if(DetectHomePositionFromRight()) // we reached Home during rampup
            {
              // STORE POSITION!!! maybe?
              StateMachineState = STATEMACHINESTATE_RAMPDOWN;
              break;
            }
          }
          
          // Rampup for all modes
          AccelerationCounter++;
          if (AccelerationCounter>=Acceleration)
          {
            ActualMotorSpeed++;
            SetMotorSpeed(ActualMotorSpeed);
            AccelerationCounter = 0;
          }
      
          // switch to estimmode - true for all modes
          if( ActualMotorSpeed >= MaxMotorSpeed )         // We change to cruising mode!
          {
            StateMachineState = STATEMACHINESTATE_CRUISE;
          //sprintf(string, "Switching to Cruise -> Position:%s",String(CurrentPosition, DEC).c_str());
          //Serial.println(string);
          }

          if( (CurrentPosition == StateMachineSwitchpoint2) && (isHomecoming==false) )
            StateMachineState = STATEMACHINESTATE_RAMPDOWN;
    break;

    ////////////////////////////////////////////////////////
    ///////// CRUISE 
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_CRUISE:
          if(isHomecoming)
          {
            // Overstepping home is for continue of cruise during home in linear mode
            if(OverSteppingHome==true)
            {
              // Overstepping after home 'FromRight'
              if(CurrentPosition==TargetPosition)
                     {
                              MovementEnabled = false;
                              Serial.println("Overstepping done!");
                              // Check for Delay & Motorcurrent
                              StateMachineState = STATEMACHINESTATE_DELAY;
                              StopWatch_Start();
                              OverSteppingHome = false;
                              break;
                     }
            }

            // Home from right detected
            if(DetectHomePositionFromRight() && (OverSteppingHome==false))
            {
              if(Acceleration == 0 )         // Ok no decelleration
              {
                // no Oversteps -> we are already finished with movement
                if(Oversteps==0)
                {
                  MovementEnabled = false;
                  isHomecoming = false;
                  StateMachineState = STATEMACHINESTATE_IDLECURRENT;
                  LastHome = CurrentPosition;         // Store Last Home
                  CurrentPosition = 0;                // Store New Home!
                  //Serial.println("Found Home");
                  break;
                }
                else           // Detected home 'FromRight' - linear mode with overstepping
                {
                  CurrentPosition = 0;                // Store New Home!
                  LastHome = CurrentPosition;
                  TargetPosition = Oversteps*(-1);
                  StateMachineState = STATEMACHINESTATE_CRUISE;
                  //Serial.println("Starting Overstepping");
                  OverSteppingHome = true;
                  break;
                }
              }
              else    // We are in Accelerated Home mode --> Rampdown and cruiseback
              {
                StateMachineState = STATEMACHINESTATE_RAMPDOWN;
                break;
              }
            }
          }
          else      // no homecoming - regular movement
          {
              // Acceleration Mode!!!
              if(Acceleration != 0)
                if( CurrentPosition == StateMachineSwitchpoint2 )   // We arrived at Rampdown position
                {
                  //Serial.println("Switchpoint#2 -> Rampdown");
                  StateMachineState = STATEMACHINESTATE_RAMPDOWN;
                  AccelerationCounter = 0;
                }
    
              // Linear Mode
              if(Acceleration == 0)
                     if(CurrentPosition==TargetPosition)
                     {
                              MovementEnabled = false;
                              //Serial.println("Cruise Finished - Target Pos");
                              // Check for Delay & Motorcurrent
                              StateMachineState = STATEMACHINESTATE_DELAY;
                              StopWatch_Start();
                     }
              AccelerationCounter = 0;
          }
    break;
    
    ////////////////////////////////////////////////////////
    ///////// RAMPDOWN 
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_RAMPDOWN:
          
          AccelerationCounter++;
          if (AccelerationCounter>=Acceleration)
          {
            if(ActualMotorSpeed!=0)
              ActualMotorSpeed--;
            SetMotorSpeed(ActualMotorSpeed);
            AccelerationCounter = 0;
          }

//          if(ActualMotorSpeed == 0)
//          {
              // homecoming
              if(isHomecoming)        
              {
                if(ActualMotorSpeed == 0)
                {
                  StateMachineState = STATEMACHINESTATE_DELAY;
                  MovementEnabled = false;
                  StopWatch_Start();
                }
                break;
              }
              else      // no homecoming, accelerated movement
              {
                if(CurrentPosition==TargetPosition)
                {
                  //sprintf(string, "Actualmotorspeed=%s",String(ActualMotorSpeed, DEC).c_str());
                  //Serial.println(string);
                  //sprintf(string, "AcutalMotorspeed=0 -> Position:%s",String(CurrentPosition, DEC).c_str());
                  //Serial.println(string);
                  MovementEnabled = false;
                  StateMachineState = STATEMACHINESTATE_DELAY;
                  StopWatch_Start();
                }
              }
    //       }
    break;

    ////////////////////////////////////////////////////////
    ///////// DELAY
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_DELAY:
        // OK we have waited the time necessary for the timer.
        if(StopWatch_Time()>DirectionChangeDelayTime)
          {
              if(isHomecoming)    // Homecoming --> Turn direction and look for home!
              {
                // How about Oversteps?
                //Serial.println("Starting Cruiseback to Home!");
                StateMachineState = STATEMACHINESTATE_CRUISEBACK;
                MotorDirection=1;
                SetMotorSpeed(CruiseBackSpeed);
                MovementEnabled = true;
                break;
              }
              else
              {
              
                  // There is an cruiseback required
                  if( (Oversteps!=0) && (MotorDirection == 0) )
                  {
                    //Serial.println("Starting Cruiseback2!");
                    StateMachineState = STATEMACHINESTATE_CRUISEBACK;
                    TargetPosition += Oversteps;
                    MotorDirection=1;
                    SetMotorSpeed(CruiseBackSpeed);
                    MovementEnabled = true;
                  }
                  else
                  {
                    StateMachineState = STATEMACHINESTATE_IDLECURRENT;
                    StopWatch_Start();
                  }
              }
          }
        
    break;

    ////////////////////////////////////////////////////////
    ///////// CRUISEBACK
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_CRUISEBACK:
          // Check for Home
          if(isHomecoming)
          {
              if(DetectHomePositionFromLeft())
                {
                    MovementEnabled = false;
                    isHomecoming=false;
                    //Serial.println("Cruiseback found Home");
                    LastHome = CurrentPosition;         // Store Last Home
                    CurrentPosition = 0;                // Store New Home!
                    StateMachineState = STATEMACHINESTATE_IDLECURRENT;
                    StopWatch_Start();
                    break;
                }
                break;
          }
          else  // no homecoming - just regular cruiseback
          {
            if(CurrentPosition == TargetPosition)
            {
                  //Serial.println("Cruiseback finished - Cur = Target"); 
                  MovementEnabled = false;
                  StateMachineState = STATEMACHINESTATE_IDLECURRENT;
                  StopWatch_Start();
            }
          }
    break;

    ////////////////////////////////////////////////////////
    ///////// IDLECURRENT
    ////////////////////////////////////////////////////////
    case STATEMACHINESTATE_IDLECURRENT:
            MovementEnabled = false;
            if(StopWatch_Time()>DisableIdleCurrentDelayTime)
                {
                
                if(DisableIdleCurrent==false)
                  StateMachineState = STATEMACHINESTATE_IDLE;
                else
                {
                  MotorTurnOffCurrent();
                  StateMachineState = STATEMACHINESTATE_IDLE;                
                }
                
                Serial.println("DONE"); 
            }
    break;
    
    default: break;
  } 
}


void ProcessMovement()
{
    ///////////////////////////////////////////////////////////////////
    // Regular Movement, can be either by Joystick, Move or Home command
    if(MovementEnabled)
    {
        // JJJJ
        // LastWormPosition = getWormSignal();
        // Turn on the Motorcurrent (A4998 Enable Pin)
        digitalWrite(MOTOR_ENABLE, LOW);
        
        // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
            digitalWrite(MOTOR_DIRECTION1, HIGH);  // 25.11.2021 --> Change
            CurrentPosition--;
        }
        else                            // Going to the Right
        {
            digitalWrite(MOTOR_DIRECTION1, LOW); // 25.11.2021 --> Change
            CurrentPosition++;
        }
        
        digitalWrite(MOTOR_STEP1, HIGH);     // Perform one Motorstep
        digitalWrite(MOTOR_STEP1, LOW);

#ifdef SECOND_AXIS
        if((MotorDirection==0 && second_axis_dir_rev==0) ||
          (MotorDirection==1 && second_axis_dir_rev==1)) {    //forward
          digitalWrite(MOTOR_DIRECTION2, HIGH);

          if(K_xy_count == K_xy){
            digitalWrite(MOTOR_STEP2, HIGH);     // Perform one Motorstep
            digitalWrite(MOTOR_STEP2, LOW);
            K_xy_count = 0;
            CurrentPosition2 ++;
          } else {
            K_xy_count++;
          }

        } else {  //backward
          digitalWrite(MOTOR_DIRECTION2, LOW);

          if(K_xy_count == -1){
            digitalWrite(MOTOR_STEP2, HIGH);     // Perform one Motorstep
            digitalWrite(MOTOR_STEP2, LOW);
            K_xy_count = K_xy - 1;
            CurrentPosition2 --;
          } else {
            K_xy_count--;
          }
        }
#endif

    }

    if(loadcell_active && loadcell.is_ready()){
      loadcell_read = loadcell.read();
      time_meas = millis();
      sprintf(string, "m %s %s %s %s" , String(time_meas, DEC).c_str(), String(CurrentPosition, DEC).c_str(), String(CurrentPosition2, DEC).c_str(), String(loadcell_read, DEC).c_str());
      //sprintf(string, "m %d %d %d %d" , time_meas, CurrentPosition, CurrentPosition2, loadcell_read);
      Serial.println(string);
    }
}

// Step function gets called with the Timer speed.
void Step()     
{  
    ProcessStateMachine();
    ProcessMovement();
}


/////////////////////////////////////
// TIMER1_OVF_vect
// Interrupt Servie Routine
// for Timer1 --> Triggers one Step
/////////////////////////////////////
ISR(TIMER1_OVF_vect)        
{
  TCNT1 = Timer1DelayRegisterPreloadValue;
  Step();
}

void setGrating( int Number )
{
  ActiveGrating = Number;
  setWl(0);
}

void setWl( float wavelength )
{
            unsigned long CalculatedPosition;
            if( polynomial_a[ActiveGrating] == 0.0 )
              CalculatedPosition = ( wavelength - polynomial_c[ActiveGrating] ) / polynomial_b[ActiveGrating] + motor_offset[ActiveGrating];
            else
              CalculatedPosition = (-polynomial_b[ActiveGrating]+sqrt(polynomial_b[ActiveGrating]*polynomial_b[ActiveGrating]-4*polynomial_a[ActiveGrating]*(polynomial_c[ActiveGrating]-wavelength))) / (2*polynomial_a[ActiveGrating]) + motor_offset[ActiveGrating];

              sprintf(string, "Calculated: %s" , String(CalculatedPosition, DEC).c_str());
              Serial.println(string);
            
            TargetPosition = CalculatedPosition;
            isHomecoming = false;
            SetupStateMachine();  
}

/////////////////////////////////////
// ProcessReceivedData
// Parsing & Execution 
// of UART commands
/////////////////////////////////////
void ProcessReceivedData()
{
  bool understood = false;
  int GratingValue = 0;
  int i = 0;
  char *temp = strlwr(receivedChars);     // Make everything lower case!
  
  // newData defines by a '/0' from the UART Stream
  if (newData == true)
  { 
          if(hasStringInside( temp , "whoareyou" ) && (understood == false))
          {
              Serial.println(MY_IDENTITY);
              understood = true;
          }

          if(hasStringInside( temp , "getinputs" ) && (understood == false))
          {
              MotorPositionZeroState = digitalRead(MOTOR_POSITION);
              WormPositionZeroState = digitalRead(WORM_POSITION);      // Also the "Turret Position State"
              sprintf(string, "Mot=%d, Worm=%d" , MotorPositionZeroState , WormPositionZeroState );
              Serial.println(string);
              understood = true;
          }

          if(hasStringInside( temp , "lasthome" ) && (understood == false))
          {
              sprintf(string, "Lasthome: %s" , String(LastHome, DEC).c_str());
              Serial.println(string);
              understood = true;
          }

          //////////////////////////////////////////////
          // Trigger the 'home' command
          //////////////////////////////////////////////
          if(hasStringInside( temp , "home" ) && (understood == false))
          {
            Serial.println("Searching for Home Position");
            isHomecoming = true;
            SetupStateMachine();
            
            understood = true;
          }

#ifdef LOADCELL
          //////////////////////////////////////////////
          // read the average of n measured values from the loadcell
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "loadcellav" ) && (understood == false))
          {
            if(StateMachineState != STATEMACHINESTATE_IDLE){
              Serial.println("Ongoing Movement!");
              understood = true;
            }
            else
            {
              long n = getLongElementFromString(temp,1,' ');
              loadcell_read = loadcell.read_average(n);
              sprintf(string, "loadcellAverage: %s", String(loadcell_read, DEC).c_str());
              Serial.println(string);
              understood = true;
            }
          }

          //////////////////////////////////////////////
          // read one raw value from loadcell
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "loadcellraw" ) && (understood == false))
          {
            if(StateMachineState != STATEMACHINESTATE_IDLE){
              Serial.println("Ongoing Movement!");
              understood = true;
            }
            else
            {
              loadcell_read = loadcell.read();
              sprintf(string, "loadcellRaw: %s", String(loadcell_read, DEC).c_str());
              Serial.println(string);
              understood = true;
            }
          }
          //////////////////////////////////////////////
          // start continious measurements from loadcell
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "loadcellstart" ) && (understood == false))
          {
            Serial.println("measurement start!");
            loadcell_active = true;
            understood = true;
          }
          //////////////////////////////////////////////
          // stop continious measurements from loadcell
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "loadcellstop" ) && (understood == false))
          {
            Serial.println("measurement end!");
            loadcell_active = false;
            understood = true;
          }
#endif

#ifdef SECOND_AXIS //XXX
          //////////////////////////////////////////////
          // Set the 'gotorel' command --> relative movement
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "gotorelrev" ) && (understood == false))
          {
            // Staying Relative!
            long relpos = getLongElementFromString(temp,1,' ');
            second_axis_dir_rev = 1;
            TargetPosition = CurrentPosition + relpos;
            isHomecoming = false;
            SetupStateMachine();
            //sprintf(string, "Moving relative position: %s", String(relpos, DEC).c_str());
            //Serial.println(string);
            understood = true;
          }
#endif

          //////////////////////////////////////////////
          // Set the 'gotorel' command --> relative movement
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "gotorel" ) && (understood == false))
          {
            // Staying Relative!
            long relpos = getLongElementFromString(temp,1,' ');
#ifdef SECOND_AXIS
            second_axis_dir_rev = 0;
#endif
            TargetPosition = CurrentPosition + relpos;
            isHomecoming = false;
            SetupStateMachine();
            //sprintf(string, "Moving relative position: %s", String(relpos, DEC).c_str());
            //Serial.println(string);
            understood = true;
          }


          //////////////////////////////////////////////
          // Set the 'goto' command --> absolute movement
          //////////////////////////////////////////////
          if(hasStringInside( temp , "goto" ) && (understood == false))
          {
            TargetPosition = getLongElementFromString(temp,1,' ');
            sprintf(string, "Moving to absolute position: %s" , String(TargetPosition, DEC).c_str());
            Serial.println(string);
            isHomecoming = false;
            SetupStateMachine();
            
            understood = true;
          }

          if(hasStringInside( temp , "setwl" ) && (understood == false))
          {
            char *wl_string = getCharElementFromString( temp , 1 , ' ' );
            float wlValue = String(wl_string).toFloat();
            free(wl_string);
            sprintf(string, "Setting to: %s[nm]" , String(wlValue).c_str() );
            Serial.println(string);
            setWl( wlValue );
           
            understood = true;
          }

          if(hasStringInside( temp , "getpolynomials" ) && (understood == false))
          {
          sprintf(string, "Grating:%d, Polynomials: a=%s b=%s c=%s", (ActiveGrating+1)
              , String(polynomial_a[ActiveGrating]).c_str()
              , String(polynomial_b[ActiveGrating]).c_str()
              , String(polynomial_c[ActiveGrating]).c_str()  );
              Serial.println(string);

              understood = true;
          }
          
          /* 14.04.2022 --> kicked out due to low memmory.
          if(hasStringInside( temp , "setpolynomials" ) && (understood == false))
          {
            char *poly_string;
            float poly = 0.0;
            
            GratingValue = getLongElementFromString( temp , 1 , ' ' );
            if(GratingValue<1 || GratingValue>3)
            {
               Serial.println("Error: no valid Grating defined");
            }
            else
            {
              GratingValue--;
              for (i=0;i<3;i++)
              {
                poly_string = getCharElementFromString( temp , (i+2) , ' ' );
                poly = String(poly_string).toFloat();
                free(poly_string);
                if(i==0) polynomial_a[GratingValue] = poly;
                if(i==1) polynomial_b[GratingValue] = poly;
                if(i==2) polynomial_c[GratingValue] = poly;
              }
              sprintf(string, "Grating:%d, Polynomials: a=%s b=%s c=%s", (GratingValue+1)
              , String(polynomial_a[GratingValue]).c_str()
              , String(polynomial_b[GratingValue]).c_str()
              , String(polynomial_c[GratingValue]).c_str()  );
              Serial.println(string);
            }
           
            understood = true;
          }
          */

          if(hasStringInside( temp , "setgrating" ) && (understood == false))
          {
             int GratingValue = getLongElementFromString(temp,1,' ');
             if( GratingValue < 1 ) GratingValue=1;
             if( GratingValue > 3 ) GratingValue=3;
             sprintf(string, "Setting Grating: %d" , GratingValue );
             Serial.println(string);             
             GratingValue--;
             setGrating(GratingValue);

             understood = true;
          }

          /////////////////////////////////////////////
          // Set the 'disableidlecurrentdelaytime' between 0 and 100
          //////////////////////////////////////////////
          if(hasStringInside( temp , "disableidlecurrentdelaytime" ) && (understood == false))
          {
            DisableIdleCurrentDelayTime = getLongElementFromString(temp,1,' ');
            if(DisableIdleCurrentDelayTime < 0)       DisableIdleCurrentDelayTime = 0;
            if(DisableIdleCurrentDelayTime > 5000)    DisableIdleCurrentDelayTime = 5000;
            sprintf(string, "Setting DisableIdleCurrentDelayTime: %s",String(DisableIdleCurrentDelayTime, DEC).c_str());
            Serial.println(string);
            understood = true;
          }

          /////////////////////////////////////////////
          // Set the 'disableidlecurrentdelaytime' between 0 and 100
          //////////////////////////////////////////////
          if(hasStringInside( temp , "directionchangedelaytime" ) && (understood == false))
          {
            DirectionChangeDelayTime = getLongElementFromString(temp,1,' ');
            if(DirectionChangeDelayTime < 0)         DirectionChangeDelayTime = 0;
            if(DirectionChangeDelayTime > 5000)      DirectionChangeDelayTime = 5000;
            sprintf(string, "Setting DirectionChangeDelayTime: %s",String(DirectionChangeDelayTime, DEC).c_str());
            Serial.println(string);
            
            understood = true;
          }

          if(hasStringInside( temp , "disableidlecurrent" ) && (understood == false))
          {
            DisableIdleCurrent = true;
            
            if(StateMachineState == STATEMACHINESTATE_IDLE)
              MotorTurnOffCurrent();
                        
            Serial.println("Idle Current Disabled!");
            understood = true;
          }

          if(hasStringInside( temp , "enableidlecurrent" ) && (understood == false))
          {
            DisableIdleCurrent = false;
            
            if(StateMachineState == STATEMACHINESTATE_IDLE)
              MotorTurnOnCurrent();
            
            Serial.println("Idle Current Enabled!");
            understood = true;
          }          


          //////////////////////////////////////////////
          // Set the 'acceleration' between 0 and 100
          //////////////////////////////////////////////
          if(hasStringInside( temp , "acceleration" ) && (understood == false))
          {
            Acceleration = getLongElementFromString(temp,1,' ');
            if(Acceleration < 0)
              Acceleration = 0;
            if(Acceleration > 100)
              Acceleration = 100;


            // To enable linear movement
            if(Acceleration==0)
                Acceleration = 0;
            else
                Acceleration = 101-Acceleration;
            
            sprintf(string, "Setting Acceleration to : %d",Acceleration);
            Serial.println(string);
            
            
            understood = true;
          }

          //////////////////////////////////////////////
          // Set the 'oversteps' 
          //////////////////////////////////////////////
          if(hasStringInside( temp , "oversteps" ) && (understood == false))
          {
            Oversteps = getLongElementFromString(temp,1,' ');
            if(Oversteps < 0)
              Oversteps = 0;
            if(Oversteps > 10000)
              Oversteps = 10000;
            sprintf(string, "Setting Oversteps to : %d",Oversteps);
            Serial.println(string);
            understood = true;
          }

          //////////////////////////////////////////////
          // Set the 'CruiseBackSpeed' between 0 and 1000
          //////////////////////////////////////////////
          if(hasStringInside( temp , "cruisebackspeed" ) && (understood == false))
          {
            CruiseBackSpeed = getLongElementFromString(temp,1,' ');
            if(CruiseBackSpeed < 0)
              CruiseBackSpeed = 0;
            if(CruiseBackSpeed > 1000)
              CruiseBackSpeed = 1000;
            sprintf(string, "Setting cruisebackspeed to : %d",CruiseBackSpeed);
            Serial.println(string);
            understood = true;
          }

          //////////////////////////////////////////////
          // Set the 'motorspeed' between 1 and 1000
          //////////////////////////////////////////////
          if(hasStringInside( temp , "motorspeed" ) && (understood == false))
          {
            MaxMotorSpeed = getLongElementFromString(temp,1,' ');
            if(MaxMotorSpeed < 0)
              MaxMotorSpeed = 0;
            if(MaxMotorSpeed > 1000)
              MaxMotorSpeed = 1000;
            
            sprintf(string, "Setting motorspeed: %d",MaxMotorSpeed);
            Serial.println(string);
            
            //setTimer1Time( 500-MaxMotorSpeed ); // in case we are moving!
            understood = true;
          }

           //////////////////////////////////////////////
          // 'getpos' command:
          // Read back the current position
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "getpos" ) && (understood == false))
          {
            sprintf(string, "Current position: %s %s",
              String(CurrentPosition, DEC).c_str(),
              String(CurrentPosition2, DEC).c_str());
            Serial.println(string);
            understood = true;
          }

          //////////////////////////////////////////////
          // 'getWL' command:
          // Read back the current position
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "getwl" ) && (understood == false))
          {
            long pos = CurrentPosition-motor_offset[ActiveGrating];
            double WL = (double)pos*pos*polynomial_a[ActiveGrating] + (double)pos*polynomial_b[ActiveGrating] + (double)polynomial_c[ActiveGrating];
            sprintf(string, "Current WL: %2.2f - Grating: %d",WL, ActiveGrating+1 );
            Serial.println(string);
            understood = true;
          }

          //////////////////////////////////////////////
          // Trigger the 'abort' command:
          // useful for unwanted movement or 'forever home' searching.
          //////////////////////////////////////////////         
          if(hasStringInside( temp , "abort" ) && (understood == false))
          {
            sprintf(string, "Aborting movement!");
            Serial.println(string);
            Abort();
            understood = true;
          }

          //////////////////////////////////////////////
          // In case no command was understood
          // tell the user
          //////////////////////////////////////////////         
          if(understood == false)
            Serial.println("no valid command");
          
          newData = false;
  }  
}

//////////////////////////////////////////////
// Main Loop
////////////////////////////////////////////// 

void loop()
{
     // PROCESS UART
    ProcessUART();
    ProcessReceivedData();
   
   // GET INPUTS from Joystick & Motorpositions
   if(JOYSTICKVERSION)
   {
     joystick_x_pos = analogRead(ACD_X_PIN);
     joystick_y_pos = analogRead(ACD_Y_PIN);
     MotorPositionZeroState = digitalRead(MOTOR_POSITION);
     WormPositionZeroState = digitalRead(WORM_POSITION);      // Also the "Turret Position State"
   }
  
  /////////////////////////
  // GET INPUTS from Joystick & Motorpositions

  if( JOYSTICKVERSION && (StateMachineState == STATEMACHINESTATE_IDLE) )            // Joystick Driven Movement is blocked during CommandDrivenMovement or when no Joystick is connected.
  {
      // To avoid very slow moving because of Joystick Error
      // Spacing = 15 works quite good
      joystick_value = map( joystick_x_pos , 0 , 1023 , -100 , 100 );
      if( (joystick_value < 20) && joystick_value>-20 )
      {
        MovementEnabled = false;
        joystick_value = 0;
      }
      else
      {
        if(joystick_value > 20)
        {
          MotorDirection = 0;
          SetMotorSpeed( joystick_value*2 );
          MovementEnabled= true;
        }

        if(joystick_value < -20)
        {
          MotorDirection = 1;
          SetMotorSpeed( -joystick_value*2 );
          MovementEnabled= true;
        }
      }
  }

  

  if(DISPLAYVERSION)
  {
    if(lastTimeStamp>millis())  // to avoid overflow bug!
      lastTimeStamp=millis();
      
    if(millis()-lastTimeStamp>50)
    {
        lastTimeStamp = millis();
        // Display Data on the 4x20 Character Display
      sprintf(JoyString, "dir=%d,joy=%d   ",MotorDirection,joystick_value);
      sprintf(PositionString, "p=%s    ",String(CurrentPosition, DEC).c_str());   // longstrings have to be used with the Arduino-String Class
      //sprintf(StateString, "Mot=%d,Tur=%d", MotorPositionZeroState , WormPositionZeroState );
      sprintf(StateString, "LastHome=%s", String(LastHome, DEC).c_str() );
  //    lcd.begin(20, 4);
  //    lcd.clear();
      lcd.setCursor(0, 0); lcd.print(TopString);
      lcd.setCursor(0, 1); lcd.print(JoyString);
      lcd.setCursor(-4, 2); lcd.print(PositionString);
      lcd.setCursor(-4, 3); lcd.print(StateString);
    }
  }
  
  // 13.06.2022, might cause trouble with display version, is so --> move delay into DISPLAYVERSION CODE!
  //delay(20);
}
