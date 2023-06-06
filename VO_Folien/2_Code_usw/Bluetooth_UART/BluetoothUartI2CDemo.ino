/*
 *****************************************************************************
 * Organisation: Universität Graz
 * Abteilung: Institut für Physik
 * Anwendung: Beispiel Sample-Code für die Vorlesungsübung
 * 
 * Computergestützte Experimente und Signalauswertung
 * PHY.W04UB/UNT.038UB
 *  
 * Projekt: Demonstration Bluetooth / UART / I2C
 * Beispiel: 
 * Programmierer: Jan Enenkel
 * Datum: 23.12.2022
 * Hardware: Arduino Nano + AZDelivery HC-05 Blueooth Modul + ams AG TMD4903
 * Programmbeschreibung: Messung des TMD4905 über I2C und Ausgabe über Bluetooth
 * sowieo chatten zwischen PC und Smartphone (SoftUart vs. Hardware UART) möglich
 * 
 ******************************************************************************
*/
#include<Wire.h>              // Include für die I2C Schnittstelle
#include <SoftwareSerial.h>   // Include für die SoftwareSerielle Schnittstelle

#define uchar unsigned char     // definition des uchar aus bequemlichkeitsgründen
#define DEV_ADDR 0x39           // definition der I2C Device Address des TMD4903

// Eine Instanz der software Seriellen Schnittstelle mit den PINs D2 und D3 Bilden für das Bluetooth Modul
SoftwareSerial btSerial( 2 , 3 ); // D2 = RX, D3 = TX

// Globale Variablen
char string[80];            
uchar data_buffer[8];                 // 8 Bytes wo die TMD4903 Daten reingespeichert werden können
bool didTMD4903InitWork = false;      // Globale Flag-Bit Variable die anzeigt ob die TMD4903 Initialisierung geklappt hat
long lastTimeStamp = 0;               // Ein long Integer welcher den letztens "Zeitstempel" speichert, siehe Dokumentation des "millis()" Befehls.
bool measurementEnabled = true;       // Ein Boolean um die Messung Ein/Ausschalten zu können.

// I2C Write funktion - kann ein Byte in einem I2C Sensor beschreiben.
// I2C Benötigt zum schreiben:
// deviceAddr - ist die I2C Addresse des jeweiligen Sensors
// registerAddr -  ist die Register Addresse in dem jeweiligen Sensor welche beschrieben werden wird
// dataToDevice - inhalt welcher in das Register beschrieben werden soll
// gibt "true" zurück wenn die Kommunikation erfolgreich war, und "false" falls nicht.
// Bei Fragen kann die I2C Spezifikation als auch die Beschreibung der Wire Library hilfreich sein.
bool I2C_Write( uchar deviceAddr , uchar registerAddr , uchar dataToDevice )
{
  Wire.begin();
  Wire.beginTransmission(deviceAddr);
  Wire.write(registerAddr);
  Wire.write(dataToDevice);
  if(Wire.endTransmission()==0)
    return true;
  return false;
}

// I2C BlockRead funktion - kann mehrere Bytes von einem I2C Sensor lesen 
// I2C Benötigt zum lesen:
// deviceAddr - ist die I2C Addresse des jeweiligen Sensors
// registerAddr -  ist die Register Addresse in dem jeweiligen Sensor von welcher das lesen starten soll - es wird je nach I2C Spezifikation automatisch inkrementiert
// requestedBytes - ist die Anzahl wieviele Register ausgelesen werden sollen, dabei wird immer pro byte ausgegangen.
// dataFromDevice[] - Array in welches die gelesenen Daten beschrieben werden sollen, das Array muss unbedingt soviele Elemente beinhalten wie gelesen wird,
//                  - sonst crasht der Arduino weil er "irgendwo" hin ließt oder gar was anderes überschreibt.
// Gibt die Anzahl an gelesenen bytes zurück, wenn alles geklappt hat sollte diese natürlich requested Bytes betragen.
uchar I2C_BlockRead( uchar deviceAddr , uchar registerAddr , uchar requestedBytes , uchar dataFromDevice[] )
{
    uchar bytesReceived = 0;
    Wire.beginTransmission(deviceAddr);                 // Start I2C Transmission
    Wire.write(registerAddr);                           // Register Adress
    Wire.endTransmission();                             // Stop I2C Transmission
    Wire.requestFrom(deviceAddr, requestedBytes);       // Request the Amount of Bytes
    Wire.endTransmission();
    uchar remaining = requestedBytes;
  
    while (Wire.available() && remaining--)
        {
            dataFromDevice[bytesReceived] = Wire.read();
            ++bytesReceived;
        }

  return bytesReceived;
}

