#include <WiFiS3.h>
#include <Wire.h> 
#include <LiquidCrystal_I2C.h>

#include "arduino_secrets.h" 
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;

int status = WL_IDLE_STATUS;
WiFiServer server(23);

const int vibrationPins[] = {3, 5, 6, 9}; // 진동 모터가 연결된 핀 번호 배열
boolean alreadyConnected = false;

LiquidCrystal_I2C lcd(0x27, 20, 4);

void setup() {
  startSerial();
  checkWifiModule();
  connectToWifi();
  startServer();
  setPinModes();
  initLCD();
}

void loop() {
  checkForClient();
}

void startSerial() {
  Serial.begin(9600);
  while (!Serial) {
    ; // 시리얼 포트 연결 대기
  }
}

void checkWifiModule() {
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    while (true);
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println("Please upgrade the firmware");
  }
}

void connectToWifi() {
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(ssid);
    status = WiFi.begin(ssid, pass);
    delay(10000);
  }
  printWifiStatus();
}

void startServer() {
  server.begin();
}

void setPinModes() {
  for (int i = 0; i < 4; i++) {
    pinMode(vibrationPins[i], OUTPUT);
  }
}

void initLCD() {
  lcd.init();
  lcd.backlight();
}

void checkForClient() {
  WiFiClient client = server.available();

  if (client) {
    if (!alreadyConnected) {
      client.flush();
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("New client connected");
      client.println("Connected to Arduino");
      alreadyConnected = true;
    }

    if (client.available() > 0) {
      String clientInput = client.readStringUntil('\n');
      processClientInput(clientInput);
    }
  }
}

void processClientInput(String clientInput) {
  // 예: "5000;[1, 2, 6]"
  int semiColonIndex = clientInput.indexOf(';');
  long vibrationDuration = clientInput.substring(0, semiColonIndex).toInt();
  String vibrationData = clientInput.substring(semiColonIndex + 1);

  // LCD에 동작 시간과 진동 데이터 표시
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Duration: " + String(vibrationDuration) + "ms");
  lcd.setCursor(0, 1);
  lcd.print("Vibration: " + vibrationData);

  // 진동 데이터 처리
  controlVibration(vibrationDuration, vibrationData);
}

void controlVibration(long duration, String vibrationData) {
  // 'vibrationData' 예시: "[1, 2, 6]"
  // 진동 패턴 추출 및 파싱
  int pattern = vibrationData[1] - '0'; // 첫 번째 문자를 숫자로 변환
  int intensity = vibrationData[4] - '0'; // 네 번째 문자를 숫자로 변환

  long startTime = millis();
  while (millis() - startTime < duration) {
    int currentIntensity;
    long elapsedTime = millis() - startTime;
    float progress = (float)elapsedTime / (float)duration;

    switch (pattern) {
      case 0: // 점차 증가
        currentIntensity = map(progress * 100, 0, 100, 0, intensity);
        break;
      case 1: // 점차 감소
        currentIntensity = map((1 - progress) * 100, 0, 100, 0, intensity);
        break;
      case 2: // 일정한 강도
        currentIntensity = intensity;
        break;
      default:
        currentIntensity = 0;
    }

    for (int i = 0; i < 4; i++) {
      analogWrite(vibrationPins[i], currentIntensity);
    }
  }

  // 진동 멈춤
  for (int i = 0; i < 4; i++) {
    analogWrite(vibrationPins[i], 0);
  }
}

void printWifiStatus() {
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}
