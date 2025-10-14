# coding: utf-8
from graphics import *
from variaveis import *
import time, math
import os, sys
import cv2
import mediapipe as mp

# Adjust Python path to find the Computer-Vision module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
computer_vision_dir = os.path.join(parent_dir, 'Computer-Vision')
sys.path.append(computer_vision_dir)

from utils import normalize_coordinates, init_mediapipe_pose, init_mediapipe_hands

import threading
import queue
import time

class VisionController:
    def __init__(self):
        """Initialize vision control system for both players"""
        self.cap = cv2.VideoCapture(0)
        # Optimizar configuración de cámara para mejor rendimiento
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 480)  # Resolución más pequeña para mejor rendimiento
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        self.cap.set(cv2.CAP_PROP_FPS, 60)  # Aumentar FPS
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimizar buffer para menor latencia
        
        # Configurar MediaPipe Hands para mejor rendimiento
        self.hands = mp.solutions.hands.Hands(
            max_num_hands=2,  # Limitar a 2 manos para mejor rendimiento
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0  # Usar modelo más ligero
        )
        
        # Configurar pose detection más rápido
        self.pose_p1 = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0,  # Modelo más ligero
            smooth_landmarks=False,  # Desactivar suavizado para menor latencia
        )
        self.pose_p2 = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0,
            smooth_landmarks=False,
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
        
        # Cooldowns optimizados para mejor respuesta
        self.cooldowns = {
            1: {"jump": 0, "kick": 0},
            2: {"jump": 0, "kick": 0}
        }
        self.COOLDOWN_FRAMES = 8  # Reducido para más rapidez
        self.KNEE_HEIGHT_THRESHOLD = 0.08  # Más sensible para patadas

    def _process_frames(self):
        """Background thread for processing frames"""
        last_process_time = time.time()
        processing_interval = 1.0 / 60  # Target 60fps para mejor respuesta
        
        while self.running:
            current_time = time.time()
            if current_time - last_process_time < processing_interval:
                continue  # Sin sleep para máxima velocidad
                
            ret, frame = self.cap.read()
            if not ret:
                continue

            try:
                # Flip frame for selfie view
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]
                center_x = width // 2
                
                # Convert to RGB for MediaPipe (using the same frame for both players)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process hands first (usually faster than pose)
                hand_results = self.hands.process(rgb_frame)
                
                # Process poses in parallel for both players
                pose_results_p1 = self.pose_p1.process(rgb_frame)
                pose_results_p2 = self.pose_p2.process(rgb_frame)
                
                # Update controls immediately
                if pose_results_p1.pose_landmarks:
                    self._process_pose(1, pose_results_p1, frame.shape)
                if pose_results_p2.pose_landmarks:
                    self._process_pose(2, pose_results_p2, frame.shape)
                if hand_results and hand_results.multi_hand_landmarks:
                    self._process_hands(hand_results, width, center_x)
                
                # Create and show debug view
                debug_frame = frame.copy()
                self._draw_debug_view(debug_frame, width, height, center_x)
                cv2.imshow('Game Controls Debug', debug_frame)
                cv2.waitKey(1)
                
                # Update the frame queue with minimal delay
                while self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        break
                self.frame_queue.put_nowait(self.players)
                
                last_process_time = time.time()
                
            except Exception as e:
                print(f"Frame processing error: {e}")
                continue
                
                # Process the frame
                height, width = frame.shape[:2]
                center_x = width // 2
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Split and process frames
                frame_p1 = rgb_frame[:, :center_x]
                frame_p2 = rgb_frame[:, center_x:]
                pose_results_p1 = self.pose_p1.process(frame_p1)
                pose_results_p2 = self.pose_p2.process(frame_p2)
                hand_results = self.hands.process(rgb_frame)
                
                # Update player states
                self._process_pose(1, pose_results_p1, frame.shape)
                self._process_pose(2, pose_results_p2, frame.shape)
                if hand_results.multi_hand_landmarks:
                    self._process_hands(hand_results, width, center_x)
                self._update_cooldowns()
                
                # Draw debug view
                self._draw_debug_view(frame, width, height, center_x)
                
                # Put the results in the queue
                if self.result_queue.full():
                    self.result_queue.get_nowait()
                self.result_queue.put_nowait((frame, self.players.copy()))
                
            except queue.Full:
                continue  # Skip frame if queues are full
            except Exception as e:
                print(f"Error processing frame: {e}")
                
            time.sleep(0.01)  # Small delay to prevent thread from consuming too much CPU

    def process_frame(self):
        """Get the latest processed frame and control states"""
        try:
            players = self.frame_queue.get_nowait()
            return None, players
        except queue.Empty:
            return None, self.players

    def _process_pose(self, player, results, frame_shape):
        """Process pose detection for kick controls"""
        if results and results.pose_landmarks:
            hip = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            knee = results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]
            
            # Check kick state
            knee_height = knee.y - hip.y
            if self.cooldowns[player]["kick"] == 0:
                if knee_height < -self.KNEE_HEIGHT_THRESHOLD:
                    self.players[player]["kick"] = "kicking"
                    self.cooldowns[player]["kick"] = self.COOLDOWN_FRAMES
                else:
                    self.players[player]["kick"] = "ready"
            else:
                # Reset kick state when cooldown is active
                self.players[player]["kick"] = "ready"
                knee_height = knee.y - hip.y
                if knee_height < -self.KNEE_HEIGHT_THRESHOLD:
                    self.players[player]["kick"] = "kicking"
                    self.cooldowns[player]["kick"] = self.COOLDOWN_FRAMES
                else:
                    self.players[player]["kick"] = "ready"

    def _process_hands(self, results, width, center_x):
        """Process hand landmarks for movement and jump controls"""
        # Reset movement states at the start of each frame
        for player in [1, 2]:
            self.players[player]["movement"] = "none"
            
        if not results.multi_hand_landmarks:
            return
            
        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Determine which player based on hand position
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            wrist_x = int(wrist.x * width)
            player = 1 if wrist_x < center_x else 2
            
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
                # Detección de salto más sensible
                if wrist.y < 0.5:  # Hand raised above 50% of screen height
                    if self.cooldowns[player]["jump"] == 0:
                        self.players[player]["jump"] = "jumping"
                        self.cooldowns[player]["jump"] = 10  # Cooldown más corto
                else:
                    self.players[player]["jump"] = "ready"

    def _update_cooldowns(self):
        """Update cooldown timers"""
        for player in [1, 2]:
            # Update jump cooldown
            if self.cooldowns[player]["jump"] > 0:
                self.cooldowns[player]["jump"] -= 1
                if self.cooldowns[player]["jump"] == 0:
                    self.players[player]["jump"] = "ready"
                    
            # Update kick cooldown
            if self.cooldowns[player]["kick"] > 0:
                self.cooldowns[player]["kick"] -= 1
                if self.cooldowns[player]["kick"] == 0:
                    self.players[player]["kick"] = "ready"
                self.cooldowns[player]["kick"] -= 1

    def _draw_debug_view(self, frame, width, height, center_x):
        """Draw debug visualization window with full body tracking"""
        # Draw center line
        cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)
        
        # Draw pose landmarks for both players
        if hasattr(self.pose_p1, 'pose_landmarks_'):
            self._draw_pose_landmarks(frame, self.pose_p1.pose_landmarks_, self.players[1]["color"])
        if hasattr(self.pose_p2, 'pose_landmarks_'):
            self._draw_pose_landmarks(frame, self.pose_p2.pose_landmarks_, self.players[2]["color"])
            
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
            
            # Draw thicker lines for better visibility
            cv2.line(frame, start_pos, end_pos, color, 2)
            
        # Draw landmarks with circles for better visibility
        for idx, landmark in enumerate(pose_landmarks.landmark):
            pos = normalize_coordinates(landmark, frame.shape)
            # Draw larger circles for key points (head, shoulders, hips)
            if idx in [0, 11, 12, 23, 24]:  # Key body points
                cv2.circle(frame, pos, 5, color, -1)
            else:
                cv2.circle(frame, pos, 3, color, -1)
                pos = normalize_coordinates(landmark, frame.shape)
                cv2.circle(frame, pos, 3, color, -1)

    def cleanup(self):
        """Release camera and close windows"""
        self.running = False
        if self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()

