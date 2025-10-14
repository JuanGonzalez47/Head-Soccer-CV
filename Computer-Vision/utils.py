import cv2
import numpy as np
import mediapipe as mp

def init_mediapipe_pose():
    """Initialize MediaPipe Pose detector"""
    mp_pose = mp.solutions.pose
    return mp_pose.Pose(
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

def init_mediapipe_hands():
    """Initialize MediaPipe Hands detector"""
    mp_hands = mp.solutions.hands
    return mp_hands.Hands(
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    )

def draw_landmarks(image, results, mp_drawing, mp_pose):
    """Draw the detected pose landmarks on the image"""
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS
        )
    return image

def normalize_coordinates(landmark, image_shape):
    """Convert normalized coordinates to pixel coordinates"""
    return (
        int(landmark.x * image_shape[1]),
        int(landmark.y * image_shape[0])
    )

def calculate_angle(a, b, c):
    """Calculate angle between three points"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle