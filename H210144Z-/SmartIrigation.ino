#include <WiFi.h>
#include <WebServer.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <DHT_U.h>

#define MAX_READINGS 20  // Max number of points to plot

float tempReadings[MAX_READINGS];
float humReadings[MAX_READINGS];
float moistureReadings[MAX_READINGS];
int readingIndex = 0;

// --- FUNCTION PROTOTYPES ---
void handleRoot();
void handleLogin();
void handleLoginPost();
void handleManualPump();
void handleGraph();
void handleCrops();
void handleReport();
void sendNotification(String message);
void checkHardwareStatus();
// ----------------------------

#define SOIL_PIN 34
#define RELAY_PIN 26
#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

WebServer server(80);

const char* ssid = "Voltimor";
const char* password = "abc123456";

int soilDry = 4095;
int soilWet = 1400;
int moistureThreshold = 50;

bool pumpOn = false;
bool loggedIn = false;
bool hardwareFailure = false;  // Variable to track hardware status

unsigned long lastUpdate = 0;
unsigned long updateInterval = 10000;  // every 10 seconds

void sendNotification(String message) {
  String notificationModal = R"====(
    <div id="notification" style="position: fixed; top: -100px; left: 50%; transform: translateX(-50%); background-color: #008080; color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); font-size: 18px; z-index: 9999; transition: top 0.7s ease;">
      )====" + message + R"====(
    </div>
    <script>
      window.onload = function() {
        document.getElementById('notification').style.top = '30px';
        setTimeout(function() {
          document.getElementById('notification').style.top = '-100px';
        }, 4000);
      };
    </script>
  )====";
  server.send(200, "text/html", notificationModal);
}

void checkHardwareStatus() {
  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();
  int moisture = analogRead(SOIL_PIN);

  bool previousStatus = hardwareFailure;  // Remember old status

  if (isnan(humidity) || isnan(temp) || moisture < soilWet) {
    hardwareFailure = true;
  } else {
    hardwareFailure = false;
  }

  // Only send notifications if status changes
  if (hardwareFailure && !previousStatus) {
    sendNotification("Warning: Hardware failure detected!");
  } else if (!hardwareFailure && previousStatus) {
    sendNotification("Info: Hardware restored and working properly!");
  }
}

void generateReport() {
  String report = "<html><head><style>";
  
  // CSS Styling for the report
  report += "body { font-family: Arial, sans-serif; background-color: #f4f4f9; margin: 0; padding: 0; color: #333; }";
  report += "h1 { text-align: center; color: #4CAF50; margin-top: 20px; }";
  report += ".container { width: 80%; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }";
  report += ".report-table { width: 100%; border-collapse: collapse; margin-top: 20px; }";
  report += ".report-table th, .report-table td { padding: 12px 20px; text-align: left; border-bottom: 1px solid #ddd; }";
  report += ".report-table th { background-color: #4CAF50; color: white; }";
  report += ".report-table tr:hover { background-color: #f1f1f1; }";
  report += ".footer { text-align: center; margin-top: 20px; font-size: 0.9em; color: #888; }";
  report += "</style></head><body>";
  
  // Header of the report
  report += "<h1>SMART Irrigation System Report</h1>";
  
  // Container for the content
  report += "<div class='container'>";
  
  // Current time in seconds since system start
  report += "<p>Date: " + String(millis() / 1000) + " seconds since startup</p>";
  
  // Sensor Readings
  report += "<h2>Sensor Readings</h2>";
  report += "<table class='report-table'>";
  report += "<tr><th>Parameter</th><th>Value</th></tr>";
  report += "<tr><td>Temperature (°C)</td><td>" + String(dht.readTemperature()) + "</td></tr>";
  report += "<tr><td>Humidity (%)</td><td>" + String(dht.readHumidity()) + "</td></tr>";

  int moistureRaw = analogRead(SOIL_PIN);
  int moisture = map(moistureRaw, soilDry, soilWet, 0, 100);
  report += "<tr><td>Soil Moisture (%)</td><td>" + String(moisture) + "</td></tr>";
  report += "</table>";

  // Hardware Status
  report += "<h2>Hardware Status</h2>";
  if (hardwareFailure) {
    report += "<p style='color: red;'>Hardware failure detected! Please check sensors and connections.</p>";
  } else {
    report += "<p>All hardware working correctly.</p>";
  }
  
  // Pump Status
  report += "<h2>Pump Status</h2>";
  report += "<p>" + String(pumpOn ? "Pump is On" : "Pump is Off") + "</p>";
  
  // Footer section
  report += "<div class='footer'>Generated on: " + getTime() + "</div>";
  
  report += "</div>"; // End of container
  
  // Close HTML tags
  report += "</body></html>";

  // Send the styled HTML report to the client
  server.send(200, "text/html", report);
}

