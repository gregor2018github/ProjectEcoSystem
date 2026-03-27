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
_font_btn_label: pygame.font.Font | None = None

# Button layout constants (single source of truth for ui + event_handler)
_BTN_W          = 90   # button width
_BTN_H          = 30   # button height
_BTN_INNER_GAP  = 5    # gap between buttons within a group
_BTN_SECTION_GAP = 12  # gap between bottom of one group and label of next
_BTN_LABEL_H    = 13   # height allocated for section label text
_BTN_LABEL_PAD  = 4    # gap between label and first button of group
_BTN_PANEL_PAD  = 8    # panel internal padding (top/bottom/sides)

def get_stats_font() -> pygame.font.Font:
    """Get the cached stats font, initializing if needed."""
    global _font_stats
    if _font_stats is None:
        _font_stats = pygame.font.Font(None, config.STATS_FONT_SIZE)
    return _font_stats

def get_hud_font() -> pygame.font.Font:
    global _font_hud
    if _font_hud is None:
        _font_hud = pygame.font.Font(None, 20)
    return _font_hud

def get_button_font() -> pygame.font.Font:
    """Get the cached button font, initializing if needed."""
    global _font_button
    if _font_button is None:
        _font_button = pygame.font.Font(None, 24)
    return _font_button

def get_btn_label_font() -> pygame.font.Font:
    global _font_btn_label
    if _font_btn_label is None:
        _font_btn_label = pygame.font.Font(None, 14)
    return _font_btn_label


def get_button_rects() -> dict[str, pygame.Rect]:
    """Return all button rects — single source of truth for ui and event_handler."""
    bx = config.XLIM - config.BUTTON_X_OFFSET
    y  = config.BUTTON_Y_START + _BTN_PANEL_PAD

    rects: dict[str, pygame.Rect] = {}

    def add_group(names: list[str]) -> None:
        nonlocal y
        y += _BTN_LABEL_H + _BTN_LABEL_PAD   # space for section label
        for i, name in enumerate(names):
            rects[name] = pygame.Rect(bx, y, _BTN_W, _BTN_H)
            y += _BTN_H + (_BTN_INNER_GAP if i < len(names) - 1 else 0)

    add_group(['exit', 'pause', 'settings'])
    y += _BTN_SECTION_GAP
    add_group(['add_pred', 'rem_pred', 'add_prey', 'rem_prey'])
    y += _BTN_SECTION_GAP
    add_group(['statistics', 'kill_pop'])

    return rects


