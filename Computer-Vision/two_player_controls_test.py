import cv2
import numpy as np
import mediapipe as mp
from utils import normalize_coordinates, init_mediapipe_pose, init_mediapipe_hands

def test_two_player_controls():
    """
    Test all control movements for two players:
    Each player has their own half of the screen:
    - Player 1: Left half (0-50% of screen width)
    - Player 2: Right half (50-100% of screen width)
    
    Controls for each player:
    - Right hand open/closed for movement
    - Left hand raised for jumping
    - Knee raised for kicking
    """
    cap = cv2.VideoCapture(0)
    # Initialize MediaPipe with higher detection confidence for stability
    hands = init_mediapipe_hands()
    # Configure separate pose detection for each player
    pose_p1 = mp.solutions.pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
        smooth_landmarks=True,
    )
    pose_p2 = mp.solutions.pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
        smooth_landmarks=True,
    )
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    mp_pose = mp.solutions.pose

    # Control states for both players
    players = {
        1: {"movement": "none", "jump": "ready", "kick": "ready", "color": (0, 255, 0)},  # Green for P1
        2: {"movement": "none", "jump": "ready", "kick": "ready", "color": (0, 0, 255)}   # Red for P2
    }
    
    # Cooldown variables
    cooldowns = {
        1: {"jump": 0, "kick": 0},
        2: {"jump": 0, "kick": 0}
    }
    COOLDOWN_FRAMES = 15
    
    # Thresholds
    KNEE_HEIGHT_THRESHOLD = 0.1  # How high knee should be relative to hip
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Flip the frame horizontally for selfie view
            frame = cv2.flip(frame, 1)
            
            # Draw center line to divide player areas
            height, width = frame.shape[:2]
            center_x = width // 2
            cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)
            
            # Add player area labels
            cv2.putText(frame, "Player 1", (10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, players[1]["color"], 2)
            cv2.putText(frame, "Player 2", (center_x + 10, height - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, players[2]["color"], 2)
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Split frame into two halves
            height, width = rgb_frame.shape[:2]
            frame_p1 = rgb_frame[:, :center_x]
            frame_p2 = rgb_frame[:, center_x:]
            
            # Process pose for each player separately
            pose_results_p1 = pose_p1.process(frame_p1)
            pose_results_p2 = pose_p2.process(frame_p2)
            
            # Process hands (for movement and jump)
            hand_results = hands.process(rgb_frame)
            
            # Track detected poses for both players
            detected_poses = []
            
            # Process Player 1's pose (left half)
            if pose_results_p1.pose_landmarks is not None:
                # Store original landmarks with adjusted x-coordinates
                landmarks = pose_results_p1.pose_landmarks.landmark
                # Use original pose_landmarks but update x-coordinates when accessing
                detected_poses.append((1, pose_results_p1.pose_landmarks))
                # Store original x values for drawing
                p1_x_adjustments = {idx: landmark.x * center_x / width for idx, landmark in enumerate(landmarks)}
            
            # Process Player 2's pose (right half)
            if pose_results_p2.pose_landmarks is not None:
                # Store original landmarks with adjusted x-coordinates
                landmarks = pose_results_p2.pose_landmarks.landmark
                # Use original pose_landmarks but update x-coordinates when accessing
                detected_poses.append((2, pose_results_p2.pose_landmarks))
                # Store original x values for drawing
                p2_x_adjustments = {idx: (landmark.x * center_x + center_x) / width for idx, landmark in enumerate(landmarks)}
                
            # Draw pose landmarks for detected players
            for player, landmarks in detected_poses:
                # Get the correct x adjustments
                x_adjustments = p1_x_adjustments if player == 1 else p2_x_adjustments
                
                # Draw landmarks at adjusted positions using cv2
                for connection in mp_pose.POSE_CONNECTIONS:
                    start_idx = connection[0]
                    end_idx = connection[1]
                    
                    # Get landmarks with adjusted x coordinates
                    start_landmark = landmarks.landmark[start_idx]
                    end_landmark = landmarks.landmark[end_idx]
                    
                    # Create adjusted coordinates
                    start_pos = normalize_coordinates(
                        type('Point', (), {'x': x_adjustments[start_idx], 'y': start_landmark.y}),
                        frame.shape
                    )
                    end_pos = normalize_coordinates(
                        type('Point', (), {'x': x_adjustments[end_idx], 'y': end_landmark.y}),
                        frame.shape
                    )
                    
                    # Draw the connection
                    cv2.line(frame, start_pos, end_pos, players[player]["color"], 2)
                    
                # Draw landmark points
                for idx, landmark in enumerate(landmarks.landmark):
                    pos = normalize_coordinates(
                        type('Point', (), {'x': x_adjustments[idx], 'y': landmark.y}),
                        frame.shape
                    )
                    cv2.circle(frame, pos, 3, players[player]["color"], -1)
                
                # Process kick detection for each detected player
                for player, landmarks in detected_poses:
                    # Get hip and knee landmarks for kick detection
                    hip = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP.value]
                    knee = landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                    
                    hip_coords = normalize_coordinates(hip, frame.shape)
                    knee_coords = normalize_coordinates(knee, frame.shape)
                    
                    # Draw kick detection points with player color
                    cv2.circle(frame, hip_coords, 5, players[player]["color"], -1)
                    cv2.circle(frame, knee_coords, 5, players[player]["color"], -1)
                    cv2.line(frame, hip_coords, knee_coords, players[player]["color"], 2)
                    
                    # Detect kick based on knee height
                    if cooldowns[player]["kick"] == 0:
                        knee_height = knee.y - hip.y
                        if knee_height < -KNEE_HEIGHT_THRESHOLD:
                            players[player]["kick"] = "kicking"
                            cooldowns[player]["kick"] = COOLDOWN_FRAMES
                        else:
                            players[player]["kick"] = "ready"
                            
                    # Draw kick threshold
                    threshold_y = int(hip_coords[1] - (frame.shape[0] * KNEE_HEIGHT_THRESHOLD))
                    cv2.line(frame, (hip_coords[0] - 50, threshold_y),
                            (hip_coords[0] + 50, threshold_y), players[player]["color"], 1)
            
            # Process hand landmarks if available
            if hand_results.multi_hand_landmarks:
                for hand_idx, hand_landmarks in enumerate(hand_results.multi_hand_landmarks):
                    # Get hand center point to determine which player
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    wrist_x = int(wrist.x * width)
                    player = 1 if wrist_x < center_x else 2
                    
                    # Draw hand landmarks with player color
                    mp_drawing.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=players[player]["color"])
                    )
                    
                    # Get hand label (Left/Right)
                    hand_label = hand_results.multi_handedness[hand_idx].classification[0].label
                    
                    if hand_label == "Right":  # Movement control
                        # Get finger tip and pip landmarks
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
                        
                        # Check if each finger is extended
                        fingers_extended = [tip.y < pip.y for tip, pip in zip(finger_tips, finger_pips)]
                        extended_count = sum(fingers_extended)
                        
                        # Determine hand state
                        if extended_count >= 3:
                            players[player]["movement"] = "open"
                        elif extended_count <= 1:
                            players[player]["movement"] = "closed"
                        else:
                            players[player]["movement"] = "none"
                            
                        # Visualize finger detection
                        for tip, pip, is_extended in zip(finger_tips, finger_pips, fingers_extended):
                            tip_coords = normalize_coordinates(tip, frame.shape)
                            pip_coords = normalize_coordinates(pip, frame.shape)
                            color = players[player]["color"] if is_extended else (128, 128, 128)
                            cv2.line(frame, tip_coords, pip_coords, color, 2)
                            
                    elif hand_label == "Left":  # Jump control
                        if cooldowns[player]["jump"] == 0:
                            if wrist.y < 0.4:  # Hand raised above 40% of screen height
                                players[player]["jump"] = "jumping"
                                cooldowns[player]["jump"] = COOLDOWN_FRAMES
                            else:
                                players[player]["jump"] = "ready"
                                
                        # Draw jump threshold for this player's side
                        threshold_y = int(frame.shape[0] * 0.4)
                        start_x = 0 if player == 1 else center_x
                        end_x = center_x if player == 1 else width
                        cv2.line(frame, (start_x, threshold_y),
                                (end_x, threshold_y), players[player]["color"], 1)
            
            # Update cooldowns
            for player in [1, 2]:
                if cooldowns[player]["jump"] > 0:
                    cooldowns[player]["jump"] -= 1
                if cooldowns[player]["kick"] > 0:
                    cooldowns[player]["kick"] -= 1
                
            # Display states for both players
            for player in [1, 2]:
                y_offset = 30 if player == 1 else 90
                cv2.putText(frame, f"P{player} Movement: {players[player]['movement']}", (10, y_offset),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, players[player]["color"], 2)
                cv2.putText(frame, f"P{player} Jump: {players[player]['jump']}", (10, y_offset + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, players[player]["color"], 2)
                cv2.putText(frame, f"P{player} Kick: {players[player]['kick']}", (10, y_offset + 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, players[player]["color"], 2)
            
            # Display frame
            cv2.imshow('Two Player Controls Test', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    test_two_player_controls()