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
 * Beispiel: Moveo Roboter - ESP32 mit Bluetooth BLE
 * Programmierer: Jan Enenkel
 * Datum: 13.2.2023
 * Hardware: ESP32
 * Programmbeschreibung: Verbindung mit einem XBOX Controller über Bluetooth BLE
 *                       Anschließende String formatierung und dann Senden via SW UART an den Arduino Mega
 * 
 * 
 ******************************************************************************
*/

#define uchar unsigned char
#include <XboxSeriesXControllerESP32_asukiaaa.hpp>      // asukiaaa Bibliothek muss eingebunden werden.

#define RXD2 16       // Definition der SW UART Pins
#define TXD2 17

// Addresse von Jan's X-Box Controller
XboxSeriesXControllerESP32_asukiaaa::Core xboxController("3c:fa:06:4f:a3:a7");    
long lastTimeStamp = 0;

uchar btnA_last = 0;
uchar btnB_last = 0;
uchar btnX_last = 0;
uchar btnY_last = 0;

uchar btnDirUp_last = 0;
uchar btnDirLeft_last = 0;
uchar btnDirRight_last = 0;
uchar btnDirDown_last = 0;

uchar btnShare_last = 0;
uchar btnStart_last = 0;
uchar btnSelect_last = 0;
uchar btnXbox_last = 0;

uchar btnLB_last = 0;
uchar btnRB_last = 0;
uchar btnLS_last = 0;
uchar btnRS_last = 0;

uchar btnA = 0;
uchar btnB = 0;
uchar btnX = 0;
uchar btnY = 0;

uchar btnDirUp = 0;
uchar btnDirLeft = 0;
uchar btnDirRight = 0;
uchar btnDirDown = 0;

uchar btnShare = 0;
uchar btnStart = 0;
uchar btnSelect = 0;
uchar btnXbox = 0;

uchar btnLB = 0;
uchar btnRB = 0;
uchar btnLS = 0;
uchar btnRS = 0;

bool firstConnection = false;

// Initialisieren
void setup()
{
  Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);
  Serial.begin(115200);
  Serial.println("#Partytime");
  xboxController.begin();
  lastTimeStamp = millis();
}

void storeLastButtonValues()
{
      btnA_last = xboxController.xboxNotif.btnA;
      btnB_last = xboxController.xboxNotif.btnB;
      btnX_last = xboxController.xboxNotif.btnX;
      btnY_last = xboxController.xboxNotif.btnY;

      btnDirUp_last = xboxController.xboxNotif.btnDirUp;
      btnDirLeft_last = xboxController.xboxNotif.btnDirLeft;
      btnDirRight_last = xboxController.xboxNotif.btnDirRight;
      btnDirDown_last = xboxController.xboxNotif.btnDirDown;

      btnShare_last = xboxController.xboxNotif.btnShare;
      btnStart_last = xboxController.xboxNotif.btnStart;
      btnSelect_last = xboxController.xboxNotif.btnSelect;
      btnXbox_last = xboxController.xboxNotif.btnXbox; 

      btnLB_last = xboxController.xboxNotif.btnLB;
      btnRB_last = xboxController.xboxNotif.btnRB;
      btnLS_last = xboxController.xboxNotif.btnLS;
      btnRS_last = xboxController.xboxNotif.btnRS;
}

// Hauptprogrammschleife
void loop()
{
  xboxController.onLoop();
  
  if (xboxController.isConnected())
  {
    if(firstConnection==false)
    {
      Serial.println("Connected to: " + xboxController.buildDeviceAddressStr());
      firstConnection=true;
    }
    
    if (xboxController.isWaitingForFirstNotification())
    {
      Serial.println("waiting for first notification");
    }
    else
    {
      if(millis()< lastTimeStamp)
        lastTimeStamp = millis();
        
      if(millis() >  lastTimeStamp+50)        // Alle 50ms einmal Daten schicken!
      {
            lastTimeStamp = millis();
            
            // Daten verpacken --> String Parsing
            uint16_t trigLT = xboxController.xboxNotif.trigLT;
            uint16_t trigRT  = xboxController.xboxNotif.trigRT ;
            uint16_t joystickMax = XboxControllerNotificationParser::maxJoy;
            float Joystick_LeftHorizontal = 2.0*(((float)xboxController.xboxNotif.joyLHori / (float)joystickMax)-0.5);
            float Joystick_LeftVertical = 2.0*(((float)xboxController.xboxNotif.joyLVert / (float)joystickMax)-0.5);
            float Joystick_RightHorizontal = 2.0*(((float)xboxController.xboxNotif.joyRHori / (float)joystickMax)-0.5);
            float Joystick_RightVertical = 2.0*(((float)xboxController.xboxNotif.joyRVert / (float)joystickMax)-0.5);
      
            String s = "<" + String(xboxController.xboxNotif.btnA) + String(",")
                           + String(xboxController.xboxNotif.btnB) + String(",")
                           + String(xboxController.xboxNotif.btnY) + String(",")
                           + String(xboxController.xboxNotif.btnX) + String(",")
                           + String(trigLT) + String(",")
                           + String(trigRT) + String(",")
                           + String(Joystick_LeftHorizontal) + String(",")
                           + String(Joystick_LeftVertical) + String(",")
                           + String(Joystick_RightHorizontal) + String(",")
                           + String(Joystick_RightVertical) + String(">");
                           
            Serial.println(s);
            Serial2.println(s);
      }
    }
 }
 else
 {
    firstConnection = false;
    Serial.println("not connected");
    if (xboxController.getCountFailedConnection() > 2)
    {
      ESP.restart();
    }
  } 

  delay(50);  // 50ms warten
}
