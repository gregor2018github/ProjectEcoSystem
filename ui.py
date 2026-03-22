################################################
# Imports
################################################

from __future__ import annotations
import pygame
import config
from hover_window import HoverWindow
from grass_array import GrassArray

################################################
# Minimap configuration and state
################################################

MINIMAP_WIDTH = 150  # Minimap width in pixels
MINIMAP_MARGIN = 10  # Margin from screen edges
MINIMAP_BORDER_WIDTH = 2  # Border thickness
MINIMAP_SHOW_DURATION = 2000  # How long minimap stays visible after movement stops (ms)
MINIMAP_FADE_DURATION = 300  # Duration of fade in/out transition (ms)

_minimap_last_active: int = 0  # Timestamp when camera last moved
_minimap_alpha: float = 0.0    # Current alpha (0.0 to 1.0)
_last_camera_x: float = 0.0    # Last camera position
_last_camera_y: float = 0.0
_last_minimap_tick: int = 0    # Last tick for dt calculation

################################################
# Cached fonts (initialized lazily to avoid pygame init issues)
################################################

_font_stats: pygame.font.Font | None = None
_font_button: pygame.font.Font | None = None

def get_stats_font() -> pygame.font.Font:
    """Get the cached stats font, initializing if needed."""
    global _font_stats
    if _font_stats is None:
        _font_stats = pygame.font.Font(None, config.STATS_FONT_SIZE)
    return _font_stats

def get_button_font() -> pygame.font.Font:
    """Get the cached button font, initializing if needed."""
    global _font_button
    if _font_button is None:
        _font_button = pygame.font.Font(None, 24)
    return _font_button

################################################
# Button Drawing Functions
################################################

# Track the button that was last clicked and when
button_clicked: pygame.Rect | None = None
button_click_time: int = 0

def draw_button(
    surface: pygame.Surface,
    rect: pygame.Rect,
    text: str,
    font: pygame.font.Font,
    mouse_pos: tuple[int, int]
) -> None:
    """Draw a styled button with hover and click effects.
    
    Renders a button with rounded corners, hover highlighting, and a
    brief visual click effect when pressed.
    
    Args:
        surface: The pygame surface to draw on.
        rect: The rectangle defining the button's position and size.
        text: The text to display on the button.
        font: The font to use for the button text.
        mouse_pos: Current mouse position for hover detection.
    """
    hover = rect.collidepoint(mouse_pos)
    # Check if this button is currently being clicked to apply visual effect
    button_effect = False
    current_time = pygame.time.get_ticks()
    
    if config.BUTTON_CLICK_VISUAL_EFFECT and button_clicked == rect and \
       current_time - button_click_time < config.BUTTON_CLICK_DURATION:
        # Visual click effect: darker background, shifted position
        pygame.draw.rect(surface, (40, 80, 60), pygame.Rect(
            rect.left + 2, rect.top + 2, rect.width - 2, rect.height - 2
        ), border_radius=8)
        button_effect = True
    else:
        # Normal button appearance
        if hover:
            pygame.draw.rect(surface, (80, 120, 100), rect, border_radius=8) # Lighter green for hover
        else:
            pygame.draw.rect(surface, (60, 100, 80), rect, border_radius=8)
    
    # Always draw the border
    if hover or button_effect:
        pygame.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=8) # Thicker border on hover/click
    else:
        pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=8)
    
    # Adjust text position slightly when button is pressed
    text_surface = font.render(text, True, (255, 255, 255))
    if button_effect:
        text_rect = text_surface.get_rect(center=(rect.centerx + 1, rect.centery + 1))
    else:
        text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def register_button_click(rect: pygame.Rect) -> None:
    """Register a button click for visual effect tracking.
    
    Records the clicked button and timestamp to trigger the visual
    click effect in subsequent draw calls.
    
    Args:
        rect: The rectangle of the button that was clicked.
    """
    global button_clicked, button_click_time
    button_clicked = rect
    button_click_time = pygame.time.get_ticks()

#################################################
# Minimap Drawing Function
#################################################