#### VARIÁVEIS ####
tela = GraphWin("Head Soccer", x, y, False)

# Initialize vision controller
try:
    vision_controller = VisionController()
    use_vision = True
    print("Vision controller initialized successfully!")
except Exception as e:
    print(f"Could not initialize vision controller: {e}")
    print("Falling back to keyboard controls")
    use_vision = False

intro = Image(Point(x / 2, y / 2), "../assets/Imagens/intro2.gif")
intro.draw(tela)

jogar = Image(Point(175, 500), "../assets/Imagens/jogar.gif")
jogar.draw(tela)

sair = Image(Point(425, 500), "../assets/Imagens/sair.gif")
sair.draw(tela)

####################
## LOOP DA INTRO ###
####################
while True:
    enter = tela.checkKey()
    check = tela.checkMouse()
    if check != None:
        check_x = check.getX()
        check_y = check.getY()
        if (470 <= check_y <= 530) and (75 <= check_x <= 275):
            time.sleep(0.06)
            break
        elif (470 <= check_y <= 530) and (325 <= check_x <= 525):
            time.sleep(0.2)
            if use_vision:
                vision_controller.cleanup()
            tela.close()
    else:
        if enter == "Return":
            time.sleep(0.06)
            break
    time.sleep(0.07)

c_bola = Circle(Point(x / 2, 100), raio)
c_bola.draw(tela)

