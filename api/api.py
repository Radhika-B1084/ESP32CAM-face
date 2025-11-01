from fastapi import FastAPI, Request
from fastapi.responses import Response
import cv2
import numpy as np
from ultralytics import YOLO
import uvicorn

app = FastAPI()

model = YOLO('yolov8n.pt')

current_frame = None
detection_data = {"total_faces": 0, "frame_number": 0, "avg_confidence": 0, "detections": []}
frame_count = 0

@app.post("/upload/camera1")
async def receive_frame(request: Request):
    global current_frame, detection_data, frame_count
    
    try:
        # Read raw bytes from request body
        contents = await request.body()
        
        # Decode JPEG
        frame = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid image"}
        
        frame_count += 1
        
        # YOLO detection
        results = model(frame, conf=0.5)
        
        detections = []
        total_conf = 0
        face_count = 0
        
        for result in results:
            for box in result.boxes:
                face_count += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                total_conf += conf
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f'{conf:.2f}', (x1, y1-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                detections.append({"face_id": face_count, "confidence": round(conf, 2)})
        
        cv2.putText(frame, f'Faces: {face_count}', (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        current_frame = frame.copy()
        detection_data = {
            "total_faces": face_count,
            "frame_number": frame_count,
            "avg_confidence": round(total_conf / face_count, 2) if face_count > 0 else 0,
            "detections": detections
        }
        
        print(f"[API] Frame {frame_count} - {face_count} faces")
        return {"status": "ok", "faces": face_count}
        
    except Exception as e:
        print(f"[API] Error: {e}")
        return {"error": str(e)}

@app.get("/stats/camera1")
async def get_stats():
    return detection_data

@app.get("/frame/camera1")
async def get_frame():
    if current_frame is not None:
        _, buffer = cv2.imencode('.jpg', current_frame)
        return Response(content=buffer.tobytes(), media_type="image/jpeg")
    return {"error": "No frame"}

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
