################################################
# Miscellaneous configuration settings
################################################

LOCKED_SCREEN_SIZE = False  # If True, screen size is fixed to default values. If False, screen size is set to user's display size.
XLIM = 1540  # Screen width (viewport)
YLIM = 850   # Screen height (viewport)

# World size multiplier (world is this many times larger than screen)
WORLD_SIZE_MULTIPLIER = 2.0  # 2x width and 2x height = 4x total area
WORLD_WIDTH = XLIM * WORLD_SIZE_MULTIPLIER   # Will be recalculated after screen size is set
WORLD_HEIGHT = YLIM * WORLD_SIZE_MULTIPLIER  # Will be recalculated after screen size is set

# Camera/viewport offset (top-left corner of visible area in world coordinates)
camera_x = 0.0
camera_y = 0.0
CAMERA_SPEED = 15  # Pixels per frame when moving camera

# Zoom settings
zoom_level = 1.0       # Current zoom (1.0 = default, >1 = zoomed in, <1 = zoomed out)
ZOOM_MIN = 1.0         # Recalculated at startup so full world fits on screen
ZOOM_MAX = 4.0         # Maximum zoom in
ZOOM_STEP = 0.1        # Zoom change per scroll tick / key press

NUM_PREDATORS = 5
NUM_PREYS = 55
CHUNKSIZE = 10  # 10x10 pixels

# Grass total tracking (updated incrementally for performance)
total_grass = 0.0

################################################
# Evolution settings
################################################

MUTATION_RATE = 0.05  # 5% mutation - increment is ±(MUTATION_RATE * base_value)

################################################
# PREDATOR behavior
################################################

PRED_AVOID_PRED = True
PREDATOR_REPRODUCTION_RATE = 0.000 # conditionless reproduction rate
PREDATOR_HIGH_AGE_HEALTH = 0.95 # daily survival chance for high age predators
PREDATOR_MATING_CLOSE_DISTANCE = 10  # Distance at which mating occurs (both predators close enough)

# Predator traits that can change evolutionarily
PREDATOR_SPEED = 3.15
PREDATOR_PREDATOR_AVOID_DISTANCE = 140 # distance to avoid other predators
PREDATOR_SMELL_DISTANCE = 200 # distance to smell prey
PREDATOR_MAX_FOOD = 500
PREDATOR_FOOD_GAIN_PER_KILL = 350
PREDATOR_REGULAR_ENERGY_COST = 0.7
PREDATOR_HUNTING_ENERGY_COST = 0.9 
PREDATOR_STARV_BORDER = 0.2   # x% of max food
PREDATOR_MAX_AGE = 1200 # max age in rounds
PREDATOR_MATING_SEARCH_DISTANCE = 500  # Distance to search for potential mates

################################################
# PREY behavior
################################################

PREY_REPRODUCTION_RATE = 0.002 # conditionless reproduction rate
PREY_REGULAR_ENERGY_COST = 0.95
PREY_MATING_CLOSE_DISTANCE = 5  # Distance at which mating occurs (both prey close enough)

# Prey traits that can change evolutionarily
PREY_SPEED = 3
PREY_FEAR_DISTANCE = 20
PREY_MATING_SIMULATION = True  # If True, complexer mating behavior is enabled, otherwise simply spawns new prey at reproduction rate
PREY_MATING_SEARCH_DISTANCE = 500  # Distance to search for potential mates
PREY_MAX_FOOD = 200
PREY_FOOD_GAIN_PER_GRASS = 0.15 # x% of grass amount of the chunk the prey is in
PREY_STARV_BORDER = 0.2  # x% of max food
PREY_FLEE_ENERGY_COST = 1.00
PREY_MAX_AGE = 900 # max age in rounds
PREY_HIGH_AGE_HEALTH = 0.95 # daily survival chance for high age preys

################################################
# Grass
################################################

DEFAULT_GRASS_AMOUNT = 6
GRASS_MAX_AMOUNT = 10
GRASS_GROWTH_RATE = 0.005
GRASS_COLOR_MAX = 90

################################################
# Statistics display
################################################

STATS_FONT_SIZE = 27
STATS_X_OFFSET = 20
STATS_Y_OFFSET = 20
STATS_LINE_HEIGHT = 20

UPDATE_SPEED_POPULATION_GRAPH = 30
UPDATE_SPEED_PHASE_GRAPH = 30
UPDATE_SPEED_TABLE = 70

PHASE_DIAGRAM_LIMIT = 20000
POPULATION_GRAPH_LIMIT = 20000

################################################
# Simulation
################################################
    
FPS = 120 # Maximum allowed frames per second
STATS_FPS_PAUSED = 60
STATS_FPS_UNLIMITED = 0 # 0 means unlimited in pygame clock.tick()

