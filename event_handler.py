################################################
# Imports
################################################

from __future__ import annotations
import pygame
import random
import config
import os
from animals import Predator, Prey, Animal
from grass_array import GrassArray
from simulation import setup_simulation
from ui import register_button_click
from settings_window import SettingsWindow
from statistics_window import StatisticsWindow

################################################
# Sound management
################################################

# Initialize click sound
click_sound: pygame.mixer.Sound | None = None

def initialize_sounds() -> None:
    """Initialize the sound system and load click sound.
    
    Loads the click sound file from the assets folder if button click
    sounds are enabled in the configuration.
    """
    global click_sound
    if config.BUTTON_CLICK_SOUND_ENABLED:
        pygame.mixer.init()
        # Load the click sound file
        current_directory = os.path.dirname(os.path.abspath(__file__))
        sound_file_path = os.path.join(current_directory, "assets", "click.mp3")
        click_sound = pygame.mixer.Sound(sound_file_path)

def play_click_sound() -> None:
    """Play the button click sound effect if enabled and loaded."""
    if config.BUTTON_CLICK_SOUND_ENABLED and click_sound:
        pygame.mixer.Sound.play(click_sound)

################################################
# Event processing function
################################################

def process_event(
    event: pygame.event.Event,
    predators: list[Predator],
    preys: list[Prey],
    grass: GrassArray,
    screen: pygame.Surface,
    running: bool,
    stopped: bool,
    hover_animal: Animal | None,
    locked_animal: Animal | None,
    all_animals_for_hover: list[Animal]
) -> tuple[bool, bool, list[Predator], list[Prey], GrassArray, bool, Animal | None, Animal | None]:
    """Process a single pygame event and update simulation state.
    
    Handles quit events, keyboard input (space to pause), mouse motion for
    hovering over animals, and mouse clicks for buttons and animal selection.
    
    Args:
        event: The pygame event to process.
        predators: List of predator objects.
        preys: List of prey objects.
        grass: GrassArray for grass management.
        screen: The pygame display surface.
        running: Whether the simulation is running.
        stopped: Whether the simulation is paused.
        hover_animal: Currently hovered animal, or None.
        locked_animal: Currently locked/selected animal, or None.
        all_animals_for_hover: Combined list of all animals for hover detection.
    
    Returns:
        A tuple containing:
            - running: Updated running state
            - stopped: Updated paused state
            - predators: Updated predators list
            - preys: Updated preys list
            - grass: Updated GrassArray
            - event_handled_by_button: Whether a button consumed the event
            - hover_animal: Updated hover animal
            - locked_animal: Updated locked animal
    """
    event_handled_by_button = False # Initialize flag
    original_event_type = event.type # Store original event type

    if event.type == pygame.QUIT:
        running = False
    
    if event.type == pygame.KEYDOWN: # Handle key presses
        if event.key == pygame.K_SPACE: # Toggle pause/resume on Spacebar
            stopped = not stopped
            play_click_sound() # Optional: play sound for keyboard toggle
            event_handled_by_button = True # Treat as a direct control action

    if event.type == pygame.MOUSEMOTION:
        # We use event.pos for MOUSEMOTION as it's the most current for this specific event.
        # Use get_screen_rect() to check collision with screen-space mouse position
        current_hover = None # Temporary variable for this event processing
        for animal in reversed(all_animals_for_hover): 
            if animal.alive and animal.get_screen_rect().collidepoint(event.pos):
                current_hover = animal
                break # Found an animal, stop checking
        hover_animal = current_hover # Update the actual hover_animal state

    if original_event_type == pygame.MOUSEBUTTONDOWN: # Use original_event_type for clarity
        mouse_pos = event.pos
        button_x = config.XLIM - config.BUTTON_X_OFFSET
        
        exit_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        pause_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        settings_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 2 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        add_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 3 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        rem_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        rem_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 6 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 7 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)

        # Button click handling (sets event_handled_by_button to True if a button is clicked)
        if exit_button_rect.collidepoint(mouse_pos):
            register_button_click(exit_button_rect)
            play_click_sound()
            running = False
            event_handled_by_button = True
        elif pause_button_rect.collidepoint(mouse_pos):
            register_button_click(pause_button_rect)
            play_click_sound()
            stopped = not stopped
            event_handled_by_button = True
        elif settings_button_rect.collidepoint(mouse_pos):
            register_button_click(settings_button_rect)
            play_click_sound()
            settings_win = SettingsWindow(screen)
            action, new_settings = settings_win.run()

            # Save new settings to global simulation parameters
            config.PREDATOR_SPEED = new_settings["Predator Speed"]
            config.PREDATOR_PREDATOR_AVOID_DISTANCE = new_settings["Predator Avoidance Distance"]
            config.PREDATOR_SMELL_DISTANCE = new_settings["Predator Smell Distance"]
            config.PREDATOR_REPRODUCTION_RATE = new_settings["Predator Reproduction Rate"]
            config.PREDATOR_MAX_FOOD = new_settings["Predator Health"]
            config.PREDATOR_FOOD_GAIN_PER_KILL = new_settings["Predator Food Gain per Kill"]
            config.PREDATOR_REGULAR_ENERGY_COST = new_settings["Predator Regular Energy Cost"]
            config.PREDATOR_HUNTING_ENERGY_COST = new_settings["Predator Hunting Energy Cost"]
            config.PREDATOR_STARV_BORDER = new_settings["Predator Starvation Border"]
            config.PREDATOR_MAX_AGE = new_settings["Predator Max Age"]
            config.PREDATOR_HIGH_AGE_HEALTH = new_settings["Predator High Age Health"]
            
            config.PREY_SPEED = new_settings["Prey Speed"]
            config.PREY_FEAR_DISTANCE = new_settings["Prey Fear Distance"]
            config.PREY_REPRODUCTION_RATE = new_settings["Prey Reproduction Rate"]
            config.PREY_FOOD_GAIN_PER_GRASS = new_settings["Prey Food Gain per Grass"]
            config.PREY_MAX_FOOD = new_settings["Prey Health"]
            config.PREY_STARV_BORDER = new_settings["Prey Starvation Border"]
            config.PREY_REGULAR_ENERGY_COST = new_settings["Prey Regular Energy Cost"]
            config.PREY_FLEE_ENERGY_COST = new_settings["Prey Flee Energy Cost"]
            config.PREY_MAX_AGE = new_settings["Prey Max Age"]
            config.PREY_HIGH_AGE_HEALTH = new_settings["Prey High Age Health"]
            
            config.GRASS_GROWTH_RATE = new_settings["Grass Growth Rate"]
            config.GRASS_MAX_AMOUNT = new_settings["Grass max per Field"]
            config.DEFAULT_GRASS_AMOUNT = new_settings["Grass Start Value"]
            
            config.FPS = new_settings["FPS"]
            
            event_handled_by_button = True # Settings window interaction is a button interaction
            
            if action == "restart":
                predators, preys, grass = setup_simulation()
                play_click_sound()
                stopped = False # Ensure simulation runs after restart
            elif action == "resume":
                # If resuming, ensure the simulation is not stopped
                play_click_sound()
                stopped = False
            elif action == "cancel":
                # If cancelling settings changes, the simulation should also resume
                play_click_sound()
                stopped = False
            # "resume" or "cancel" action implies continuing with current/updated settings
        elif add_pred_button_rect.collidepoint(mouse_pos):
            register_button_click(add_pred_button_rect)
            play_click_sound()
            # Spawn new predator in the visible area (screen + camera offset)
            spawn_x = random.uniform(config.camera_x, config.camera_x + config.XLIM)
            spawn_y = random.uniform(config.camera_y, config.camera_y + config.YLIM)
            predators.append(Predator(spawn_x, spawn_y))
            event_handled_by_button = True
        elif rem_pred_button_rect.collidepoint(mouse_pos):
            register_button_click(rem_pred_button_rect)
            play_click_sound()
            # Remove a random predator if any exist
            if predators:
                predators.pop(random.randrange(len(predators)))
            event_handled_by_button = True
        elif add_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(add_prey_button_rect)
            play_click_sound()
            # Spawn new prey in the visible area (screen + camera offset)
            spawn_x = random.uniform(config.camera_x, config.camera_x + config.XLIM)
            spawn_y = random.uniform(config.camera_y, config.camera_y + config.YLIM)
            preys.append(Prey(spawn_x, spawn_y))
            event_handled_by_button = True
        elif rem_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(rem_prey_button_rect)
            play_click_sound()
            # Remove a random prey if any exist
            if preys:
                preys.pop(random.randrange(len(preys)))
            event_handled_by_button = True
        elif stats_button_rect.collidepoint(mouse_pos):
            register_button_click(stats_button_rect)
            play_click_sound()
            stats_win = StatisticsWindow(predators, preys, grass, not stopped)
            stopped = not stats_win.run()
            pygame.display.set_caption("Simulation")
            event_handled_by_button = True
        
        # Handle locking/unlocking based on non-button clicks
        if not event_handled_by_button: # Only process if no button was clicked
            clicked_on_animal_this_click = False
            # MOUSEBUTTONDOWN uses event.pos for click location
            # Use get_screen_rect() to check collision with screen-space mouse position
            for animal_check in all_animals_for_hover: 
                if animal_check.alive and animal_check.get_screen_rect().collidepoint(event.pos):
                    locked_animal = animal_check # Lock on this animal
                    clicked_on_animal_this_click = True
                    break 
            
            if not clicked_on_animal_this_click: # Click was not on an animal (and not on a button)
                locked_animal = None # Unlock

    return running, stopped, predators, preys, grass, event_handled_by_button, hover_animal, locked_animal
