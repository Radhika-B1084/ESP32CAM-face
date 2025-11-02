# **ESP-32 Cam Face Detection | IOT Workshop**
### **Software Requirements**
We are working with the **ESP32 CAM (AI-Thinker Module)**.

**Install Arduino IDE:**
- Download from https://www.arduino.cc/en/software
- Install and open Arduino IDE

**Install ESP32 Board Support:**
- Go to File > Preferences
- Add to "Additional Boards Manager URLs":
  ``` bash
  https://dl.espressif.com/dl/package_esp32_index.json
  ```
- Tools > Board > Boards Manager
- Search "esp32" and install "esp32 by Espressif Systems"

**Install Python (3.12):**
- Download from https://www.python.org/downloads/
- Important: Check "Add Python to PATH" during installation
- Verify installation in the terminal:
  ``` bash
  python --version
  ```
---
### **0. Creating a Web Server**
We will be using the sample code from Arduino IDE to perform this. We are primarily doing this to check that our board is functional.
- Open Arduino IDE
- Files > Examples > ESP32 > Camera > CameraWebServer
- Update the Wi-Fi Credentials (Make sure to connect to a 2.4 GHz network)
- Select Board: Tools > Board > **AI-Thinker ESP32-CAM**
- Select the correct COM port (Incase you are not able to find the COM port open **Device Manager** and under **Ports (COM and LPT)** observe what COM pops up when you plug in the ESP)
- While pressing the BOOT button on the board, press the RESET button and release the BOOT button
- Click on Upload

Once the code is uploaded
- Press the RESET button
- Open the Serial Monitor (Tools > Serial Monitor (115200 baud))
- Look for: ```IP address: 192.168.x.x```
- Make sure your device is connected to the same WiFi as the ESP and copy this IP address, paste it on your browser 
- Click "Start Streaming" to see live video


Yay! We have successfully checked if our ESP32 CAM is working

---
### **2. Serial Communication with YOLO**
We will now capture frames from ESP32-CAM via serial commuincation to the laptop and detect faces using the popular YOLO algorithm
#### **1. Upload the following code on ESP32**
``` C++
#include "esp_camera.h"
#include <Arduino.h>

// Select camera model
#define CAMERA_MODEL_AI_THINKER

// Camera pin definitions for AI-THINKER
#ifdef CAMERA_MODEL_AI_THINKER
  #define PWDN_GPIO_NUM     32
  #define RESET_GPIO_NUM    -1
  #define XCLK_GPIO_NUM      0
  #define SIOD_GPIO_NUM     26
  #define SIOC_GPIO_NUM     27
  #define Y9_GPIO_NUM       35
  #define Y8_GPIO_NUM       34
  #define Y7_GPIO_NUM       39
  #define Y6_GPIO_NUM       36
  #define Y5_GPIO_NUM       21
  #define Y4_GPIO_NUM       19
  #define Y3_GPIO_NUM       18
  #define Y2_GPIO_NUM        5
  #define VSYNC_GPIO_NUM    25
  #define HREF_GPIO_NUM     23
  #define PCLK_GPIO_NUM     22
#endif

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  
  delay(1000);
  Serial.println("\n\nInitializing camera...");
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QQVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Initialize camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return;
  }
  
  Serial.println("Camera initialized successfully!");
  Serial.println("Streaming frames over serial...");
}

void loop() {
  camera_fb_t *fb = esp_camera_fb_get();
  
  if (!fb) {
    Serial.println("0");
    delay(100);
    return;
  }
  
  // Send frame size
  Serial.println(fb->len);
  delay(10);
  
  // Send JPEG bytes
  Serial.write(fb->buf, fb->len);
  delay(10);
  
  // Send end marker
  Serial.println("ENDIMG");
  
  esp_camera_fb_return(fb);
  
  delay(500);
}
```
#### **1. Install Python Libraries**
``` bash
py -3.12 -m pip install pyserial numpy opencv-python ultralytics
```
#### **2. Create Python Script**
```python
import serial
import numpy as np
import cv2
from ultralytics import YOLO
import time

# Initialize serial connection
ser = serial.Serial('COM5', 115200, timeout=5)
time.sleep(2)  # Wait for serial connection to establish

# Load YOLO detection model (will auto-download)
print("Loading YOLO detection model...")
model = YOLO('yolov8n.pt')  # nano model - auto downloads

# Confidence threshold (0-1)
conf_threshold = 0.5
frame_count = 0

print("Starting face detection. Press ESC to exit.")

while True:
    try:
        # Read length line from serial
        length_line = ser.readline().strip()
        if not length_line:
            continue
            
        if not length_line.isdigit():
            continue
            
        length = int(length_line)
        
        # Read image bytes
        img_bytes = ser.read(length)
        
        # Read end marker
        end_marker = ser.readline().strip()
        if end_marker != b'ENDIMG':
            continue

        # Decode image
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            continue

        # Run YOLO face detection
        results = model(img, conf=conf_threshold)
        
        face_count = 0

        # Draw bounding boxes and labels
        for result in results:
            boxes = result.boxes
            for box in boxes:
                face_count += 1
                # Get coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                
                # Draw rectangle (green for detected faces)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Put confidence label
                label = f'Face {conf:.2f}'
                cv2.putText(img, label, (x1, y1 - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Display frame count and face count
        cv2.putText(img, f'Faces: {face_count}', (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(img, f'Frame: {frame_count}', (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        frame_count += 1

        # Display frame
        cv2.imshow("ESP32-CAM Face Detection", img)
        
        # Press ESC to exit
        key = cv2.waitKey(1)
        if key == 27:  # ESC key
            print("Exiting...")
            break
        elif key == ord('s'):  # 's' to save current frame
            filename = f"face_detection_{frame_count}.jpg"
            cv2.imwrite(filename, img)
            print(f"Saved {filename}")

    except Exception as e:
        print(f"Error: {e}")
        continue

cv2.destroyAllWindows()
ser.close()
print("Serial connection closed.")
```
Before running the file make sure no other software is using the COM that ESP is connected to (for instance Arduino etc). Run the file :)

