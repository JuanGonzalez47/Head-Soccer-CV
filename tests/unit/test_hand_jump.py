"""Unit tests for hand jumping detection."""

import cv2
import numpy as np
import mediapipe as mp
from src.utils.utils import normalize_coordinates, init_mediapipe_hands

def test_hand_jump_detection():
    """
    Test left hand raising detection for jumping.
    Tests the detection of jumping state based on left hand height.
    """
    cap = cv2.VideoCapture(0)
    hands = init_mediapipe_hands()
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    # Control variables
    jump_state = "ready"
    cooldown = 0
    COOLDOWN_FRAMES = 15
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Flip frame for selfie view
            frame = cv2.flip(frame, 1)
            
            # Process frame
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    # Only process left hand
                    if results.multi_handedness[hand_idx].classification[0].label == "Left":
                        # Draw hand landmarks
                        mp_drawing.draw_landmarks(
                            frame, 
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Get wrist position for jump detection
                        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                        middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
                
                        # Convert to pixel coordinates
                        wrist_coords = normalize_coordinates(wrist, frame.shape)
                        palm_coords = normalize_coordinates(middle_pip, frame.shape)
                        
                        # Visualize detection points
                        cv2.circle(frame, wrist_coords, 5, (255, 0, 0), -1)
                        cv2.circle(frame, palm_coords, 5, (0, 255, 0), -1)
                        cv2.line(frame, wrist_coords, palm_coords, (0, 255, 255), 2)
                        
                        # Check for jump trigger
                        if cooldown == 0:
                            if wrist.y < 0.4:  # Hand above 40% screen height
                                jump_state = "jumping"
                                cooldown = COOLDOWN_FRAMES
                            else:
                                jump_state = "ready"
                        
                        # Draw threshold line
                        threshold_y = int(frame.shape[0] * 0.4)
                        cv2.line(frame, (0, threshold_y),
                                (frame.shape[1], threshold_y), (0, 0, 255), 1)
            
            # Update cooldown
            if cooldown > 0:
                cooldown -= 1
                
            # Show state
            cv2.putText(frame, f"Jump State: {jump_state}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Hand Jump Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_hand_jump_detection()