def draw_minimap(screen: pygame.Surface) -> None:
    """Draw a minimap showing the current viewport position in the world.
    
    The minimap appears when the camera moves with a smooth fade-in,
    stays visible for a duration, then fades out smoothly.
    Shows a black border for the world boundary and a white rectangle
    indicating the current visible area.
    
    Args:
        screen: The pygame surface to draw on.
    """
    global _minimap_last_active, _minimap_alpha, _last_camera_x, _last_camera_y, _last_minimap_tick
    
    current_time = pygame.time.get_ticks()
    
    # Initialize or calculate delta time
    if _last_minimap_tick == 0:
        _last_minimap_tick = current_time
    dt = current_time - _last_minimap_tick
    _last_minimap_tick = current_time
    
    # Check if camera has moved
    camera_moved = config.camera_x != _last_camera_x or config.camera_y != _last_camera_y
    if camera_moved:
        _minimap_last_active = current_time
        _last_camera_x = config.camera_x
        _last_camera_y = config.camera_y
    
    # Target alpha: 1.0 if moving or recently moved, 0.0 otherwise
    target_alpha = 1.0 if (current_time - _minimap_last_active) < MINIMAP_SHOW_DURATION else 0.0
    
    # Smoothly transition alpha towards target
    if _minimap_alpha < target_alpha:
        _minimap_alpha = min(target_alpha, _minimap_alpha + dt / MINIMAP_FADE_DURATION)
    elif _minimap_alpha > target_alpha:
        _minimap_alpha = max(target_alpha, _minimap_alpha - dt / MINIMAP_FADE_DURATION)
    
    # Don't draw if fully transparent
    if _minimap_alpha <= 0.0:
        return
    
    # Calculate minimap dimensions maintaining world aspect ratio
    world_aspect = config.WORLD_WIDTH / config.WORLD_HEIGHT
    minimap_width = MINIMAP_WIDTH
    minimap_height = int(minimap_width / world_aspect)
    
    # Position minimap at bottom-left
    minimap_x = MINIMAP_MARGIN
    minimap_y = config.YLIM - minimap_height - MINIMAP_MARGIN
    
    # Create a surface with alpha channel for the minimap
    minimap_surface = pygame.Surface((minimap_width, minimap_height), pygame.SRCALPHA)
    
    # Draw minimap background (same color as button background: 60, 100, 80)
    alpha_value = int(255 * _minimap_alpha)
    pygame.draw.rect(minimap_surface, (60, 100, 80, alpha_value), 
                     pygame.Rect(0, 0, minimap_width, minimap_height))
    
    # Draw black border around minimap (world boundary)
    pygame.draw.rect(minimap_surface, (0, 0, 0, alpha_value), 
                     pygame.Rect(0, 0, minimap_width, minimap_height), MINIMAP_BORDER_WIDTH)
    
    # Calculate viewport rectangle on minimap
    scale_x = minimap_width / config.WORLD_WIDTH
    scale_y = minimap_height / config.WORLD_HEIGHT
    
    viewport_x = int(config.camera_x * scale_x)
    viewport_y = int(config.camera_y * scale_y)
    viewport_w = int(config.XLIM * scale_x)
    viewport_h = int(config.YLIM * scale_y)
    
    # Draw white rectangle showing current viewport
    viewport_rect = pygame.Rect(viewport_x, viewport_y, viewport_w, viewport_h)
    pygame.draw.rect(minimap_surface, (255, 255, 255, alpha_value), viewport_rect, MINIMAP_BORDER_WIDTH)
    
    # Blit the minimap surface to the screen
    screen.blit(minimap_surface, (minimap_x, minimap_y))

#################################################
# Main Drawing Function for Simulation
#################################################

