import cv2
import numpy as np
import mediapipe as mp
from utils import normalize_coordinates, init_mediapipe_pose

def detect_knee_motion():
    """
    Test knee raising detection for kicking
    Returns kick state based on knee height relative to hip
    """
    cap = cv2.VideoCapture(0)
    pose = init_mediapipe_pose()
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    
    # Variables for kick detection
    kick_state = "ready"
    cooldown = 0
    COOLDOWN_FRAMES = 15  # Prevent rapid consecutive kicks
    KNEE_HEIGHT_THRESHOLD = 0.1  # How high knee should be relative to hip

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue
            
        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)
        
        # Convert the BGR image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect pose
        results = pose.process(image)
        
        if results.pose_landmarks:
            # Draw pose landmarks
            mp_drawing.draw_landmarks(
                frame, 
                results.pose_landmarks, 
                mp_pose.POSE_CONNECTIONS
            )
            
            # Get hip and knee landmarks
            hip = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
            knee = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
            
            # Convert landmarks to pixel coordinates
            hip_coords = normalize_coordinates(hip, frame.shape)
            knee_coords = normalize_coordinates(knee, frame.shape)
            
            # Draw landmarks for visualization
            cv2.circle(frame, hip_coords, 5, (255, 0, 0), -1)  # Blue for hip
            cv2.circle(frame, knee_coords, 5, (0, 255, 0), -1)  # Green for knee
            cv2.line(frame, hip_coords, knee_coords, (0, 255, 255), 2)
            
            # Detect kick based on knee height relative to hip
            if cooldown == 0:
                # Negative value means knee is above hip
                knee_height = knee.y - hip.y
                
                if knee_height < -KNEE_HEIGHT_THRESHOLD:  # Knee raised high enough
                    kick_state = "kicking"
                    cooldown = COOLDOWN_FRAMES
                else:
                    kick_state = "ready"
                    
            # Visualize kick threshold
            threshold_y = int(hip_coords[1] - (frame.shape[0] * KNEE_HEIGHT_THRESHOLD))
            cv2.line(frame, (hip_coords[0] - 50, threshold_y), 
                    (hip_coords[0] + 50, threshold_y), (255, 0, 0), 1)
        
        # Update cooldown
        if cooldown > 0:
            cooldown -= 1
            
        # Display kick state
        cv2.putText(frame, f"Kick State: {kick_state}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Knee Kick Detection', frame)
        
        # Break the loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_knee_motion()