# FPS counter (updates every 2 seconds for lightweight performance)
current_fps = 0.0  # Displayed FPS value
FPS_UPDATE_INTERVAL = 2.0  # Seconds between FPS updates

# Cached average traits for manual spawning (preserved when a population dies out)
last_pred_trait_avgs: dict = {}
last_prey_trait_avgs: dict = {}

# Snapshot of trait values at simulation start (never changes mid-run)
start_pred_traits: dict = {}
start_prey_traits: dict = {}

# Maps settings-window display names to SoA trait attribute names
SETTINGS_TO_PRED_TRAIT: dict = {
    "Predator Speed": "speed",
    "Predator Avoidance Distance": "predator_avoid_distance",
    "Predator Smell Distance": "smell_distance",
    "Predator Health": "max_food",
    "Predator Food Gain per Kill": "food_gain_per_kill",
    "Predator Regular Energy Cost": "regular_energy_cost",
    "Predator Hunting Energy Cost": "hunting_energy_cost",
    "Predator Starvation Border": "starv_border",
    "Predator Max Age": "max_age",
    "Predator High Age Health": "high_age_health",
}
SETTINGS_TO_PREY_TRAIT: dict = {
    "Prey Speed": "speed",
    "Prey Fear Distance": "fear_distance",
    "Prey Food Gain per Grass": "food_gain_per_grass",
    "Prey Health": "max_food",
    "Prey Starvation Border": "starv_border",
    "Prey Flee Energy Cost": "flee_energy_cost",
    "Prey Max Age": "max_age",
    "Prey High Age Health": "high_age_health",
}

################################################
# Global statistics counters
################################################

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

################################################
# Button layout constants for the right side of the screen
################################################

BUTTON_WIDTH = 80
BUTTON_HEIGHT = 30
BUTTON_X_OFFSET = 100
BUTTON_Y_START = 10
BUTTON_Y_GAP = 40

################################################
# Button click effects
################################################

BUTTON_CLICK_SOUND_ENABLED = True  # Set to False to disable click sounds
BUTTON_CLICK_VISUAL_EFFECT = True  # Set to False to disable visual effects
BUTTON_CLICK_DURATION = 100  # milliseconds for the visual effect to last

################################################
# Font
################################################

FONT_COLORS = (255, 255, 255)  # White

################################################
# Global default settings dictionary (standard values)
################################################

default_settings = {
    "Predator Speed": PREDATOR_SPEED,
    "Predator Avoidance Distance": PREDATOR_PREDATOR_AVOID_DISTANCE,
    "Predator Smell Distance": PREDATOR_SMELL_DISTANCE,
    "Predator Reproduction Rate": PREDATOR_REPRODUCTION_RATE,
    "Predator Health": PREDATOR_MAX_FOOD,
    "Predator Food Gain per Kill": PREDATOR_FOOD_GAIN_PER_KILL,
    "Predator Regular Energy Cost": PREDATOR_REGULAR_ENERGY_COST,
    "Predator Hunting Energy Cost": PREDATOR_HUNTING_ENERGY_COST,
    "Predator Starvation Border": PREDATOR_STARV_BORDER,
    "Predator Max Age": PREDATOR_MAX_AGE,
    "Predator High Age Health": PREDATOR_HIGH_AGE_HEALTH,

    "Prey Speed": PREY_SPEED,
    "Prey Fear Distance": PREY_FEAR_DISTANCE,
    "Prey Reproduction Rate": PREY_REPRODUCTION_RATE,
    "Prey Food Gain per Grass": PREY_FOOD_GAIN_PER_GRASS,
    "Prey Health": PREY_MAX_FOOD,
    "Prey Starvation Border": PREY_STARV_BORDER,
    "Prey Regular Energy Cost": PREY_REGULAR_ENERGY_COST,
    "Prey Flee Energy Cost": PREY_FLEE_ENERGY_COST,
    "Prey Max Age": PREY_MAX_AGE,
    "Prey High Age Health": PREY_HIGH_AGE_HEALTH,

    "Grass Growth Rate": GRASS_GROWTH_RATE,
    "Grass max per Field": GRASS_MAX_AMOUNT,
    "Grass Start Value": DEFAULT_GRASS_AMOUNT,

    "FPS": FPS
}

################################################
# Global statistics history dictionary for charting
################################################

stats_history = {
    "Prey Count": [],
    "Predator Count": [],
    "Grass Total": [],
    "Prey deceased": [],
    "Predator deceased": [],
    "Prey born": [],
    "Predator born": [],
    "Rounds passed": [],
    "Prey dead by hunting": [],
    "Prey dead by starvation": [],
    "Predator dead by starvation": [],
    "Prey dead by age": [],
    "Predator dead by age": [],
}