---
### **3. ESP32 Dashboard with an API**
Serial communication is kinda boring, hence we will now see how ESP32 hosts a dashboard, sends frames to an API server and displays results in real-time. So the architecture looks like this:
``` bash
ESP32-CAM
  ↓ (sends frames every 500ms)
Cloud API (your server)
  ↓ 
ESP32 Dashboard
  ↓ (fetches results)
Browser
```
So the API server is actually somehitng that we are hosting from our own servers.
#### Upload this code on the ESP32
```C++
#include "esp_camera.h"
#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// WiFi credentials
const char* ssid = "";
const char* password = "";

// API Server (your computer)
const char* apiUrl = "http://IP/upload/camera1";
const char* statsUrl = "http://IP/stats/camera1";
const char* frameUrl = "http://IP/frame/camera1";

// Camera pins (AI-THINKER)
#define CAMERA_MODEL_AI_THINKER

#ifdef CAMERA_MODEL_AI_THINKER
  #define PWDN_GPIO_NUM     32
  #define RESET_GPIO_NUM    -1
  #define XCLK_GPIO_NUM      0
  #define SIOD_GPIO_NUM     26
  #define SIOC_GPIO_NUM     27
  #define Y9_GPIO_NUM       35
  #define Y8_GPIO_NUM       34
  #define Y7_GPIO_NUM       39
  #define Y6_GPIO_NUM       36
  #define Y5_GPIO_NUM       21
  #define Y4_GPIO_NUM       19
  #define Y3_GPIO_NUM       18
  #define Y2_GPIO_NUM        5
  #define VSYNC_GPIO_NUM    25
  #define HREF_GPIO_NUM     23
  #define PCLK_GPIO_NUM     22
#endif

WebServer server(80);
String latestStats = "{\"total_faces\":0,\"frame_number\":0,\"avg_confidence\":0,\"detections\":[]}";

// Forward declarations
void handleDashboard();
void handleApiStats();

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n================================");
  Serial.println("ESP32-CAM → API → Dashboard");
  Serial.println("================================\n");
  
  // Initialize camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  if(psramFound()){
    config.frame_size = FRAMESIZE_VGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[ERROR] Camera init failed: 0x%x\n", err);
    return;
  }
  Serial.println("[CAM] ✓ Camera initialized!");
  
  // Connect to WiFi
  Serial.print("\n[WiFi] Connecting to: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[ERROR] WiFi failed");
    return;
  }
  
  // Setup web server routes
  server.on("/", handleDashboard);
  server.on("/api/stats", handleApiStats);
  
  server.begin();
  
  Serial.println("\n================================");
  Serial.print("Dashboard: http://");
  Serial.println(WiFi.localIP());
  Serial.print(" API: ");
  Serial.println(apiUrl);
  Serial.println("================================\n");
}

void handleDashboard() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
  <title>ESP32-CAM Face Detection | IoT Workshop</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    body {
      font-family: 'Inter', sans-serif;
      background: radial-gradient(circle at top, #0d102b, #07071a 70%);
      color: #fff;
      min-height: 100vh;
      padding: 20px;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      background: rgba(255,255,255,0.05);
      border-radius: 20px;
      box-shadow: 0 0 25px rgba(0,0,0,0.5);
      overflow: hidden;
      backdrop-filter: blur(6px);
      border: 1px solid rgba(255,255,255,0.1);
    }

    /* Header */
    .header {
      background: linear-gradient(90deg, #6a8cff, #ffcc70);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-align: center;
      padding: 35px 15px 20px;
    }

    .header h1 {
      font-size: 2rem;
      font-weight: 800;
    }

    .header p {
      color: #bbb;
      font-weight: 500;
      letter-spacing: 0.5px;
      margin-top: 5px;
    }

    /* Content Layout */
    .content {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 25px;
      padding: 30px;
    }

    .feed, .stats {
      background: rgba(255,255,255,0.05);
      border-radius: 14px;
      padding: 20px;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 0 15px rgba(0,0,0,0.3);
      transition: 0.3s ease;
    }

    .feed:hover, .stats:hover {
      transform: translateY(-3px);
      box-shadow: 0 0 20px rgba(255,255,255,0.1);
    }

    h2 {
      font-size: 1.1rem;
      font-weight: 700;
      margin-bottom: 15px;
      background: linear-gradient(90deg, #6a8cff, #ffcc70);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    #videoFeed {
      width: 100%;
      border-radius: 10px;
      border: 2px solid rgba(255,255,255,0.2);
      display: block;
      background: #111;
      height: auto;
      box-shadow: 0 0 10px rgba(0,0,0,0.3);
    }

    /* Stats Panel */
    .stat-box {
      background: rgba(255,255,255,0.08);
      padding: 15px;
      border-radius: 10px;
      margin-bottom: 15px;
      border-left: 4px solid #6a8cff;
    }

    .stat-box h3 {
      font-size: 0.9em;
      color: #b0b0c0;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .stat-box .value {
      font-size: 2em;
      font-weight: 700;
      background: linear-gradient(90deg, #6a8cff, #ffcc70);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .status {
      padding: 10px;
      border-radius: 6px;
      text-align: center;
      font-weight: 600;
      margin-bottom: 15px;
      background: rgba(76,175,80,0.1);
      color: #81c784;
      border: 1px solid rgba(129,199,132,0.3);
    }

    .status.error {
      background: rgba(244,67,54,0.1);
      color: #ef9a9a;
      border-color: rgba(239,83,80,0.3);
    }

    /* Detections */
    .detection-list {
      background: rgba(255,255,255,0.05);
      border-radius: 10px;
      padding: 15px;
      max-height: 300px;
      overflow-y: auto;
      border: 1px solid rgba(255,255,255,0.1);
    }

    .detection-item {
      padding: 8px;
      background: rgba(255,255,255,0.08);
      border-radius: 6px;
      margin-bottom: 6px;
      border-left: 3px solid #81c784;
      font-size: 0.9em;
      color: #e0e0e0;
    }

    footer {
      text-align: center;
      padding: 15px;
      font-size: 0.85em;
      color: #888;
      border-top: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.02);
    }

    @media (max-width: 768px) {
      .content { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>ESP32-CAM Face Detection</h1>
      <p>IoT Workshop • Electronics & Robotics Club</p>
    </div>

    <div class="content">
      <div class="feed">
        <h2>Live Feed</h2>
        <img id="videoFeed" alt="Live Stream">
      </div>

      <div class="stats">
        <div class="status" id="status">Loading...</div>

        <h2>Statistics</h2>
        <div class="stat-box">
          <h3>Total Faces</h3>
          <div class="value" id="faceCount">0</div>
        </div>
        <div class="stat-box">
          <h3>Frame Number</h3>
          <div class="value" id="frameNumber">0</div>
        </div>
        <div class="stat-box">
          <h3>Avg Confidence</h3>
          <div class="value" id="avgConfidence">0%</div>
        </div>

        <h3 style="margin-top:20px; margin-bottom:10px;">Detections</h3>
        <div class="detection-list" id="detectionList">
          <p style="color:#888; text-align:center;">No faces detected</p>
        </div>
      </div>
    </div>

    <footer>
      © 2025 Electronics & Robotics Club, IIT Bombay | IoT Workshop Dashboard
    </footer>
  </div>

  <script>
    const API_URL = "";
    const CAMERA_ID = "camera1";
    
    // Update feed
    setInterval(() => {
      document.getElementById('videoFeed').src = API_URL + '/frame/' + CAMERA_ID + '?t=' + Date.now();
    }, 100);

    // Update stats
    async function updateStats() {
      try {
        const response = await fetch(API_URL + '/stats/' + CAMERA_ID);
        const data = await response.json();
        
        document.getElementById('faceCount').textContent = data.total_faces;
        document.getElementById('frameNumber').textContent = data.frame_number;
        document.getElementById('avgConfidence').textContent = (data.avg_confidence * 100).toFixed(1) + '%';
        
        const status = document.getElementById('status');
        status.textContent = '✓ Connected - ' + new Date().toLocaleTimeString();
        status.classList.remove('error');
        
        const detectionList = document.getElementById('detectionList');
        if (data.detections && data.detections.length > 0) {
          detectionList.innerHTML = data.detections.map(d => 
            `<div class="detection-item">Face #${d.face_id}: ${(d.confidence * 100).toFixed(1)}% confidence</div>`
          ).join('');
        } else {
          detectionList.innerHTML = '<p style="color:#888; text-align:center;">No faces detected</p>';
        }
      } catch (error) {
        const status = document.getElementById('status');
        status.classList.add('error');
        status.textContent = '✗ Error loading data';
      }
    }
    
    setInterval(updateStats, 500);
    updateStats();
  </script>
