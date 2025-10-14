x = 1200
y = 600
vel = 7  # Increased for better control
dy2 = 1.5  # Better jump height
dy = 1.5   # Better jump height
atrito = 1/4  # Adjusted friction for better ball control
pulando = False
pulando2 = False
cont = 0
cont2 = 0
cont_pulo = 2  # Jump cycle
raio = 15
raio_cabeca = 28
larg_b = 25
alt_b = 40
velx_bola = 0
vely_bola = 5  # Strong initial fall
larg_t = 55
alt_t = 96
chute = False
chute2 = False
cont_chute = 0
cont_chute2 = 0
chao = 544  # Ground level
altura_inicial = 503  # Initial character Y position
gol = False
contador_gol1 = 0
contador_gol2 = 0
cont_trave = 0

# Jump settings
JUMP_FORCE = -18  # Increased jump force for more responsive jumps
GRAVITY = 1.0     # Standard gravity for better physics feel
MAX_JUMP_TIME = 20  # Quick but controlled jump duration

# Kick settings
KICK_FRAMES = 12  # Faster kick animation for better responsiveness
KICK_HEIGHT = 18  # Increased kick height for better ball interaction

# Movement limits - set to None to allow full field movement
PLAYER1_MAX_X = None  # Allow full field movement
PLAYER2_MIN_X = None  # Allow full field movement

# Ball physics
BALL_GRAVITY = 0.8     # More realistic ball fall
BALL_BOUNCE = 0.65    # Better bounce feel
BALL_AIR_RESISTANCE = 0.98  # Slightly reduced air resistance for smoother movement
