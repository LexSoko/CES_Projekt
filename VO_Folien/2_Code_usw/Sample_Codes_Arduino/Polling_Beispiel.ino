/*
 *****************************************************************************
 * Organisation: Universität Graz
 * Abteilung: Institut für Physik
 * Anwendung: Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt: Sample Code
 * Beispiel: Polling
 * Programmierer: Jan Enenkel
 * Datum: 3.3.2022
 * Für diese Demo müssen folgende Bibliotheken Installiert sein:
 * - MCP4725 von Rob Tillart – Version 0.3.3
 * - BH1750 von Christopher Laws – Version 1.3.0
 * - Adafruit_VL53L0X von adafruit – Version 1.2.0
 * - Accelerometer ADXL345 by Seeed Studio – Version 1.0.0
 *******************************************************************************/

#include <Wire.h>
#include <Servo.h>
#include <ADXL345.h>
#include <BH1750.h>
#include <Adafruit_VL53L0X.h>
#include <MCP4725.h>

Servo Servo1;                     // Instanz eines Servos  
Servo Servo2;                     // Instanz eines Servos
ADXL345 adxl;                     // Instanz eines G-Sensors vom Typ ADXL345

MCP4725 DAC( 0x62 );              // Instanz eines DAC vom Typ MCP4625
                                  // Der DAC hat die I2C Addresse 0x62
                                  
BH1750 LightSensor(0x23);         // Instanz eines Lichtsensors vom Typ BH1750
                                  // Der Lichtsensor hat die I2C Addresse 0x23;

// Instanz eines VL53L0X Distanzsensors 
Adafruit_VL53L0X DistanceSensor = Adafruit_VL53L0X();

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

/////////////////////////////////////////////////////////
// Hauptschleife - hier wird programmiert
/////////////////////////////////////////////////////////

void loop()
{
  long startTime = millis();                          // Speichere den aktuellen Timestamp (0= Zeitpunkt wo der Arudino gestartet wird)
  float lightValue = getLuxValue();                   // Polle einen Lichtwert, dabei handelt es sich um einen klassischen "wait-until-finished" befehl
  long elapsedTime = millis()-startTime;              // Speichere die vergangen Zeit durch den getLuxValue befehl, beim BH1750 wird diese ca. 190ms betragen.
  Serial.println( String("I=") + String( lightValue ) + String("[lux] , t=") + String(elapsedTime) + String("ms") );      // Ausgabe des Messwerts + der Messzeit
  delay(1000);                                        // warte eine ganze Sekunde, die Gesammtzykluszeit für einen schleifendurchlauf beträgt daher ca. 1190ms.
}