def draw_simulation(
    screen: pygame.Surface,
    predators: list,
    preys: list,
    grass: GrassArray,
    hover_animal=None,
    current_mouse_pos: tuple[int, int] | None = None,
    locked_animal=None,
) -> None:
    """Draw the complete simulation frame including all visual elements.
    
    Renders the grass grid, all animals, statistics overlay, control buttons,
    and any hover/locked animal information windows.
    
    Args:
        screen: The pygame surface to draw on.
        predators: List of predator objects to draw.
        preys: List of prey objects to draw.
        grass: GrassArray for efficient grass rendering.
        hover_animal: Animal currently being hovered over, or None.
        current_mouse_pos: Current mouse position for hover window placement.
        locked_animal: Animal whose info window is locked/pinned, or None.
    """
    screen.fill((0, 0, 0))
    
    # Draw grass using GrassArray's optimized method
    grass.draw_visible(screen, int(config.camera_x), int(config.camera_y))
    
    for p in preys: # Draw the prey
        p.draw(screen)
    for p in predators: # Draw the predators
        p.draw(screen)
    # Render statistics text in the top-left corner
    font = get_stats_font()
    # Format rounds in thousands (K)
    rounds_display = f"{config.rounds_passed//1000}K" if config.rounds_passed >= 1000 else str(config.rounds_passed)
    # Format FPS display
    fps_display = f"{config.current_fps:.0f}" if config.current_fps > 0 else "--"
    stats_descr = [
        f"Rounds:",
        f"FPS:",
        "",  # Blank line for separation
        f"Prey:",
        f"Predators:",
        "",  # Blank line
        f"Prey Deaths:",
        f"    By Starvation:",
        f"    By Old Age:",
        f"    Hunted Down:",
        "",  # Blank line
        f"Predator Deaths:",
        f"    By Starvation:",
        f"    By Old Age:",
    ]
    stats = [
        f"{rounds_display}",
        f"{fps_display}",
        "",  # Blank line for separation
        f"{len(preys)} (Born: {config.prey_born})",
        f"{len(predators)} (Born: {config.predator_born})",
        "",  # Blank line
        f"{config.prey_deceased}",
        f"{config.prey_dead_by_starvation}",
        f"{config.prey_dead_by_age}",
        f"{config.prey_dead_by_hunting}",
        "",  # Blank line
        f"{config.predator_deceased}",
        f"{config.predator_dead_by_starvation}",
        f"{config.predator_dead_by_age}",
    ]
    y_offset = config.STATS_Y_OFFSET
    # Draw the statistics text
    for line in stats_descr:
        text_surface = font.render(line, True, config.FONT_COLORS)
        screen.blit(text_surface, (config.STATS_X_OFFSET, y_offset))
        y_offset += config.STATS_LINE_HEIGHT
    y_offset = config.STATS_Y_OFFSET
    for line in stats:
        text_surface = font.render(line, True, config.FONT_COLORS)
        screen.blit(text_surface, (config.STATS_X_OFFSET + 160, y_offset))
        y_offset += config.STATS_LINE_HEIGHT

    # Buttons on the right side of the screen
    button_x = config.XLIM - config.BUTTON_X_OFFSET
    # Get current mouse position for button hover effects, as current_mouse_pos might be from a past event if mouse isn't moving
    button_hover_mouse_pos = pygame.mouse.get_pos() 

    exit_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    pause_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    settings_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 2 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    add_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 3 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    rem_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    rem_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 6 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 7 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    font_button = get_button_font()

    draw_button(screen, exit_button_rect, "Exit", font_button, button_hover_mouse_pos)
    draw_button(screen, pause_button_rect, "Stop/Play", font_button, button_hover_mouse_pos)
    draw_button(screen, settings_button_rect, "Settings", font_button, button_hover_mouse_pos)
    draw_button(screen, add_pred_button_rect, "Add Pred", font_button, button_hover_mouse_pos)
    draw_button(screen, rem_pred_button_rect, "Rem Pred", font_button, button_hover_mouse_pos)
    draw_button(screen, add_prey_button_rect, "Add Prey", font_button, button_hover_mouse_pos)
    draw_button(screen, rem_prey_button_rect, "Rem Prey", font_button, button_hover_mouse_pos)
    draw_button(screen, stats_button_rect, "Statistics", font_button, button_hover_mouse_pos)
    
    # Draw locked animal's info window if one is selected and alive
    if locked_animal and locked_animal.alive:
        # Anchor position for locked window is the animal's screen position (with camera offset)
        locked_anchor_pos = (int(locked_animal.x - config.camera_x), int(locked_animal.y - config.camera_y))
        hw_locked = HoverWindow(locked_animal, locked_anchor_pos)
        hw_locked.draw(screen)
    
    # Draw hover window if an animal is being hovered over,
    # it's alive, and it's not the currently locked animal (or no animal is locked)
    if hover_animal and hover_animal.alive and current_mouse_pos:
        if locked_animal is None or hover_animal != locked_animal:
            # Anchor position for hover window is the current mouse position
            hw_hover = HoverWindow(hover_animal, current_mouse_pos)
            hw_hover.draw(screen)
    
    # Draw minimap (shows when camera moves)
    draw_minimap(screen)
    
    pygame.display.flip()