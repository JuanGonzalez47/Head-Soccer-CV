"""Unit tests for hand movement detection."""

import cv2
import numpy as np
import mediapipe as mp
from src.utils.utils import normalize_coordinates, init_mediapipe_hands

def test_hand_movement_detection():
    """
    Test right hand open/close detection for movement control.
    Tests the detection of hand state (open/closed) for movement control.
    """
    cap = cv2.VideoCapture(0)
    hands = init_mediapipe_hands()
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    # Control states
    movement_state = "none"
    hand_state = "none"
    
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
                    # Only process right hand
                    if results.multi_handedness[hand_idx].classification[0].label == "Right":
                        # Draw hand landmarks
                        mp_drawing.draw_landmarks(
                            frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Get finger landmarks
                        finger_tips = [
                            hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
                        ]
                        finger_pips = [
                            hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP],
                            hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]
                        ]
                        
                        # Check finger extension
                        fingers_extended = [tip.y < pip.y for tip, pip in zip(finger_tips, finger_pips)]
                        extended_count = sum(fingers_extended)
                        
                        # Determine hand state
                        if extended_count >= 3:
                            hand_state = "open"
                            movement_state = "right"
                        elif extended_count <= 1:
                            hand_state = "closed"
                            movement_state = "left"
                        else:
                            hand_state = "none"
                            movement_state = "none"
                            
                        # Visualize finger detection
                        for tip, pip, is_extended in zip(finger_tips, finger_pips, fingers_extended):
                            tip_coords = normalize_coordinates(tip, frame.shape)
                            pip_coords = normalize_coordinates(pip, frame.shape)
                            color = (0, 255, 0) if is_extended else (0, 0, 255)
                            cv2.line(frame, tip_coords, pip_coords, color, 2)
            
            # Show states
            cv2.putText(frame, f"Hand state: {hand_state}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Movement: {movement_state}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Hand Movement Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_hand_movement_detection()