def _draw_button_panel(screen: pygame.Surface, rects: dict[str, pygame.Rect]) -> None:
    font = get_btn_label_font()

    bx       = config.XLIM - config.BUTTON_X_OFFSET
    panel_x  = bx - _BTN_PANEL_PAD
    panel_y  = config.BUTTON_Y_START
    panel_w  = _BTN_W + 2 * _BTN_PANEL_PAD
    panel_h  = max(r.bottom for r in rects.values()) + _BTN_PANEL_PAD - panel_y

    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill((6, 18, 6, 160))
    screen.blit(bg, (panel_x, panel_y))
    pygame.draw.rect(screen, (50, 90, 50), (panel_x, panel_y, panel_w, panel_h), 1)

    C_LBL = (100, 140, 100)
    C_DIV = (45, 80, 45)

    sections = [
        ('SIM',        'exit'),
        ('POPULATION', 'add_pred'),
        ('TOOLS',      'statistics'),
    ]
    for title, first_key in sections:
        first_rect = rects[first_key]
        lbl_y = first_rect.top - _BTN_LABEL_H - _BTN_LABEL_PAD

        if title != 'SIM':
            div_y = lbl_y - _BTN_SECTION_GAP // 2
            pygame.draw.line(screen, C_DIV,
                             (panel_x + 5, div_y), (panel_x + panel_w - 5, div_y))

        s = font.render(title, True, C_LBL)
        screen.blit(s, (panel_x + (panel_w - s.get_width()) // 2, lbl_y))

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
    current_time = pygame.time.get_ticks()
    button_effect = (
        config.BUTTON_CLICK_VISUAL_EFFECT
        and button_clicked == rect
        and current_time - button_click_time < config.BUTTON_CLICK_DURATION
    )

    if button_effect:
        bg_color  = (10, 28, 10)
        bdr_color = (55, 95, 55)
        draw_rect = pygame.Rect(rect.left + 1, rect.top + 1, rect.width - 1, rect.height - 1)
    elif hover:
        bg_color  = (36, 76, 36)
        bdr_color = (90, 145, 90)
        draw_rect = rect
    else:
        bg_color  = (22, 52, 22)
        bdr_color = (55, 95, 55)
        draw_rect = rect

    pygame.draw.rect(surface, bg_color, draw_rect, border_radius=7)

    # Subtle 1-px top-edge highlight for depth (skip when pressed)
    if not button_effect:
        hl_color = (60, 110, 60) if not hover else (80, 140, 80)
        pygame.draw.line(
            surface, hl_color,
            (draw_rect.left + 7, draw_rect.top + 1),
            (draw_rect.right - 8, draw_rect.top + 1),
        )

    pygame.draw.rect(surface, bdr_color, draw_rect, 2, border_radius=7)

    text_surface = font.render(text, True, (215, 240, 215))
    offset = 1 if button_effect else 0
    text_rect = text_surface.get_rect(center=(rect.centerx + offset, rect.centery + offset))
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

    alpha_value = int(255 * _minimap_alpha)

    # Dark green background matching the HUD panel
    pygame.draw.rect(minimap_surface, (6, 18, 6, alpha_value),
                     pygame.Rect(0, 0, minimap_width, minimap_height))

    # Border matching HUD border color
    pygame.draw.rect(minimap_surface, (50, 90, 50, alpha_value),
                     pygame.Rect(0, 0, minimap_width, minimap_height), MINIMAP_BORDER_WIDTH)

    # Calculate viewport rectangle on minimap
    scale_x = minimap_width / config.WORLD_WIDTH
    scale_y = minimap_height / config.WORLD_HEIGHT

    viewport_x = int(config.camera_x * scale_x)
    viewport_y = int(config.camera_y * scale_y)
    viewport_w = int((config.XLIM / config.zoom_level) * scale_x)
    viewport_h = int((config.YLIM / config.zoom_level) * scale_y)

    # Semi-transparent fill inside viewport rect
    vp_fill = pygame.Surface((viewport_w, viewport_h), pygame.SRCALPHA)
    vp_fill.fill((150, 200, 150, int(40 * _minimap_alpha)))
    minimap_surface.blit(vp_fill, (viewport_x, viewport_y))

    # Bright green border for the viewport indicator
    viewport_rect = pygame.Rect(viewport_x, viewport_y, viewport_w, viewport_h)
    pygame.draw.rect(minimap_surface, (155, 210, 155, alpha_value), viewport_rect, MINIMAP_BORDER_WIDTH)

    # Blit the minimap surface to the screen
    screen.blit(minimap_surface, (minimap_x, minimap_y))

def _draw_stats_panel(screen: pygame.Surface, predators: list, preys: list) -> None:
    font = get_hud_font()

    PAD    = 9
    LINE_H = 21
    DIV_H  = 8   # total vertical space for a divider row
    PANEL_W = 210

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
    V1R = PX + 142           # col-1 value right edge  (count / prey deaths)
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
    button_hover_mouse_pos = pygame.mouse.get_pos()
    btn = get_button_rects()
    _draw_button_panel(screen, btn)
    font_button = get_button_font()

    draw_button(screen, btn['exit'],       "Exit",       font_button, button_hover_mouse_pos)
    draw_button(screen, btn['pause'],      "Stop/Play",  font_button, button_hover_mouse_pos)
    draw_button(screen, btn['settings'],   "Settings",   font_button, button_hover_mouse_pos)
    draw_button(screen, btn['add_pred'],   "Add Pred",   font_button, button_hover_mouse_pos)
    draw_button(screen, btn['rem_pred'],   "Rem Pred",   font_button, button_hover_mouse_pos)
    draw_button(screen, btn['add_prey'],   "Add Prey",   font_button, button_hover_mouse_pos)
    draw_button(screen, btn['rem_prey'],   "Rem Prey",   font_button, button_hover_mouse_pos)
    draw_button(screen, btn['statistics'], "Statistics", font_button, button_hover_mouse_pos)
    draw_button(screen, btn['kill_pop'],   "Kill Pop",   font_button, button_hover_mouse_pos)
    
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