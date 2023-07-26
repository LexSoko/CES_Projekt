#include <AccelStepper.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>

// Stepper Motor Setup
AccelStepper Winder_Stepper(AccelStepper::DRIVER, 3, 4);
AccelStepper Feeder_Stepper(AccelStepper::DRIVER, 7, 8);

//SD Card CS Pin
const int CS = 53;
bool SD_Check = false;
String Config = "";
File Load_Config;

//Firmware
String Firmware_V = "v0.3.1.8:";

//Enable SW for Stepper Motor
int w_en = 2;
int f_en = 6;

//Limit switch
int L_SW = 5;
int R_SW = 9;

//E-Stop Switch
int E_Stop = 13;

//Analog Buttons
int Left_Button = A0;
int Right_Button = A1;
int Winder_DisableButton = A2;
int Feeder_DisableButton = A3;
int Speed_Pot = A5;

//Toggle Switch Contol
int Winder_Toggle = 11;
int Feeder_Toggle = 12;

//Serial Data Input
String Serial_Input;
String EStop_Input;

//Visual Basic Pause
bool Pause = false;

//Pot Speed Input
int Pot;

//Winding Parameters
long Winding_Steps;
int Winding_Speed;
int Feeder_StepsWidth;
long Feeder_Steps;
int Feeder_Speed;
int LayersCounter;
int FDir = 0;
bool FDir0;
bool FDir1;
int WDir = 0;
bool WDir0;
int Winding_StepsA;

//Variables for the serial input array
int ct[9];
int gt[9];

//Homing
bool Home_L = false;
bool Home_R = false;
bool Home_ = false;

//Feeder and Winder Check
bool F_CH = true;
bool W_CH = true;
bool A_CH = true;

//E-Stop Check
bool E_CH = true;

//Manual Feeder speed to compensate for the microsteping
int MicroStepF;
int MicroStepW;
float Fn;
float Wn;
int LeadS;
float FeederRatio;
float WinderRatio;

//Counters
int StepW_Counter = 0;
bool T_CH = true;

void setup()
{ 
  Serial.begin(115200); // USB serial port 0

  Load_File();
  
  //Winder Direction
  Winder_Stepper.setPinsInverted(true,false,false);

  pinMode(L_SW, INPUT_PULLUP); // Left Limit Switch
  pinMode(R_SW, INPUT_PULLUP); // Right Limit Switch

  pinMode(E_Stop, INPUT_PULLUP); // E Stop Pin
  
  // Stepper Motor Driver Enable Pin
  pinMode(w_en, OUTPUT); // Winder Stpper Motor Enable Pin
  pinMode(f_en, OUTPUT); // Feeder Stpper Motor Enable Pin
  // Stepper Motor Driver Enable Mode
  digitalWrite(w_en, HIGH);
  digitalWrite(f_en, HIGH);

  // Control Buttons
  pinMode(Left_Button, INPUT);
  pinMode(Right_Button, INPUT);
  pinMode(Winder_DisableButton, INPUT);
  pinMode(Feeder_DisableButton, INPUT);
  pinMode(Speed_Pot, INPUT);

  // Toogle Control
  pinMode(Winder_Toggle, INPUT_PULLUP); 
  pinMode(Feeder_Toggle, INPUT_PULLUP);

  Winder_Reset();
  Feeder_Reset();
  Initial_FDir();
  Home_Reset();
  Input_Reset();
}

void Load_File()
{
  Config = "";
  if (!SD.begin(CS))
     {
     Serial.print("Error: Memory card initialization failed.");
     SD_Check = false;
     }
     else
     {
     SD_Check = true;
     }
     
     if (SD_Check == true)
     {
     Load_Config = SD.open("Config.ini");
         if (Load_Config) 
         {
             while (Load_Config.available()) 
             {
             Config += (char)Load_Config.read();
             }
             Load_Config.close();
         }
         gt[0] = Config.indexOf(':');
         MicroStepF = Config.substring(0, gt[0]).toInt();
         gt[1] = Config.indexOf(':', gt[0]+1);
         MicroStepW = Config.substring(gt[0]+1, gt[1]).toInt();
         gt[2] = Config.indexOf(':', gt[1]+1);
         LeadS = Config.substring(gt[1]+1, gt[2]).toInt();
         gt[3] = Config.indexOf(':', gt[2]+1);
         FeederRatio = Config.substring(gt[2]+1, gt[3]).toInt();
         gt[4] = Config.indexOf(':', gt[3]+1);
         WinderRatio = Config.substring(gt[3]+1, gt[4]).toInt();
         Winding_StepsA = MicroStepW * WinderRatio;
     }
}

