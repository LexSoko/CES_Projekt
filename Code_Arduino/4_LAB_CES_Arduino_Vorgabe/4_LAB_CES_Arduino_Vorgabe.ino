/*
 *****************************************************************************
 * Organisation:  Universität Graz
 * Abteilung:     Institut für Physik
 * Anwendung:     Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt:       Übungsteil - Vorgabe
 * Beispiel:      Selbsterfunden?
 * Programmierer: Max Jost, Martin Steiner, Aleksey Sokolov
 * Gruppe:        34
 * Nickname:      MMA-34 
 * Custom Meme:   https://www.wien.gv.at/kontakte/ma34/index.html
 ******************************************************************************
*/




/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Includes                                      */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

#include <Wire.h>
#include <Servo.h>
#include <ADXL345.h>
#include <BH1750.h>
#include <Adafruit_VL53L0X.h>
#include <MCP4725.h>




/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Library Instantiations                        */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

Servo Servo1;                     // Instanz eines Servos  
Servo Servo2;                     // Instanz eines Servos
ADXL345 adxl;                     // Instanz eines G-Sensors vom Typ ADXL345

MCP4725 DAC( 0x62 );              // Instanz eines DAC vom Typ MCP4625
                                  // Der DAC hat die I2C Addresse 0x62
                                  
BH1750 LightSensor(0x23);         // Instanz eines Lichtsensors vom Typ BH1750
                                  // Der Lichtsensor hat die I2C Addresse 0x23;

// Instanz eines VL53L0X Distanzsensors 
Adafruit_VL53L0X DistanceSensor = Adafruit_VL53L0X();




/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Pin Definitions                               */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

// Deklaration von globalen Variablen welche den Joystickpin anzeigen.
int JoystickX_PIN = A0;
int JoystickY_PIN = A1;

// Definition eines Servo Pins
#define SERVO1_PIN 2
#define SERVO2_PIN 3

// Definition der RGB Pins.
#define R_PIN 7
#define G_PIN 5
#define B_PIN 6




/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Setup Function                                */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

// Setup funktion Initialisiert den Arduino und alle HW-Blöcke, wie für die Übung benötigt
void setup() {
  
  Serial.begin(57600);    // Initialisieren der UART auf 57600 BAUD

  while(!Serial)          // Warten bis die serielle schnitstelle Initialisiert ist
  {
    delay(1);
  }
  
  Wire.begin();                  // Initialisieren des I2C

  DAC.begin();                   // Initialisieren des DAC
  DAC.setValue(0);               // DAC auf 0 setzen

  pinMode( R_PIN , OUTPUT );     // Rote LED-pin auf Ausgang stellen
  pinMode( G_PIN , OUTPUT );     // Grüne LED-pin auf Ausgang stellen
  pinMode( B_PIN , OUTPUT );     // Blaue LED-pin auf Ausgang stellen.

  adxl.powerOn();                // Initialisieren des G-Sensors
  
  Servo1.attach(SERVO1_PIN);             // Servo mit Digital-Pin(2) verbinden
  Servo2.attach(SERVO2_PIN);             // Servo mit Digital-Pin(3) verbinden

  // Initialisieren des LichtSensors für einen Singleshot mode
  LightSensor.begin(BH1750::ONE_TIME_HIGH_RES_MODE);

  // Initialisieren des DistanzSensors VL53L0X
  bool initWorked = DistanceSensor.begin();
  if(!initWorked)
  {
    Serial.println("VL53L0X init failed, no Partytime");
  }
  else
  {
    DistanceSensor.startRangeContinuous();
    Serial.println("#Partytime");  
  }
}




/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Custom Functions                              */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

// Zur Verfügung gestellte Debug Funktion - mit dieser Funktion können Sie 
// jederzeit eine Variable vom Typ Float (und natürlich auch integer) über die Serielle Schnittstelle ausgeben.
void debugString( const char *start_str , float variable , const char *ending_str )
{
  char str[50];
  strcpy(str,start_str);
  dtostrf(variable, 2, 2, &str[strlen(str)]);
  strcat(str,ending_str);
  Serial.println(str);
}

// Zur Verfügung gestellte Einlesefunktion des Lichtsensors.
// Die Messwerte werden in der Einheit LUX ausgegeben.
float getLuxValue()
{
  LightSensor.configure(BH1750::ONE_TIME_HIGH_RES_MODE);
  while( !LightSensor.measurementReady(true) )
  {
    yield();
  }

  return LightSensor.readLightLevel();  
}


void SetRGBLed(int Value){
  if(Value == 0)
  {
    digitalWrite(R_PIN, LOW);
    digitalWrite(G_PIN, LOW);
    digitalWrite(B_PIN, LOW);

  }
  if(Value == 1)
  {
    digitalWrite(R_PIN, HIGH);
    digitalWrite(G_PIN, LOW);
    digitalWrite(B_PIN, LOW);
  }
  if(Value == 2)
  {
    digitalWrite(R_PIN, LOW);
    digitalWrite(G_PIN, HIGH);
    digitalWrite(B_PIN, LOW);
  }
  if(Value == 3)
  {
    digitalWrite(R_PIN, LOW);
    digitalWrite(G_PIN, LOW);
    digitalWrite(B_PIN, HIGH);
  }
}


/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/
/*                    Main Loop                                     */
/* %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%*/

int counter = 0;
float TP_x[10];
int TP_Index_x = 0;
float TP_Filter_x(float Eingangswert)
{
  TP_x[TP_Index_x] = Eingangswert;
  TP_Index_x++;
  if(TP_Index_x >= 10)
    TP_Index_x = 0;
    int i = 0;
    float Ruckgabewert = 0.0;
    for( i = 0 ; i < 10; i++)
      Ruckgabewert += TP_x[i];
    return Ruckgabewert/10.0;
}
void loop()
{
  if( DistanceSensor.isRangeComplete())
  {
    int Messwert = DistanceSensor.readRange();
    if(Messwert > 200)
      Messwert = 200;
      Serial.println(String(Messwert));
  } 
  else
  {
      Serial.println("range not complete");
  }



}
