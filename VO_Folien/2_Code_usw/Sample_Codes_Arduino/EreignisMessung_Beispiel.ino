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
 * Beispiel: EreignisMessung
 * Programmierer: Jan Enenkel
 * Datum: 17.3.2023
 * Hardware: Universität Graz - Physik Übungsboard - Arduino Uno ( mit CH340 )
 * Programmbeschreibung: Dieser Code misst wie oft der Joystick innerhalb von 10 sekunden 
 * bewegt werden kann
  ******************************************************************************
*/


int JoystickX_PIN = A0;       // Joystick Pin X-Achse als A0 definieren.

// Setup Funktion wird einmal beim hochfahren des Arduino Ausgeführt
void setup()
{
  Serial.begin(57600);    // Initialisieren der UART auf 57600 BAUD
  while(!Serial)          // Warten bis die serielle schnitstelle Initialisiert ist
  {
    delay(1);
  }

  Serial.println( "#Partytime" );   // Wenn initialisierung abgeschlossen ist soll 
}


// Globale Variablen - sollte bei größeren Programmen vermieden werden.
float measurementVoltage        = 0.0;         // aktuelle Messspannung
float measurementLastVoltage    = 0.0;         // letzter Messwert
bool measurementActive = false;                // bool "flag" ob die Messung gerade läuft oder nicht
long startTimeOfMeasurement = 0;               // startzeitpunkt der Messung
int eventCounter = 0;                          // ereignisZähler für die 10 Sekunden

// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{ 
  if(Serial.available() > 0)            // Falls im eingangsbuffer der seriellen Schnittstelle Daten sind
  {
    if(Serial.read() == '$')            // Wenns das Empfangene Zeichen ein '$' ist starte die Messung
    {
      eventCounter = 0;                                       // Counter zurücksetzen
      measurementActive = true;                               // Messung nun Offiziell gestartet
      startTimeOfMeasurement = millis();                      // Zeitpunkt der Messung speichern
      Serial.println("Messung gestartet - 10 sekunden");      // Dem User mitteilen das die Messung gestartet wurde
    }

    // Falls übrigens ein $ während der Messung vom User kommt, so wird die Messung einfach neu gestartet.
  }
  
  if(measurementActive)       // Wenn eine Messung läuft so springe in diesen Code-Block
  {
    int measurementValue       = analogRead( JoystickX_PIN );           // Auslesen des ADC und in measurementValue Speichern
    measurementVoltage         = measurementValue*5.0/1023;             // Umrechnen des measurementValue in measurementVoltage
  
    // Wenn der Messwert größer als 3.0V ist, aber der vorhergehende kleiner war ( Übergang )
    if( (measurementVoltage > 3.0) && (measurementLastVoltage < 3.0) )  
      eventCounter++;                                                   // erhöhe den eventCounter um 1.

    measurementLastVoltage = measurementVoltage;                        // speichere die aktuellen wert als den letzten messwert (für den nächsten Schleifendurchlauf nötig)

    if( millis() < startTimeOfMeasurement )                             // für den Unwahrscheinlichen fall das der millicounter einen Überlauf hatte. (49.5 Tage bis dies passiert, jedoch bei micros schon nach 70 minuten)
    {
      Serial.println("Timer Überlauf / Messung gestoppt");
      measurementActive = false;
    }
    
    if( millis() > (startTimeOfMeasurement+10000) )                                                          // wenn 10 sekunden vergangen sind
    {
      measurementActive = false;                                                                             // Beende die Messung
      Serial.println(String("Messung fertig: ") + String(eventCounter) + String(" Ereignisse gemessen") );   // Ausgabe des Resultats!
    } 
  }
}
