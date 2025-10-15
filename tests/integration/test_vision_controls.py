"""Integration tests for the vision control system."""

import cv2
import numpy as np
import mediapipe as mp
from src.utils.utils import normalize_coordinates, init_mediapipe_pose, init_mediapipe_hands

def test_all_controls():
    """
    Test all control movements together:
    - Right hand open/closed for movement
    - Left hand raised for jumping
    - Knee raised for kicking
    """
    cap = cv2.VideoCapture(0)
    hands = init_mediapipe_hands()
    pose = init_mediapipe_pose()
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose

    # Control states
    movement_state = "none"  # From right hand open/closed
    jump_state = "ready"     # From left hand raised
    kick_state = "ready"     # From knee raised
    
    # Cooldown variables
    jump_cooldown = 0
    kick_cooldown = 0
    COOLDOWN_FRAMES = 15
    
    # Thresholds
    KNEE_HEIGHT_THRESHOLD = 0.007  # How high knee should be relative to hip
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Flip the frame horizontally for selfie view
            frame = cv2.flip(frame, 1)
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process pose first (for knee detection)
            pose_results = pose.process(rgb_frame)
            
            # Process hands (for movement and jump)
            hand_results = hands.process(rgb_frame)
            
            # Draw pose landmarks if available
            if pose_results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    pose_results.pose_landmarks,
                    mp_pose.POSE_CONNECTIONS
                )
                
                # Get hip and knee landmarks for kick detection
                hip = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
                knee = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
                
                hip_coords = normalize_coordinates(hip, frame.shape)
                knee_coords = normalize_coordinates(knee, frame.shape)
                
                # Draw kick detection points
                cv2.circle(frame, hip_coords, 5, (255, 0, 0), -1)
                cv2.circle(frame, knee_coords, 5, (0, 255, 0), -1)
                cv2.line(frame, hip_coords, knee_coords, (0, 255, 255), 2)
                
                # Detect kick based on knee height
                if kick_cooldown == 0:
                    knee_height = knee.y - hip.y
                    if knee_height < -KNEE_HEIGHT_THRESHOLD:
                        kick_state = "kicking"
                        kick_cooldown = COOLDOWN_FRAMES
                    else:
                        kick_state = "ready"
                        
                # Draw kick threshold
                threshold_y = int(hip_coords[1] - (frame.shape[0] * KNEE_HEIGHT_THRESHOLD))
                cv2.line(frame, (hip_coords[0] - 50, threshold_y),
                        (hip_coords[0] + 50, threshold_y), (255, 0, 0), 1)
            
            # Process hand landmarks if available
            if hand_results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Get hand label (Left/Right)
                    hand_label = hand_results.multi_handedness[hand_idx].classification[0].label
                    
                    if hand_label == "Right":  # Movement control
                        # Get finger tip and pip (middle knuckle) landmarks
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
                        
                        # Check if each finger is extended (tip is above pip)
                        fingers_extended = [tip.y < pip.y for tip, pip in zip(finger_tips, finger_pips)]
                        
                        # Count extended fingers
                        extended_count = sum(fingers_extended)
                        
                        # Determine hand state based on number of extended fingers
                        if extended_count >= 3:  # 3 or more fingers extended
                            movement_state = "open"
                        elif extended_count <= 1:  # 1 or fewer fingers extended
                            movement_state = "closed"
                        else:
                            movement_state = "none"
                            
                        # Visualize finger detection
                        for tip, pip, is_extended in zip(finger_tips, finger_pips, fingers_extended):
                            tip_coords = normalize_coordinates(tip, frame.shape)
                            pip_coords = normalize_coordinates(pip, frame.shape)
                            color = (0, 255, 0) if is_extended else (0, 0, 255)  # Green if extended, red if not
                            cv2.line(frame, tip_coords, pip_coords, color, 2)
                            
                    elif hand_label == "Left":  # Jump control
                        wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                        
                        if jump_cooldown == 0:
                            if wrist.y < 0.4:  # Hand raised above 40% of screen height
                                jump_state = "jumping"
                                jump_cooldown = COOLDOWN_FRAMES
                            else:
                                jump_state = "ready"
                                
                        # Draw jump threshold
                        threshold_y = int(frame.shape[0] * 0.4)
                        cv2.line(frame, (0, threshold_y),
                                (frame.shape[1], threshold_y), (0, 0, 255), 1)
            
            # Update cooldowns
            if jump_cooldown > 0:
                jump_cooldown -= 1
            if kick_cooldown > 0:
                kick_cooldown -= 1
                
            # Display states
            cv2.putText(frame, f"Movement: {movement_state}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Jump: {jump_state}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Kick: {kick_state}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            cv2.imshow('Integrated Controls Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_all_controls()