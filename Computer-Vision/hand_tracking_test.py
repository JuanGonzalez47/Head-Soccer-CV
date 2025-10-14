import cv2
import numpy as np
import mediapipe as mp
from utils import normalize_coordinates, init_mediapipe_hands

def detect_hand_movement():
    """
    Test right hand open/close detection for movement control
    Returns hand state (open/closed) for right hand only
    """
    cap = cv2.VideoCapture(0)
    hands = init_mediapipe_hands()
    mp_drawing = mp.solutions.drawing_utils
    
    hand_state = "none"
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Reset states at the start of each frame
            movement = "none"
            hand_state = "none"
            
            # Flip the frame horizontally for a later selfie-view display
            frame = cv2.flip(frame, 1)
            
            # Convert the BGR image to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame and detect hands
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, 
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS
                    )
                    
                    # Get finger landmarks
                    thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
                    index_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP]
                    middle_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP]
                    ring_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.RING_FINGER_TIP]
                    pinky_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.PINKY_TIP]
                    
                    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]
                    
                    # Calculate vertical distances from wrist to fingertips
                    finger_heights = [
                        index_tip.y - wrist.y,
                        middle_tip.y - wrist.y,
                        ring_tip.y - wrist.y,
                        pinky_tip.y - wrist.y
                    ]
                    
                    # Count extended fingers (fingers above wrist)
                    extended_fingers = sum(1 for height in finger_heights if height < -0.1)
                    
                    # Determine hand state based on number of extended fingers
                    hand_state = "open" if extended_fingers >= 3 else "closed"
                    
                    # Set movement based on hand state
                    movement = "right" if hand_state == "open" else "left"
                    
                    # Draw circles on fingertips for visualization
                    h, w, _ = frame.shape
                    for landmark in [thumb_tip, index_tip, middle_tip, ring_tip, pinky_tip]:
                        x, y = normalize_coordinates(landmark, frame.shape)
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
                        
                    # Draw hand state indicator
                    color = (0, 255, 0) if hand_state == "open" else (0, 0, 255)
                    cv2.putText(frame, f"Extended fingers: {extended_fingers}", (10, 110),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                    
            # Display movement and hand state
            cv2.putText(frame, f"Movement: {movement}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Hand state: {hand_state}", (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display the frame
            cv2.imshow('Hand Movement Test', frame)
            
            # Break the loop when 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_hand_movement()