# IMPORTS
import random
import pygame
from config import *                 # CONSTANTS
from animals import Predator, Prey   # Animal classes
from grass import Grass              # Grass class
from simulation import setup_simulation, update_simulation              # Simulation functions
from ui import draw_simulation, settings_menu, show_statistics_window   # UI functions

# MAIN 

def main():
    pygame.init()
    # Get user's display info and compute window dimensions
    info = pygame.display.Info()
    screen_width = min(2500, info.current_w)
    screen_height = min(1300, info.current_h)
    # Update globals so rest of simulation uses these dimensions
    global XLIM, YLIM
    XLIM = screen_width
    YLIM = screen_height

    screen = pygame.display.set_mode((XLIM, YLIM))
    clock = pygame.time.Clock()
    predators, preys, grass = setup_simulation()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Handle click on Stop button
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                button_x = XLIM - BUTTON_X_OFFSET
                settings_button_rect = pygame.Rect(button_x, BUTTON_Y_START, BUTTON_WIDTH, BUTTON_HEIGHT)
                stop_button_rect = pygame.Rect(button_x, BUTTON_Y_START + BUTTON_Y_GAP, BUTTON_WIDTH, BUTTON_HEIGHT)
                add_pred_button_rect = pygame.Rect(button_x, BUTTON_Y_START + 2 * BUTTON_Y_GAP, BUTTON_WIDTH, BUTTON_HEIGHT)
                add_prey_button_rect = pygame.Rect(button_x, BUTTON_Y_START + 3 * BUTTON_Y_GAP, BUTTON_WIDTH, BUTTON_HEIGHT)
                stats_button_rect = pygame.Rect(button_x, BUTTON_Y_START + 4 * BUTTON_Y_GAP, BUTTON_WIDTH, BUTTON_HEIGHT)
                if settings_button_rect.collidepoint(mouse_pos):
                    action, new_settings = settings_menu(screen)
                    # Save new settings to global simulation parameters
                    global PREY_MAX_FOOD, PREDATOR_MAX_FOOD, PREY_REPRODUCTION_RATE, PREDATOR_REPRODUCTION_RATE, GRASS_GROWTH_RATE, GRASS_MAX_AMOUNT, PREY_FEAR_DISTANCE, PREY_SPEED, PREDATOR_SPEED
                    PREY_MAX_FOOD = new_settings["Prey Health"]
                    PREDATOR_MAX_FOOD = new_settings["Predator Health"]
                    PREY_REPRODUCTION_RATE = new_settings["Prey Reproduction Rate"]
                    PREDATOR_REPRODUCTION_RATE = new_settings["Predator Reproduction Rate"]
                    GRASS_GROWTH_RATE = new_settings["Grass Growth Rate"]
                    GRASS_MAX_AMOUNT = new_settings["Max Grass per Field"]
                    PREY_FEAR_DISTANCE = new_settings["Prey Fear Distance"]
                    PREY_SPEED = new_settings["Prey Speed"]
                    PREDATOR_SPEED = new_settings["Predator Speed"]
                    
                    if action == "restart":
                        predators, preys, grass = setup_simulation()
                    elif action == "resume":
                        # Continue with updated settings
                        pass
                elif stop_button_rect.collidepoint(mouse_pos):
                    running = False
                elif add_pred_button_rect.collidepoint(mouse_pos):
                    predators.append(Predator(random.uniform(0, XLIM), random.uniform(0, YLIM)))
                elif add_prey_button_rect.collidepoint(mouse_pos):
                    preys.append(Prey(random.uniform(0, XLIM), random.uniform(0, YLIM)))
                # NEW: Handle click on Statistics button
                elif stats_button_rect.collidepoint(mouse_pos):
                    show_statistics_window(predators, preys, grass)

        # Calculate simulation step
        update_simulation(predators, preys, grass)
        # Render simulation state only after update
        draw_simulation(screen, predators, preys, grass)
        clock.tick(FPS)  # 30 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
