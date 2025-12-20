################################################
# Imports
################################################

from __future__ import annotations
import pygame
import config
from ui import draw_button, register_button_click
from simulation import update_simulation
from animals import Predator, Prey
from grass_array import GrassArray

################################################
# Statistics Window Class
################################################

class StatisticsWindow:
    """A window displaying simulation statistics as line charts.
    
    Shows population trends (prey, predator, grass) and event history
    (births, deaths) over time using line charts.
    
    Attributes:
        stat_screen: The pygame display surface for the statistics window.
        font: The font used for rendering text.
        running_stats: Whether the statistics window is currently active.
        margin: Margin size in pixels around chart elements.
        chart_width: Width of the chart area in pixels.
        chart_height: Height of each chart in pixels.
        pop_chart_rect: Rectangle defining the population chart area.
        event_chart_rect: Rectangle defining the events chart area.
        close_rect: Rectangle defining the close button area.
    """
    
    def __init__(self, predators: list[Predator], preys: list[Prey], grass: GrassArray) -> None:
        """Initialize the statistics window with charts and UI elements."""
        self.predators = predators
        self.preys = preys
        self.grass = grass
        self.simulation_running = False

        self.stat_screen = pygame.display.set_mode((config.XLIM, config.YLIM))
        pygame.display.set_caption("Statistics")
        self.font = pygame.font.Font(None, 20)
        self.running_stats = True

        self.margin = 40
        self.chart_width = config.XLIM - 2 * self.margin
        self.chart_height = int((config.YLIM - 3 * self.margin - config.BUTTON_HEIGHT) / 2)
        self.pop_chart_rect = pygame.Rect(self.margin, self.margin, self.chart_width, self.chart_height)
        
        # Split bottom area into two
        bottom_y = self.margin + self.chart_height + self.margin
        half_width = (self.chart_width - self.margin) // 2
        
        self.event_chart_rect = pygame.Rect(self.margin, bottom_y, half_width, self.chart_height)
        self.stats_table_rect = pygame.Rect(self.margin + half_width + self.margin, bottom_y, half_width, self.chart_height)
        
        self.close_rect = pygame.Rect(config.XLIM - self.margin - config.BUTTON_WIDTH, config.YLIM - self.margin - config.BUTTON_HEIGHT + 10, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)
        
        toggle_width = 140
        self.toggle_sim_rect = pygame.Rect(self.close_rect.left - toggle_width - 10, self.close_rect.top, toggle_width, config.BUTTON_HEIGHT)

    def run(self) -> None:
        """Run the statistics window event loop.
        
        Displays population and event charts, handles user input,
        and closes when the user presses Escape or clicks the Close button.
        """
        from event_handler import play_click_sound
        
        clock = pygame.time.Clock()
        fps_frame_count = 0
        fps_timer = 0.0

        def draw_line_chart(
            surface: pygame.Surface,
            rect: pygame.Rect,
            series: list[int | float],
            color: tuple[int, int, int]
        ) -> None:
            """Draw a line chart on the given surface.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                series: List of numeric values to plot.
                color: RGB tuple for the line color.
            """
            if len(series) < 2:
                return
            # Scale series within chart rect
            min_val = float(min(series))
            max_val = float(max(series))
            if max_val == min_val:
                max_val += 1
            points = []
            n = len(series)
            step = rect.width / (n - 1)
            for i, val in enumerate(series):
                # Map value to y coordinate (invert as y increases downwards)
                # Convert to float to handle NumPy types
                val_f = float(val)
                y = rect.bottom - ((val_f - min_val) / (max_val - min_val)) * rect.height
                x = rect.left + i * step
                points.append((float(x), float(y)))
            pygame.draw.lines(surface, color, False, points, 2)

        def draw_phase_diagram(
            surface: pygame.Surface,
            rect: pygame.Rect,
            x_series: list[int | float],
            y_series: list[int | float],
            mouse_pos: tuple[int, int] | None = None,
            limit: int = 20000
        ) -> None:
            """Draw a phase diagram (Prey vs Predator) for the recent history.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                x_series: Data for the X axis (Prey).
                y_series: Data for the Y axis (Predator).
                mouse_pos: Current mouse position for hover effects.
                limit: Number of recent data points to show.
            """
            if len(x_series) < 2 or len(y_series) < 2:
                return
            
            # Slice data to the limit
            start_idx = max(0, len(x_series) - limit)
            xs = x_series[start_idx:]
            ys = y_series[start_idx:]
            
            if len(xs) < 2: return

            # Determine scaling range
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            # Add padding to ranges
            pad_x = (max_x - min_x) * 0.05 if max_x != min_x else 1.0
            pad_y = (max_y - min_y) * 0.05 if max_y != min_y else 1.0
            min_x -= pad_x
            max_x += pad_x
            min_y -= pad_y
            max_y += pad_y

            points = []
            data_points = []
            for x, y in zip(xs, ys):
                # Map to screen coordinates
                px = rect.left + ((x - min_x) / (max_x - min_x)) * rect.width
                py = rect.bottom - ((y - min_y) / (max_y - min_y)) * rect.height
                points.append((px, py))
                data_points.append((x, y))
            
            # Draw the path with gradient
            if len(points) > 1:
                for i in range(len(points) - 1):
                    t = i / (len(points) - 1)
                    # Fade from dark blue to bright cyan
                    # Start: (0, 40, 80) End: (0, 200, 255)
                    r = 0
                    g = int(40 + (200 - 40) * t)
                    b = int(80 + (255 - 80) * t)
                    pygame.draw.line(surface, (r, g, b), points[i], points[i+1], 2)
                
            # Draw the 'head' (current state)
            if points:
                pygame.draw.circle(surface, (255, 255, 255), points[-1], 4)
                
            # Draw Axis Labels (Min/Max)
            font = self.font
            col_prey = (255, 255, 255) # White for Prey (X)
            col_pred = (255, 0, 0)     # Red for Predator (Y)
            
            # X Axis Labels (Prey)
            s_min_x = font.render(f"{int(min_x)}", True, col_prey)
            s_max_x = font.render(f"{int(max_x)}", True, col_prey)
            surface.blit(s_min_x, (rect.left, rect.bottom + 5))
            surface.blit(s_max_x, (rect.right - s_max_x.get_width(), rect.bottom + 5))
            
            # Y Axis Labels (Predator)
            s_min_y = font.render(f"{int(min_y)}", True, col_pred)
            s_max_y = font.render(f"{int(max_y)}", True, col_pred)
            surface.blit(s_min_y, (rect.left - s_min_y.get_width() - 5, rect.bottom - s_min_y.get_height()))
            surface.blit(s_max_y, (rect.left - s_max_y.get_width() - 5, rect.top))
            
            # Axis Titles
            x_title = font.render("Prey", True, col_prey)
            y_title = font.render("Predator", True, col_pred)
            surface.blit(x_title, (rect.centerx - x_title.get_width()//2, rect.bottom + 20))
            
            y_title_rot = pygame.transform.rotate(y_title, 90)
            surface.blit(y_title_rot, (rect.left - 30, rect.centery - y_title_rot.get_height()//2))

            # Hover logic
            if mouse_pos and rect.collidepoint(mouse_pos):
                # Find closest point
                min_dist = float('inf')
                closest_idx = -1
                mx, my = mouse_pos
                
                for i, (px, py) in enumerate(points):
                    dist = ((px - mx)**2 + (py - my)**2)**0.5
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = i
                
                if closest_idx != -1 and min_dist < 30: # Threshold
                    # Draw popup
                    cx, cy = points[closest_idx]
                    val_x, val_y = data_points[closest_idx]
                    
                    # Draw highlight circle
                    pygame.draw.circle(surface, (255, 255, 0), (int(cx), int(cy)), 6, 2)
                    
                    # Prepare text
                    ratio = (val_x / val_y) if val_y != 0 else 0
                    lines = [
                        f"Prey: {int(val_x)}",
                        f"Pred: {int(val_y)}",
                        f"Prey per Pred: {ratio:.2f}" if val_y != 0 else "Prey per Pred: Infinity"
                    ]
                    
                    # Calculate box size
                    box_w = 0
                    box_h = len(lines) * 20 + 10
                    surfs = []
                    for line in lines:
                        s = self.font.render(line, True, (255, 255, 255))
                        surfs.append(s)
                        box_w = max(box_w, s.get_width())
                    box_w += 20
                    
                    # Position box near mouse but keep in bounds
                    box_x = mx + 15
                    box_y = my + 15
                    if box_x + box_w > rect.right: box_x = mx - box_w - 15
                    if box_y + box_h > rect.bottom: box_y = my - box_h - 15
                    
                    # Draw box
                    pygame.draw.rect(surface, (40, 40, 40), (box_x, box_y, box_w, box_h))
                    pygame.draw.rect(surface, (100, 100, 100), (box_x, box_y, box_w, box_h), 1)
                    
                    # Draw text
                    curr_y = box_y + 5
                    for s in surfs:
                        surface.blit(s, (box_x + 10, curr_y))
                        curr_y += 20
        
        def get_value_at_x(series: list[int | float], rect: pygame.Rect, mouse_x: int) -> float | None:
            """Get the interpolated value from a series at a given x position.
            
            Args:
                series: List of numeric values.
                rect: The rectangle defining the chart area.
                mouse_x: The x coordinate to get the value at.
                
            Returns:
                The interpolated value at the given x position, or None if invalid.
            """
            if len(series) < 2:
                return None
            n = len(series)
            # Calculate the index (possibly fractional) corresponding to mouse_x
            relative_x = mouse_x - rect.left
            index_f = relative_x / rect.width * (n - 1)
            index = int(index_f)
            if index < 0 or index >= n - 1:
                if index == n - 1:
                    return float(series[n - 1])
                return None
            # Linear interpolation between index and index + 1
            t = index_f - index
            val = float(series[index]) * (1 - t) + float(series[index + 1]) * t
            return val
        
        def draw_hover_line(
            surface: pygame.Surface,
            rect: pygame.Rect,
            mouse_x: int,
            series_list: list[tuple[list[int | float], tuple[int, int, int], str]]
        ) -> None:
            """Draw a vertical hover line and display values at intersection points.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                mouse_x: The x coordinate of the mouse.
                series_list: List of tuples (series_data, color, label).
            """
            # Draw vertical line
            pygame.draw.line(surface, (255, 255, 0), (mouse_x, rect.top), (mouse_x, rect.bottom), 1)
            
            # Calculate the round number based on mouse position
            # Use the first non-empty series to determine the round
            round_num = None
            for series, _, _ in series_list:
                if len(series) >= 2:
                    n = len(series)
                    relative_x = mouse_x - rect.left
                    index_f = relative_x / rect.width * (n - 1)
                    round_num = int(round(index_f))
                    round_num = max(0, min(round_num, n - 1))
                    break
            
            # Calculate and display values
            y_offset = rect.top + 5
            
            # Display round number first
            if round_num is not None:
                round_text = f"Round: {round_num}"
                round_surface = self.font.render(round_text, True, (255, 255, 0))
                bg_rect = round_surface.get_rect(topleft=(mouse_x + 10, y_offset))
                bg_rect.inflate_ip(4, 2)
                pygame.draw.rect(surface, (30, 30, 30), bg_rect)
                surface.blit(round_surface, (mouse_x + 10, y_offset))
                y_offset += 18
            
            for series, color, label in series_list:
                val = get_value_at_x(series, rect, mouse_x)
                if val is not None:
                    if val == int(val):
                        text = f"{label}: {int(val)}"
                    else:
                        text = f"{label}: {val:.1f}"
                    text_surface = self.font.render(text, True, color)
                    # Draw background for readability
                    bg_rect = text_surface.get_rect(topleft=(mouse_x + 10, y_offset))
                    bg_rect.inflate_ip(4, 2)
                    pygame.draw.rect(surface, (30, 30, 30), bg_rect)
                    surface.blit(text_surface, (mouse_x + 10, y_offset))
                    y_offset += 18
        
        def draw_statistics_table(surface: pygame.Surface, rect: pygame.Rect) -> None:
            """Draw a table of current statistics."""
            # Calculate stats
            prey_count = config.stats_history["Prey Count"][-1] if config.stats_history["Prey Count"] else 0
            pred_count = config.stats_history["Predator Count"][-1] if config.stats_history["Predator Count"] else 0
            grass_count = round(float(config.stats_history["Grass Total"][-1]) / 1000) if config.stats_history["Grass Total"] else 0
            
            max_prey = max(config.stats_history["Prey Count"]) if config.stats_history["Prey Count"] else 0
            max_pred = max(config.stats_history["Predator Count"]) if config.stats_history["Predator Count"] else 0
            
            avg_prey = sum(config.stats_history["Prey Count"]) / len(config.stats_history["Prey Count"]) if config.stats_history["Prey Count"] else 0
            avg_pred = sum(config.stats_history["Predator Count"]) / len(config.stats_history["Predator Count"]) if config.stats_history["Predator Count"] else 0
            
            ratio = prey_count / pred_count if pred_count > 0 else float('inf')
            
            rows = [
                ("Statistic", "Value"),
                ("-" * 20, "-" * 10),
                ("Current Prey", f"{prey_count}"),
                ("Current Predator", f"{pred_count}"),
                ("Current Grass", f"{grass_count} K"),
                ("", ""),
                ("Max Prey", f"{max_prey}"),
                ("Max Predator", f"{max_pred}"),
                ("", ""),
                ("Avg Prey", f"{avg_prey:.1f}"),
                ("Avg Predator", f"{avg_pred:.1f}"),
                ("", ""),
                ("Prey/Predator Ratio", f"{ratio:.2f}"),
            ]
            
            line_height = 20
            
            # Align the table to the left with a margin
            table_width = 300
            margin = 20
            start_x = rect.left + margin
            start_y = rect.top + 20
            
            col1_x = start_x
            col2_x = start_x + table_width
            
            for label, value in rows:
                label_surf = self.font.render(label, True, (200, 200, 200))
                value_surf = self.font.render(value, True, (255, 255, 255))
                
                surface.blit(label_surf, (col1_x, start_y))
                surface.blit(value_surf, (col2_x - value_surf.get_width(), start_y))
                
                start_y += line_height

        while self.running_stats:
            # Track frame time for FPS calculation
            dt = clock.get_time() / 1000.0
            fps_frame_count += 1
            fps_timer += dt
            
            # Update displayed FPS every 2 seconds
            if fps_timer >= config.FPS_UPDATE_INTERVAL:
                config.current_fps = fps_frame_count / fps_timer
                fps_frame_count = 0
                fps_timer = 0.0

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running_stats = False
                    elif event.key == pygame.K_SPACE:
                        self.simulation_running = not self.simulation_running
                        play_click_sound()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.close_rect.collidepoint(event.pos):
                        register_button_click(self.close_rect)
                        play_click_sound()
                        self.running_stats = False
                    elif self.toggle_sim_rect.collidepoint(event.pos):
                        register_button_click(self.toggle_sim_rect)
                        play_click_sound()
                        self.simulation_running = not self.simulation_running
            
            if self.simulation_running:
                update_simulation(self.predators, self.preys, self.grass)
            
            mouse_pos = pygame.mouse.get_pos()
            
            self.stat_screen.fill((30, 30, 30))
            
            pygame.draw.rect(self.stat_screen, (200,200,200), self.pop_chart_rect, 1)
            pygame.draw.rect(self.stat_screen, (200,200,200), self.event_chart_rect, 1)
            pygame.draw.rect(self.stat_screen, (200,200,200), self.stats_table_rect, 1)
            
            header_parts = [
                ( "Population (", (255,255,255) ),
                ( "Prey", (255,255,255) ),
                ( ", ", (255,255,255) ),
                ( "Predator", (255,0,0) ),
                ( ", ", (255,255,255) ),
                ( "Grass", (0,255,0) ),
                ( ")", (255,255,255) ),
            ]
            x_offset = self.pop_chart_rect.left
            y_offset = self.pop_chart_rect.top - 30
            for text, color in header_parts:
                part = self.font.render(text, True, color)
                self.stat_screen.blit(part, (x_offset, y_offset))
                x_offset += part.get_width()

            events_header_parts = [
                ( "Phase Diagram: Predator vs Prey (Last 20000 Rounds)", (0, 200, 255) ),
            ]
            x_offset = self.event_chart_rect.left
            y_offset = self.event_chart_rect.top - 30
            for text, color in events_header_parts:
                part = self.font.render(text, True, color)
                self.stat_screen.blit(part, (x_offset, y_offset))
                x_offset += part.get_width()
            
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Prey Count"], (255,255,255))
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Predator Count"], (255,0,0))
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Grass Total"], (0,255,0))
            
            draw_phase_diagram(
                self.stat_screen, 
                self.event_chart_rect, 
                config.stats_history["Prey Count"], 
                config.stats_history["Predator Count"],
                mouse_pos=mouse_pos,
                limit=20000
            )
            
            draw_statistics_table(self.stat_screen, self.stats_table_rect)
            
            # Draw hover lines with values when mouse is over a chart
            mouse_x, mouse_y = mouse_pos
            if self.pop_chart_rect.collidepoint(mouse_pos):
                pop_series = [
                    (config.stats_history["Prey Count"], (255,255,255), "Prey"),
                    (config.stats_history["Predator Count"], (255,0,0), "Predator"),
                    (config.stats_history["Grass Total"], (0,255,0), "Grass"),
                ]
                draw_hover_line(self.stat_screen, self.pop_chart_rect, mouse_x, pop_series)
            
            fps_label = self.font.render(f"FPS: {int(config.current_fps)}", True, (255,255,0))
            fps_x = config.XLIM - self.margin - fps_label.get_width()
            self.stat_screen.blit(fps_label, (fps_x, self.margin - config.BUTTON_HEIGHT))
            
            rounds_label = self.font.render(f"Rounds: {config.rounds_passed}", True, (255,255,0))
            rounds_x = fps_x - 20 - rounds_label.get_width()
            self.stat_screen.blit(rounds_label, (rounds_x, self.margin - config.BUTTON_HEIGHT))
            
            draw_button(self.stat_screen, self.close_rect, "Close", self.font, mouse_pos)
            
            toggle_text = "Stop Simulation" if self.simulation_running else "Start Simulation"
            draw_button(self.stat_screen, self.toggle_sim_rect, toggle_text, self.font, mouse_pos)

            pygame.display.flip()
            clock.tick(config.FPS)
            
        # Restore main screen
        pygame.display.set_mode((config.XLIM, config.YLIM))
        pygame.display.set_caption("Simulation")