String getTime() {
  return "2025-05-09 12:00:00"; // Example timestamp
}
void downloadReport() {
  String report = "<html><head><style>";
  // Include the same CSS here
  report += "</style></head><body>";
  report += "<h1>SMART Irrigation System Report</h1>";

  // Add report content here as plain text or HTML format
  report += "<p>Generated on: " + getTime() + "</p>";
  
  // Send as an HTML file for download
  server.sendHeader("Content-Disposition", "attachment; filename=irrigation_report.html");
  server.send(200, "text/html", report);
}

void loop() {
  server.handleClient();  // Handle client requests
  
  if (millis() - lastUpdate > updateInterval) {
    lastUpdate = millis();

    float humidity = dht.readHumidity();
    float temp = dht.readTemperature();
    int moistureRaw = analogRead(SOIL_PIN);
    int moisture = map(moistureRaw, soilDry, soilWet, 0, 100);
    moisture = constrain(moisture, 0, 100);

    if (!isnan(temp) && !isnan(humidity)) {
      tempReadings[readingIndex] = temp;
      humReadings[readingIndex] = humidity;
      moistureReadings[readingIndex] = moisture;

      readingIndex = (readingIndex + 1) % MAX_READINGS; // Circular buffer
    }
  }
}



void handleLogin() {
  String html = R"====(
  <!DOCTYPE html>
  <html>
  <head>
    <title>Login</title>
    <style>
      body { font-family: Arial, sans-serif; background-color: #f4f4f4; text-align: center; padding: 50px; }
      input[type="text"], input[type="password"] {
        padding: 10px; margin: 10px; width: 200px;
        border: 1px solid #ccc; border-radius: 5px;
      }
      button {
        padding: 10px 20px; background-color: #008080;
        color: white; border: none; border-radius: 5px; cursor: pointer;
      }
      h2 { color: #008080; }
    </style>
  </head>
  <body>
    <h2>Login to Smart Irrigation Dashboard</h2>
    <form action="/login" method="POST">
      <input type="text" name="username" placeholder="Username" required><br>
      <input type="password" name="password" placeholder="Password" required><br>
      <button type="submit">Login</button>
    </form>
  </body>
  </html>
  )====";
  server.send(200, "text/html", html);
}

void handleLoginPost() {
  String username = server.arg("username");
  String password = server.arg("password");

  if (username == "admin" && password == "1234") {
    loggedIn = true;
    server.sendHeader("Location", "/");
    server.send(303);
  } else {
    String html = R"====(
    <!DOCTYPE html>
    <html>
    <head><title>Login Failed</title></head>
    <body>
      <h2>Login Failed</h2>
      <p style='color:red;'>Incorrect username or password.</p>
      <a href='/login'><button>Try Again</button></a>
    </body>
    </html>
    )====";
    server.send(200, "text/html", html);
  }
}

void handleManualPump() {
  if (!loggedIn) {
    server.sendHeader("Location", "/login");
    server.send(303);
    return;
  }

  if (server.hasArg("action")) {
    String action = server.arg("action");
    if (action == "on") {
      digitalWrite(RELAY_PIN, LOW);
      pumpOn = true;
      sendNotification("Pump Manually Turned ON");
    } else if (action == "off") {
      digitalWrite(RELAY_PIN, HIGH);
      pumpOn = false;
      sendNotification("Pump Manually Turned OFF");
    }
  }

  server.sendHeader("Location", "/");
  server.send(303);
}

