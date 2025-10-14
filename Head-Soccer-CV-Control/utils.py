import mediapipe as mp

def normalize_coordinates(x, y, width, height):
    """Normalize coordinates to [0, 1] range"""
    return x / width, y / height

def init_mediapipe_hands():
    """Initialize MediaPipe hands module with optimal settings"""
    return mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=4,  # Track up to 4 hands (2 per player)
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

def init_mediapipe_pose():
    """Initialize MediaPipe pose module with optimal settings"""
    return mp.solutions.pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=1,
        smooth_landmarks=True
    )