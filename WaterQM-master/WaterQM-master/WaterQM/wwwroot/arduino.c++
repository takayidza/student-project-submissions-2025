#include <SoftwareSerial.h>

// Define pins
const int phPin = A0;          // pH sensor analog pin
const int waterLevelPin = A1;  // Water level sensor analog pin
const int turbidityPin = A2;   // Turbidity sensor analog pin

// Calibration values for pH sensor
const float phOffset = 0.0;    // Adjust this based on your calibration
const float phSlope = 1.0;     // Adjust this based on your calibration

// Calibration values for water level sensor
const float waterLevelOffset = 0.0; // Adjust this based on your calibration
const float waterLevelSlope = 1.0;  // Adjust this based on your calibration

// Calibration values for turbidity sensor
const float turbidityOffset = 0.0;  // Adjust this based on your calibration
const float turbiditySlope = 1.0;   // Adjust this based on your calibration

// Error thresholds
const float phMinValue = 0.0;
const float phMaxValue = 14.0;
const float waterLevelMinValue = 0.0;
const float waterLevelMaxValue = 100.0;
const float turbidityMinValue = 0.0;   // NTU units - adjust based on your sensor
const float turbidityMaxValue = 3000.0; // NTU units - adjust based on your sensor

void setup() {
  // Initialize serial communication
  Serial.begin(9600);

  // Set analog pins as input
  pinMode(phPin, INPUT);
  pinMode(waterLevelPin, INPUT);
  pinMode(turbidityPin, INPUT);

  // Wait for serial port to connect
  while (!Serial) {
    delay(10);
  }

  //Serial.println("Water Quality Monitoring System");
  //Serial.println("pH, Water Level (%), Turbidity (NTU)");
}

float readPhSensor() {
  // Read pH sensor value
  int rawValue = analogRead(phPin);

  // Convert to voltage (assuming 5V reference)
  float voltage = rawValue * (5.0 / 1023.0);

  // Convert to pH value
  float phValue = (voltage * phSlope) + phOffset;

  // Check if reading is within valid range
  if (phValue < phMinValue || phValue > phMaxValue) {
    return 0.0; // Return 0 to indicate error
  }

  return phValue;
}

float readWaterLevelSensor() {
  // Read water level sensor value
  int rawValue = analogRead(waterLevelPin);

  // Convert to voltage (assuming 5V reference)
  float voltage = rawValue * (5.0 / 1023.0);

  // Convert to water level in cm
  float waterLevel = (voltage * waterLevelSlope) + waterLevelOffset;

  // Check if reading is within valid range
  if (waterLevel < waterLevelMinValue || waterLevel > waterLevelMaxValue) {
    //  return 0.0; // Return 0 to indicate error.  THIS IS COMMENTED OUT
  }

  return waterLevel;
}

float readTurbiditySensor() {
  // Read turbidity sensor value
  int rawValue = analogRead(turbidityPin);
float turbidity = map(rawValue, 0, 750, 100, 0);
  // Convert to voltage (assuming 5V reference)
  //float voltage = rawValue * (5.0 / 1023.0);

  // Convert voltage to turbidity (NTU)
  // This formula needs to be calibrated for your specific sensor
  // Example formula: Higher voltage = clearer water (lower NTU)
  //float turbidity = -1120.4 * voltage * voltage + 5742.3 * voltage - 4352.9;

  // Ensure turbidity doesn't go below 0
  if (turbidity < 0) {
    turbidity = 0;
  }

  // Check if reading is within valid range
  if (turbidity < turbidityMinValue || turbidity > turbidityMaxValue) {
    return 0.0; // Return 0 to indicate error
  }

  return turbidity;
}

void loop() {
  // Read all sensors
  float phValue = readPhSensor();
  float waterLevelValue = readWaterLevelSensor();
  float turbidityValue = readTurbiditySensor();

  // If any sensor fails, set its value to 0.  <-- PROBLEM AREA
  if (phValue == 0.0) {
    phValue = 0.0;
  }

  if (waterLevelValue == 0.0) {
    waterLevelValue = 0.0;
  }

  if (turbidityValue == 0.0) {
    turbidityValue = 0.0;
  }

  // // Debug information (optional)
  // Serial.print("Raw turbidity: ");
  // Serial.print(analogRead(turbidityPin));
  // Serial.print(", Voltage: ");
  // Serial.print(analogRead(turbidityPin) * (5.0 / 1023.0));
  // Serial.print("V | ");

  // Send data in format: "phValue,waterLevelValue,turbidityValue"
  Serial.print(phValue, 2);
  Serial.print(",");
  Serial.print(waterLevelValue, 2);
  Serial.print(",");
  Serial.println(turbidityValue, 2);

  // Wait before next reading
  delay(1000); // Adjust delay as needed
}
