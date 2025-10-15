"""Unit tests for knee kick detection."""

import cv2
import numpy as np
import mediapipe as mp
from src.utils.utils import normalize_coordinates, init_mediapipe_pose

def test_knee_kick_detection():
    """
    Test knee raising detection for kicking.
    Tests the detection of kicking state based on knee height relative to hip.
    """
    cap = cv2.VideoCapture(0)
    pose = init_mediapipe_pose()
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    
    # Control variables
    kick_state = "ready"
    cooldown = 0
    COOLDOWN_FRAMES = 15
    KNEE_HEIGHT_THRESHOLD = 0.007  # Threshold for knee height relative to hip
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Flip frame for selfie view
            frame = cv2.flip(frame, 1)
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)
            
            if results.pose_landmarks:
                # Draw pose landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )
                
                # Get landmarks for kick detection
                hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
                knee = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
                
                # Convert to pixel coordinates
                hip_coords = normalize_coordinates(hip, frame.shape)
                knee_coords = normalize_coordinates(knee, frame.shape)
                
                # Visualize detection points
                cv2.circle(frame, hip_coords, 5, (255, 0, 0), -1)
                cv2.circle(frame, knee_coords, 5, (0, 255, 0), -1)
                cv2.line(frame, hip_coords, knee_coords, (0, 255, 255), 2)
                
                # Check for kick trigger
                if cooldown == 0:
                    knee_height = knee.y - hip.y
                    if knee_height < -KNEE_HEIGHT_THRESHOLD:
                        kick_state = "kicking"
                        cooldown = COOLDOWN_FRAMES
                    else:
                        kick_state = "ready"
                        
                # Draw threshold line
                threshold_y = int(hip_coords[1] - (frame.shape[0] * KNEE_HEIGHT_THRESHOLD))
                cv2.line(frame, (hip_coords[0] - 50, threshold_y),
                        (hip_coords[0] + 50, threshold_y), (255, 0, 0), 1)
            
            # Update cooldown
            if cooldown > 0:
                cooldown -= 1
                
            # Show state
            cv2.putText(frame, f"Kick State: {kick_state}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Knee Kick Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_knee_kick_detection()