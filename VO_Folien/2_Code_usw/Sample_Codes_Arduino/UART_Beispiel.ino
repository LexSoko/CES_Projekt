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
 * Beispiel: UART
 * Programmierer: Jan Enenkel
 * Datum: 16.3.2023
 * Hardware: Universität Graz - Physik Übungsboard - Arduino Uno ( mit CH340 )
 * Programmbeschreibung: Dieser Code soll wenn ein "c" eintrifft 
 * eine Messreihe an den PC Schicken
 ******************************************************************************
*/

// Setup Funktion wird einmal beim hochfahren des Arduino Ausgeführt
void setup() {
  
  Serial.begin(57600);    // Initialisieren der UART auf 57600 BAUD
  while(!Serial)          // Warten bis die serielle schnitstelle Initialisiert ist
  {
    delay(1);
  }

  Serial.println( "#Partytime" );   // Wenn initialisierung abgeschlossen ist soll 
}

// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{
  int messwert = 0;               // Variable mit namen 'messwert' wo die Messung gespeichert werden kann
  if(Serial.available() > 0)      // Falls im eingangsbuffer der seriellen Schnittstelle daten sind
  {
    if(Serial.read() == 'c')      // Wenns das Empfangene Zeichen ein 'c' ist starte die Messung (sonst Ignoriere)
    {
      for( int i = 0; i < 10; i++ )           // Starte eine schleife mit 10x durchläufen
        {
          messwert = analogRead(A0);                                              // Messung eines Messwerts
          String ausgabeString = String(i) + String(";") + String(messwert);      // Formierung eines Ausgabestrings
          Serial.println( ausgabeString );                                        // Ausgabe des Strings über die UART
        }
    }  
  } 
}