cabeca = Circle(Point(300, 491), raio_cabeca)
cabeca.draw(tela)
pe = Circle(Point(300, 529), raio)
pe.draw(tela)

cabeca2 = Circle(Point(900, 491), raio_cabeca)
cabeca2.draw(tela)
pe2 = Circle(Point(900, 529), raio)
pe2.draw(tela)

col_trave1 = Circle(Point(105, 360), 5)
col_trave1.draw(tela)

col_trave2 = Circle(Point(x - 105, 360), 5)
col_trave2.draw(tela)

bg = Image(Point(x / 2, y / 2), "../assets/Imagens/bg.gif")
bg.draw(tela)

#### BONECO ESQUERDO ####
boneco = Image(Point(300, 503), "../assets/Imagens/LeftChar.gif")
boneco.draw(tela)

#### BONECO DIREITO ####
boneco2 = Image(Point(900, 503), "../assets/Imagens/RightChar.gif")
boneco2.draw(tela)

#### BOLA ####
bola = Image(Point(x / 2, 100), "../assets/Imagens/ball.gif")
bola.draw(tela)

### TRAVE ESQUERDA ###
trave1 = Image(Point(55, 450), "../assets/Imagens/trave1.gif")
trave1.draw(tela)

### TRAVE DIREITA ###
trave2 = Image(Point(x - 55, 450), "../assets/Imagens/trave2.gif")
trave2.draw(tela)

x1_trave2 = trave2.getAnchor().getX() - larg_t
x2_trave2 = trave2.getAnchor().getX() + larg_t

x1_trave1 = trave1.getAnchor().getX() - larg_t
y1_trave = trave1.getAnchor().getY() - alt_t
x2_trave1 = trave1.getAnchor().getX() + larg_t
y2_trave = trave1.getAnchor().getY() + alt_t

x_cabeca = cabeca.getCenter().getX()
y_cabeca = cabeca.getCenter().getY()
x_cabeca2 = cabeca2.getCenter().getX()
y_cabeca2 = cabeca2.getCenter().getY()

x_pe = pe.getCenter().getX()
y_pe = pe.getCenter().getY()
x_pe2 = pe2.getCenter().getX()
y_pe2 = pe2.getCenter().getY()

x_bola = c_bola.getCenter().getX()
y_bola = c_bola.getCenter().getY()

placar1 = Text(Point(x / 2 + 20, 40), "")
placar1.setStyle("bold")
placar1.setTextColor("white")
placar1.setSize(25)
placar1.draw(tela)

placar2 = Text(Point(x / 2 - 20, 40), "")
placar2.setStyle("bold")
placar2.setTextColor("white")
placar2.setSize(25)
placar2.draw(tela)

# pygame.mixer.init()
# pygame.mixer.music.load('Sons/gol.wav')

