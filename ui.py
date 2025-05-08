import pygame
import config

def draw_line_chart(surface, rect, series, color):
    if len(series) < 2:
        return
    # Scale series within chart rect
    min_val = min(series)
    max_val = max(series)
    if max_val == min_val:
        max_val += 1
    points = []
    n = len(series)
    step = rect.width / (n - 1)
    for i, val in enumerate(series):
        # Map value to y coordinate (invert as y increases downwards)
        y = rect.bottom - ((val - min_val) / (max_val - min_val)) * rect.height
        x = rect.left + i * step
        points.append((x, y))
    pygame.draw.lines(surface, color, False, points, 2)

# Modified statistics window to be fullscreen with updated headers and without axis descriptions
def show_statistics_window(predators, preys, grass):
    stat_screen = pygame.display.set_mode((config.XLIM, config.YLIM))
    pygame.display.set_caption("Statistics")
    font = pygame.font.Font(None, 20)
    running_stats = True

    margin = 40
    chart_width = config.XLIM - 2 * margin
    chart_height = int((config.YLIM - 3 * margin - config.BUTTON_HEIGHT) / 2)
    pop_chart_rect = pygame.Rect(margin, margin, chart_width, chart_height)
    event_chart_rect = pygame.Rect(margin, margin + chart_height + margin, chart_width, chart_height)
    close_rect = pygame.Rect((config.XLIM - config.BUTTON_WIDTH) // 2, config.YLIM - margin - config.BUTTON_HEIGHT + 10, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    
    while running_stats:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running_stats = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if close_rect.collidepoint(event.pos):
                    running_stats = False
                    
        stat_screen.fill((30, 30, 30))
        
        pygame.draw.rect(stat_screen, (200,200,200), pop_chart_rect, 1)
        pygame.draw.rect(stat_screen, (200,200,200), event_chart_rect, 1)
        
        # --- Population header with colored labels for top graph ---
        # Order: Prey (white), Predator (red), Grass (green)
        header_parts = [
            ( "Population (", (255,255,255) ),
            ( "Prey", (255,255,255) ),
            ( ", ", (255,255,255) ),
            ( "Predator", (255,0,0) ),
            ( ", ", (255,255,255) ),
            ( "Grass", (0,255,0) ),
            ( ")", (255,255,255) ),
        ]
        x_offset = pop_chart_rect.left
        y_offset = pop_chart_rect.top - 30
        for text, color in header_parts:
            part = font.render(text, True, color)
            stat_screen.blit(part, (x_offset, y_offset))
            x_offset += part.get_width()

        # --- Events header with colored labels for second graph ---
        # Order: Prey deceased (gray), Predator deceased (orange), Prey born (green), Predator born (blue)
        events_header_parts = [
            ( "Events (", (255,255,255) ),
            ( "Prey deceased", (150,150,150) ),
            ( ", ", (255,255,255) ),
            ( "Predator deceased", (255,165,0) ),
            ( ", ", (255,255,255) ),
            ( "Prey born", (0,255,0) ),
            ( ", ", (255,255,255) ),
            ( "Predator born", (0,0,255) ),
            ( ")", (255,255,255) ),
        ]
        x_offset = event_chart_rect.left
        y_offset = event_chart_rect.top - 30
        for text, color in events_header_parts:
            part = font.render(text, True, color)
            stat_screen.blit(part, (x_offset, y_offset))
            x_offset += part.get_width()
        
        # --- Draw line charts in top graph, including Grass Total ---
        draw_line_chart(stat_screen, pop_chart_rect, config.stats_history["Prey Count"], (255,255,255))
        draw_line_chart(stat_screen, pop_chart_rect, config.stats_history["Predator Count"], (255,0,0))
        draw_line_chart(stat_screen, pop_chart_rect, config.stats_history["Grass Total"], (0,255,0))
        
        # --- Draw line charts for events graph (unchanged drawing order) ---
        draw_line_chart(stat_screen, event_chart_rect, config.stats_history["Prey deceased"], (150,150,150))
        draw_line_chart(stat_screen, event_chart_rect, config.stats_history["Predator deceased"], (255,165,0))
        draw_line_chart(stat_screen, event_chart_rect, config.stats_history["Prey born"], (0,255,0))
        draw_line_chart(stat_screen, event_chart_rect, config.stats_history["Predator born"], (0,0,255))
        
        rounds_label = font.render(f"Rounds: {config.rounds_passed}", True, (255,255,0))
        stat_screen.blit(rounds_label, (margin, config.YLIM - margin - config.BUTTON_HEIGHT - 25))
        draw_button(stat_screen, close_rect, "Close", font)
        pygame.display.flip()
        
    stat_screen = pygame.display.set_mode((config.XLIM, config.YLIM))
    pygame.display.set_caption("Simulation")

# Helper function to draw nicer buttons
def draw_button(surface, rect, text, font):
    pygame.draw.rect(surface, (60, 100, 80), rect, border_radius=8)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=8)
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# Updated settings_menu() with scrolling and a Reset button
def settings_menu(screen):
    modal_rect = pygame.Rect(200, 100, 600, 400)
    font = pygame.font.Font(None, 32)
    btn_rect_standard = pygame.Rect(modal_rect.left + 50, modal_rect.bottom - 60, 100, 40)
    btn_rect_resume = pygame.Rect(modal_rect.left + 250, modal_rect.bottom - 60, 100, 40)
    btn_rect_cancel = pygame.Rect(modal_rect.left + 450, modal_rect.bottom - 60, 100, 40)
    btn_rect_reset = pygame.Rect(modal_rect.left + 250, modal_rect.bottom - 110, 150, 30)
    
    # Initialize settings and error tracking
    settings = {
        "Prey Health": config.PREY_MAX_FOOD,
        "Predator Health": config.PREDATOR_MAX_FOOD,
        "Prey Reproduction Rate": config.PREY_REPRODUCTION_RATE,
        "Predator Reproduction Rate": config.PREDATOR_REPRODUCTION_RATE,
        "Grass Growth Rate": config.GRASS_GROWTH_RATE,
        "Max Grass per Field": config.GRASS_MAX_AMOUNT,
        "Prey Fear Distance": config.PREY_FEAR_DISTANCE,
        "Prey Speed": config.PREY_SPEED,
        "Predator Speed": config.PREDATOR_SPEED
    }
    error_fields = {}  # keys with conversion errors
    scroll_offset = 0
    active_key = None    # Tracks the key being edited
    active_text = ""     # Tracks the current text input for that key
    running_settings = True
    action = None
    while running_settings:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running_settings = False
                action = "cancel"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_rect_standard.collidepoint(event.pos):
                    # Before exiting, validate active editing field
                    if active_key is not None:
                        try:
                            val = float(active_text)
                            if val.is_integer():
                                val = int(val)
                            settings[active_key] = val
                            error_fields.pop(active_key, None)
                        except ValueError:
                            error_fields[active_key] = True
                            continue  # Do not exit if error exists
                    action = "restart"
                    running_settings = False
                elif btn_rect_resume.collidepoint(event.pos):
                    if active_key is not None:
                        try:
                            val = float(active_text)
                            if val.is_integer():
                                val = int(val)
                            settings[active_key] = val
                            error_fields.pop(active_key, None)
                        except ValueError:
                            error_fields[active_key] = True
                            continue
                    action = "resume"
                    running_settings = False
                elif btn_rect_cancel.collidepoint(event.pos):
                    action = "cancel"
                    running_settings = False
                elif btn_rect_reset.collidepoint(event.pos):
                    for key, value in config.default_settings.items():
                        settings[key] = value
                        error_fields.pop(key, None)
                else:
                    params_area = pygame.Rect(modal_rect.left + 50, modal_rect.top + 70, modal_rect.width - 100, modal_rect.height - 220)
                    keys_list = list(settings.keys())
                    for i, key in enumerate(keys_list):
                        line_rect = pygame.Rect(params_area.left, params_area.top + i*30 + scroll_offset, params_area.width, 30)
                        if line_rect.collidepoint(event.pos):
                            active_key = key
                            active_text = str(settings[key])
                            error_fields.pop(key, None)
                            break
            if event.type == pygame.KEYDOWN and active_key is not None:
                if event.key == pygame.K_BACKSPACE:
                    active_text = active_text[:-1]
                    settings[active_key] = active_text
                elif event.key == pygame.K_RETURN:
                    try:
                        val = float(active_text)
                        if val.is_integer():
                            val = int(val)
                        settings[active_key] = val
                        error_fields.pop(active_key, None)
                        active_key = None
                        active_text = ""
                    except ValueError:
                        error_fields[active_key] = True
                else:
                    if event.unicode in "0123456789.-":
                        active_text += event.unicode
                    settings[active_key] = active_text
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset += event.y * 20
        # Clamp scrolling
        params_area = pygame.Rect(modal_rect.left + 50, modal_rect.top + 70, modal_rect.width - 100, modal_rect.height - 220)
        total_content = len(settings) * 30
        min_scroll = min(0, params_area.height - total_content)
        scroll_offset = max(min_scroll, min(0, scroll_offset))
        
        pygame.draw.rect(screen, (240,240,240), modal_rect)
        header = font.render("Simulation Settings", True, (0,0,0))
        screen.blit(header, (modal_rect.centerx - header.get_width()//2, modal_rect.top + 20))
        
        params_area = pygame.Rect(modal_rect.left + 50, modal_rect.top + 70, modal_rect.width - 100, modal_rect.height - 220)
        pygame.draw.rect(screen, (200, 200, 200), params_area)
        param_font = pygame.font.Font(None, 24)
        keys = list(settings.keys())
        for i, key in enumerate(keys):
            y = params_area.top + i * 30 + scroll_offset
            # Changed condition to include the top boundary
            if y >= params_area.top and y < params_area.bottom:
                text_val = str(settings[key])
                rect = pygame.Rect(params_area.left, y - 5, params_area.width, 30)
                if key == active_key:
                    if error_fields.get(key, False):
                        pygame.draw.rect(screen, (255, 0, 0), rect)
                    else:
                        pygame.draw.rect(screen, (180, 180, 250), rect)
                label = f"{key} (std: {config.default_settings[key]}): {text_val}"
                text_surface = param_font.render(label, True, (0,0,0))
                screen.blit(text_surface, (rect.left + 10, rect.top + 5))
                if key == active_key:
                    caret_x = rect.left + 10 + param_font.size(label)[0]
                    caret_y = rect.top + 5
                    caret_height = param_font.get_height()
                    pygame.draw.line(screen, (0,0,0), (caret_x, caret_y), (caret_x, caret_y + caret_height), 2)
        btn_font = pygame.font.Font(None, 24)
        draw_button(screen, btn_rect_standard, "Restart", btn_font)
        draw_button(screen, btn_rect_resume, "Resume", btn_font)
        draw_button(screen, btn_rect_cancel, "Cancel", btn_font)
        draw_button(screen, btn_rect_reset, "Reset to std", btn_font)
        pygame.display.flip()
    # Before returning, ensure all settings values are numeric.
    for key in settings:
        if isinstance(settings[key], str):
            try:
                num_val = float(settings[key])
                if num_val.is_integer():
                    settings[key] = int(num_val)
                else:
                    settings[key] = num_val
            except ValueError:
                settings[key] = config.default_settings[key]
    return action, settings

# Updated draw_simulation(): use draw_button for all buttons
def draw_simulation(screen, predators, preys, grass):
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
    stats = [
        f"Prey Count: {len(preys)}",
        f"Predator Count: {len(predators)}",
        f"Prey deceased: {config.prey_deceased}",
        f"Predator deceased: {config.predator_deceased}",
        f"Prey born: {config.prey_born}",
        f"Predator born: {config.predator_born}",
        f"Rounds passed: {rounds_display}"
    ]
    y_offset = config.STATS_Y_OFFSET
    for line in stats:
        text_surface = font.render(line, True, config.FONT_COLORS)
        screen.blit(text_surface, (config.STATS_X_OFFSET, y_offset))
        y_offset += config.STATS_LINE_HEIGHT

    # Buttons on the right side of the screen
    button_x = config.XLIM - config.BUTTON_X_OFFSET

    exit_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    pause_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    settings_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 2 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    add_pred_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 3 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    add_prey_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 4 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    stats_button_rect = pygame.Rect(button_x, config.BUTTON_Y_START + 5 * config.BUTTON_Y_GAP, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
    font_button = pygame.font.Font(None, 24)

    draw_button(screen, exit_button_rect, "Exit", font_button)
    draw_button(screen, pause_button_rect, "Stop/Play", font_button)
    draw_button(screen, settings_button_rect, "Settings", font_button)
    draw_button(screen, add_pred_button_rect, "Add Pred", font_button)
    draw_button(screen, add_prey_button_rect, "Add Prey", font_button)
    draw_button(screen, stats_button_rect, "Statistics", font_button)
    
    pygame.display.flip()