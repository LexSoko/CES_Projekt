/*
 *****************************************************************************
 * Project: Spincoater 1v0
 * Description: Fan Controller with Display
 * Usage for: generation of thin films
 * Board: Arduino Nano                                                                         
 * Hardware: 4x20 Character Display, Joystick, PWM Input, PWM Output
 * Date: 02.072.2021
 * 
 * Revision History:
 * 02.07.2021: Derivative from Enceladus 2v0
 * 06.04.2023: Update to clean Display & Adding Timer for Spincoating Time
 * Programmmer: Jan Enenkel                                                          
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

// DEFINTION OF DIGITAL PINS for Display
#define DISP_RS 4
#define DISP_E 5
#define DISP_D4 6
#define DISP_D5 7
#define DISP_D6 8
#define DISP_D7 9

#define MY_IDENTITY "Spincoater1"

// I/O DEFINITIONS for the Joystick
int ADC_X_PIN = A7;
int ADC_Y_PIN = A6;
#define JOYSTICK_BUTTON 1
#define ON_OFF_BUTTON 0
#define PWM_PIN 12
#define INTERRUPT_PIN 2

// Create a Display
LiquidCrystal lcd(DISP_RS, DISP_E, DISP_D4, DISP_D5, DISP_D6, DISP_D7);


///////////////////////////////////////////////////////////////
//////////////////// GLOBAL VARIABLES /////////////////////////
///////////////////////////////////////////////////////////////

// General Usecase String for UART Feedback
char string[100];

// 4x20 Character Display Strings
String TopString;           // Display Top String
String JoyString;           // Joystick Parameters
String PositionString;
String StateString;
long startingTimeStamp = 0;

bool Mutex = false;

#define JOYSTICK_X_SPACING 15
#define JOYSTICK_Y_SPACING 15
// Joystick Position & Button State
int joystick_x_pos = 0;
int joystick_y_pos = 0;
int JoystickButtonState = 0;
int OnOffButtonState = 0;
int JoystickValueX = 0;           // Absolut Intensitiy how much the joystick to 
int JoystickDirectionX = 0;           // Absolut Intensitiy how much the joystick to 
int JoystickValueY = 0;           // Absolut Intensitiy how much the joystick to 
int JoystickDirectionY = 0;           // Absolut Intensitiy how much the joystick to 
bool JoyStickButtonEvent = false;
bool OnOffButtonEvent = false;
int LastJoystickButtonState = 1;
int LastOnOffButtonState = 1;

int RPMValue = 0;


// Inputs from the Motorposition
int Timer1DelayRegisterPreloadValue = 65300;              //

#define TIMESTAMPMAX 50
unsigned long TimeStamps[TIMESTAMPMAX];
unsigned char TimeStampCounter = 0;


// UART Interface Variables
const byte numChars = 96;
char receivedChars[numChars];   // an array to store the received data
char tempChars[numChars];
bool newData = false;

int LocalPWM = 0;
int SetPWM = 0;
bool PWMOn = false;
bool tik = false;


int TP[50];
int TP_Index = 0;

int TP_Filter( int Eingangswert )
{
  TP[TP_Index]=Eingangswert;

  TP_Index++;
  if(TP_Index>=50)
  TP_Index=0;

  int i = 0;
  long Ruckgabewert = 0;
    for(i=0;i<50;i++)
      Ruckgabewert+=TP[i];
  return Ruckgabewert/50;
}


///////////////////////////////////////////
// Initialize the IC
///////////////////////////////////////////

void rising()
{
  if(Mutex==false)
  {
      if(TimeStampCounter<=TIMESTAMPMAX-1)
      {
        TimeStamps[TimeStampCounter] = micros();
        TimeStampCounter++;
      }
  }
}

long getTimeStampDifference()
{ 
  Mutex = true; 
  unsigned char i = 0;
  unsigned long temp = 0;
  unsigned long delta = 0;
  
  if(TimeStampCounter<=1)
  {
    Mutex = false;
    return 0;
  }

  for( i = 0; i < (TimeStampCounter-1); i++)
  {
    delta = TimeStamps[i+1]-TimeStamps[i];
    temp += delta;
  }
  
  temp = temp/(TimeStampCounter-1);
  TimeStampCounter=0;
  
  Mutex = false;
  return temp;
}

void setup() {
  // I/Os
  // Display
  pinMode(DISP_RS, OUTPUT);
  pinMode(DISP_E, OUTPUT);
  pinMode(DISP_D4, OUTPUT);
  pinMode(DISP_D5, OUTPUT);
  pinMode(DISP_D6, OUTPUT);
  pinMode(DISP_D7, OUTPUT);

  pinMode(JOYSTICK_BUTTON, INPUT_PULLUP);
  pinMode(ON_OFF_BUTTON, INPUT_PULLUP);
  pinMode(INTERRUPT_PIN, INPUT);
  pinMode(PWM_PIN, OUTPUT);
  digitalWrite(PWM_PIN, HIGH);
  
  // Initialize Serial Interface
  Serial.begin(57600);

  lcd.begin(20, 4);
  lcd.clear();
    
  // Configure Timer!
  noInterrupts();           // disable all interrupts
  TCCR1A = 0;
  TCCR1B = 0;

  TCNT1 = Timer1DelayRegisterPreloadValue;            // preload timer 65536-16MHz/256/2Hz
  TCCR1B |= (1 << CS11);    // no 8 prescaler --> 0.5 us per clock
  TIMSK1 |= (1 << TOIE1);   // enable timer overflow interrupt
  interrupts();             // enable all interrupts          // enable all interrupts

  attachInterrupt(digitalPinToInterrupt(2), rising , RISING );

  TopString = String("#Partytime");
  Serial.println("Spincoater 1v0");
  Serial.println(TopString);
}


// Step function gets called with the Timer speed.
void Step()     
{  
  if(PWMOn==true)
  {
      if(tik==true)
      {
        Timer1DelayRegisterPreloadValue = 65275+(250-SetPWM);
        digitalWrite(PWM_PIN, HIGH);
      }
      else
      {
        Timer1DelayRegisterPreloadValue = 65280+SetPWM;
        digitalWrite(PWM_PIN, LOW);  
      }
      
      tik = !tik;
  }
  else
    digitalWrite(PWM_PIN, HIGH);
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

//////////////////////////////////////////////
// ProcessInputs
//////////////////////////////////////////////         

void ProcessInputs()
{
      // GET INPUTS from Joystick & Motorpositions
     joystick_x_pos = analogRead(ADC_X_PIN);
     joystick_y_pos = analogRead(ADC_Y_PIN);
     JoystickButtonState = digitalRead(JOYSTICK_BUTTON);
     OnOffButtonState    = digitalRead(ON_OFF_BUTTON);

     if( (LastJoystickButtonState==1) && (JoystickButtonState==0) )
     {
     
     }

     if( (LastOnOffButtonState==1) && (OnOffButtonState==0) )     // We have a button pressed Event!
     {
        if(PWMOn)     // Turning Off!!!
        {
            PWMOn = false;
            Timer1DelayRegisterPreloadValue = 65300;
        }
        else        // Turning On!
        {
        startingTimeStamp = millis();
        PWMOn = true;
        digitalWrite(PWM_PIN, LOW);  
        } 
     }

      LastJoystickButtonState = JoystickButtonState;
      LastOnOffButtonState = OnOffButtonState;
      
      // To avoid very slow moving because of Joystick Error
      int joystickValue = map(joystick_x_pos , 0 , 1023 , 100 , -100 );
      if( (joystickValue>10) || (joystickValue<-10) )
      {
        LocalPWM += joystickValue/30;

        if(LocalPWM>255)
          LocalPWM = 255;
        if(LocalPWM<0)
          LocalPWM = 0;
      }  
}

void DisplayParameters()
{
   unsigned long DeltaTime = getTimeStampDifference();
   RPMValue = 30000000/DeltaTime;
   if(RPMValue<200)
     RPMValue = 0;

    SetPWM = LocalPWM;    
    JoyString = String("PMW=") + String(SetPWM) + String("/255   ");
    int FilteredRPMValue = (int)TP_Filter(RPMValue);
    PositionString = String("RPM=") + String(FilteredRPMValue) + String("   ");
    
    if(PWMOn)
    {
      StateString = String("Motor=[ON]  ");
      TopString = String("T=") + String((millis()-startingTimeStamp)/1000) + String("[s]    ");
    }
    else
    {
      StateString = String( "Motor=[OFF]  ");
      TopString = String("#Partytime   ");
    }
    
    lcd.setCursor(0, 0); lcd.print(TopString.c_str());
    lcd.setCursor(0, 1); lcd.print(JoyString.c_str());
    lcd.setCursor(-4, 2); lcd.print(PositionString.c_str());
    lcd.setCursor(-4, 3); lcd.print(StateString.c_str());
}


void loop()
{
    ProcessInputs();
    DisplayParameters();

    delay(20);
}