</body>
</html>
  )";
  
  server.send(200, "text/html", html);
}

void handleApiStats() {
  server.send(200, "application/json", latestStats);
}

void loop() {
  server.handleClient();
  
  // Send frame to API and get stats back every 500ms
  static unsigned long lastSend = 0;
  if (millis() - lastSend > 500) {
    lastSend = millis();
    
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      // Send frame to API
      HTTPClient http;
      http.begin(apiUrl);
      http.addHeader("Content-Type", "image/jpeg");
      int response = http.POST(fb->buf, fb->len);
      http.end();
      esp_camera_fb_return(fb);
      
      // Get stats from API
      HTTPClient httpStats;
      httpStats.begin(statsUrl);
      int statsResponse = httpStats.GET();
      if (statsResponse == 200) {
        latestStats = httpStats.getString();
      }
      httpStats.end();
    }
  }
}
```
#### **Update these lines with YOUR details:**
``` C++
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_PASSWORD";
const char* apiUrl = "http://API_IP/upload/ROLL_NUMBER";
const char* statsUrl = "http://API_IP/stats/ROLL_NUMBER";
const char* frameUrl = "http://API_IP/frame/ROLL_NUMBER";
const API_URL = "API_IP";
```

#### **You can finally access the dashboard**
- Find the ESP32 CAM IP from the Serial Monitor on Arduino IDE
- Open Browser ```http://ESP32_IP```
- You should see Live stream, Face Counts, Real time Detections and Confidence scores


#### **With that we come to the end of this year's IOT workshop's hands-on activity. Hope you all had fun learning!**