void handleRoot() {
  if (!loggedIn) {
    server.sendHeader("Location", "/login");
    server.send(303);
    return;
  }

  checkHardwareStatus();  // Check hardware status on the main page load

  float humidity = dht.readHumidity();
  float temp = dht.readTemperature();

  if (isnan(humidity) || isnan(temp)) {
    humidity = random(40, 80);
    temp = random(20, 35);
  }

  int moisture = analogRead(SOIL_PIN);
  int moisturePercent = map(moisture, soilDry, soilWet, 0, 100);
  moisturePercent = constrain(moisturePercent, 0, 100);

  String pumpStatus = pumpOn ? "ON" : "OFF";
  String popup = "";

  if (server.hasArg("threshold")) {
    moistureThreshold = server.arg("threshold").toInt();
  }

  if (moisturePercent < moistureThreshold && !pumpOn) {
    digitalWrite(RELAY_PIN, LOW);
    pumpOn = true;
    popup = "<script>alert('Irrigation Started');</script>";
    sendNotification("Irrigation has started!");
  } else if (moisturePercent >= moistureThreshold && pumpOn) {
    digitalWrite(RELAY_PIN, HIGH);
    pumpOn = false;
    popup = "<script>alert('Irrigation Stopped');</script>";
    sendNotification("Irrigation has stopped!");
  }

  String html = popup + R"====(
  <!DOCTYPE html>
  <html>
  <head>
    <title>Smart Irrigation Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
      body { font-family: Arial; background: #f4f4f4; margin: 0; padding: 0; }
      header { background: #004d4d; padding: 20px; text-align: center; color: white; }
      .container { display: flex; flex-wrap: wrap; justify-content: center; margin: 20px; }
      .card {
        background: white; border-radius: 10px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin: 20px; padding: 20px;
        text-align: center; width: 300px;
      }
      canvas { width: 200px; height: 200px; }
      .btns { text-align: center; margin: 20px; }
      button {
        padding: 10px 20px; margin: 10px;
        font-size: 16px; background: #008080;
        border: none; color: white; border-radius: 5px; cursor: pointer;
      }
      input[type=range] { width: 100%; }
    </style>
  </head>
  <body>
    <header><h2>Smart Irrigation Dashboard</h2></header>

    <div class="container">
      <div class="card">
        <h3>Temperature</h3>
        <canvas id="tempChart"></canvas>
      </div>
      <div class="card">
        <h3>Humidity</h3>
        <canvas id="humChart"></canvas>
      </div>
      <div class="card">
        <h3>Soil Moisture</h3>
        <canvas id="soilChart"></canvas>
      </div>
      <div class="card">
        <h3>Pump Status</h3>
        <div id="pumpStatus" style="font-size:24px; padding: 20px; border-radius: 10px; background-color: #f0f0f0;">
          <div style="color: )====" + (pumpOn ? "green" : "red") + R"====(; font-weight: bold; font-size: 28px;">
            )====" + pumpStatus + R"====(
          </div>
          <div style="font-size: 16px; color: #777;">Status of the irrigation pump</div>
        </div>
      </div>
      <div class="card">
        <h3>Threshold Control</h3>
        <form method="GET">
          <input type="range" min="0" max="100" name="threshold" value=")====" + String(moistureThreshold) + R"====(" oninput="this.nextElementSibling.value = this.value">
          <output>)====" + String(moistureThreshold) + R"====(</output>%<br><br>
          <input type="submit" value="Set">
        </form>
      </div>
      <div class="card">
        <h3>Manual Control</h3>
        <form action="/manual" method="GET">
          <button name="action" value="on">Turn Pump ON</button><br><br>
          <button name="action" value="off">Turn Pump OFF</button>
        </form>
      </div>
    </div>

    <div class="btns">
      <form action="/graph" style="display:inline;"><button>Show Graph</button></form>
      <form action="/crops" style="display:inline;"><button>Crop Info</button></form>

      <!-- Add this new form for the Download System Report button -->
      <form action="/report" style="display:inline;">
        <button>Download System Report</button>
      </form>
    </div>

    <script>
      const temp = )====" + String(temp) + R"====(;
      const humidity = )====" + String(humidity) + R"====(;
      const moisture = )====" + String(moisturePercent) + R"====(;

      function createGauge(id, value, max, color) {
        new Chart(document.getElementById(id), {
          type: 'doughnut',
          data: {
            datasets: [{
              data: [value, max - value],
              backgroundColor: [color, '#e0e0e0'],
              borderWidth: 0
            }]
          },
          options: {
            circumference: 180,
            rotation: 270,
            cutout: '70%',
            plugins: {
              tooltip: {enabled: false},
              legend: {display: false},
              title: {
                display: true,
                text: value + (id === "soilChart" ? "%" : id === "humChart" ? "%" : "°C"),
                position: 'bottom'
              }
            }
          }
        });
      }

      createGauge('tempChart', temp, 50, 'orange');
      createGauge('humChart', humidity, 100, 'blue');
      createGauge('soilChart', moisture, 100, 'green');
    </script>
  </body>
  </html>
  )====";

  server.send(200, "text/html", html);
}




void handleGraph() {
  String tempData = "";
  String humData = "";
  String moistureData = "";
  String labels = "";

  for (int i = 0; i < MAX_READINGS; i++) {
    int index = (readingIndex + i) % MAX_READINGS; // order correctly
    tempData += String(tempReadings[index]) + ",";
    humData += String(humReadings[index]) + ",";
    moistureData += String(moistureReadings[index]) + ",";
    labels += String(i * 10) + ","; // Assuming 10 sec intervals
  }

  String html = R"====(
  <!DOCTYPE html>
  <html>
  <head><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><meta http-equiv="refresh" content="10"></head>
  <body>
    <canvas id="myChart" width="400" height="200"></canvas>
    <script>
      var ctx = document.getElementById('myChart').getContext('2d');
      var chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: [)====" + labels + R"====(],
          datasets: [{
            label: 'Temperature (°C)',
            data: [)====" + tempData + R"====(],
            borderColor: 'red',
            fill: false
          },{
            label: 'Humidity (%)',
            data: [)====" + humData + R"====(],
            borderColor: 'blue',
            fill: false
          },{
            label: 'Soil Moisture (%)',
            data: [)====" + moistureData + R"====(],
            borderColor: 'green',
            fill: false
          }]
        },
        options: {
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    </script>
  </body>
  </html>
  )====";

  server.send(200, "text/html", html);
}


