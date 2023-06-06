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
 * Beispiel: NTC Auswertung
 * Programmierer: Jan Enenkel
 * Datum: 10.3.2022
 * Hardware: Arduino Nano
 * Programmbeschreibung: Auswerten eines NTCs von einer 3D Drucker Düse
 ******************************************************************************
*/


//////////////////////////////////////////////
// Globale Variablen
//////////////////////////////////////////////

int INPUT_PIN     = A0;       // Eingangspin des NTC

// Berechnung eines NTC3950 Temperatursensors abhängig vom ADC Wert.
float calculateNTCTemperature(int ADC_Value)
{
  float B = 3950.0;                     // B-Wert aus dem Datenblatt entnommen
  float Tn = (25.0+273.15);
  float U2 = ADC_Value*5.0/1024.0;      // Berechnung der Spannung (ADC Referenz und Spannungsteiler Spannung müssen nicht immer identisch sein.
  float U1 = 5.0;                       // Eingangspannung
  float R1 = 4.7;                       // R1 wird in Serie mit 4.7kOhm beschrieben
  float Rn = 100.0;   
  float T = 1/( 1/Tn + (1/B)*log(U2*R1/((U1-U2)*Rn))) - 273.15;
  return T;
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

// Setup Funktion wird einmal beim hochfahren des Arduino Ausgeführt
void setup()
{
  Serial.begin(57600);                                  // Standard 57600 Baud
  Serial.println("#Partytime");                         // Because we need more #partytime 
}

// Loop funktion wird kontinuierlich ausgeführt nach der Setup funktion.
void loop()
{
  int ADCValue = analogRead(INPUT_PIN);                     // Spannung einlesen als ADC Wert
  float NTCValue = calculateNTCTemperature(ADCValue);       // Umrechnung auf Temperatur!
  debugString( "Temperatur=" , NTCValue , "[°C]" );         // Ausgabe per serieller Schnittstelle
  delay(500);                                               // nur alle 500ms ausführen.
}
