# CONSTANTS
XLIM = 1540
YLIM = 850
NUM_PREDATORS = 5
NUM_PREYS = 55
MAX_ANIMALS_PER_CHUNK = 10
CHUNKSIZE = 10  # 10x10 pixels

# PREDATOR behavior
PREDATOR_SPEED = 3.1
PRED_AVOID_PRED = True
PREDATOR_PREDATOR_AVOID_DISTANCE = 100
PREDATOR_MAX_FOOD = 400
PREDATOR_FOOD_GAIN_PER_KILL = 350
PREDATOR_STARV_BORDER = 0.2   # 20% of max food

# PREY behavior
PREY_SPEED = 3
PREY_FEAR_DISTANCE = 20
PREY_REPRODUCTION_RATE = 0.002
PREDATOR_REPRODUCTION_RATE = 0.000
PREY_MAX_FOOD = 200
PREY_FOOD_GAIN_PER_GRASS = 0.15 # x% of grass amount of the chunk the prey is in
PREY_STARV_BORDER = 0.2  # 20% of max food

# Grass
DEFAULT_GRASS_AMOUNT = 6
GRASS_MAX_AMOUNT = 10
GRASS_GROWTH_RATE = 0.005
GRASS_COLOR_MAX = 90

# statistics display
STATS_FONT_SIZE = 27
STATS_X_OFFSET = 20
STATS_Y_OFFSET = 20
STATS_LINE_HEIGHT = 20

# simulation
FPS = 30

# Global statistics counters
prey_deceased = 0
predator_deceased = 0
prey_born = 0
predator_born = 0
rounds_passed = 0

# Button layout constants for the right side of the screen
BUTTON_WIDTH = 80
BUTTON_HEIGHT = 30
BUTTON_X_OFFSET = 100
BUTTON_Y_START = 10
BUTTON_Y_GAP = 40

# Font
FONT_COLORS = (255, 255, 255)  # White

# Global default settings dictionary (standard values)
default_settings = {
    "Prey Health": PREY_MAX_FOOD,
    "Predator Health": PREDATOR_MAX_FOOD,
    "Prey Reproduction Rate": PREY_REPRODUCTION_RATE,
    "Predator Reproduction Rate": PREDATOR_REPRODUCTION_RATE,
    "Grass Growth Rate": GRASS_GROWTH_RATE,
    "Max Grass per Field": GRASS_MAX_AMOUNT,
    "Prey Fear Distance": PREY_FEAR_DISTANCE,
    "Prey Speed": PREY_SPEED,
    "Predator Speed": PREDATOR_SPEED
}

# Global statistics history dictionary for charting (added "Grass Total")
stats_history = {
    "Prey Count": [],
    "Predator Count": [],
    "Grass Total": [],
    "Prey deceased": [],
    "Predator deceased": [],
    "Prey born": [],
    "Predator born": [],
    "Rounds passed": []
}