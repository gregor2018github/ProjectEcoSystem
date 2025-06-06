import pygame
import config
from hover_window import HoverWindow # Import HoverWindow

# Track the button that was last clicked and when
button_clicked = None
button_click_time = 0

# Helper function to draw nicer buttons
def draw_button(surface, rect, text, font, mouse_pos):
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

# Register a button click for visual effect
def register_button_click(rect):
    global button_clicked, button_click_time
    button_clicked = rect
    button_click_time = pygame.time.get_ticks()

# Updated draw_simulation(): use draw_button for all buttons
# Add hover_animal, current_mouse_pos, and locked_animal parameters
def draw_simulation(screen, predators, preys, grass, hover_animal=None, current_mouse_pos=None, locked_animal=None):
    screen.fill((0, 0, 0))
    for (i, j), g in grass.items(): # Draw the grass grid
        pos = (i * config.CHUNKSIZE, j * config.CHUNKSIZE)
        g.draw(screen, pos, config.CHUNKSIZE)
    for p in preys: # Draw the prey
        p.draw(screen)
    for p in predators: # Draw the predators
        p.draw(screen)
    # Render statistics text in the top-left corner
    font = pygame.font.Font(None, config.STATS_FONT_SIZE)
    # Format rounds in thousands (K)
    rounds_display = f"{config.rounds_passed//1000}K" if config.rounds_passed >= 1000 else str(config.rounds_passed)
    stats_descr = [
        f"Rounds:",
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
    add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    font_button = pygame.font.Font(None, 24)

    draw_button(screen, exit_button_rect, "Exit", font_button, button_hover_mouse_pos)
    draw_button(screen, pause_button_rect, "Stop/Play", font_button, button_hover_mouse_pos)
    draw_button(screen, settings_button_rect, "Settings", font_button, button_hover_mouse_pos)
    draw_button(screen, add_pred_button_rect, "Add Pred", font_button, button_hover_mouse_pos)
    draw_button(screen, add_prey_button_rect, "Add Prey", font_button, button_hover_mouse_pos)
    draw_button(screen, stats_button_rect, "Statistics", font_button, button_hover_mouse_pos)
    
    # Draw locked animal's info window if one is selected and alive
    if locked_animal and locked_animal.alive:
        # Anchor position for locked window is the animal's current position
        locked_anchor_pos = (locked_animal.x, locked_animal.y)
        hw_locked = HoverWindow(locked_animal, locked_anchor_pos)
        hw_locked.draw(screen)
    
    # Draw hover window if an animal is being hovered over,
    # it's alive, and it's not the currently locked animal (or no animal is locked)
    if hover_animal and hover_animal.alive and current_mouse_pos:
        if locked_animal is None or hover_animal != locked_animal:
            # Anchor position for hover window is the current mouse position
            hw_hover = HoverWindow(hover_animal, current_mouse_pos)
            hw_hover.draw(screen)
    
    pygame.display.flip()