void handleCrops() {
if (!loggedIn) {
server.sendHeader("Location", "/login");
server.send(303);
return;
}

String html = R"====(

  <!DOCTYPE html>

  <html>
  <head>
    <title>Crop Information</title>
    <style>
      body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: linear-gradient(to right, #d4fc79, #96e6a1);
        margin: 0;
        padding: 0;
      }
      header {
        background-color: #008080;
        color: white;
        padding: 20px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
      }
      .search-container {
        text-align: center;
        margin: 20px;
      }
      .search-container input {
        width: 50%;
        padding: 10px;
        font-size: 16px;
        border-radius: 8px;
        border: 1px solid #ccc;
      }
      .container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        padding: 20px;
      }
      .card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        margin: 15px;
        padding: 20px;
        width: 300px;
        transition: transform 0.2s;
      }
      .card:hover {
        transform: translateY(-10px);
      }
      h3 {
        color: #004d4d;
      }
      p {
        font-size: 16px;
        color: #555;
      }
      .tip {
        margin-top: 10px;
        font-style: italic;
        color: #006400;
      }
      .btn-back {
        display: block;
        margin: 30px auto;
        padding: 10px 20px;
        background-color: #004d4d;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 18px;
        text-decoration: none;
        text-align: center;
        cursor: pointer;
      }
    </style>
    <script>
      function searchCrops() {
        var input = document.getElementById('cropSearch').value.toLowerCase();
        var cards = document.getElementsByClassName('card');
        for (var i = 0; i < cards.length; i++) {
          var title = cards[i].getElementsByTagName('h3')[0].innerText.toLowerCase();
          if (title.includes(input)) {
            cards[i].style.display = '';
          } else {
            cards[i].style.display = 'none';
          }
        }
      }
    </script>
  </head>
  <body>
    <header>Recommended Crops</header>


<div class="search-container">
  <input type="text" id="cropSearch" onkeyup="searchCrops()" placeholder="Search for a crop...">
</div>

<div class="container">
  <div class="card">
    <h3>Rice</h3>
    <p><strong>Moisture:</strong> 60-80%</p>
    <p><strong>Temp:</strong> 20-35°C</p>
    <p><strong>Humidity:</strong> High</p>
    <p class="tip"> Irrigate fields regularly to keep water standing.</p>
  </div>
  <div class="card">
    <h3>Wheat</h3>
    <p><strong>Moisture:</strong> 40-60%</p>
    <p><strong>Temp:</strong> 15-25°C</p>
    <p><strong>Humidity:</strong> Moderate</p>
    <p class="tip">Irrigate at tillering and flowering stages.</p>
  </div>
  <div class="card">
    <h3>Maize (Corn)</h3>
    <p><strong>Moisture:</strong> 50-70%</p>
    <p><strong>Temp:</strong> 18-27°C</p>
    <p><strong>Humidity:</strong> Moderate</p>
    <p class="tip"> Irrigate during tasseling and silking stages.</p>
  </div>
  <div class="card">
    <h3>Potato</h3>
    <p><strong>Moisture:</strong> 60-80%</p>
    <p><strong>Temp:</strong> 15-20°C</p>
    <p><strong>Humidity:</strong> High</p>
    <p class="tip"> Maintain moist soil but avoid waterlogging.</p>
  </div>
  <div class="card">
    <h3>Tomato</h3>
    <p><strong>Moisture:</strong> 60-80%</p>
    <p><strong>Temp:</strong> 20-25°C</p>
    <p><strong>Humidity:</strong> Moderate-High</p>
    <p class="tip"> Water deeply but less frequently to promote deep roots.</p>
  </div>
</div>

<a href="/" class="btn-back">Back to Dashboard</a>


  </body>
  </html>
  )====";

server.send(200, "text/html", html);
}
void setup() {
  Serial.begin(115200);
  dht.begin();

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.print("Connected to WiFi. IP: ");
  Serial.println(WiFi.localIP());

  server.on("/", HTTP_GET, handleRoot);
  server.on("/login", HTTP_GET, handleLogin);
  server.on("/login", HTTP_POST, handleLoginPost);
  server.on("/manual", HTTP_GET, handleManualPump);
  server.on("/graph", HTTP_GET, handleGraph);
  server.on("/crops", HTTP_GET, handleCrops);
  server.on("/report", HTTP_GET, generateReport); // <-- this is the new report page
  server.on("/download", HTTP_GET, downloadReport);

  server.begin()
}    
Add Smart Irrigation Arduino sketch