#### LOOP DO JOGO ###
tela.ligar_Buffer()
while True:
    placar1.setText(contador_gol1)
    placar2.setText(contador_gol2)
    while not (gol):
        lista = []
        
        # Handle keyboard input
        keyboard_input = tela.checkKey_Buffer()
        if keyboard_input:
            lista.extend(keyboard_input)
            
        # Process vision controls if enabled
        if use_vision:
            frame, players = vision_controller.process_frame()
            
            # Convert Player 1 controls to key inputs
            if players[1]["movement"] == "left":
                lista.append("a")
            elif players[1]["movement"] == "right":
                lista.append("d")
            if players[1]["jump"] == "jumping":
                lista.append("w")
            if players[1]["kick"] == "kicking":
                lista.append("space")
                
            # Convert Player 2 controls to key inputs
            if players[2]["movement"] == "left":
                lista.append("Left")
            elif players[2]["movement"] == "right":
                lista.append("Right")
            if players[2]["jump"] == "jumping":
                lista.append("Up")
            if players[2]["kick"] == "kicking":
                lista.append("Return")

        update()

        colisao_cabeca = math.hypot((x_cabeca - x_bola), (y_cabeca - y_bola))
        colisao_pe = math.hypot((x_pe - x_bola), (y_pe - y_bola))

        colisao_cabeca2 = math.hypot((x_cabeca2 - x_bola), (y_cabeca2 - y_bola))
        colisao_pe2 = math.hypot((x_pe2 - x_bola), (y_pe2 - y_bola))

        if (not (y_bola + raio <= y1_trave and x_bola >= x1_trave2)) and (
            not (y_bola + raio <= y1_trave and x_bola <= x2_trave1)
        ):
            if y_bola + raio < chao:
                if vely_bola < 12:
                    vely_bola += 0.4
                if y_bola + raio + vely_bola > chao:
                    vely_bola = chao - (y_bola + raio)
            else:
                if not (vely_bola <= 3):
                    vely_bola = (vely_bola * -0.7) // 1
                else:
                    vely_bola = 0
            cont_trave = 0
        else:
            if y_bola + raio < y1_trave:
                if vely_bola < 12:
                    vely_bola += 0.4
                if y_bola + raio + vely_bola > y1_trave:
                    vely_bola = y1_trave - (y_bola + raio)
            cont_trave += 1
            if cont_trave >= 60:
                if x_bola > x / 2:
                    bola.move(-1, 0)
                    c_bola.move(-1, 0)
                else:
                    bola.move(1, 0)
                    c_bola.move(1, 0)

        if y_bola + raio > chao:
            c_bola.move(0, chao - (y_bola + raio))
            bola.move(0, chao - (y_bola + raio))

        if y_bola + raio == chao:
            if velx_bola > 0:
                velx_bola -= atrito
            if velx_bola < 0:
                velx_bola += atrito

        if colisao_cabeca <= 80:
            if x_bola - raio >= x_cabeca + raio_cabeca:
                if (
                    (x_cabeca - raio_cabeca)
                    <= (x_bola - raio + velx_bola)
                    <= (x_cabeca + raio_cabeca)
                ):
                    velx_bola = (x_cabeca + raio_cabeca) - (x_bola - raio)

            if not (x_bola == x_cabeca):
                a_cabeca = (y_cabeca - y_bola) / (x_cabeca - x_bola)
                teta_cabeca = math.atan(a_cabeca)
            else:
                teta_cabeca = 0

            if not (x_bola == x_pe):
                a_pe = (y_pe - y_bola) / (x_pe - x_bola)
                teta_pe = math.atan(a_pe)
            else:
                teta_pe = 0

        if colisao_cabeca2 <= 80:

            if x_bola + raio <= x_cabeca2 - raio_cabeca:
                if (
                    (x_cabeca2 - raio_cabeca)
                    <= (x_bola + raio + velx_bola)
                    <= (x_cabeca2 + raio_cabeca)
                ):
                    velx_bola = (x_cabeca2 - raio_cabeca) - (x_bola + raio)

            if not (x_bola == x_pe2):
                a_pe2 = (y_pe2 - y_bola) / (x_pe2 - x_bola)
                teta_pe2 = math.atan(a_pe2)
            else:
                teta_pe2 = 0

            if not (x_bola == x_cabeca2):
                a_cabeca2 = (y_cabeca2 - y_bola) / (x_cabeca2 - x_bola)
                teta_cabeca2 = math.atan(a_cabeca2)
            else:
                teta_cabeca2 = 0

        if not (2 * raio >= colisao_cabeca and 2 * raio >= colisao_pe):
            if 2 * raio >= colisao_pe:  ### COLISÃO COM O PÉ ###
                if chute:
                    vely_bola = (2.8 * vel * math.sin(teta_pe)) // 1
                    velx_bola = (1.2 * vel * math.cos(teta_pe)) // 1
                else:
                    if y_pe <= y_bola and x_pe >= x_bola:
                        velx_bola = (vel * math.cos(teta_pe)) // -1
                        vely_bola = (vel * math.sin(teta_pe)) // -1
                    else:
                        velx_bola = (vel * math.cos(teta_pe)) // 1
                        vely_bola = (vel * math.sin(teta_pe)) // 1

                if y_bola + raio + vely_bola > chao:
                    vely_bola = chao - (y_bola + raio)
            if not (chute):
                if (
                    2 * (raio_cabeca - 8) >= colisao_cabeca
                ):  ### COLISAO COM A CABEÇA ###
                    if (y_cabeca <= y_bola and x_cabeca >= x_bola) or (
                        y_cabeca >= y_bola and x_cabeca >= x_bola
                    ):
                        velx_bola = (1.2 * vel * math.cos(teta_cabeca)) // -1
                        vely_bola = (2 * vel * math.sin(teta_cabeca)) // -1
                    else:
                        velx_bola = (vel * math.cos(teta_cabeca)) // 1
                        vely_bola = (vel * math.sin(teta_cabeca)) // 1
            else:
                if raio >= colisao_cabeca:  ### COLISAO COM A CABEÇA ###
                    if (y_cabeca <= y_bola and x_cabeca >= x_bola) or (
                        y_cabeca >= y_bola and x_cabeca >= x_bola
                    ):
                        velx_bola = (vel * math.cos(teta_cabeca)) // -1
                        vely_bola = (vel * math.sin(teta_cabeca)) // -1
                    else:
                        velx_bola = (vel * math.cos(teta_cabeca)) // 1
                        vely_bola = (vel * math.sin(teta_cabeca)) // 1

        else:
            velx_bola = (vel * math.cos(teta_pe)) // 1
            vely_bola = (vel * math.sin(teta_pe)) // 1

        if not (2 * raio >= colisao_cabeca2 and 2 * raio >= colisao_pe2):
            if 2 * raio >= colisao_pe2:  ### COLISÃO COM O PÉ ###
                if chute2:
                    vely_bola = (1.2 * vel * math.cos(teta_pe2)) // -1
                    velx_bola = (vel * math.cos(teta_pe2)) // -1
                else:
                    if y_pe2 <= y_bola and x_pe2 >= x_bola:
                        velx_bola = (vel * math.cos(teta_pe2)) // -1
                        vely_bola = (vel * math.sin(teta_pe2)) // -1
                    else:
                        velx_bola = (vel * math.cos(teta_pe2)) // 1
                        vely_bola = (vel * math.sin(teta_pe2)) // 1

                if y_bola + raio + vely_bola > chao:
                    vely_bola = chao - (y_bola + raio)
            if not (chute2):
                if (
                    2 * (raio_cabeca - 8) >= colisao_cabeca2
                ):  ### COLISAO COM A CABEÇA ###
                    if (y_cabeca2 <= y_bola and x_cabeca2 >= x_bola) or (
                        y_cabeca2 >= y_bola and x_cabeca2 >= x_bola
                    ):
                        velx_bola = (vel * math.cos(teta_cabeca2)) // -1
                        vely_bola = (vel * math.sin(teta_cabeca2)) // -1
                    else:
                        velx_bola = (vel * math.cos(teta_cabeca2)) // 1
                        vely_bola = (vel * math.sin(teta_cabeca2)) // 1
                else:
                    if raio >= colisao_cabeca2:  ### COLISAO COM A CABEÇA ###
                        if (y_cabeca2 <= y_bola and x_cabeca2 >= x_bola) or (
                            y_cabeca2 >= y_bola and x_cabeca2 >= x_bola
                        ):
                            velx_bola = (vel * math.cos(teta_cabeca2)) // -1
                            vely_bola = (vel * math.sin(teta_cabeca2)) // -1
                        else:
                            velx_bola = (vel * math.cos(teta_cabeca2)) // 1
                            vely_bola = (vel * math.sin(teta_cabeca2)) // 1

        else:
            velx_bola = (vel * math.cos(teta_pe2)) // -1
            vely_bola = (vel * math.sin(teta_pe2)) // -1

        bola.move(2 * velx_bola // 1, 2 * vely_bola // 1)
        c_bola.move(2 * velx_bola // 1, 2 * vely_bola // 1)

        if len(lista) > 0:
            if ("Left" in lista) and (x_cabeca2 - raio_cabeca > 0):
                boneco2.move(-vel, 0)
                cabeca2.move(-vel, 0)
                pe2.move(-vel, 0)

            if ("Right" in lista) and (x_cabeca2 + raio_cabeca < x):
                boneco2.move(vel, 0)
                cabeca2.move(vel, 0)
                pe2.move(vel, 0)

            if ("a" in lista) and (x_cabeca - raio_cabeca > 0):
                boneco.move(-vel, 0)
                cabeca.move(-vel, 0)
                pe.move(-vel, 0)

            if ("d" in lista) and (x_cabeca + raio_cabeca < x):
                boneco.move(vel, 0)
                cabeca.move(vel, 0)
                pe.move(vel, 0)

        if not (chute):
            if len(lista) > 0 and ("space" in lista):
                chute = True
        else:
            if cont_chute // 1 == 0:
                pe.move(0, 8)
                boneco.undraw()
                boneco = Image(
                    Point(boneco.getAnchor().getX(), boneco.getAnchor().getY()),
                    "../assets/Imagens/LeftChar_kick1.gif",
                )
                boneco.draw(tela)
            if cont_chute // 8 == 1:
                pe.move(2, -2)
                boneco.undraw()
                boneco = Image(
                    Point(boneco.getAnchor().getX(), boneco.getAnchor().getY()),
                    "../assets/Imagens/LeftChar_kick2.gif",
                )
                boneco.draw(tela)
            cont_chute += 1
            if cont_chute == 15:
                boneco.undraw()
                boneco = Image(
                    Point(boneco.getAnchor().getX(), boneco.getAnchor().getY()),
                    "../assets/Imagens/LeftChar.gif",
                )
                boneco.draw(tela)
                cont_chute = 0
                pe.move(-14, 6)
                chute = False

        if not (chute2):
            if len(lista) > 0 and ("Return" in lista):
                chute2 = True
        else:
            if cont_chute2 // 1 == 0:
                pe2.move(0, 8)
                boneco2.undraw()
                boneco2 = Image(
                    Point(boneco2.getAnchor().getX(), boneco2.getAnchor().getY()),
                    "../assets/Imagens/RightChar_kick1.gif",
                )
                boneco2.draw(tela)
            if cont_chute2 // 8 == 1:
                pe2.move(-2, -2)
                boneco2.undraw()
                boneco2 = Image(
                    Point(boneco2.getAnchor().getX(), boneco2.getAnchor().getY()),
                    "../assets/Imagens/RightChar_kick2.gif",
                )
                boneco2.draw(tela)
            cont_chute2 += 1
            if cont_chute2 == 15:
                boneco2.undraw()
                boneco2 = Image(
                    Point(boneco2.getAnchor().getX(), boneco2.getAnchor().getY()),
                    "../assets/Imagens/RightChar.gif",
                )
                boneco2.draw(tela)
                cont_chute2 = 0
                pe2.move(14, 6)
                chute2 = False

        ##### PULO BONECO2 ####
        if not (pulando):
            if len(lista) > 0 and ("w" in lista):
                pulando = True
        else:
            if cont <= 24:
                if cont // 12 == 0:
                    boneco.move(0, -dy)
                    cabeca.move(0, -dy)
                    pe.move(0, -dy)
                    dy += 1
                if cont // 12 == 1:
                    dy -= 1
                    boneco.move(0, dy)
                    cabeca.move(0, dy)
                    pe.move(0, dy)
                cont += 1
            else:
                pulando = False
                cont = 0

        if not (pulando2):
            if len(lista) > 0 and ("Up" in lista):
                pulando2 = True
        else:
            if cont2 <= 24:
                if cont2 // 12 == 0:
                    boneco2.move(0, -dy2)
                    cabeca2.move(0, -dy2)
                    pe2.move(0, -dy2)
                    dy2 += 1
                if cont2 // 12 == 1:
                    dy2 -= 1
                    boneco2.move(0, dy2)
                    cabeca2.move(0, dy2)
                    pe2.move(0, dy2)
                cont2 += 1
            else:
                pulando2 = False
                cont2 = 0

        if x_bola + raio > x:
            if velx_bola > 0:
                velx_bola = (velx_bola * -1) * 0.7
        if x_bola - raio < 0:
            if velx_bola < 0:
                velx_bola = (velx_bola * -1) * 0.7
        if y_bola - raio < 0:
            if vely_bola < 0:
                vely_bola = (vely_bola * -1) * 0.7

        x_boneco = boneco.getAnchor().getX()
        y_boneco = boneco.getAnchor().getY()
        x_boneco2 = boneco2.getAnchor().getX()
        y_boneco2 = boneco2.getAnchor().getY()

        x_cabeca = cabeca.getCenter().getX()
        y_cabeca = cabeca.getCenter().getY()
        x_cabeca2 = cabeca2.getCenter().getX()
        y_cabeca2 = cabeca2.getCenter().getY()

        x_pe = pe.getCenter().getX()
        y_pe = pe.getCenter().getY()
        x_pe2 = pe2.getCenter().getX()
        y_pe2 = pe2.getCenter().getY()

        x_bola = c_bola.getCenter().getX()
        y_bola = c_bola.getCenter().getY()

        x_t2 = col_trave2.getCenter().getX()
        y_t2 = col_trave2.getCenter().getY()

        x_t1 = col_trave1.getCenter().getX()
        y_t1 = col_trave1.getCenter().getY()

        if x_bola > 900:
            if not (x_bola == x_t2):
                a_t2 = (y_t2 - y_bola) / (x_t2 - x_bola)
                teta_t2 = math.atan(a_t2)
            else:
                teta_t2 = 0
            if y_bola + raio <= y1_trave and x_bola >= x1_trave2:
                if y_bola + raio + vely_bola > y1_trave - 5:
                    if vely_bola < 3:
                        vely_bola = 0
                    vely_bola = (vely_bola * -0.8) // 1

            if raio >= math.hypot((x_t2 - x_bola), (y_t2 - y_bola)):
                velx_bola = (vel * math.cos(teta_t2)) // -1
                vely_bola = (vel * math.sin(teta_t2)) // -1

            if (x_bola >= x1_trave2) and (y_bola - raio >= y1_trave):
                # pygame.mixer.music.play()
                gol = True
                lado = "right"

        elif x_bola < 300:
            if not (x_bola == x_t1):
                a_t1 = (y_t1 - y_bola) / (x_t1 - x_bola)
                teta_t1 = math.atan(a_t1)
            else:
                teta_t1 = 0
            if y_bola + raio <= y1_trave and x_bola <= x2_trave1:
                if y_bola + raio + vely_bola > y1_trave - 5:
                    if vely_bola < 3:
                        vely_bola = 0
                    vely_bola = (vely_bola * -0.8) // 1

            if raio >= math.hypot((x_t1 - x_bola), (y_t1 - y_bola)):
                velx_bola = (vel * math.cos(teta_t1)) // 1
                vely_bola = (vel * math.sin(teta_t1)) // 1

            if (x_bola <= x2_trave1) and (y_bola - raio >= y1_trave):
                # pygame.mixer.music.play()
                gol = True
                lado = "left"

        time.sleep(0.018)
        tela.update()

    if lado == "left":
        contador_gol1 += 1
    elif lado == "right":
        contador_gol2 += 1

    gol = False
    pulando = False
    pulando2 = False
    dy = 1
    dy2 = 1
    cont = 0
    cont2 = 0
    cont_chute = 0
    cont_chute2 = 0
    bola.move(x / 2 - x_bola, 100 - y_bola)
    c_bola.move(x / 2 - x_bola, 100 - y_bola)
    boneco.move(300 - x_boneco, 503 - y_boneco)
    cabeca.move(300 - x_cabeca, 491 - y_cabeca)
    pe.move(300 - x_pe, 529 - y_pe)
    boneco2.move(900 - x_boneco2, 503 - y_boneco2)
    cabeca2.move(900 - x_cabeca2, 491 - y_cabeca2)
    pe2.move(900 - x_pe2, 529 - y_pe2)
    velx_bola = 0
    vely_bola = 0

    time.sleep(1)