void Winder_moveTo(int W_Steps)
{
  Winder_Stepper.moveTo(W_Steps);
}

void Feeder_moveTo(int F_Steps)
{
  Feeder_Stepper.moveTo(F_Steps);
}

void Feeder_SpeedSetup(int FSpeed) //Setting Speed for Feeder
{
  Feeder_Stepper.setMaxSpeed(FSpeed);
  Feeder_Stepper.setAcceleration(FSpeed);
}

void Winder_SpeedSetup(int WSpeed) //Setting Speed for Winder
{
  Winder_Stepper.setMaxSpeed(WSpeed);
  Winder_Stepper.setAcceleration(WSpeed);
}

void Winder_Reset()
{
  Winder_Stepper.setMaxSpeed(0);
  Winder_Stepper.setAcceleration(0);
  Winder_Stepper.setCurrentPosition(0);
  Winder_Stepper.moveTo(0);
}

void Feeder_Reset()
{
  Feeder_Stepper.setMaxSpeed(0);
  Feeder_Stepper.setAcceleration(0);
  Feeder_Stepper.setCurrentPosition(0);
  Feeder_Stepper.moveTo(0);
}

void Input_Reset()
{
  Winding_Steps = 0;
  Winding_Speed = 0;
  Feeder_StepsWidth = 0;
  Feeder_Steps = 0;
  Serial.flush();
}

void Initial_FDir()
{
  if (FDir == 0)
  {
   FDir0 = false;
   FDir1 = true;
  }
  else if (FDir == 1)
  {
   FDir0 = true;
   FDir1 = false;
  }
  Feeder_SetDir(FDir0); //Feeder Dir //false : Left to Right //true : Right to Left
}

void Initial_WDir()
{
  if (WDir == 0)
  {
   WDir0 = true;
  }
  else if (WDir == 1)
  {
   WDir0 = false;
  }
  Winder_SetDir(WDir0); //Winder Dir //false : Clockwise //true : Counter Clockwise 
}

void Feeder_SetDir(bool DirSet)
{
  Feeder_Stepper.setPinsInverted(DirSet,false,false);
}

void Winder_SetDir(bool DirSet)
{
  Winder_Stepper.setPinsInverted(DirSet,false,false);
}

void Home_Reset()
{
  Home_L = false;
  Home_R = false;
  if (Home_L == false && Home_R == false && Home_ == true)
  {
  Serial.print("HOME_END");
  Serial.flush();
  Home_ = false;
  }
}

void Home_Toggle()
{
  Home_L = false;
  Home_R = false;
  if (Home_L == false && Home_R == false && Home_ == true)
  {
  Serial.print("HOME_TOGGLE");
  Serial.flush();
  Home_ = false;
  }
}

void Feeder_Dir()
{     
      if (Feeder_Stepper.currentPosition() == Feeder_StepsWidth * LayersCounter && LayersCounter % 2 != 0)
      {
       LayersCounter++;
       Feeder_SetDir(FDir1);
      }
      else if (Feeder_Stepper.currentPosition() == Feeder_StepsWidth * LayersCounter && LayersCounter % 2 == 0)
      {
       LayersCounter++;
       Feeder_SetDir(FDir0);
      }
}

