#include <Arduino.h>

constexpr uint8_t ESTOP_PIN = 2;
constexpr uint8_t RELAY_PIN = 8;
constexpr uint8_t LEFT_PWM_PIN = 9;
constexpr uint8_t RIGHT_PWM_PIN = 10;
constexpr unsigned long HEARTBEAT_TIMEOUT_MS = 250;
constexpr int PWM_NEUTRAL = 127;

unsigned long lastHeartbeatMs = 0;
bool hostReady = false;

void setMotorNeutral() {
  analogWrite(LEFT_PWM_PIN, PWM_NEUTRAL);
  analogWrite(RIGHT_PWM_PIN, PWM_NEUTRAL);
}

bool estopActive() {
  return digitalRead(ESTOP_PIN) == LOW;
}

bool heartbeatExpired() {
  return !hostReady || (millis() - lastHeartbeatMs) > HEARTBEAT_TIMEOUT_MS;
}

void setRelaySafe(bool enabled) {
  digitalWrite(RELAY_PIN, enabled ? HIGH : LOW);
}

void handleSerialCommand(String command) {
  command.trim();
  if (command == "HB") {
    hostReady = true;
    lastHeartbeatMs = millis();
    Serial.println("OK HB");
    return;
  }
  if (command.startsWith("PWM ")) {
    int split = command.indexOf(' ', 4);
    if (split < 0) {
      Serial.println("ERR PWM");
      return;
    }
    int left = constrain(command.substring(4, split).toInt(), 0, 255);
    int right = constrain(command.substring(split + 1).toInt(), 0, 255);
    if (estopActive() || heartbeatExpired()) {
      setMotorNeutral();
      Serial.println("ERR SAFE");
      return;
    }
    analogWrite(LEFT_PWM_PIN, left);
    analogWrite(RIGHT_PWM_PIN, right);
    Serial.println("OK PWM");
    return;
  }
  Serial.println("ERR UNKNOWN");
}

void setup() {
  pinMode(ESTOP_PIN, INPUT_PULLUP);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LEFT_PWM_PIN, OUTPUT);
  pinMode(RIGHT_PWM_PIN, OUTPUT);
  setMotorNeutral();
  setRelaySafe(false);
  Serial.begin(115200);
}

void loop() {
  if (Serial.available() > 0) {
    handleSerialCommand(Serial.readStringUntil('\n'));
  }

  bool safe = !estopActive() && !heartbeatExpired();
  if (!safe) {
    setMotorNeutral();
  }
  setRelaySafe(safe);

  static unsigned long lastReportMs = 0;
  if (millis() - lastReportMs > 100) {
    lastReportMs = millis();
    Serial.print("STATUS estop=");
    Serial.print(estopActive() ? 1 : 0);
    Serial.print(" heartbeat_expired=");
    Serial.print(heartbeatExpired() ? 1 : 0);
    Serial.print(" relay=");
    Serial.println(safe ? 1 : 0);
  }
}
