/*
 *****************************************************************************
 * Organisation: Universität Graz
 * Abteilung: Institut für Physik
 * Anwendung: Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt: Drohne
 * Beispiel: 
 * Programmierer: Jan Enenkel
 ******************************************************************************
*/
#include <Wire.h>
#include <Servo.h>
#include <ADXL345.h>


Servo Servo1;                     // Instanz eines Servos  
Servo Servo2;                     // Instanz eines Servos
ADXL345 adxl;                     // Instanz eines G-Sensors vom Typ ADXL345

// Deklaration von globalen Variablen welche den Joystickpin anzeigen.
int JoystickX_PIN = A0;
int JoystickY_PIN = A1;

// Definition eines Servo Pins
#define SERVO1_PIN 2
#define SERVO2_PIN 3


// Setup funktion Initialisiert den Arduino und alle HW-Blöcke wie für die Übung benötigt
void setup() {
  
  Serial.begin(57600);    // Initialisieren der UART auf 57600 BAUD

  while(!Serial)          // Warten bis die serielle schnitstelle Initialisiert ist
  {
    delay(1);
  }
  
 Wire.begin();                  // Initialisieren des I2C

 adxl.powerOn();                // Initialisieren des G-Sensors

 Servo1.attach(SERVO1_PIN);             // Servo mit Digital-Pin(2) verbinden
 Servo2.attach(SERVO2_PIN);             // Servo mit Digital-Pin(3) verbinden
 Serial.println("#Partytime");  
}

////////////////////////////////////////////////////////////////////
// Globale Variablen welche einen moving Average Filter darstellen
float TP_x[10];
float TP_y[10];
int TP_Index_x = 0;
int TP_Index_y = 0;

////////////////////////////////////////////////////////////////////
// Moving Average Filter für die x-Achse
float TP_Filter_x( float Eingangswert )
{
  TP_x[TP_Index_x]=Eingangswert;

  TP_Index_x++;
  if(TP_Index_x>=10)
  TP_Index_x=0;

  int i = 0;
  float Ruckgabewert = 0.0;
    for(i=0;i<10;i++)
      Ruckgabewert+=TP_x[i];
  return Ruckgabewert/10.0;   
}

////////////////////////////////////////////////////////////////////
// Moving Average Filter für die y-Achse
float TP_Filter_y( float Eingangswert )
{
  TP_y[TP_Index_y]=Eingangswert;

  TP_Index_y++;
  if(TP_Index_y>=10)
  TP_Index_y=0;

  int i = 0;
  float Ruckgabewert = 0.0;
    for(i=0;i<10;i++)
      Ruckgabewert+=TP_y[i];
  return Ruckgabewert/10.0;   
}

char string[50];
bool JoystickMode = true;
float LastJoystickSpannungX = 0.0;

void loop()
{
  int JoyStickXPos = analogRead(JoystickX_PIN);       // Auslesen der Joysticks
  int JoyStickYPos = analogRead(JoystickY_PIN);
  
  float JoystickSpannungX = JoyStickXPos*5.0/1023;    // Umrechnen auf Spannungen
  float JoystickSpannungY = JoyStickYPos*5.0/1023;
  
  if( (JoystickSpannungX > 4.95) && (LastJoystickSpannungX<4.5) )   // Falls der Joystick Button gedrückt wurde
  {                                                                 // bei Joystick Button drücken mißt der ADC 5.0V
    JoystickMode = !JoystickMode;                                   // Wechseln des Mode
    if(JoystickMode==true)                                          // Wenn Joystick Mode true ist --> Joystick Mode
      Serial.println("Joystick-Mode Ein!");
    else                                                            // Wenn Joystick Mode false ist --> G-Sensor Mode!
      Serial.println("G-Sensor-Mode Ein!");
  }

  LastJoystickSpannungX = JoystickSpannungX;                        // Letzten Spannungswert merkten weil nur so sichergestellt werden kann das der Mode sauber umgestellt wird (Flankengesteuert)
   
  if(JoystickMode==true)                                            // Joystick Mode zum Steuern der Drohne
  {  
    int valX = map(JoyStickXPos, 250, 780, 0, 180);                 // Mappen der Werte für X und Y
    int valY = map(JoyStickYPos, 250, 780, 0, 180);
    Servo2.write(valX);                                             // Beschreiben der Servos, mit maximaler Geschwindigkeit (kein Delay)
    Servo1.write(valY);
  }
  else                      // G-Sensor Mode zum Regeln der Drohne
  {
    int x, y, z;
    
    // einlesen des G-Sensors
    adxl.readXYZ(&x, &y, &z);
  
    // Berechnung der G-Werte
    float X = x/256.0;
    float Y = y/256.0;
    float Z = z/256.0;

    // Lineares mathematisches Modell ( wäre auch mit Map-Befehl möglich )
    X = (X+1.0)*90.0;
    Y = (Y+1.0)*90.0;
  
    // Filter Funktion - funktioniert nur mit geeigneter Zeitverzögerung
    int Servo1Pos = TP_Filter_x(X);
    int Servo2Pos = TP_Filter_y(Y);

    delay(10);              // 10ms Delay nötig weil sonst der Filter nicht funktioniert (Moving Average filter durchlaufzeit)
     
    Servo1.write( Servo1Pos );      // Beschreiben der Servos
    Servo2.write( Servo2Pos ); 
  }
}
