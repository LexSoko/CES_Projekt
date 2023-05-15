/*
 *****************************************************************************
 * Organisation: Universität Graz
 * Abteilung: Institut für Physik
 * Anwendung: Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt: Übungsteil - Vorgabe
 * Beispiel: GPIO - LED
 * Programmierer: Jan Enenkel
 * Datum: 16.3.2023
 * Hardware: Universität Graz - Physik Übungsboard - Arduino Uno ( mit CH340 )
 * Programmbeschreibung: Dieser Code soll eine GPIO als Ausgang konfigurieren
 * und anschließend die LED mit 2s leuchten lassen: 
 * - eine sekunde Leuchten
 * - eine sekunde nicht Leuchten
 ******************************************************************************
*/

// Defintion des D7 pins als "R_PIN" an welchem die Rote LED angeschlossen ist.
#define R_PIN 7

// Setup Funktion wird einmal beim hochfahren des Arduino Ausgeführt
void setup() {
  
  pinMode( R_PIN , OUTPUT );     // Rote LED-pin auf Ausgang stellen

}

// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{
  digitalWrite( R_PIN , HIGH );   // Rote LED auf High stellen (+5V) damit leuchtet die LED
  delay(1000);                    // 1000ms warten
  digitalWrite( R_PIN , LOW );    // Rote LED auf Low stellen (0V) damit erlischt die LED
  delay(1000);                    // Wieder 1000ms warten
                                  // Durchlaufzeit wird ca. 2 sekunden benötigen
}
