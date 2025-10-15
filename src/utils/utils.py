import mediapipe as mp

def normalize_coordinates(landmark, frame_shape):
    """
    Convert MediaPipe normalized coordinates to pixel coordinates.
    
    Args:
        landmark: MediaPipe landmark with normalized coordinates
        frame_shape: Shape of the frame (height, width)
        
    Returns:
        tuple: (x, y) coordinates in pixels
    """
    return (
        int(landmark.x * frame_shape[1]),
        int(landmark.y * frame_shape[0])
    )

def init_mediapipe_hands(
    static_image_mode=False,
    max_num_hands=4,  # Track up to 4 hands (2 per player)
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5
):
    """
    Initialize MediaPipe Hands solution with specified parameters.
    
    Args:
        static_image_mode: Whether to treat input images as static
        max_num_hands: Maximum number of hands to detect
        min_detection_confidence: Minimum confidence for detection
        min_tracking_confidence: Minimum confidence for tracking
        
    Returns:
        mediapipe.solutions.hands.Hands: Configured hands solution
    """
    return mp.solutions.hands.Hands(
        static_image_mode=static_image_mode,
        max_num_hands=max_num_hands,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence
    )

def init_mediapipe_pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
):
    """
    Initialize MediaPipe Pose solution with specified parameters.
    
    Args:
        static_image_mode: Whether to treat input images as static
        model_complexity: Model complexity (0, 1, or 2)
        min_detection_confidence: Minimum confidence for detection
        min_tracking_confidence: Minimum confidence for tracking
        
    Returns:
        mediapipe.solutions.pose.Pose: Configured pose solution
    """
    return mp.solutions.pose.Pose(
        static_image_mode=static_image_mode,
        model_complexity=model_complexity,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
        smooth_landmarks=True
    )