// Funktion zum Initialisieren des TMD4903
// Dabei wird der TMD4903 in den ALS Mode gesetzt
// es können Verstärkung (gain) als auch Integrations Zeit (in ms) eingestellt werden
// Der TMD4903 kann 1-4-16-64x Gain einstellen mit den Variablen von 0-1-2-3.
// Die Integrationszeit kann direkt in ms eingestellt werden, welches in Datenblatt des TMD4903 nachgelesen werden kann.
bool InitTMD4903( uchar deviceAddress , uchar gain , int integrationTime_ms )
{
  bool status = false;
  
  // Integrationszeit kann eingestellt werden zwischen 2.78 and 711ms
  if( integrationTime_ms > 711 )
    integrationTime_ms = 711;
  if( integrationTime_ms < 3)
    integrationTime_ms = 3;

  // Berechnung des ATime Werts, wie im Datenblatt des TMD4903 angegeben.
  uchar ATimeValue = ((integrationTime_ms-711.0)/(-2.78));

  status = I2C_Write(deviceAddress,0x80,0x01);    // 0x80 = Enable Register
  I2C_Write(deviceAddress,0x81,ATimeValue);       // 0x81 = ATime Register                          - Einstellen der Integrationszeit
  I2C_Write(deviceAddress,0x90, gain&0x03 );      // 0x90 = Konfiguration des Setting Register1     - Stellen der Verstärkung
  I2C_Write(deviceAddress,0x9F,0x00);             // 0x9F = Konfiguration des Setting Register2
  I2C_Write(deviceAddress,0x80,0x03);             // 0x80 = Enable Register - einschalten der ALS Engine (Ambient Light Sensing)
  return status;
}

// Setupfunktion des Arduino - diese Funktion wird nach dem Hochfahren des Arduino einmalig ausgeführt
void setup()
{
  btSerial.begin(115200);       // Konfiguration des Software UART mit 115200 BAUD.
  Serial.begin(115200);         // Konfiguration des Hardware UART mit 115200 BAUD.

  // Initialisieren des TMG4903, I2C Addresse = 0x39, gain = 64x, integrationTime = 50ms
  didTMD4903InitWork = InitTMD4903( 0x39 , 3 , 50 );

  if( didTMD4903InitWork )                                  // Abfragen ob die Initialisierung funktioniert hat
    Serial.println("#Partytime");                           // Wenn ja --> "#Partytime" über die Hardware serielle Schnittstelle schicken.
  else
    Serial.println("Init of TMD4903 did not work!");        // Wenn nein --> Fehlermeldung schicken

  // Programming Mode on when Pin4 is high!
  pinMode(4, OUTPUT);                                       // Pin4 als Ausgang setzen
  digitalWrite(4, LOW);                                     // Pin4 auf GND setzen, falls das Bluetooth Modul Programmiert werden soll muss dieser Pin auf High gesetzt werden.
                                                            // Siehe HC-05 Programmierbeschreibung.
  btSerial.println("#Partytime");                           // Über Bluetooth ein "#Partytime" schicken.
}

// Hauptschleife des Programms
void loop()
{
  char data;
  
  if (btSerial.available())     // Wenn Daten über Bluetooth eintreffen
  {
    data = btSerial.read();     // in "data" speichern
    Serial.write(data);         // und an den PC UART schicken
    if(data == '$')             // falls das empfangene zeichen ein "$" ist die messung ein/ausschalten
      measurementEnabled = !measurementEnabled;
  }

  if (Serial.available())       // Wenn Daten über den PC eintreffen
  {
    data = Serial.read();       // in "data" speichern
    btSerial.write(data);       // und per Bluetooth schicken
   if(data == '$')             // falls das empfangene zeichen ein "$" ist die messung ein/ausschalten
      measurementEnabled = !measurementEnabled;
  }

  if(millis()<lastTimeStamp)   // Vermeidung wenn es bei millis zu einem überlauf kommt ( siehe millis() Doku auf Arduino.cc )
    lastTimeStamp = millis();

  // Beispiel einer Stopuhrmethode - dabei wird der "lastTimeStamp" mit dem aktuellen millis() wert verglichen.
  if(millis()>(lastTimeStamp+100))    // Alle 100ms ausführen
  {
      lastTimeStamp = millis();       // neuen Zeitstempel "stempeln"
      if( didTMD4903InitWork && measurementEnabled )                                    // In diesen Block nur dann reinspringen wenn der TMD funktioniert und es auch vom User her erlaubt ist.
      {
          uchar receivedBytes = I2C_BlockRead( DEV_ADDR , 0x94 , 8 , data_buffer );     // Lese 8 bytes des TMD4903 welcher die I2C Addresse 0x39 hat von seiner RegisterAddresse 0x94
                                                                                        // die gelsenen Bytes werden in data_buffer gespeichert, und es wird zurückgegeben wieviele Bytes gelesen wurden
          if(receivedBytes==0)                                                          // wenn keine Bytes gelesen wurden
          {
            Serial.println("sensor Error!");                                            // Ausgabe einer Fehlermeldung via UART an den PC
            btSerial.println("sensor Error!");                                          // Ausgabe einer Fehlermeldung via UART an das Bluetooth modul (und damit ans smartphone)
          }
          else                                                                          // lesen hat geklappt
          {
            int value = data_buffer[1]*256 + data_buffer[0];                            // Berechnung des CH0 Wertes des TMD4903
            sprintf(string, "%d" , value );                                             // Ausgabe als String
            btSerial.println(string);                                                   // String per Bluetooth verschicken
          }
      }
   }

   Serial.flush();                                                                      // Eigentlich wären flush befehle nicht nötig, aber der Buffer wird nach einiger Zeit langsam
   btSerial.flush();                                                                    // nicht klar ob von PC oder Bluetooth das problem kommt.
}
