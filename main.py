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

def _apply_zoom(delta: float, screen_cx: int, screen_cy: int) -> None:
    """Adjust zoom level, keeping the world point under (screen_cx, screen_cy) fixed."""
    old_zoom = config.zoom_level
    new_zoom = max(config.ZOOM_MIN, min(config.ZOOM_MAX, old_zoom + delta))
    if new_zoom == old_zoom:
        return

    # World point currently under the screen center / cursor
    world_x = screen_cx / old_zoom + config.camera_x
    world_y = screen_cy / old_zoom + config.camera_y

    config.zoom_level = new_zoom

    # Adjust camera so that same world point stays under screen_cx/screen_cy
    config.camera_x = world_x - screen_cx / new_zoom
    config.camera_y = world_y - screen_cy / new_zoom

    # Clamp camera
    max_cam_x = max(0, config.WORLD_WIDTH - config.XLIM / new_zoom)
    max_cam_y = max(0, config.WORLD_HEIGHT - config.YLIM / new_zoom)
    config.camera_x = max(0, min(max_cam_x, config.camera_x))
    config.camera_y = max(0, min(max_cam_y, config.camera_y))


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

    # Sync default_settings so "Reset to std" in the settings menu uses the start-screen values
    config.default_settings["FPS"] = config.FPS

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

    # Set minimum zoom so the entire world fits on screen
    config.ZOOM_MIN = min(config.XLIM / config.WORLD_WIDTH, config.YLIM / config.WORLD_HEIGHT)

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
    hover_uid = None  # Persistent UID for hovered animal
    mouse_drag_active = False  # True while left mouse button is held
    mouse_dragged = False  # True if mouse moved enough to count as a drag
    pending_click_event = None  # Deferred MOUSEBUTTONDOWN until we know it's not a drag

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

        # Build temporary view lists for event processing (hover/click detection)
        event_views = build_predator_views(pred_arrays) + build_prey_views(prey_arrays)

        # Handle continuous key presses for camera movement
        keys = pygame.key.get_pressed()
        # Camera speed in world units (slower when zoomed in so it feels consistent)
        cam_speed = config.CAMERA_SPEED / config.zoom_level
        max_cam_x = max(0, config.WORLD_WIDTH - config.XLIM / config.zoom_level)
        max_cam_y = max(0, config.WORLD_HEIGHT - config.YLIM / config.zoom_level)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            config.camera_y = max(0, config.camera_y - cam_speed)
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            config.camera_y = min(max_cam_y, config.camera_y + cam_speed)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            config.camera_x = max(0, config.camera_x - cam_speed)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            config.camera_x = min(max_cam_x, config.camera_x + cam_speed)

        # Handle continuous zoom with +/- keys
        if keys[pygame.K_PLUS] or keys[pygame.K_KP_PLUS] or keys[pygame.K_EQUALS]:
            _apply_zoom(config.ZOOM_STEP, config.XLIM // 2, config.YLIM // 2)
        if keys[pygame.K_MINUS] or keys[pygame.K_KP_MINUS]:
            _apply_zoom(-config.ZOOM_STEP, config.XLIM // 2, config.YLIM // 2)

        for event in pygame.event.get():
            # Scroll wheel zoom (button 4 = scroll up, 5 = scroll down)
            if event.type == pygame.MOUSEWHEEL:
                _apply_zoom(config.ZOOM_STEP * event.y, *pygame.mouse.get_pos())
                continue

            # Mouse drag panning: defer left-click until we know it's not a drag
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_drag_active = True
                mouse_dragged = False
                pending_click_event = event
                continue  # Don't process yet — wait for mouseup or drag
            elif event.type == pygame.MOUSEMOTION and mouse_drag_active:
                rel_x, rel_y = event.rel
                if not mouse_dragged and (abs(rel_x) > 2 or abs(rel_y) > 2):
                    mouse_dragged = True
                if mouse_dragged:
                    # Convert screen-pixel drag to world units
                    max_cx = max(0, config.WORLD_WIDTH - config.XLIM / config.zoom_level)
                    max_cy = max(0, config.WORLD_HEIGHT - config.YLIM / config.zoom_level)
                    config.camera_x = max(0, min(max_cx, config.camera_x - rel_x / config.zoom_level))
                    config.camera_y = max(0, min(max_cy, config.camera_y - rel_y / config.zoom_level))
                    continue  # Skip process_event so hover doesn't flicker while dragging
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if not mouse_dragged and pending_click_event is not None:
                    # It was a real click, not a drag — process the deferred mousedown now
                    running, stopped, pred_arrays, prey_arrays, grass, _, hover_animal, locked_animal = process_event(
                        pending_click_event, pred_arrays, prey_arrays, grass, screen, running, stopped,
                        hover_animal, locked_animal, event_views
                    )
                    locked_uid = locked_animal.uid if locked_animal is not None else None
                    hover_uid = hover_animal.uid if hover_animal is not None else None
                # Reset drag state
                mouse_drag_active = False
                mouse_dragged = False
                pending_click_event = None
                continue

            running, stopped, pred_arrays, prey_arrays, grass, _, hover_animal, locked_animal = process_event(
                event, pred_arrays, prey_arrays, grass, screen, running, stopped,
                hover_animal, locked_animal, event_views
            )

            # Track UIDs so we can re-resolve after simulation update
            if locked_animal is not None:
                locked_uid = locked_animal.uid
            else:
                locked_uid = None
            if hover_animal is not None:
                hover_uid = hover_animal.uid
            else:
                hover_uid = None

        # Update simulation state if not stopped
        if not stopped:
            update_simulation(pred_arrays, prey_arrays, grass)

        # Rebuild views AFTER simulation update (compact may have reordered indices)
        predator_views = build_predator_views(pred_arrays)
        prey_views = build_prey_views(prey_arrays)
        all_views = predator_views + prey_views

        # Re-resolve hover and locked animals by UID against fresh views
        if locked_uid is not None:
            locked_animal = find_view_by_uid(all_views, locked_uid)
            if locked_animal is None or not locked_animal.alive:
                locked_animal = None
                locked_uid = None
        else:
            locked_animal = None

        if hover_uid is not None:
            hover_animal = find_view_by_uid(all_views, hover_uid)
            if hover_animal is None or not hover_animal.alive:
                hover_animal = None
                hover_uid = None
        else:
            hover_animal = None

        # Always render the simulation state
        draw_simulation(screen, predator_views, prey_views, grass, hover_animal, current_mouse_pos, locked_animal)

        clock.tick(config.FPS)  # Cap FPS

    pygame.quit()

if __name__ == "__main__":
    main()
