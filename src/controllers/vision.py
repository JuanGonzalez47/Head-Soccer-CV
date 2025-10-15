import cv2
import mediapipe as mp
import queue
import threading
import time
from .base import Controller
from ..utils.utils import normalize_coordinates

class VisionController(Controller):
    """Controller implementation using computer vision for gesture-based input"""
    
    def __init__(self):
        """Initialize vision control system for both players"""
        self.cap = cv2.VideoCapture(0)
        # Optimize camera configuration for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduced resolution
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)  # Reduced FPS
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Configure MediaPipe Hands with optimized settings for two players
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=4,             # Increased for better multi-hand detection
            min_detection_confidence=0.3, # Lowered for better detection
            min_tracking_confidence=0.3,  # Lowered for better tracking
            model_complexity=0           # Use lightest model
        )
        
        # Configure pose detection for faster processing - single instance
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.3,  # Lowered for better detection
            min_tracking_confidence=0.3,   # Lowered for better tracking
            model_complexity=0,           # Use lightest model
            smooth_landmarks=True        # Enable smoothing for stability
        )
        
        # Frame processing thread and queue
        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_frames)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.mp_pose = mp.solutions.pose

        # Control states for both players
        self.players = {
            1: {"movement": "none", "jump": "ready", "kick": "ready", "color": (0, 255, 0)},
            2: {"movement": "none", "jump": "ready", "kick": "ready", "color": (0, 0, 255)}
        }
        
        # Initialize control states
        self.cooldowns = {
            1: {"jump": 0, "kick": 0},
            2: {"jump": 0, "kick": 0}
        }
        self.COOLDOWN_FRAMES = 3
        self.KNEE_HEIGHT_THRESHOLD = 0.007
    
    def _process_frames(self):
        """Background thread for processing frames with improved state management"""
        last_process_time = time.time()
        processing_interval = 1.0 / 60  # Target 60fps
        
        while self.running:
            current_time = time.time()
            if current_time - last_process_time < processing_interval:
                continue
                
            ret, frame = self.cap.read()
            if not ret:
                continue

            try:
                # Flip frame for selfie view
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]
                center_x = width // 2
                
                # Reset states at the start of each frame
                for player in [1, 2]:
                    # Only reset movement, keep jump/kick state for cooldown
                    self.players[player]["movement"] = "none"
                    # Reset states if cooldowns are done
                    if self.cooldowns[player]["jump"] == 0:
                        self.players[player]["jump"] = "ready"
                    if self.cooldowns[player]["kick"] == 0:
                        self.players[player]["kick"] = "ready"
                    # Update cooldowns
                    if self.cooldowns[player]["jump"] > 0:
                        self.cooldowns[player]["jump"] -= 1
                    if self.cooldowns[player]["kick"] > 0:
                        self.cooldowns[player]["kick"] -= 1
                
                # Split frame for processing each player's area
                # Convert to RGB once for MediaPipe
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process hands and pose in a single pass for better performance
                hand_results = self.hands.process(rgb_frame)
                pose_results = self.pose.process(rgb_frame)
                
                # Track detected players positions
                player_positions = []
                if pose_results.pose_landmarks:
                    # Get nose positions for player tracking
                    nose = pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
                    if nose.visibility > 0.5:
                        x_pos = int(nose.x * width)
                        player_positions.append(x_pos)
                
                # Update controls based on detected poses and hands
                if pose_results.pose_landmarks:
                    # Determine which player based on nose position
                    nose = pose_results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
                    if nose.visibility > 0.5:
                        x_pos = int(nose.x * width)
                        player = 1 if x_pos < center_x else 2
                        self._process_pose(player, pose_results, frame.shape)
                            
                if hand_results and hand_results.multi_hand_landmarks:
                    self._process_hands(hand_results, width, center_x)
                
                # Create and show debug view
                debug_frame = frame.copy()
                self._draw_debug_view(debug_frame, width, height, center_x)
                cv2.imshow('Game Controls Debug', debug_frame)
                cv2.waitKey(1)
                
                # Update the frame queue with minimal delay
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put_nowait(self.players)
                
                last_process_time = time.time()
                
            except Exception as e:
                print(f"Frame processing error: {e}")
                continue
    
    def process_input(self):
        """Get the latest processed frame and control states"""
        try:
            players = self.frame_queue.get_nowait()
            return {k: {key: val for key, val in v.items() if key != 'color'} 
                   for k, v in players.items()}
        except queue.Empty:
            return {k: {key: val for key, val in v.items() if key != 'color'} 
                   for k, v in self.players.items()}
    
    def reset_states(self):
        """Reset all player states after a goal or game reset"""
        # Reset all player states
        for player in [1, 2]:
            self.players[player]["movement"] = "none"
            self.players[player]["jump"] = "ready"
            self.players[player]["kick"] = "ready"
            self.cooldowns[player]["jump"] = 0
            self.cooldowns[player]["kick"] = 0
            
        # Clear frame queue to prevent stale states
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break

    def _process_pose(self, player, results, frame_shape):
        """Process pose detection for kick controls"""
        if results and results.pose_landmarks:
            # Get required landmarks for right leg
            right_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            right_knee = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            left_hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            left_knee = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_KNEE.value]
            
            # Detectar patada si cualquiera de las rodillas está por encima de la cadera
            right_knee_height = right_knee.y - right_hip.y
            left_knee_height = left_knee.y - left_hip.y
            
            # Usar el umbral más significativo de las dos rodillas
            knee_height = min(right_knee_height, left_knee_height)
            
            if self.cooldowns[player]["kick"] == 0:
                # Aumentar el umbral para una mejor detección
                if knee_height < -0.1:  # Umbral más sensible
                    self.players[player]["kick"] = "kicking"
                    self.cooldowns[player]["kick"] = self.COOLDOWN_FRAMES
                else:
                    self.players[player]["kick"] = "ready"
            # Si cualquier rodilla baja, resetear más rápido
            elif right_knee_height >= -0.05 and left_knee_height >= -0.05:
                self.cooldowns[player]["kick"] = 0

    def _process_hands(self, results, width, center_x):
        """Process hand landmarks for movement and jump controls"""
        # Reset movement states at start of frame
        for player in [1, 2]:
            self.players[player]["movement"] = "none"
            
        if not results.multi_hand_landmarks:
            return
            
        # Process each detected hand
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Simple player assignment based on hand position
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            wrist_x = int(wrist.x * width)
            player = 1 if wrist_x < center_x else 2
            
            # Get hand orientation (left/right hand)
            hand_label = results.multi_handedness[hand_idx].classification[0].label
            
            if hand_label == "Right":  # Movement control
                # Check finger positions for movement control
                finger_tips = [
                    self.mp_hands.HandLandmark.INDEX_FINGER_TIP,
                    self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                    self.mp_hands.HandLandmark.RING_FINGER_TIP,
                    self.mp_hands.HandLandmark.PINKY_TIP
                ]
                finger_pips = [
                    self.mp_hands.HandLandmark.INDEX_FINGER_PIP,
                    self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
                    self.mp_hands.HandLandmark.RING_FINGER_PIP,
                    self.mp_hands.HandLandmark.PINKY_PIP
                ]
                
                # Count extended fingers
                extended_count = sum(
                    1 for tip, pip in zip(finger_tips, finger_pips)
                    if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y
                )
                
                # Update movement state based on extended fingers
                if extended_count >= 3:
                    self.players[player]["movement"] = "right"
                elif extended_count <= 1:
                    self.players[player]["movement"] = "left"
                    
            elif hand_label == "Left":  # Jump control
                wrist_y = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].y
                if self.cooldowns[player]["jump"] == 0:
                    if wrist_y < 0.5:
                        self.players[player]["jump"] = "jumping"
                        self.cooldowns[player]["jump"] = self.COOLDOWN_FRAMES
                    else:
                        self.players[player]["jump"] = "ready"
                elif wrist_y >= 0.5:  # Si la mano baja, resetear más rápido
                    self.cooldowns[player]["jump"] = min(2, self.cooldowns[player]["jump"])
                # Note: cooldown is now handled in _process_frames

    def _draw_debug_view(self, frame, width, height, center_x):
        """Draw debug visualization window with minimal UI"""
        # Draw center line
        cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)
            
        # Draw kick thresholds
        for player in [1, 2]:
            start_x = 0 if player == 1 else center_x
            end_x = center_x if player == 1 else width
            threshold_y = int(height * 0.4)  # Jump threshold
            cv2.line(frame, (start_x, threshold_y), (end_x, threshold_y), 
                    self.players[player]["color"], 1)
            
        # Add player labels with current states
        for player in [1, 2]:
            y_offset = 30 if player == 1 else 90
            x_offset = 10 if player == 1 else center_x + 10
            cv2.putText(frame, f"P{player} Move: {self.players[player]['movement']}", 
                       (x_offset, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                       self.players[player]["color"], 2)
            cv2.putText(frame, f"P{player} Jump: {self.players[player]['jump']}", 
                       (x_offset, y_offset + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                       self.players[player]["color"], 2)
            cv2.putText(frame, f"P{player} Kick: {self.players[player]['kick']}", 
                       (x_offset, y_offset + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, 
                       self.players[player]["color"], 2)
    
    def _draw_pose_landmarks(self, frame, pose_landmarks, color):
        """Draw pose landmarks and connections"""
        if not pose_landmarks:
            return
            
        # Draw all pose connections with better visualization
        for connection in self.mp_pose.POSE_CONNECTIONS:
            start_idx = connection[0]
            end_idx = connection[1]
            
            start_point = pose_landmarks.landmark[start_idx]
            end_point = pose_landmarks.landmark[end_idx]
            
            start_pos = normalize_coordinates(start_point, frame.shape)
            end_pos = normalize_coordinates(end_point, frame.shape)
            
            cv2.line(frame, start_pos, end_pos, color, 2)
            
        # Draw landmarks with circles for better visibility
        for idx, landmark in enumerate(pose_landmarks.landmark):
            pos = normalize_coordinates(landmark, frame.shape)
            if idx in [0, 11, 12, 23, 24]:  # Key body points
                cv2.circle(frame, pos, 5, color, -1)
            else:
                cv2.circle(frame, pos, 3, color, -1)

    def cleanup(self):
        """Release camera and close windows"""
        self.running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()
