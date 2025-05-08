import pygame
import random
import config
import os
from animals import Predator, Prey
from simulation import setup_simulation
from ui import settings_menu, show_statistics_window, register_button_click

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

def process_event(event, predators, preys, grass, screen, running, stopped):
    if event.type == pygame.QUIT:
        running = False
    
    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_pos = event.pos
        button_x = config.XLIM - config.BUTTON_X_OFFSET
        
        exit_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        pause_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        settings_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 2 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        add_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 3 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)

        if exit_button_rect.collidepoint(mouse_pos):
            register_button_click(exit_button_rect)
            play_click_sound()
            running = False
        elif pause_button_rect.collidepoint(mouse_pos):
            register_button_click(pause_button_rect)
            play_click_sound()
            stopped = not stopped
        elif settings_button_rect.collidepoint(mouse_pos):
            register_button_click(settings_button_rect)
            play_click_sound()
            action, new_settings = settings_menu(screen)
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
        elif add_prey_button_rect.collidepoint(mouse_pos):
            register_button_click(add_prey_button_rect)
            play_click_sound()
            preys.append(Prey(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
        elif stats_button_rect.collidepoint(mouse_pos):
            register_button_click(stats_button_rect)
            play_click_sound()
            show_statistics_window(predators, preys, grass)
            # Ensure the main screen is re-established as the display mode after stats window closes
            pygame.display.set_mode((config.XLIM, config.YLIM))
            stopped = False # Resume simulation rendering

    return running, stopped, predators, preys, grass
