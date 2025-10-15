"""Integration tests for two player vision controls."""

import cv2
import numpy as np
import mediapipe as mp
from src.utils.utils import normalize_coordinates, init_mediapipe_pose, init_mediapipe_hands
from dataclasses import dataclass

@dataclass
class PlayerControls:
    """Data class to store player control states."""
    movement_state: str = "none"
    jump_state: str = "ready"
    kick_state: str = "ready"
    jump_cooldown: int = 0
    kick_cooldown: int = 0

def test_two_player_controls():
    """
    Test vision controls for two players simultaneously with split screen:
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

    # Constants
    COOLDOWN_FRAMES = 15
    KNEE_HEIGHT_THRESHOLD = 0.007
    
    # Initialize player states
    player1 = PlayerControls()
    player2 = PlayerControls()
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Flip the frame horizontally for selfie view
            frame = cv2.flip(frame, 1)
            
            # Split frame for two players
            frame_height = frame.shape[0]
            frame_width = frame.shape[1]
            split_x = frame_width // 2
            
            # Create separate frames for each player
            player1_frame = frame[:, :split_x]
            player2_frame = frame[:, split_x:]
            
            # Draw split line
            cv2.line(frame, (split_x, 0), (split_x, frame_height),
                     (255, 255, 255), 2)
            
            # Process each player's frame
            for player_idx, (player_frame, player) in enumerate(
                [(player1_frame, player1), (player2_frame, player2)]):
                
                # Convert to RGB for MediaPipe
                rgb_frame = cv2.cvtColor(player_frame, cv2.COLOR_BGR2RGB)
                
                # Process pose
                pose_results = pose.process(rgb_frame)
                if pose_results.pose_landmarks:
                    mp_drawing.draw_landmarks(
                        player_frame,
                        pose_results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS
                    )
                    
                    # Get hip and knee landmarks
                    hip = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP]
                    knee = pose_results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE]
                    
                    # Normalize coordinates for the split frame
                    hip_coords = normalize_coordinates(hip, player_frame.shape)
                    knee_coords = normalize_coordinates(knee, player_frame.shape)
                    
                    # Draw kick detection points
                    cv2.circle(player_frame, hip_coords, 5, (255, 0, 0), -1)
                    cv2.circle(player_frame, knee_coords, 5, (0, 255, 0), -1)
                    cv2.line(player_frame, hip_coords, knee_coords, (0, 255, 255), 2)
                    
                    # Detect kick
                    if player.kick_cooldown == 0:
                        knee_height = knee.y - hip.y
                        if knee_height < -KNEE_HEIGHT_THRESHOLD:
                            player.kick_state = "kicking"
                            player.kick_cooldown = COOLDOWN_FRAMES
                        else:
                            player.kick_state = "ready"
                    
                    # Draw kick threshold
                    threshold_y = int(hip_coords[1] - (player_frame.shape[0] * KNEE_HEIGHT_THRESHOLD))
                    cv2.line(player_frame, (hip_coords[0] - 50, threshold_y),
                            (hip_coords[0] + 50, threshold_y), (255, 0, 0), 1)
                
                # Process hands
                hand_results = hands.process(rgb_frame)
                if hand_results.multi_hand_landmarks:
                    for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                        # Draw hand landmarks
                        mp_drawing.draw_landmarks(
                            player_frame,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Get hand label
                        hand_label = hand_results.multi_handedness[hand_idx].classification[0].label
                        
                        if hand_label == "Right":  # Movement control
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
                            
                            # Set movement state
                            if extended_count >= 3:
                                player.movement_state = "open"
                            elif extended_count <= 1:
                                player.movement_state = "closed"
                            else:
                                player.movement_state = "none"
                                
                            # Visualize finger detection
                            for tip, pip, is_extended in zip(finger_tips, finger_pips, fingers_extended):
                                tip_coords = normalize_coordinates(tip, player_frame.shape)
                                pip_coords = normalize_coordinates(pip, player_frame.shape)
                                color = (0, 255, 0) if is_extended else (0, 0, 255)
                                cv2.line(player_frame, tip_coords, pip_coords, color, 2)
                                
                        elif hand_label == "Left":  # Jump control
                            wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                            
                            if player.jump_cooldown == 0:
                                if wrist.y < 0.4:
                                    player.jump_state = "jumping"
                                    player.jump_cooldown = COOLDOWN_FRAMES
                                else:
                                    player.jump_state = "ready"
                                    
                            # Draw jump threshold
                            threshold_y = int(player_frame.shape[0] * 0.4)
                            cv2.line(player_frame, (0, threshold_y),
                                    (player_frame.shape[1], threshold_y), (0, 0, 255), 1)
                
                # Update cooldowns
                if player.jump_cooldown > 0:
                    player.jump_cooldown -= 1
                if player.kick_cooldown > 0:
                    player.kick_cooldown -= 1
                
                # Display states
                offset_x = 10 if player_idx == 0 else split_x + 10
                cv2.putText(frame, f"P{player_idx + 1} Movement: {player.movement_state}",
                           (offset_x, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"P{player_idx + 1} Jump: {player.jump_state}",
                           (offset_x, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"P{player_idx + 1} Kick: {player.kick_state}",
                           (offset_x, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display the combined frame
            cv2.imshow('Two Player Controls Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_two_player_controls()