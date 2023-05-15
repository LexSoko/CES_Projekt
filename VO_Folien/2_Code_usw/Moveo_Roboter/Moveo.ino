/*
 *****************************************************************************
 * Organisation: Universität Graz
 * Abteilung: Institut für Physik
 * Anwendung: Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt: Samplecode
 * Beispiel: Moveo Roboter
 * Programmierer: Jan Enenkel
 * Datum: 15.1.2023
 * Hardware: Arduino Mega verbunden mit einem Moveo 5 Achsen Roboter.
 * Programmbeschreibung: Kann entweder über UART oder über Xbox Controller Befehle annehmen und den Roboter dementsprechend bewegen. 
 *                       Zu späterem Zeitpunkt noch einen G-code Parser einbauen um komplette Bewegungen durchführen zu können.
 * 
 * 
 ******************************************************************************
*/

#include <Servo.h>
#define MY_IDENTITY "Moveo1"

// Pin definitions
const int joystickX = A0;
const int joystickY = A1;
const int motor4CLK = A5;
const int motor4CW = A4;
const int enPin = 8;
const int motor3CLK = 13;
const int motor3CW = 12;
const int motor1CLK = 3;
const int motor1CW = 6;
const int motor2CLK = A2;
const int motor2CW = A3;
const int motor6CLK = 2;
const int motor6CW = 5;
const int motor5CLK = 4;
const int motor5CW = 7;
const int servoPin = 22;

// X-Box Input Buttons - XBox Data is sent from XBox Controller to ESP32 Bluetooth Mode, then sent via UART to the Arduino.
int btnA = 0;
int btnB = 0;
int btnY = 0;
int btnX = 0;
int trigLT = 0;
int trigRT = 0;
float Joystick_LeftHorizontal = 0.0;
float Joystick_LeftVertical = 0.0;
float Joystick_RightHorizontal = 0.0;
float Joystick_RightVertical = 0.0;

// Storage of the last Button Value - this is necessary to trigger edge-triggered button pressing
int lastbtnX = 0;
int lastbtnY = 0; 
int lastbtnA = 0;

bool limitMaxMotorpos = true;       // This boolean defines if we can run freespace or are limited in movement due to mechanics

#define M1_MAXPOS 10000             // Limitations of the Motor final positions, in both directions
#define M23_MAXPOS 4500
#define M4_MAXPOS 30000
#define M5_MAXPOS 2000
#define M6_MAXPOS 7000

int MovementMode = 0;               // Movement mode

// State which the Movement mode could be
#define MODE_JOYSTICK 0            // Joystick Mode
#define MODE_GCODE 1               // G-Code Mode
#define MODE_XBOX 2                // X-Box Mode

bool MovementEnabled = false;      // Flag Bit if the Movement is enabled or not
bool ServoEnabled = false;         // Flag Bit if the Servo is enabled ot not
bool EnableGrip = false;           // Flag Bit if Grip is Closed(True) or Open(False)
int MotorDirection = 0;            // In which direction is the Motor heading.

int ActualMotor = 0;               // ACtual Motor, as only one Motor can be moved at a time.
int ActualServo = 0;               // Only one Servo, but should be selected.

int ActualServoPos = 90;           // Middle position of Servo as starting point.

// Actual position of the Motor
int m1pos = 0;
int m23pos = 0;
int m4pos = 0;
int m5pos = 0;
int m6pos = 0;

// Actual target position of the motor --> needed for G-Code mode!
int m1pos_target = 0;
int m23pos_target = 0;
int m4pos_target = 0;
int m5pos_target = 0;
int m6pos_target = 0;

// Maximal Motorspeed, was evaluated during 2.2.2023
#define M1_MAX_MOTORSPEED 100
#define M23_MAX_MOTORSPEED 40
#define M4_MAX_MOTORSPEED 300
#define M5_MAX_MOTORSPEED 40        // can also be 50
#define M6_MAX_MOTORSPEED 100

int Timer1DelayRegisterPreloadValue = 65000;

// Servo object
Servo servo;

