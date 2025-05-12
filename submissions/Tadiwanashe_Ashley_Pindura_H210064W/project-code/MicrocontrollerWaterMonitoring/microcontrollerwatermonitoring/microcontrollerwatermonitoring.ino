#include <WiFi.h>
#include <HTTPClient.h>
#include <algorithm> // For min() and max()
#include "DHT.h"

// WiFi credentials
const char* ssid = "HUAWEI-REGh";
const char* password = "6JApbqdz";
const unsigned long WIFI_TIMEOUT_MS = 15000; // 15 seconds

// Django API URL
const char* serverUrl = "http://192.168.0.159:8000/api/send-data/";

// Ultrasonic Sensor Pins
const int trigPin = 5;
const int echoPin = 18;

// Buzzer & LED Pins
const int buzzerPin = 23;
const int ledPin = 22;

// Tank height and sound speed
const float tankHeight = 4.0; // in cm
#define SOUND_SPEED 0.034  // cm/us

// DHT11 Setup
#define DHTPIN 21
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Reconnect interval
unsigned long previousMillis = 0;
const long interval = 5000; // 5 seconds

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);
  unsigned long startAttemptTime = millis();

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < WIFI_TIMEOUT_MS) {
    Serial.print(".");
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📶 IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n❌ Failed to connect to WiFi.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Setup pins
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  pinMode(ledPin, OUTPUT);

  // Connect to WiFi
  connectToWiFi();

  // Start DHT11
  dht.begin();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("🔌 WiFi disconnected. Attempting to reconnect...");
    connectToWiFi();
  }

  if (WiFi.status() == WL_CONNECTED) {
    float distance = measureDistance();
    float percentageFull = calculatePercentage(distance);

    Serial.print("Water Level: ");
    Serial.print(percentageFull);
    Serial.println("%");

    // Read DHT11
    float temperature = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(temperature) || isnan(humidity)) {
      Serial.println("❌ Failed to read from DHT11 sensor!");
      temperature = 0;
      humidity = 0;
    } else {
      Serial.print("🌡️ Temperature: ");
      Serial.print(temperature);
      Serial.println(" °C");

      Serial.print("💧 Humidity: ");
      Serial.print(humidity);
      Serial.println(" %");
    }

    // Flash buzzer + LED if level is bad
    if (percentageFull < 20.0 || percentageFull > 80.0) {
        // Flash buzzer + LED rapidly
        tone(buzzerPin, 1000);  // Turn on buzzer at 1000 Hz
        digitalWrite(ledPin, HIGH);  // Turn on LED
        delay(500);  // 500ms ON

        noTone(buzzerPin);  // Turn off buzzer
        digitalWrite(ledPin, LOW);  // Turn off LED
        delay(500);  // 500ms OFF

        // Send data each time it flashes
        sendDataToDjango(percentageFull, temperature, humidity);
    } else {
        // Safe state: make sure buzzer and LED are off
        noTone(buzzerPin);
        digitalWrite(ledPin, LOW);

        // Send data once every loop when not critical
        sendDataToDjango(percentageFull, temperature, humidity);
    }
  }

  delay(interval);
}

float measureDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  float distance = duration * SOUND_SPEED / 2;
  return distance;
}

float calculatePercentage(float distanceCm) {
  float percentage = ((tankHeight - distanceCm) / tankHeight) * 100.0;
  return std::max(0.0f, std::min(percentage, 100.0f));
}

void sendDataToDjango(float percentage, float temperature, float humidity) {
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  String jsonPayload = "{\"water_level\": " + String(percentage) +
                       ", \"temperature\": " + String(temperature) +
                       ", \"humidity\": " + String(humidity) + "}";

  Serial.print("📡 Sending: ");
  Serial.println(jsonPayload);

  int httpResponseCode = http.POST(jsonPayload);

  if (httpResponseCode > 0) {
    Serial.print("✅ Sent! Response: ");
    Serial.println(httpResponseCode);
    Serial.println(http.getString());
  } else {
    Serial.print("❌ Failed to send. Code: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}
