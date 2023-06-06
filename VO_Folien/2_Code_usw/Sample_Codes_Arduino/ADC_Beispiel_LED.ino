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
 * Beispiel: ADC - LED
 * Programmierer: Jan Enenkel
 * Datum: 16.3.2023
 * Hardware: Universität Graz - Physik Übungsboard - Arduino Uno ( mit CH340 )
 * Programmbeschreibung: Dieser den Joystick kontinuierlich abfragen, wenn die 
 * Spannung des Joystick Pins über 2.5V Beträgt so soll die LED leuchten
 * sonst nicht.
 ******************************************************************************
*/


int JoystickX_PIN = A0;       // Joystick Pin X-Achse als A0 definieren.
#define R_PIN 7               // Defintion des D7 pins als "R_PIN" an welchem die Rote LED angeschlossen ist.

// Setup Funktion wird einmal beim hochfahren des Arduino Ausgeführt
void setup() {
  // AnalogPin ist per Default (Default-State) auf Eingang gestellt!
  pinMode( R_PIN , OUTPUT );     // Rote LED-pin auf Ausgang stellen

}

// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{
  int messwert               = analogRead( JoystickX_PIN );       // Auslesen des ADC und in messwert Speichern
  float messwertSpannung     = messwert*5.0/1023;                 // Umrechnen des messwert in MesswertSpannung
  
  if(messwertSpannung > 2.5)                                      // Wenn Messwert größer als 2.5V ist
    digitalWrite( R_PIN , HIGH );                                 // LED Leuchten lassen
  else                                                            // sonst
    digitalWrite( R_PIN , LOW );                                  // LED nicht leuchten lassen.
  
                                                                  // Kein Delay, die durchlaufzeit benötigt ca. 120us.
}