const byte numChars = 96;             
char receivedChars[numChars];         // an array to store the received data from the PC
char receivedChars2[numChars];        // array to store the received data from the XBOX Controller
char string[numChars];                // String to send data.
bool newData = false;                 // regular UART
bool newData2= false;                 // SW UART


void SetMotorSpeed(int Speed)         // From Enceladus 2v0 -> exponential function verified
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
void setTimer1Time(int microseconds)    // Using ATMEga Timer directly
{
  Timer1DelayRegisterPreloadValue = 65535-(microseconds-2)*2;
}

// getLongElementFromString - this function parses a string depending on it's element count and seperator
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

// hasStringInside - this function parses a string and checks if the string does contain a certain string content
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


 // Copied from Enceladus using for HW UART --> to PC
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

 // Copied from Enceladus using for SW UART --> to ESP32
void ProcessUART2()
{
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
   
    while (Serial2.available() > 0 && newData2 == false)
    {
        rc = Serial2.read();

        if (rc != endMarker)
        {
            receivedChars2[ndx] = rc;
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

// Stringparsing function
void removeCharFromString(char* str, char c) {
  int i, j;
  for (i = 0, j = 0; str[i] != '\0'; i++) {
    if (str[i] != c) {
      str[j++] = str[i];
    }
  }
  str[j] = '\0';
}

// Parsing from the ESP32 - SW UART
void ProcessReceivedData2()
{
  bool understood = false;
  char *temp = strlwr(receivedChars2);
  
  if (newData == true)
  {
    newData = false;
    //String input = String(temp);
    //Serial.print( input + String("\n") );
    if ( hasStringInside( temp , "<" ) && hasStringInside( temp , ">" ) )
    {
        //Serial.print( "Start & Stop working!" );
        //input = input.substring(1, input.length() - 1);     // die vorzeichen entfernen ( "<" und ">" )
        removeCharFromString(temp, '<');
        removeCharFromString(temp, '>');

        String input = String(temp);
        
        int count = 0;
        while (input.length() > 0)                          // Splitstring
        {
          int commaIndex = input.indexOf(",");
          if (commaIndex == -1)
          {
            commaIndex = input.length();
          }
          String valueStr;
          if(count!=9)
          {
              valueStr = input.substring(0, commaIndex);
              input = input.substring(commaIndex + 1);
          }
          else
          {
              Serial.print( valueStr );
              valueStr = input;  
          }

          if(count==0)  { btnA = valueStr.toInt(); }                        // Here the real parsing takes place, data is sent from the ESP32
          if(count==1)  { btnB = valueStr.toInt(); }
          if(count==2)  { btnY = valueStr.toInt(); }
          if(count==3)  { btnX = valueStr.toInt(); }
          if(count==4)  { trigLT = valueStr.toInt(); }
          if(count==5)  { trigRT= valueStr.toInt(); }
          if(count==6)  { Joystick_LeftHorizontal   = valueStr.toFloat(); }
          if(count==7)  { Joystick_LeftVertical     = valueStr.toFloat(); }
          if(count==8)  { Joystick_RightHorizontal  = valueStr.toFloat(); }
          if(count==9)  { Joystick_RightVertical    = valueStr.toFloat(); }
          count++;
      }
    }
  }
}

// Parsing from the PC - HW UART
void ProcessReceivedData()
{
  bool understood = false;
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

          if(hasStringInside( temp , "joystick" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "xbox" ) && (understood == false))
          {
              MovementMode = MODE_XBOX;
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "gm1" ) && (understood == false))
          {
              int newpos = getLongElementFromString(temp,1, ' ' );
              ActualMotor = 1;
              m1pos_target = newpos;
              MovementMode = MODE_GCODE;
              SetMotorSpeed( M1_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "gm2" ) && (understood == false))
          {
              int newpos = getLongElementFromString(temp,1, ' ' );
              ActualMotor = 2;
              m23pos_target = newpos;
              MovementMode = MODE_GCODE;
              SetMotorSpeed( M23_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "gm4" ) && (understood == false))
          {
              int newpos = getLongElementFromString(temp,1, ' ' );
              ActualMotor = 4;
              m4pos_target = newpos;
              MovementMode = MODE_GCODE;
              SetMotorSpeed( M4_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }
 
          if(hasStringInside( temp , "gm5" ) && (understood == false))
          {
              int newpos = getLongElementFromString(temp,1, ' ' );
              ActualMotor = 5;
              m5pos_target = newpos;
              MovementMode = MODE_GCODE;
              SetMotorSpeed( M5_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }
          
          if(hasStringInside( temp , "gm6" ) && (understood == false))
          {
              int newpos = getLongElementFromString(temp,1, ' ' );
              ActualMotor = 6;
              m6pos_target = newpos;
              MovementMode = MODE_GCODE;
              SetMotorSpeed( M6_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "sethome" ) && (understood == false))
          {
            
            m1pos_target = 0;            
            m23pos_target = 0;
            m4pos_target = 0;
            m5pos_target = 0;
            m6pos_target = 0;
            MovementMode = MODE_GCODE;
            
            understood = true;
          }

          if(hasStringInside( temp , "getpos" ) && (understood == false))
          {
            Serial.println(String("M1=") + String(m1pos));
            Serial.println(String("M23=")+ String(m23pos));
            Serial.println(String("M4=") + String(m4pos));
            Serial.println(String("M5=") + String(m5pos));
            Serial.println(String("M6=") + String(m6pos));
            understood = true;
          }

          if(hasStringInside( temp , "reset" ) && (understood == false))
          {
              m1pos = 0;
              m23pos = 0;
              m4pos = 0;
              m5pos = 0;
              m6pos = 0;
              
              m1pos_target = 0;
              m23pos_target = 0;
              m4pos_target = 0;
              m5pos_target = 0;
              m6pos_target = 0;

              Serial.println("DONE");
              
              understood = true;
          }

          if(hasStringInside( temp , "enable" ) && (understood == false))
          {
              digitalWrite(enPin, LOW); 
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "disable" ) && (understood == false))
          {
              ActualMotor=0;
              ActualServo=0;
              digitalWrite(enPin, HIGH);
              servo.detach();
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "s1" ) && (understood == false))
          {
              servo.attach(servoPin);
              ActualServo=1;
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m1" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=1;
              SetMotorSpeed( M1_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m2" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=2;
              SetMotorSpeed( M23_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m3" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=3;
              SetMotorSpeed( M23_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m4" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=4;
              SetMotorSpeed( M4_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m5" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=5;
              SetMotorSpeed( M5_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "m6" ) && (understood == false))
          {
              MovementMode = MODE_JOYSTICK;
              ActualMotor=6;
              SetMotorSpeed( M6_MAX_MOTORSPEED );
              Serial.println("DONE");
              understood = true;
          }

          if(hasStringInside( temp , "speed" ) && (understood == false))
          {
              int motorspeed = getLongElementFromString(temp,1, ' ' );
              SetMotorSpeed( motorspeed );
              Serial.println("DONE");
              understood = true;
          }

          if(understood == false)
            Serial.println("no valid command");
          
          newData = false;
  }  
}

void setup() {
  // Set all pins to output mode
  pinMode(enPin, OUTPUT);
  pinMode(motor2CLK, OUTPUT);
  pinMode(motor2CW, OUTPUT);
  pinMode(motor4CLK, OUTPUT);
  pinMode(motor4CW, OUTPUT);
  pinMode(motor3CLK, OUTPUT);
  pinMode(motor3CW, OUTPUT);
  pinMode(motor1CLK, OUTPUT);
  pinMode(motor1CW, OUTPUT);
  pinMode(motor6CLK, OUTPUT);
  pinMode(motor6CW, OUTPUT);
  pinMode(motor5CLK, OUTPUT);
  pinMode(motor5CW, OUTPUT);
  
  // Disable all motors for the start!!!
  digitalWrite(enPin, HIGH); 

      // Configure Timer!
  noInterrupts();           // disable all interrupts
  TCCR1A = 0;
  TCCR1B = 0;

  TCNT1 = 34286;            // preload timer 65536-16MHz/256/2Hz
  TCCR1B |= (1 << CS11);    // no 8 prescaler --> 0.5 us per clock
  TIMSK1 |= (1 << TOIE1);   // enable timer overflow interrupt
  interrupts();             // enable all interrupts          // enable all interrupts

  Serial.begin(57600);          // Setup PC UART
  delay(10);
  Serial.println(MY_IDENTITY);
  Serial.println("#Partytime");

  Serial2.begin(115200);        // Setup UART to ESP32 (SW UART)
}


void PulseMotor1()              // Pulsing for Motor
{
          // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
           if( (-M1_MAXPOS>m1pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
           
           digitalWrite(motor1CW, HIGH);  // 25.11.2021 --> Change
           m1pos--;  
        }
        else                            // Going to the Right
        {
           if( (M1_MAXPOS<m1pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
              
           digitalWrite(motor1CW, LOW); // 25.11.2021 --> Change
           m1pos++;
        }
        
        digitalWrite(motor1CLK, HIGH);     // Perform one Motorstep
        digitalWrite(motor1CLK, LOW);
}

void PulseMotor23()             // Pulsing for Motor, both Motors are Parallel
{
          // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
           if( (-M23_MAXPOS>m23pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
              
           digitalWrite(motor2CW, HIGH);  // 25.11.2021 --> Change
           digitalWrite(motor3CW, HIGH);  // 25.11.2021 --> Change
           m23pos--;  
        }
        else                            // Going to the Right
        {
            if( (M23_MAXPOS<m23pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
              
           digitalWrite(motor2CW, LOW); // 25.11.2021 --> Change
           digitalWrite(motor3CW, LOW); // 25.11.2021 --> Change
           m23pos++;
        }
        
        digitalWrite(motor2CLK, HIGH);     // Perform one Motorstep
        digitalWrite(motor3CLK, HIGH);     // Perform one Motorstep
        
        digitalWrite(motor2CLK, LOW);
        digitalWrite(motor3CLK, LOW);
}

void PulseMotor4()
{
          // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
            if( (-M4_MAXPOS>m4pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
          
           digitalWrite(motor4CW, LOW);  // 25.11.2021 --> Change
           m4pos--;  
        }
        else                            // Going to the Right
        {
           if( (M4_MAXPOS<m4pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
              
           digitalWrite(motor4CW, HIGH); // 25.11.2021 --> Change
           m4pos++;
        }
        
        digitalWrite(motor4CLK, HIGH);     // Perform one Motorstep
        digitalWrite(motor4CLK, LOW);
}

void PulseMotor5()
{
          // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
           if( (-M5_MAXPOS>m5pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
           
           digitalWrite(motor5CW, HIGH);  // 25.11.2021 --> Change
           m5pos--;  
        }
        else                            // Going to the Right
        {
           if( (M5_MAXPOS<m5pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
           
           digitalWrite(motor5CW, LOW); // 25.11.2021 --> Change
           m5pos++;
        }
        
        digitalWrite(motor5CLK, HIGH);     // Perform one Motorstep
        digitalWrite(motor5CLK, LOW);
}

void PulseMotor6()
{
          // Select the direction
        if(MotorDirection==0)           // Going to the Left
        {
           if( (-M6_MAXPOS>m6pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;
          
           digitalWrite(motor6CW, LOW);  // 25.11.2021 --> Change
           m6pos--;  
        }
        else                            // Going to the Right
        {
           if( (M6_MAXPOS<m6pos) && limitMaxMotorpos)         // Ignore Stepps in case we are at the limit!!!
              return;

           digitalWrite(motor6CW, HIGH); // 25.11.2021 --> Change
           m6pos++;
        }
        
        digitalWrite(motor6CLK, HIGH);     // Perform one Motorstep
        digitalWrite(motor6CLK, LOW);
}

/////////////////////////////////////////////////////////////////////////
// ProcessStateMachine
// This function is called by a timer, so no delays allowed
/////////////////////////////////////////////////////////////////////////
void ProcessStateMachine()
{   
    if(MovementMode == MODE_GCODE)
    {
      MovementEnabled = false;

      if( m1pos != m1pos_target )
      { 
        ActualMotor = 1;
        SetMotorSpeed( M1_MAX_MOTORSPEED );   
        if(m1pos>m1pos_target)
            MotorDirection = 0;   // LEFT
        else
            MotorDirection = -1;
        MovementEnabled = true;
        return;
      }

      if( m23pos != m23pos_target )
      { 
        ActualMotor = 2; 
        SetMotorSpeed( M23_MAX_MOTORSPEED );     
        if(m23pos>m23pos_target)
            MotorDirection = 0;   // LEFT
        else
            MotorDirection = -1;
        MovementEnabled = true;
        return;
      }

      if( m4pos != m4pos_target )
      { 
        ActualMotor = 4;
        SetMotorSpeed( M4_MAX_MOTORSPEED );      
        if(m4pos>m4pos_target)
            MotorDirection = 0;   // LEFT
        else
            MotorDirection = -1;
        MovementEnabled = true;
        return;
      }

      if( m5pos != m5pos_target )
      { 
        ActualMotor = 5;
        SetMotorSpeed( M5_MAX_MOTORSPEED );      
        if(m5pos>m5pos_target)
            MotorDirection = 0;   // LEFT
        else
            MotorDirection = -1;
        MovementEnabled = true;
        return;
      }
      
      if( m6pos != m6pos_target )
      {
        ActualMotor=6;
        SetMotorSpeed( M6_MAX_MOTORSPEED );       
        if(m6pos>m6pos_target)
            MotorDirection = 0;   // LEFT
        else
            MotorDirection = -1;
        MovementEnabled = true;
        return;
      }   
    }
}


/////////////////////////////////////////////////////////////////////////
// ProcessMovment
// Necessary as the ATMEGA can run in different modes, like G-Code
// XBox or even manual mode by controlling the motors via PC.
/////////////////////////////////////////////////////////////////////////

void ProcessMovement()
{
    ///////////////////////////////////////////////////////////////////
    // Regular Movement, can be either by Joystick, Move or Home command
    if(MovementEnabled)
    {
        if(ActualMotor==1)
          PulseMotor1();
        if(ActualMotor==3 || ActualMotor==2)
          PulseMotor23();
        if(ActualMotor==4)
          PulseMotor4();
        if(ActualMotor==5)
          PulseMotor5();
        if(ActualMotor==6)
          PulseMotor6();
    }
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

// Called by the Timer
void Step()     
{  
    ProcessStateMachine();
    ProcessMovement();
}


void printFloatWithText(const char *text , float value )
{
  char buffer[20];
  dtostrf(value, 4, 2, buffer);
  Serial.println(String(text) + ": " + String(buffer));
}

float mapfloat(float x, float in_min, float in_max, float out_min, float out_max) {
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

void loop()
{
  // Process UART
  int servoPos = 90;
  ProcessUART2();
  ProcessReceivedData2();
  
  ProcessUART();
  ProcessReceivedData();

    // Read joystick values
  if(MovementMode == MODE_JOYSTICK)
  {
      int x = analogRead(joystickX);
      int y = analogRead(joystickY);
    
      // Map joystick values to servo and motor positions
      servoPos = map(x, 0, 1023, 0, 180);
      servo.write(servoPos);
      
      y = map(y, 0, 1023, -200, 200);
      if( (y > 20) || (y <-20))
      {
        if(y>20)
          MotorDirection = 0;   // LEFT
        if(y<-20)
          MotorDirection = -1;
        
        MovementEnabled = true;
      }
      else
      {
        MovementEnabled = false;
      }
  }

  if(MovementMode == MODE_XBOX)
  {
      bool motorAlreadySelected = false;
      // MOTOR1
      
      if( (trigRT > 20) || (trigLT > 20) )
      { 
        ActualMotor = 6;
        if( trigRT > trigLT )
        {
          MotorDirection =   -1;
        }
        else
        {
          MotorDirection = 0;  
        }

        int value = abs(trigRT-trigLT);
        int actualMotorspeed = mapfloat( value , 0 , 1023 , 0, M6_MAX_MOTORSPEED );
        Serial.println(String(actualMotorspeed));
        SetMotorSpeed( actualMotorspeed );
        MovementEnabled = true;
        motorAlreadySelected = true;
      }
      
      if(motorAlreadySelected == false)
      {
        if( abs(Joystick_LeftHorizontal) > abs(Joystick_LeftVertical) ) 
        {
            if( abs(Joystick_LeftHorizontal) > 0.1 )
            { // We are in Motor1
                  ActualMotor = 1;
                  if( 0 > Joystick_LeftHorizontal )
                    MotorDirection =   0;
                  else
                    MotorDirection = -1;  
                  float value = abs( Joystick_LeftHorizontal );
                  int actualMotorspeed = mapfloat( value , 0 , 1.0 , 0, M1_MAX_MOTORSPEED );
                  Serial.println(String(actualMotorspeed));
                  SetMotorSpeed( actualMotorspeed );
                  MovementEnabled = true;
                  motorAlreadySelected = true;
            }
        }
        else
        {
            if( abs(Joystick_LeftVertical) > 0.1 )
            { // We are in Motor23
              ActualMotor = 2;
              if( 0 > Joystick_LeftVertical )
                MotorDirection =   0;
              else
                MotorDirection = -1;  
              float value = abs( Joystick_LeftVertical );
              int actualMotorspeed = mapfloat( value , 0 , 1.0 , 0, M23_MAX_MOTORSPEED );
              Serial.println(String(actualMotorspeed));
              SetMotorSpeed( actualMotorspeed );
              MovementEnabled = true;
              motorAlreadySelected = true;
            }          
        }
      }

      if(motorAlreadySelected == false)
      {
        if( abs(Joystick_RightHorizontal) > abs(Joystick_RightVertical) ) 
        {
            if( abs(Joystick_RightHorizontal) > 0.1 )
            { // We are in Motor4
                  ActualMotor = 4;
                  if( 0 > Joystick_RightHorizontal )
                    MotorDirection =   0;
                  else
                    MotorDirection = -1;  
                  float value = abs( Joystick_RightHorizontal );
                  int actualMotorspeed = mapfloat( value , 0 , 1.0 , 0, M4_MAX_MOTORSPEED );
                  Serial.println(String(actualMotorspeed));
                  SetMotorSpeed( actualMotorspeed );
                  MovementEnabled = true;
                  motorAlreadySelected = true;
            }
        }
        else
        {
            if( abs(Joystick_RightVertical) > 0.1 )
            { // We are in Motor5
              ActualMotor = 5;
              if( 0 > Joystick_RightVertical )
                MotorDirection =   0;
              else
                MotorDirection = -1;  
              float value = abs( Joystick_RightVertical );
              int actualMotorspeed = mapfloat( value , 0 , 1.0 , 0, M5_MAX_MOTORSPEED );
              Serial.println(String(actualMotorspeed));
              SetMotorSpeed( actualMotorspeed );
              MovementEnabled = true;
              motorAlreadySelected = true;
            }          
        }
      }

      // X-Button -> Attach / Detach Servo
      if( (btnX == 1) && (lastbtnX == 0) )
      {
          if(ServoEnabled==true)
          {
            Serial.println("Detaching Servo!");
            ServoEnabled = false;
            servo.detach();
          }
          else
          {
            Serial.println("Attaching Servo!");
            servo.attach(servoPin);
            ServoEnabled = true;
          }
      }
      lastbtnX = btnX;

      // Y-Button -> Enable/Disable Motordrivers!
      if( (btnY == 1) && (lastbtnY == 0) )
      {
          if(MovementEnabled==true)
          {
            Serial.println("Disabling Motors!");
            MovementEnabled = false;
          }
          else
          {
            Serial.println("Enabling Motors!");
            MovementEnabled = true;
          }
      }
      lastbtnY = btnY;

      if(ServoEnabled==true)
      {
          if( (btnA == 1) && (lastbtnA == 0) )
          {
              EnableGrip = !EnableGrip;
              if(EnableGrip)
              {
                ActualServoPos = 160;
                Serial.println("Gripping");
              }
              else
              {
                ActualServoPos = 90;
                Serial.println("Release Grip");
              }
              servo.write(ActualServoPos);
          }
          lastbtnA = btnA;
      }
          
      if(motorAlreadySelected == false)
      {
        MovementEnabled = false;
      }
    } 
}
