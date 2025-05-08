import pygame
import random
import config
from animals import Predator, Prey
from simulation import setup_simulation
from ui import settings_menu, show_statistics_window

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
            running = False
        elif pause_button_rect.collidepoint(mouse_pos):
            stopped = not stopped
        elif settings_button_rect.collidepoint(mouse_pos):
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
            # "resume" or "cancel" action implies continuing with current/updated settings
        elif add_pred_button_rect.collidepoint(mouse_pos):
            predators.append(Predator(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
        elif add_prey_button_rect.collidepoint(mouse_pos):
            preys.append(Prey(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)))
        elif stats_button_rect.collidepoint(mouse_pos):
            show_statistics_window(predators, preys, grass)
            # Ensure the main screen is re-established as the display mode after stats window closes
            pygame.display.set_mode((config.XLIM, config.YLIM))


    return running, stopped, predators, preys, grass
