import pygame
import random
import config
import os
from animals import Predator, Prey
from simulation import setup_simulation
from ui import register_button_click
from settings_window import SettingsWindow
from statistics_window import StatisticsWindow

# Initialize click sound
click_sound = None

def initialize_sounds():
    global click_sound
    if config.BUTTON_CLICK_SOUND_ENABLED:
        pygame.mixer.init()
        # Load the click sound file
        current_directory = os.path.dirname(os.path.abspath(__file__))
        sound_file_path = os.path.join(current_directory, "assets", "click.mp3")
        click_sound = pygame.mixer.Sound(sound_file_path)

def play_click_sound():
    if config.BUTTON_CLICK_SOUND_ENABLED and click_sound:
        pygame.mixer.Sound.play(click_sound)

def process_event(event, predators, preys, grass, screen, running, stopped, hover_animal, locked_animal, all_animals_for_hover):
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
        current_hover = None # Temporary variable for this event processing
        for animal in reversed(all_animals_for_hover): 
            if animal.alive and animal.get_rect().collidepoint(event.pos): # MOUSEMOTION uses event.pos
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
        add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)

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
            config.PREY_MAX_FOOD = new_settings["Prey Health"]
            config.PREDATOR_MAX_FOOD = new_settings["Predator Health"]
            config.PREY_REPRODUCTION_RATE = new_settings["Prey Reproduction Rate"]
            config.PREDATOR_REPRODUCTION_RATE = new_settings["Predator Reproduction Rate"]
            config.GRASS_GROWTH_RATE = new_settings["Grass Growth Rate"]
            config.GRASS_MAX_AMOUNT = new_settings["Max Grass per Field"]
            config.PREY_FEAR_DISTANCE = new_settings["Prey Fear Distance"]
            config.PREY_SPEED = new_settings["Prey Speed"]
            config.PREDATOR_SPEED = new_settings["Predator Speed"]
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
            predators.append(Predator(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
            event_handled_by_button = True
        elif add_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(add_prey_button_rect)
            play_click_sound()
            preys.append(Prey(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
            event_handled_by_button = True
        elif stats_button_rect.collidepoint(mouse_pos):
            register_button_click(stats_button_rect)
            play_click_sound()
            stats_win = StatisticsWindow()
            stats_win.run()
            pygame.display.set_caption("Simulation")
            stopped = False # Resume simulation rendering
            event_handled_by_button = True
        
        # Handle locking/unlocking based on non-button clicks
        if not event_handled_by_button: # Only process if no button was clicked
            clicked_on_animal_this_click = False
            # MOUSEBUTTONDOWN uses event.pos for click location
            for animal_check in all_animals_for_hover: 
                if animal_check.alive and animal_check.get_rect().collidepoint(event.pos):
                    locked_animal = animal_check # Lock on this animal
                    clicked_on_animal_this_click = True
                    break 
            
            if not clicked_on_animal_this_click: # Click was not on an animal (and not on a button)
                locked_animal = None # Unlock

    return running, stopped, predators, preys, grass, event_handled_by_button, hover_animal, locked_animal
