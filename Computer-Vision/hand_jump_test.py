import cv2
import numpy as np
import mediapipe as mp
from utils import normalize_coordinates, init_mediapipe_hands

def detect_hand_jump():
    """
    Test left hand raising detection for jumping
    Returns jump state based on left hand height
    Uses hand tracking to ensure we only detect the left hand
    """
    cap = cv2.VideoCapture(0)
    hands = init_mediapipe_hands()
    mp_drawing = mp.solutions.drawing_utils
    mp_hands = mp.solutions.hands
    
    # Variables for jump detection
    jump_state = "ready"
    cooldown = 0
    COOLDOWN_FRAMES = 15  # Prevent rapid consecutive jumps
    HAND_HEIGHT_THRESHOLD = 0.1  # How high hand should be relative to shoulder

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue
            
        # Flip the frame horizontally for a later selfie-view display
        frame = cv2.flip(frame, 1)
        
        # Convert the BGR image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the image and detect hands
        results = hands.process(image)
        
        if results.multi_hand_landmarks:
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Check if this is the left hand
                if results.multi_handedness[hand_idx].classification[0].label == "Left":
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )
                    
                    # Get wrist and palm center landmarks
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
            
                    # Convert landmarks to pixel coordinates
                    wrist_coords = normalize_coordinates(wrist, frame.shape)
                    palm_coords = normalize_coordinates(middle_pip, frame.shape)
                    
                    # Draw landmarks for visualization
                    cv2.circle(frame, wrist_coords, 5, (255, 0, 0), -1)  # Blue for wrist
                    cv2.circle(frame, palm_coords, 5, (0, 255, 0), -1)  # Green for palm
                    cv2.line(frame, wrist_coords, palm_coords, (0, 255, 255), 2)
                    
                        # Detect jump based on hand height (vertical position)
                    if cooldown == 0:
                        # hand.y is 0 at top of frame and 1 at bottom
                        hand_height = wrist.y
                        if hand_height < 0.4:  # Hand raised above 40% of screen height
                            jump_state = "jumping"
                            cooldown = COOLDOWN_FRAMES
                        else:
                            jump_state = "ready"
                    
                    # Visualize jump threshold
                    threshold_y = int(frame.shape[0] * 0.4)  # 40% from top of screen
                    cv2.line(frame, (0, threshold_y), 
                            (frame.shape[1], threshold_y), (255, 0, 0), 1)
        
        # Update cooldown
        if cooldown > 0:
            cooldown -= 1
            
        # Display jump state
        cv2.putText(frame, f"Jump State: {jump_state}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow('Hand Jump Detection', frame)
        
        # Break the loop on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_hand_jump()