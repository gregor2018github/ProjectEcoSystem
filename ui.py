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
_font_hud: pygame.font.Font | None = None

def get_stats_font() -> pygame.font.Font:
    """Get the cached stats font, initializing if needed."""
    global _font_stats
    if _font_stats is None:
        _font_stats = pygame.font.Font(None, config.STATS_FONT_SIZE)
    return _font_stats

def get_hud_font() -> pygame.font.Font:
    global _font_hud
    if _font_hud is None:
        _font_hud = pygame.font.Font(None, 16)
    return _font_hud

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
    viewport_w = int((config.XLIM / config.zoom_level) * scale_x)
    viewport_h = int((config.YLIM / config.zoom_level) * scale_y)
    
    # Draw white rectangle showing current viewport
    viewport_rect = pygame.Rect(viewport_x, viewport_y, viewport_w, viewport_h)
    pygame.draw.rect(minimap_surface, (255, 255, 255, alpha_value), viewport_rect, MINIMAP_BORDER_WIDTH)
    
    # Blit the minimap surface to the screen
    screen.blit(minimap_surface, (minimap_x, minimap_y))

def _draw_stats_panel(screen: pygame.Surface, predators: list, preys: list) -> None:
    font = get_hud_font()

    PAD    = 8
    LINE_H = 17
    DIV_H  = 7   # total vertical space for a divider row
    PANEL_W = 175

    # Colors
    C_LBL = (150, 190, 150)   # muted green labels
    C_VAL = (225, 248, 225)   # bright values
    C_DIM = (100, 140, 100)   # dim headers / secondary info
    C_DIV = (45,  80,  45)    # divider line
    C_BDR = (50,  90,  50)    # panel border

    PX, PY = 8, 8  # panel top-left on screen

    # 3 sim rows + div + 3 pop rows + div + 4 death rows, plus padding
    PANEL_H = PAD + 3 * LINE_H + DIV_H + 3 * LINE_H + DIV_H + 4 * LINE_H + PAD

    # Semi-transparent panel background
    bg = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
    bg.fill((6, 18, 6, 160))
    screen.blit(bg, (PX, PY))
    pygame.draw.rect(screen, C_BDR, (PX, PY, PANEL_W, PANEL_H), 1)

    LX  = PX + PAD          # label left x
    V1R = PX + 118           # col-1 value right edge  (count / prey deaths)
    V2R = PX + PANEL_W - PAD # col-2 value right edge  (born / pred deaths / zoom)

    def blit_l(text: str, color: tuple, x: int, y: int) -> None:
        screen.blit(font.render(text, True, color), (x, y))

    def blit_r(text: str, color: tuple, right_x: int, y: int) -> None:
        s = font.render(text, True, color)
        screen.blit(s, (right_x - s.get_width(), y))

    def divider(y: int) -> None:
        pygame.draw.line(screen, C_DIV, (PX + 5, y + 3), (PX + PANEL_W - 5, y + 3))

    y = PY + PAD

    # --- Sim info ---
    rounds_str = f"{config.rounds_passed // 1000}K" if config.rounds_passed >= 1000 else str(config.rounds_passed)
    fps_str    = f"{config.current_fps:.0f}" if config.current_fps > 0 else "--"
    zoom_str   = f"{config.zoom_level:.1f}\u00d7"

    blit_l("Round", C_LBL, LX, y);  blit_r(rounds_str, C_VAL, V2R, y);  y += LINE_H
    blit_l("FPS",   C_LBL, LX, y);  blit_r(fps_str,   C_VAL, V2R, y);   y += LINE_H
    blit_l("Zoom",  C_LBL, LX, y);  blit_r(zoom_str,  C_DIM, V2R, y);   y += LINE_H

    # --- Divider ---
    divider(y); y += DIV_H

    # --- Population ---
    blit_r("Count", C_DIM, V1R, y);  blit_r("Born", C_DIM, V2R, y);  y += LINE_H
    blit_l("Prey", C_LBL, LX, y)
    blit_r(str(len(preys)),   C_VAL, V1R, y)
    blit_r(f"+{config.prey_born}", C_VAL, V2R, y);  y += LINE_H
    blit_l("Pred", C_LBL, LX, y)
    blit_r(str(len(predators)),     C_VAL, V1R, y)
    blit_r(f"+{config.predator_born}", C_VAL, V2R, y);  y += LINE_H

    # --- Divider ---
    divider(y); y += DIV_H

    # --- Deaths table ---
    blit_l("Deaths", C_DIM, LX, y);  blit_r("Prey", C_DIM, V1R, y);  blit_r("Pred", C_DIM, V2R, y);  y += LINE_H
    for label, pv, dv in [
        ("Starve", config.prey_dead_by_starvation, str(config.predator_dead_by_starvation)),
        ("Age",    config.prey_dead_by_age,         str(config.predator_dead_by_age)),
        ("Hunted", config.prey_dead_by_hunting,     "\u2014"),
    ]:
        blit_l(label,   C_LBL, LX,  y)
        blit_r(str(pv), C_VAL, V1R, y)
        blit_r(dv,      C_VAL, V2R, y)
        y += LINE_H


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
    _draw_stats_panel(screen, predators, preys)

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
    kill_pop_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 8 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    font_button = get_button_font()

    draw_button(screen, exit_button_rect, "Exit", font_button, button_hover_mouse_pos)
    draw_button(screen, pause_button_rect, "Stop/Play", font_button, button_hover_mouse_pos)
    draw_button(screen, settings_button_rect, "Settings", font_button, button_hover_mouse_pos)
    draw_button(screen, add_pred_button_rect, "Add Pred", font_button, button_hover_mouse_pos)
    draw_button(screen, rem_pred_button_rect, "Rem Pred", font_button, button_hover_mouse_pos)
    draw_button(screen, add_prey_button_rect, "Add Prey", font_button, button_hover_mouse_pos)
    draw_button(screen, rem_prey_button_rect, "Rem Prey", font_button, button_hover_mouse_pos)
    draw_button(screen, stats_button_rect, "Statistics", font_button, button_hover_mouse_pos)
    draw_button(screen, kill_pop_button_rect, "Kill Pop", font_button, button_hover_mouse_pos)
    
    # Draw locked animal's info window if one is selected and alive
    if locked_animal and locked_animal.alive:
        # Anchor position for locked window is the animal's screen position (with camera offset and zoom)
        locked_anchor_pos = (int((locked_animal.x - config.camera_x) * config.zoom_level),
                             int((locked_animal.y - config.camera_y) * config.zoom_level))
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