void loop()
{
      // Input Read Visual Basic Input from Serial
      if (Serial.available() > 0)
      {
      Serial_Input = Serial.readString();

            if (Serial_Input.substring(0,8) == "RUN_CODE")
            {
            ct[0] = Serial_Input.indexOf(',');
            ct[1] = Serial_Input.indexOf(',', ct[0]+1);
            Winding_Steps = Serial_Input.substring(ct[0]+1, ct[1]).toInt();
            ct[2] = Serial_Input.indexOf(',', ct[1]+1);
            Winding_Speed = Serial_Input.substring(ct[1]+1, ct[2]).toInt();
            ct[3] = Serial_Input.indexOf(',', ct[2]+1);
            Feeder_StepsWidth = Serial_Input.substring(ct[2]+1, ct[3]).toInt();
            ct[4] = Serial_Input.indexOf(',', ct[3]+1);
            Feeder_Steps = Serial_Input.substring(ct[3]+1, ct[4]).toInt();
            ct[5] = Serial_Input.indexOf(',', ct[4]+1);
            Feeder_Speed = Serial_Input.substring(ct[4]+1, ct[5]).toInt();
            ct[6] = Serial_Input.indexOf(',', ct[5]+1);
            FDir = Serial_Input.substring(ct[5]+1, ct[6]).toInt();
            ct[7] = Serial_Input.indexOf(',', ct[6]+1);
            WDir = Serial_Input.substring(ct[6]+1, ct[7]).toInt();
            LayersCounter = 1;
            Winder_Reset();
            Feeder_Reset();
            Initial_FDir();
            Initial_WDir();
            Home_Reset();
            Winder_SpeedSetup(Winding_Speed);
            Feeder_SpeedSetup(Feeder_Speed);
            Winder_moveTo(Winding_Steps);
            Feeder_moveTo(Feeder_Steps);
            StepW_Counter = 0;
            T_CH = false;
            Home_L = false;
            Home_R = false;
            Pause = false;
            delay(1500);
            }
            else if(Serial_Input.substring(0,1) == "Z")
            {
            Winder_Reset();
            Feeder_Reset();
            Input_Reset();
            Home_Reset();
            T_CH = false;
            Home_L = false;
            Home_R = false;
            Pause = false;
            Load_File();
            Serial.print("#:" + Config + Firmware_V);
            Serial.flush();
            }
            else if(Serial_Input.substring(0,4) == "SAVE")
            {
            T_CH = false;
            Home_L = false;
            Home_R = false;
            Pause = false;
                  if (!SD.begin(CS))
                  {
                  Serial.print("Error: Memory card initialization failed.");
                  SD_Check = false;
                  }
                  else
                  {
                  SD_Check = true;
                  }
                  
                  if (SD_Check == true)
                  {
                  SD.remove("Config.ini");
                  Load_Config = SD.open("Config.ini", FILE_WRITE);
                      if (Load_Config) 
                      {
                      Load_Config.println(Serial_Input.substring(5, Serial_Input.lastIndexOf(":") + 1));
                      Load_Config.flush();
                      Load_Config.close();
                      }
                  Load_File();
                  Serial.print("@:" + Config);
                  Serial.flush();
                  }
            }
            else if(Serial_Input.substring(0,6) == "CANCEL")
            {
            Winder_Reset();
            Feeder_Reset();
            Input_Reset();
            Home_Reset();
            T_CH = false;
            Home_L = false;
            Home_R = false;
            Pause = false;
            Serial.print("CANCEL");
            Serial.flush();
            }
            else if(Serial_Input.substring(0,5) == "PAUSE")
            {
            Pause = true;
            }
            else if(Serial_Input.substring(0,6) == "RESUME")
            {
            Pause = false;
            Winder_moveTo(Winding_Steps);
            Feeder_moveTo(Feeder_Steps);
            }
            else if(Serial_Input.substring(0,6) == "HOME_L")
            {
            Home_L = true;
            Home_R = false;
            Home_ = true;
            }
            else if(Serial_Input.substring(0,6) == "HOME_R")
            {
            Home_L = false;
            Home_R = true;
            Home_ = true;
            }
      Serial_Input = "";
      }
      
      if (digitalRead(E_Stop) == HIGH)
      {
        if (E_CH == false)
        {
        Serial.print("ESTOP_N");
        Serial.flush();
        }
        E_CH = true;
            //Main Winding Sqeuences Starts//
            if(Winding_Steps != 0 || Feeder_Steps != 0)
            {
                  if (Pause == false && digitalRead(Feeder_DisableButton) == LOW && digitalRead(Winder_DisableButton) == LOW && digitalRead(w_en) == HIGH && digitalRead(f_en) == HIGH)
                  {                    
                          // Feeder position where both Limit Switch sensor are off
                          if (digitalRead(R_SW) == HIGH && digitalRead(L_SW) == HIGH)
                          {
                                Winder_Stepper.run();
                                Feeder_Stepper.run();
                                Feeder_Dir();
                          }                          
                          // Feeder position is moving Left to Right(Dir == 0), Right Limit Switch is Off and Left Limit Switch is On
                          else if (digitalRead(R_SW) == HIGH && digitalRead(L_SW) == LOW && FDir == 0 && Feeder_Stepper.currentPosition() < 400)
                          {
                                Winder_Stepper.run();
                                Feeder_Stepper.run();
                                Feeder_Dir();
                          }                          
                          // Feeder position is moving Right to Left(Dir == 1), Right Limit Switch is ON and Left Limit Switch is Off
                          else if (digitalRead(R_SW) == LOW && digitalRead(L_SW) == HIGH && FDir == 1 && Feeder_Stepper.currentPosition() < 400)
                          {
                                Winder_Stepper.run();
                                Feeder_Stepper.run();
                                Feeder_Dir();
                          }
                          else
                          {
                                Winder_Reset();
                                Feeder_Reset();
                                Home_Reset();
                                Input_Reset();
                                Serial.print("$");
                                Serial.flush();
                          }
                          
                          //Winder Counter
                          if (StepW_Counter % Winding_StepsA == 0 && Winder_Stepper.currentPosition() >  StepW_Counter)
                          {
                            Serial.print(StepW_Counter);
                            Serial.flush();
                          }
                          else if (StepW_Counter == Winding_Steps - 1 && T_CH == false)
                          {
                            Serial.print(Winding_Steps);
                            Serial.flush();
                            T_CH = true;
                          }
                          StepW_Counter = Winder_Stepper.currentPosition();
                          
                  }
                  else if (Pause == true)
                  {
                  Winder_Stepper.stop();
                  Feeder_Stepper.stop();
                  }
                  
                  if (Winder_Stepper.distanceToGo() == 0 && Feeder_Stepper.distanceToGo() == 0)
                  {
                  Winder_Reset();
                  Feeder_Reset();
                  Home_Reset();
                  Input_Reset();
                  Serial.print("%");
                  Serial.flush();
                  }
                  else if (digitalRead(Feeder_DisableButton) == HIGH || digitalRead(Winder_DisableButton) == HIGH)
                  {
                  Winder_Reset();
                  Feeder_Reset();
                  Home_Reset();
                  Input_Reset();
                  Serial.print("!");
                  Serial.flush();
                  }
            }            
          //Manual Control//
          else if (Winding_Steps == 0 && Feeder_Steps == 0) 
            {
             //Get Pot input speed
             Pot = analogRead(Speed_Pot);
             Input_Reset();
                      ///////////////////////////////////////////////////////////////////////////////////////////////
                      if (digitalRead(Feeder_DisableButton) == LOW) //Feeder is enabled
                      {
                          if (A_CH == false)
                          {
                          Serial.print("ENABLED_ALL");
                          Serial.flush();
                          }
                          if (F_CH == false)
                          {
                          Serial.print("FEEDER_ENABLED");
                          Serial.flush();
                          }
                          F_CH = true;
                          A_CH = true;
                          
                          digitalWrite(f_en, HIGH); //Enable Feeder
                          if (digitalRead(Feeder_Toggle) == HIGH && digitalRead(Winder_Toggle) == LOW)
                          {
                            
                            Fn = MicroStepF / 200; //Factor Multipler for FEEDER stepper motor with different microstep values
                            
                                if (digitalRead(Left_Button) == HIGH && digitalRead(Right_Button) == LOW && digitalRead(L_SW) == HIGH)
                                {
                                    Feeder_SpeedSetup(Pot * Fn);
                                    Feeder_SetDir(true); //Right to Left
                                    Feeder_moveTo(1800000);
                                    Feeder_Stepper.run();
                                }
                                else if (digitalRead(Left_Button) == LOW && digitalRead(Right_Button) == HIGH && digitalRead(R_SW) == HIGH) 
                                {
                                    Feeder_SpeedSetup(Pot * Fn);
                                    Feeder_SetDir(false); //Left to Right
                                    Feeder_moveTo(1800000);
                                    Feeder_Stepper.run();
                                }
                                //Home to Left
                                else if (Home_L == true && Home_R == false && digitalRead(Left_Button) == LOW && digitalRead(Right_Button) == LOW && digitalRead(L_SW) == HIGH)
                                {
                                    Feeder_SpeedSetup(Pot * Fn);
                                    Feeder_SetDir(true); //Right to Left
                                    Feeder_moveTo(1800000);
                                    Feeder_Stepper.run();
                                }
                                //Home to Right
                                else if (Home_L == false && Home_R == true && digitalRead(Left_Button) == LOW && digitalRead(Right_Button) == LOW && digitalRead(R_SW) == HIGH)
                                {
                                    Feeder_SpeedSetup(Pot * Fn);
                                    Feeder_SetDir(false); //Left to Right
                                    Feeder_moveTo(1800000);
                                    Feeder_Stepper.run();
                                }
                                else
                                {
                                    Feeder_Reset();
                                    Initial_FDir();
                                    Home_Reset();
                                }
                          }
                          else if (Home_ == true)
                          {
                            Home_Toggle();
                          }
                      }
                      if (digitalRead(Feeder_DisableButton) == HIGH && digitalRead(Winder_DisableButton) == LOW) //Disable Feeder & Winder is enabled
                      {
                          digitalWrite(f_en, LOW);
                          Feeder_Reset();
                          Home_Reset();
                          if (F_CH == true)
                          {
                          Serial.print("FEEDER_DISABLED");
                          Serial.flush();
                          F_CH = false;
                          }
                      }
                      ///////////////////////////////////////////////////////////////////////////////////////////////
                      if (digitalRead(Winder_DisableButton) == LOW) //Winder is enabled
                      {
                          if (A_CH == false)
                          {
                          Serial.print("ENABLED_ALL");
                          Serial.flush();
                          }
                          if (W_CH == false)
                          {
                          Serial.print("WINDER_ENABLED");
                          Serial.flush();
                          }
                          W_CH = true;
                          A_CH = true;
                          
                          digitalWrite(w_en, HIGH); //Enable Winder
                          if (digitalRead(Feeder_Toggle) == LOW && digitalRead(Winder_Toggle) == HIGH)
                          {

                              Wn = (float)MicroStepW / 400; //Factor Multipler for Winder stepper motor with different microstep values
                            
                              if (digitalRead(Left_Button) == HIGH && digitalRead(Right_Button) == LOW)
                              {
                                  Winder_SpeedSetup(Pot * Wn);
                                  Winder_SetDir(false);
                                  Winder_moveTo(180000);
                                  Winder_Stepper.run();
                              }
                              else if (digitalRead(Left_Button) == LOW && digitalRead(Right_Button) == HIGH)
                              {
                                  Winder_SpeedSetup(Pot * Wn);
                                  Winder_SetDir(true);
                                  Winder_moveTo(180000);
                                  Winder_Stepper.run();
                              }
                              else
                              {
                                  Winder_Reset();
                                  Initial_FDir();
                              }

                              if (Home_ == true)
                              {
                                Home_L = false;
                                Home_R = false;
                                Home_ = false;
                                Serial.print("HOME_END");
                                Serial.flush();
                              }
                          }
                      }
                      if (digitalRead(Winder_DisableButton) == HIGH && digitalRead(Feeder_DisableButton) == LOW) //Disable Winder & Feeder is enabled
                      {
                          digitalWrite(w_en, LOW);
                          Winder_Reset();
                          Home_Reset();
                          if (W_CH == true)
                          {
                          Serial.print("WINDER_DISABLED");
                          Serial.flush();
                          W_CH = false;
                          }
                      }
                      
                      if (digitalRead(Winder_DisableButton) == HIGH && digitalRead(Feeder_DisableButton) == HIGH) //Both Winder & Feeder Disabled
                      {
                          digitalWrite(w_en, LOW);
                          digitalWrite(f_en, LOW);
                          Winder_Reset();
                          Home_Reset();
                          if (A_CH == true)
                          {
                          Serial.print("DISABLED_ALL");
                          Serial.flush();
                          A_CH = false;
                          }
                      }
            }
      }
      else
      {
      Winder_Reset();
      Feeder_Reset();
      Input_Reset();
      Home_Reset();
          if (digitalRead(E_Stop) == LOW)
          {
            if (E_CH == true)
            {
            Serial.print("ESTOP_A");
            Serial.flush();
            E_CH = false;
            }
          }
      }
}
