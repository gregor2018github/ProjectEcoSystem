# CONSTANTS
LOCKED_SCREEN_SIZE = False  # If True, screen size is fixed to default values. If False, screen size is set to user's display size.
XLIM = 1540
YLIM = 850
NUM_PREDATORS = 5
NUM_PREYS = 55
MAX_ANIMALS_PER_CHUNK = 10
CHUNKSIZE = 10  # 10x10 pixels

# PREDATOR behavior
PREDATOR_SPEED = 3.1
PRED_AVOID_PRED = True
PREDATOR_PREDATOR_AVOID_DISTANCE = 140 # distance to avoid other predators
PREDATOR_SMELL_DISTANCE = 200 # distance to smell prey
PREDATOR_REPRODUCTION_RATE = 0.000 # conditionless reproduction rate
PREDATOR_MAX_FOOD = 500
PREDATOR_FOOD_GAIN_PER_KILL = 350
PREDATOR_REGULAR_ENERGY_COST = 0.7
PREDATOR_HUNTING_ENERGY_COST = 0.9 
PREDATOR_STARV_BORDER = 0.2   # x% of max food
PREDATOR_MAX_AGE = 1200 # max age in rounds
PREDATOR_HIGH_AGE_HEALTH = 0.95 # daily survival chance for high age predators

# PREY behavior
PREY_SPEED = 3
PREY_FEAR_DISTANCE = 20
PREY_REPRODUCTION_RATE = 0.002 # conditionless reproduction rate
PREY_MAX_FOOD = 200
PREY_FOOD_GAIN_PER_GRASS = 0.15 # x% of grass amount of the chunk the prey is in
PREY_STARV_BORDER = 0.2  # x% of max food
PREY_REGULAR_ENERGY_COST = 0.95
PREY_FLEE_ENERGY_COST = 1.00
PREY_MAX_AGE = 900 # max age in rounds
PREY_HIGH_AGE_HEALTH = 0.95 # daily survival chance for high age preys

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
prey_dead_by_starvation = 0
predator_dead_by_starvation = 0
prey_dead_by_age = 0
predator_dead_by_age = 0
prey_dead_by_hunting = 0
rounds_passed = 0

# Button layout constants for the right side of the screen
BUTTON_WIDTH = 80
BUTTON_HEIGHT = 30
BUTTON_X_OFFSET = 100
BUTTON_Y_START = 10
BUTTON_Y_GAP = 40

# Button click effects
BUTTON_CLICK_SOUND_ENABLED = True  # Set to False to disable click sounds
BUTTON_CLICK_VISUAL_EFFECT = True  # Set to False to disable visual effects
BUTTON_CLICK_DURATION = 100  # milliseconds for the visual effect to last

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