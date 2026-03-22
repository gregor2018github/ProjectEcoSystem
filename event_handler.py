################################################
# Imports
################################################

from __future__ import annotations
import pygame
import random
import config
import os
from animal_arrays import PredatorArrays, PreyArrays
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
    """Initialize the sound system and load click sound."""
    global click_sound
    if config.BUTTON_CLICK_SOUND_ENABLED:
        pygame.mixer.init()
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
    pred_arrays: PredatorArrays,
    prey_arrays: PreyArrays,
    grass: GrassArray,
    screen: pygame.Surface,
    running: bool,
    stopped: bool,
    hover_animal,
    locked_animal,
    all_views: list,
) -> tuple:
    """Process a single pygame event and update simulation state.

    Args:
        event: The pygame event to process.
        pred_arrays: PredatorArrays SoA.
        prey_arrays: PreyArrays SoA.
        grass: GrassArray for grass management.
        screen: The pygame display surface.
        running: Whether the simulation is running.
        stopped: Whether the simulation is paused.
        hover_animal: Currently hovered animal view, or None.
        locked_animal: Currently locked/selected animal view, or None.
        all_views: Combined list of all animal views for hover detection.

    Returns:
        A tuple containing:
            - running, stopped, pred_arrays, prey_arrays, grass,
              event_handled_by_button, hover_animal, locked_animal
    """
    event_handled_by_button = False
    original_event_type = event.type

    if event.type == pygame.QUIT:
        running = False

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            stopped = not stopped
            play_click_sound()
            event_handled_by_button = True

    if event.type == pygame.MOUSEMOTION:
        current_hover = None
        for animal in reversed(all_views):
            if animal.alive and animal.get_screen_rect().collidepoint(event.pos):
                current_hover = animal
                break
        hover_animal = current_hover

    if original_event_type == pygame.MOUSEBUTTONDOWN:
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

            event_handled_by_button = True

            if action == "restart":
                pred_arrays, prey_arrays, grass = setup_simulation()
                play_click_sound()
                stopped = False
            elif action == "resume":
                play_click_sound()
                stopped = False
            elif action == "cancel":
                play_click_sound()
                stopped = False
        elif add_pred_button_rect.collidepoint(mouse_pos):
            register_button_click(add_pred_button_rect)
            play_click_sound()
            spawn_x = random.uniform(config.camera_x, config.camera_x + config.XLIM)
            spawn_y = random.uniform(config.camera_y, config.camera_y + config.YLIM)
            pred_arrays.add_default(spawn_x, spawn_y)
            event_handled_by_button = True
        elif rem_pred_button_rect.collidepoint(mouse_pos):
            register_button_click(rem_pred_button_rect)
            play_click_sound()
            pred_arrays.remove_random()
            event_handled_by_button = True
        elif add_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(add_prey_button_rect)
            play_click_sound()
            spawn_x = random.uniform(config.camera_x, config.camera_x + config.XLIM)
            spawn_y = random.uniform(config.camera_y, config.camera_y + config.YLIM)
            prey_arrays.add_default(spawn_x, spawn_y)
            event_handled_by_button = True
        elif rem_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(rem_prey_button_rect)
            play_click_sound()
            prey_arrays.remove_random()
            event_handled_by_button = True
        elif stats_button_rect.collidepoint(mouse_pos):
            register_button_click(stats_button_rect)
            play_click_sound()
            stats_win = StatisticsWindow(pred_arrays, prey_arrays, grass, not stopped)
            stopped = not stats_win.run()
            pygame.display.set_caption("Simulation")
            event_handled_by_button = True

        # Handle locking/unlocking based on non-button clicks
        if not event_handled_by_button:
            clicked_on_animal_this_click = False
            for animal_check in all_views:
                if animal_check.alive and animal_check.get_screen_rect().collidepoint(event.pos):
                    locked_animal = animal_check
                    clicked_on_animal_this_click = True
                    break

            if not clicked_on_animal_this_click:
                locked_animal = None

    return running, stopped, pred_arrays, prey_arrays, grass, event_handled_by_button, hover_animal, locked_animal
