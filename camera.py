from flask import Flask, Response, jsonify, request
import cv2
import numpy as np
import threading
import time
import base64

app = Flask(__name__)

# Initialize camera
cap = cv2.VideoCapture(1)
reference_face = None
lock = threading.Lock()

# Load face cascade
detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def extract_face_features(frame, face_rect):
    x, y, w, h = face_rect
    face_region = frame[y:y+h, x:x+w]
    face_region = cv2.resize(face_region, (100, 100))
    gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
    gray_face = cv2.equalizeHist(gray_face)
    return gray_face.flatten().astype(np.float32) / 255.0, face_region

def compare_faces(features1, features2):
    return np.corrcoef(features1, features2)[0, 1]

def generate_frames():
    global reference_face
    while True:
        with lock:
            ret, frame = cap.read()
        
        if not ret:
            continue
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_features, _ = extract_face_features(frame, (x, y, w, h))
            is_same_person = True
            similarity_score = 1.0
            
            if reference_face is not None:
                similarity_score = compare_faces(reference_face, face_features)
                is_same_person = similarity_score >= 0.5
            
            color = (0, 255, 0) if is_same_person else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            status = f"Same Person" if is_same_person else "Different Person"
            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/register_face', methods=['POST'])
def register_face():
    global reference_face
    with lock:
        ret, frame = cap.read()
    
    if not ret:
        return jsonify({'error': 'Failed to capture image'}), 500
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    if len(faces) == 0:
        return jsonify({'error': 'No face detected'}), 400
    
    x, y, w, h = faces[0]
    reference_face, face_image = extract_face_features(frame, (x, y, w, h))
    
    _, buffer = cv2.imencode('.jpg', face_image)
    face_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({'message': 'Face registered successfully', 'face_image': face_base64})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)