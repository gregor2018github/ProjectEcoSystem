###############################################
# Imports
###############################################

from __future__ import annotations
import pygame
import os
import config
from animal_arrays import build_predator_views, build_prey_views, find_view_by_uid
from simulation import setup_simulation, update_simulation
from ui import draw_simulation
from event_handler import process_event, initialize_sounds
from start_screen import show_start_screen

###############################################
# Main
###############################################

def main() -> None:
    """Main entry point for the ecosystem simulation.

    Initializes pygame, sets up the simulation, and runs the main game loop.
    Handles events, updates simulation state when not paused, and renders
    each frame. Supports camera movement with WASD and arrow keys.
    """
    # Prevent simulation from minimizing when losing focus in fullscreen
    os.environ['SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS'] = '0'

    pygame.init()

    # Get desktop resolution before any window is created
    info = pygame.display.Info()
    desktop_w = info.current_w
    desktop_h = info.current_h

    # Show start screen and get user configuration
    start_config = show_start_screen()

    # Apply user-selected settings to config
    config.WORLD_SIZE_MULTIPLIER = start_config["WORLD_SIZE_MULTIPLIER"]
    config.FPS = start_config["FPS"]
    config.NUM_PREYS = start_config["NUM_PREYS"]
    config.NUM_PREDATORS = start_config["NUM_PREDATORS"]

    initialize_sounds()

    # set the size of the game field, either by locked values or by display size
    if not config.LOCKED_SCREEN_SIZE:
        config.XLIM = desktop_w
        config.YLIM = desktop_h
        screen = pygame.display.set_mode((config.XLIM, config.YLIM), pygame.FULLSCREEN)
    else:
        screen = pygame.display.set_mode((config.XLIM, config.YLIM))

    # Calculate world size based on screen size (2x width and 2x height = 4x area)
    config.WORLD_WIDTH = config.XLIM * config.WORLD_SIZE_MULTIPLIER
    config.WORLD_HEIGHT = config.YLIM * config.WORLD_SIZE_MULTIPLIER

    # Initialize camera position (start at top-left)
    config.camera_x = 0.0
    config.camera_y = 0.0

    clock = pygame.time.Clock()
    pred_arrays, prey_arrays, grass = setup_simulation()

    running = True
    stopped = False
    hover_animal = None  # Stores the view currently being hovered over
    current_mouse_pos = (0, 0)
    locked_animal = None  # Stores the view whose info window is locked
    locked_uid = None  # Persistent UID for locked animal

    # FPS counter variables (lightweight, updates every 2 seconds)
    fps_frame_count = 0
    fps_timer = 0.0

    while running:
        # Track frame time for FPS calculation
        dt = clock.get_time() / 1000.0  # Delta time in seconds
        fps_frame_count += 1
        fps_timer += dt

        # Update displayed FPS every 2 seconds
        if fps_timer >= config.FPS_UPDATE_INTERVAL:
            config.current_fps = fps_frame_count / fps_timer
            fps_frame_count = 0
            fps_timer = 0.0

        current_mouse_pos = pygame.mouse.get_pos()

        # Build view lists for UI (hover, click, draw)
        predator_views = build_predator_views(pred_arrays)
        prey_views = build_prey_views(prey_arrays)
        all_views = predator_views + prey_views

        # Resolve locked animal by UID
        if locked_uid is not None:
            locked_animal = find_view_by_uid(all_views, locked_uid)
            if locked_animal is None or not locked_animal.alive:
                locked_animal = None
                locked_uid = None
        else:
            locked_animal = None

        # Handle continuous key presses for camera movement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            config.camera_y = max(0, config.camera_y - config.CAMERA_SPEED)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            config.camera_y = min(config.WORLD_HEIGHT - config.YLIM, config.camera_y + config.CAMERA_SPEED)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            config.camera_x = max(0, config.camera_x - config.CAMERA_SPEED)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            config.camera_x = min(config.WORLD_WIDTH - config.XLIM, config.camera_x + config.CAMERA_SPEED)

        for event in pygame.event.get():
            running, stopped, pred_arrays, prey_arrays, grass, _, hover_animal, locked_animal = process_event(
                event, pred_arrays, prey_arrays, grass, screen, running, stopped,
                hover_animal, locked_animal, all_views
            )
            # Update locked_uid when locked_animal changes
            if locked_animal is not None:
                locked_uid = locked_animal.uid
            else:
                locked_uid = None

        # Update simulation state if not stopped
        if not stopped:
            update_simulation(pred_arrays, prey_arrays, grass)

        # Always render the simulation state
        draw_simulation(screen, predator_views, prey_views, grass, hover_animal, current_mouse_pos, locked_animal)

        clock.tick(config.FPS)  # Cap FPS

    pygame.quit()

if __name__ == "__main__":
    main()
