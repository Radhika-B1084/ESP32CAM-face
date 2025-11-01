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
