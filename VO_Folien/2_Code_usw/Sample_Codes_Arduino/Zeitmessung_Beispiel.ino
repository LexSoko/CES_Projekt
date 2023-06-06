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
 * Beispiel: ZeitMessung
 * Programmierer: Jan Enenkel
 * Datum: 17.3.2023
 * Hardware: Universität Graz - Physik Übungsboard - Arduino Uno ( mit CH340 )
 * Programmbeschreibung: Dieser Code misst wieviel Zeit zwischen zwei Ereignissen vergangen ist und gibt diese dann bei UART aus
 * Dabei wird der micros() Befehl benutzt!
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


// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{ 
  if(Serial.available() > 0)            // Falls im eingangsbuffer der seriellen Schnittstelle Daten sind
  {
    if(Serial.read() == '$')            // Wenns das Empfangene Zeichen ein '$' ist starte die Messung
    {
      measurementActive = !measurementActive;   // Messung aktivieren/deaktivieren je nach vorhergehendem Zustand

      if(measurementActive)
      {
        Serial.println("Messung aktiviert!");           // Dem benutzer mitteilen das eine Messung aktiviert wurde
        startTimeOfMeasurement = micros();              // aktivieren der MEssung gilt quasi als erstes Event! - micros Befehl wird verwendet
      }
      else
        Serial.println("Messung deaktiviert!");
    }

    // Falls übrigens ein $ während der Messung vom User kommt, so wird die Messung einfach neu gestartet.
  }
  
  if(measurementActive)       // Wenn eine Messung läuft so springe in diesen Code-Block
  {
    int measurementValue       = analogRead( JoystickX_PIN );           // Auslesen des ADC und in measurementValue Speichern
    measurementVoltage         = measurementValue*5.0/1023;             // Umrechnen des measurementValue in measurementVoltage
  
    // Wenn der Messwert größer als 3.0V ist, aber der vorhergehende kleiner war ( Übergang )
    if( (measurementVoltage > 3.0) && (measurementLastVoltage < 3.0) )                // Wir haben ein Ereignis!
    {
      long elapsedTime = micros() - startTimeOfMeasurement;                           // Aktueller Timestamp - Timestamp wann die Messung gestartet wurde = vergangene Zeit
      Serial.println( String(elapsedTime) + String("us seit letztem Ereignis!") );    // Ausgabe des Resultats!
      startTimeOfMeasurement = micros();                                              // Messung quasi neu starten.
    }

    measurementLastVoltage = measurementVoltage;                        // speichere die aktuellen wert als den letzten messwert (für den nächsten Schleifendurchlauf nötig)

    if( micros() < startTimeOfMeasurement )                             // bei micros tritt ein überlauf bereits nach 70 minuten auf, daher schon Wahrscheinlicher als bei millis
      startTimeOfMeasurement = micros();                                // hier einfach Messung neu starten   
  }
}
