#include <Servo.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

Servo servo1, servo2, servo3, servo4, esc;
LiquidCrystal_I2C lcd(0x27, 16, 2);

#define SERVO1_PIN 3
#define SERVO2_PIN 5
#define SERVO3_PIN 6
#define SERVO4_PIN 4
#define ESC_PIN    10
#define BUZZER_PIN 11

const int ESC_MIN_US = 1000;
const int ESC_MAX_US = 1100;

void setup() {
  Serial.begin(9600); // TX/RX direct to Pi
  pinMode(BUZZER_PIN, OUTPUT);

  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.print("UIU Nano System");
  lcd.setCursor(0, 1);
  lcd.print("Pi Link Mode...");
  delay(2000);
  lcd.clear();

  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  servo3.attach(SERVO3_PIN);
  servo4.attach(SERVO4_PIN);
  esc.attach(ESC_PIN);

  servo1.write(90);
  servo2.write(0);
  servo3.write(180);
  servo4.write(90);
  esc.writeMicroseconds(ESC_MIN_US);

  delay(1000);
  lcd.clear();
  lcd.print("Waiting for Pi");
}

void fireSequence() {
  digitalWrite(BUZZER_PIN, HIGH);

  lcd.clear();
  lcd.print("!! HUMAN !!");
  lcd.setCursor(0, 1);
  lcd.print("DETECTED");
  delay(1000);

  esc.writeMicroseconds(ESC_MAX_US);
  delay(800);

  lcd.clear();
  lcd.print("TARGET LOCKED");
  lcd.setCursor(0, 1);
  lcd.print(">>> FIRE !!!");

  servo3.write(0);
  delay(800);

  servo3.write(180);
  delay(500);

  esc.writeMicroseconds(ESC_MIN_US);
  digitalWrite(BUZZER_PIN, LOW);

  lcd.clear();
  lcd.print("FIRE COMPLETE");
  lcd.setCursor(0, 1);
  lcd.print("Scanning...");
  delay(1500);

  lcd.clear();
  lcd.print("Waiting for Pi");

  while (Serial.available() > 0) {
    Serial.read();
  }
}

void loop() {
  // ==== Servo 4 — sweep left to right ====
  static int servo4Angle = 0;
  static int dir4 = 1;
  servo4.write(servo4Angle);
  servo4Angle += dir4;
  if (servo4Angle >= 180) dir4 = -1;
  if (servo4Angle <= 0)   dir4 = 1;

  // ==== Servo 1 — mirrors servo 4 ====
  servo1.write(servo4Angle);

  // ==== Servo 2 — nods up and down ====
  static int servo2Angle = 0;
  static int dir2 = 1;
  servo2.write(servo2Angle);
  servo2Angle += dir2;
  if (servo2Angle >= 45) dir2 = -1;
  if (servo2Angle <= 0)  dir2 = 1;

  // ==== Servo 3 — fires only when Pi sends 'f' ====
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'F' || cmd == 'f') {
      fireSequence();
    }
  }

  // ==== LCD — idle ====
  lcd.setCursor(0, 0);
  lcd.print("S4:");
  lcd.print(servo4Angle);
  lcd.print("        ");
  lcd.setCursor(0, 1);
  lcd.print("Scanning...     ");

  delay(80);
}