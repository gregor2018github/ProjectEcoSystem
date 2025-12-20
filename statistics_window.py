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

class Dropdown:
    def __init__(self, x, y, width, height, options, default_index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = default_index
        self.is_open = False
        self.font = pygame.font.Font(None, 20)
        self.option_rects = []
        for i in range(len(options)):
            self.option_rects.append(pygame.Rect(x, y + (i + 1) * height, width, height))

    def draw(self, surface, mouse_pos):
        # Draw main button
        hover = self.rect.collidepoint(mouse_pos)
        if self.is_open:
            color = (40, 80, 60)
        elif hover:
            color = (80, 120, 100)
        else:
            color = (60, 100, 80)
            
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        
        # Border
        border_color = (255, 255, 255) if hover or self.is_open else (200, 200, 200)
        border_width = 2 if hover or self.is_open else 1
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=4)
        
        text = self.options[self.selected_index]
        text_surf = self.font.render(text, True, (255, 255, 255))
        # Center text
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

        if self.is_open:
            for i, rect in enumerate(self.option_rects):
                opt_hover = rect.collidepoint(mouse_pos)
                opt_color = (70, 70, 70) if opt_hover else (50, 50, 50)
                pygame.draw.rect(surface, opt_color, rect)
                
                opt_border_color = (255, 255, 255) if opt_hover else (200, 200, 200)
                pygame.draw.rect(surface, opt_border_color, rect, 1)
                
                opt_text = self.options[i]
                opt_surf = self.font.render(opt_text, True, (255, 255, 255))
                opt_rect = opt_surf.get_rect(center=rect.center)
                surface.blit(opt_surf, opt_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            from event_handler import play_click_sound
            if self.is_open:
                # Check options
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_open = False
                        play_click_sound()
                        return True
                # Click outside or on main button to close
                self.is_open = False
                play_click_sound()
                return True # Consumed click
            else:
                if self.rect.collidepoint(event.pos):
                    self.is_open = True
                    play_click_sound()
                    return True # Opened
        return False
        return False
    
    def get_value(self):
        return self.options[self.selected_index]

def get_limit_value(text_value):
    # Remove " Rounds" suffix if present
    clean_value = text_value.replace(" Rounds", "")
    
    if clean_value == "MAX":
        return 1000000000 # 1 billion, effectively max
    elif clean_value.endswith("K"):
        return int(clean_value[:-1]) * 1000
    return 20000

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
    
    def __init__(self, predators: list[Predator], preys: list[Prey], grass: GrassArray, simulation_running: bool) -> None:
        """Initialize the statistics window with charts and UI elements."""
        self.predators = predators
        self.preys = preys
        self.grass = grass
        self.simulation_running = simulation_running

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

        # Phase diagram mode: 0: Pred vs Prey, 1: Pred vs Grass, 2: Prey vs Grass
        self.phase_mode = 0
        btn_w = 110
        btn_h = 20
        self.mode_btns = []
        # Position buttons above the phase diagram chart, aligned to the right
        for i in range(3):
            self.mode_btns.append(pygame.Rect(self.event_chart_rect.right - (3-i) * (btn_w + 5), bottom_y - btn_h - 5, btn_w, btn_h))

        # Surfaces for caching charts and table
        self.pop_chart_surf = pygame.Surface((self.pop_chart_rect.width, self.pop_chart_rect.height))
        self.phase_diagram_surf = pygame.Surface((self.event_chart_rect.width, self.event_chart_rect.height))
        self.stats_table_surf = pygame.Surface((self.stats_table_rect.width, self.stats_table_rect.height))
        
        self.last_pop_update = -1
        self.last_phase_update = -1
        self.last_table_update = -1
        
        # Cache for phase diagram hover
        self.phase_points = []
        self.phase_data_points = []
        self.phase_axis_values = None
        self.last_phase_mode = -1

        # Dropdowns
        dropdown_width = 100
        dropdown_height = 20
        
        # Pop chart dropdown
        # Move it to the left to avoid overlap with FPS and Rounds counters
        self.pop_limit_dropdown = Dropdown(
            self.pop_chart_rect.right - dropdown_width - 250,
            self.pop_chart_rect.top - dropdown_height - 5,
            dropdown_width,
            dropdown_height,
            ["20K Rounds", "50K Rounds", "MAX Rounds"]
        )
        
        # Phase chart dropdown
        # Place it to the left of mode buttons
        first_mode_btn_x = self.event_chart_rect.right - 3 * (btn_w + 5)
        self.phase_limit_dropdown = Dropdown(
            first_mode_btn_x - dropdown_width - 10,
            bottom_y - btn_h - 5,
            dropdown_width,
            dropdown_height,
            ["20K Rounds", "50K Rounds", "MAX Rounds"]
        )
        
        self.last_pop_limit = get_limit_value(self.pop_limit_dropdown.get_value())
        self.last_phase_limit = get_limit_value(self.phase_limit_dropdown.get_value())

    def run(self) -> bool:
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
            color: tuple[int, int, int],
            limit: int = config.POPULATION_GRAPH_LIMIT
        ) -> None:
            """Draw a line chart on the given surface.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                series: List of numeric values to plot.
                color: RGB tuple for the line color.
                limit: Maximum number of data points to display.
            """
            if len(series) < 2:
                return
            
            # Slice data to the limit
            start_idx = max(0, len(series) - limit)
            data_slice = series[start_idx:]
            
            if len(data_slice) < 2:
                return

            # Scale series within chart rect
            min_val = float(min(data_slice))
            max_val = float(max(data_slice))
            if max_val == min_val:
                max_val += 1
            points = []
            n = len(data_slice)
            step = rect.width / (n - 1)
            for i, val in enumerate(data_slice):
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
            x_label: str,
            y_label: str,
            x_color: tuple[int, int, int],
            y_color: tuple[int, int, int],
            limit: int = config.PHASE_DIAGRAM_LIMIT
        ) -> tuple[list[tuple[float, float]], list[tuple[float, float]], tuple[float, float, float, float]]:
            """Draw a phase diagram for the recent history.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                x_series: Data for the X axis.
                y_series: Data for the Y axis.
                x_label: Label for the X axis.
                y_label: Label for the Y axis.
                x_color: Color for the X axis labels.
                y_color: Color for the Y axis labels.
                limit: Number of recent data points to show.
            """
            if len(x_series) < 2 or len(y_series) < 2:
                return [], []
            
            # Slice data to the limit
            start_idx = max(0, len(x_series) - limit)
            xs = x_series[start_idx:]
            ys = y_series[start_idx:]
            
            if len(xs) < 2: return [], []

            # Determine scaling range
            min_x, max_x = float(min(xs)), float(max(xs))
            min_y, max_y = float(min(ys)), float(max(ys))
            
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
                # Ensure we use floats to avoid NumPy type issues with pygame
                xf, yf = float(x), float(y)
                px = rect.left + ((xf - min_x) / (max_x - min_x)) * rect.width
                py = rect.bottom - ((yf - min_y) / (max_y - min_y)) * rect.height
                points.append((float(px), float(py)))
                data_points.append((xf, yf))
            
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
                pygame.draw.circle(surface, (255, 255, 255), (float(points[-1][0]), float(points[-1][1])), 4)
                
            return points, data_points, (min_x, max_x, min_y, max_y)

        def draw_phase_labels(
            surface: pygame.Surface,
            rect: pygame.Rect,
            x_label: str,
            y_label: str,
            x_color: tuple[int, int, int],
            y_color: tuple[int, int, int],
            axis_values: tuple[float, float, float, float] | None
        ) -> None:
            """Draw axis labels and titles for the phase diagram."""
            if axis_values is None:
                return
                
            min_x, max_x, min_y, max_y = axis_values
            font = self.font
            
            # X Axis Labels
            s_min_x = font.render(f"{int(min_x)}", True, x_color)
            s_max_x = font.render(f"{int(max_x)}", True, x_color)
            surface.blit(s_min_x, (rect.left, rect.bottom + 5))
            surface.blit(s_max_x, (rect.right - s_max_x.get_width(), rect.bottom + 5))
            
            # Y Axis Labels
            s_min_y = font.render(f"{int(min_y)}", True, y_color)
            s_max_y = font.render(f"{int(max_y)}", True, y_color)
            surface.blit(s_min_y, (rect.left - s_min_y.get_width() - 5, rect.bottom - s_min_y.get_height()))
            surface.blit(s_max_y, (rect.left - s_max_y.get_width() - 5, rect.top))
            
            # Axis Titles
            x_title_surf = font.render(x_label, True, x_color)
            y_title_surf = font.render(y_label, True, y_color)
            surface.blit(x_title_surf, (rect.centerx - x_title_surf.get_width()//2, rect.bottom + 20))
            
            y_title_rot = pygame.transform.rotate(y_title_surf, 90)
            surface.blit(y_title_rot, (rect.left - 30, rect.centery - y_title_rot.get_height()//2))

        def draw_phase_hover(
            surface: pygame.Surface,
            rect: pygame.Rect,
            mouse_pos: tuple[int, int],
            points: list[tuple[float, float]],
            data_points: list[tuple[float, float]],
            x_label: str,
            y_label: str
        ) -> None:
            """Draw hover information for the phase diagram."""
            if not points or not rect.collidepoint(mouse_pos):
                return
                
            # Find closest point
            min_dist = float('inf')
            closest_idx = -1
            mx, my = mouse_pos
            
            for i, (px, py) in enumerate(points):
                # Convert local point to global coordinates
                gpx = px + rect.left
                gpy = py + rect.top
                dist = ((gpx - mx)**2 + (gpy - my)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            
            if closest_idx != -1 and min_dist < 30: # Threshold
                # Draw popup
                px, py = points[closest_idx]
                cx = px + rect.left
                cy = py + rect.top
                val_x, val_y = data_points[closest_idx]
                
                # Draw highlight circle
                pygame.draw.circle(surface, (255, 255, 0), (int(cx), int(cy)), 6, 2)
                
                # Prepare text
                ratio = (val_x / val_y) if val_y != 0 else 0
                lines = [
                    f"{x_label}: {int(val_x)}",
                    f"{y_label}: {int(val_y)}",
                ]
                if x_label == "Prey" and y_label == "Predator":
                    lines.append(f"Prey per Pred: {ratio:.2f}" if val_y != 0 else "Prey per Pred: Infinity")
                elif x_label == "Grass" and y_label == "Predator":
                    lines.append(f"Grass per Pred: {val_x/val_y:.1f}" if val_y != 0 else "Grass per Pred: Infinity")
                elif x_label == "Grass" and y_label == "Prey":
                    lines.append(f"Grass per Prey: {val_x/val_y:.1f}" if val_y != 0 else "Grass per Prey: Infinity")
                
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
            series_list: list[tuple[list[int | float], tuple[int, int, int], str]],
            limit: int = config.POPULATION_GRAPH_LIMIT
        ) -> None:
            """Draw a vertical hover line and display values at intersection points.
            
            Args:
                surface: The pygame surface to draw on.
                rect: The rectangle defining the chart area.
                mouse_x: The x coordinate of the mouse.
                series_list: List of tuples (series_data, color, label).
                limit: Maximum number of data points to display.
            """
            # Draw vertical line
            pygame.draw.line(surface, (255, 255, 0), (mouse_x, rect.top), (mouse_x, rect.bottom), 1)
            
            # Calculate the round number based on mouse position
            # Use the first non-empty series to determine the round
            round_num = None
            for series, _, _ in series_list:
                if len(series) >= 2:
                    # Slice series to match chart display
                    start_idx = max(0, len(series) - limit)
                    sliced_series = series[start_idx:]
                    
                    n = len(sliced_series)
                    if n < 2: continue
                    
                    relative_x = mouse_x - rect.left
                    index_f = relative_x / rect.width * (n - 1)
                    idx = int(round(index_f))
                    idx = max(0, min(idx, n - 1))
                    round_num = start_idx + idx
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
                # Slice series to match chart display
                start_idx = max(0, len(series) - limit)
                sliced_series = series[start_idx:]
                
                val = get_value_at_x(sliced_series, rect, mouse_x)
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
                if self.pop_limit_dropdown.handle_event(event):
                    continue
                if self.phase_limit_dropdown.handle_event(event):
                    continue

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
                    
                    # Check phase diagram mode buttons
                    for i, btn_rect in enumerate(self.mode_btns):
                        if btn_rect.collidepoint(event.pos):
                            register_button_click(btn_rect)
                            play_click_sound()
                            self.phase_mode = i
            
            if self.simulation_running:
                update_simulation(self.predators, self.preys, self.grass)
            
            mouse_pos = pygame.mouse.get_pos()

            # Get current limits
            pop_limit = get_limit_value(self.pop_limit_dropdown.get_value())
            phase_limit = get_limit_value(self.phase_limit_dropdown.get_value())
            
            # Check for changes
            if pop_limit != self.last_pop_limit:
                self.last_pop_update = -1
                self.last_pop_limit = pop_limit
                
            if phase_limit != self.last_phase_limit:
                self.last_phase_update = -1
                self.last_phase_limit = phase_limit

            # Determine series and labels based on mode for phase diagram
            if self.phase_mode == 0: # Pred vs Prey
                x_data = config.stats_history["Prey Count"]
                y_data = config.stats_history["Predator Count"]
                x_label, y_label = "Prey", "Predator"
                x_col, y_col = (255, 255, 255), (255, 0, 0)
            elif self.phase_mode == 1: # Pred vs Grass
                x_data = config.stats_history["Grass Total"]
                y_data = config.stats_history["Predator Count"]
                x_label, y_label = "Grass", "Predator"
                x_col, y_col = (0, 255, 0), (255, 0, 0)
            else: # Prey vs Grass
                x_data = config.stats_history["Grass Total"]
                y_data = config.stats_history["Prey Count"]
                x_label, y_label = "Grass", "Prey"
                x_col, y_col = (0, 255, 0), (255, 255, 255)

            # Update population chart surface
            if config.rounds_passed - self.last_pop_update >= config.UPDATE_SPEED_POPULATION_GRAPH or self.last_pop_update == -1:
                self.pop_chart_surf.fill((30, 30, 30))
                temp_rect = pygame.Rect(0, 0, self.pop_chart_rect.width, self.pop_chart_rect.height)
                draw_line_chart(self.pop_chart_surf, temp_rect, config.stats_history["Prey Count"], (255,255,255), limit=pop_limit)
                draw_line_chart(self.pop_chart_surf, temp_rect, config.stats_history["Predator Count"], (255,0,0), limit=pop_limit)
                draw_line_chart(self.pop_chart_surf, temp_rect, config.stats_history["Grass Total"], (0,255,0), limit=pop_limit)
                self.last_pop_update = config.rounds_passed

            # Update phase diagram surface
            if (config.rounds_passed - self.last_phase_update >= config.UPDATE_SPEED_PHASE_GRAPH or 
                self.last_phase_update == -1 or 
                self.last_phase_mode != self.phase_mode):
                
                self.phase_diagram_surf.fill((30, 30, 30))
                temp_rect = pygame.Rect(0, 0, self.event_chart_rect.width, self.event_chart_rect.height)
                self.phase_points, self.phase_data_points, self.phase_axis_values = draw_phase_diagram(
                    self.phase_diagram_surf, 
                    temp_rect, 
                    x_data, 
                    y_data,
                    x_label,
                    y_label,
                    x_col,
                    y_col,
                    limit=phase_limit
                )
                self.last_phase_update = config.rounds_passed
                self.last_phase_mode = self.phase_mode

            # Update statistics table surface
            if config.rounds_passed - self.last_table_update >= config.UPDATE_SPEED_TABLE or self.last_table_update == -1:
                self.stats_table_surf.fill((30, 30, 30))
                temp_rect = pygame.Rect(0, 0, self.stats_table_rect.width, self.stats_table_rect.height)
                draw_statistics_table(self.stats_table_surf, temp_rect)
                self.last_table_update = config.rounds_passed

            self.stat_screen.fill((30, 30, 30))
            
            # Blit cached surfaces
            self.stat_screen.blit(self.pop_chart_surf, self.pop_chart_rect)
            self.stat_screen.blit(self.phase_diagram_surf, self.event_chart_rect)
            self.stat_screen.blit(self.stats_table_surf, self.stats_table_rect)
            
            # Draw borders
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
            y_offset = self.pop_chart_rect.top - 15
            for text, color in header_parts:
                part = self.font.render(text, True, color)
                self.stat_screen.blit(part, (x_offset, y_offset))
                x_offset += part.get_width()

            # Phase Diagram Header and Mode Selection
            mode_names = ["Pred vs Prey", "Pred vs Grass", "Prey vs Grass"]
            phase_limit_text = f"{phase_limit}" if phase_limit < 1000000000 else "MAX"
            events_header_parts = [
                ( f"Phase Diagram (Last {phase_limit_text} Rounds)", (0, 200, 255) ),
            ]
            x_offset = self.event_chart_rect.left
            y_offset = self.event_chart_rect.top - 15
            for text, color in events_header_parts:
                part = self.font.render(text, True, color)
                self.stat_screen.blit(part, (x_offset, y_offset))
                x_offset += part.get_width()
            
            # Draw mode selection buttons
            for i, btn_rect in enumerate(self.mode_btns):
                # Highlight active mode
                btn_text = mode_names[i]
                if self.phase_mode == i:
                    # Draw a highlight background for the active button
                    pygame.draw.rect(self.stat_screen, (100, 150, 120), btn_rect, border_radius=8)
                
                draw_button(self.stat_screen, btn_rect, btn_text, self.font, mouse_pos)
                
                if self.phase_mode == i:
                    # Add a white border for the active button
                    pygame.draw.rect(self.stat_screen, (255, 255, 255), btn_rect, 2, border_radius=8)

            # Draw phase diagram labels
            draw_phase_labels(
                self.stat_screen,
                self.event_chart_rect,
                x_label,
                y_label,
                x_col,
                y_col,
                self.phase_axis_values
            )

            # Draw phase diagram hover (interactive)
            draw_phase_hover(
                self.stat_screen,
                self.event_chart_rect,
                mouse_pos,
                self.phase_points,
                self.phase_data_points,
                x_label,
                y_label
            )
            
            # Draw hover lines with values when mouse is over a chart
            mouse_x, mouse_y = mouse_pos
            if self.pop_chart_rect.collidepoint(mouse_pos):
                pop_series = [
                    (config.stats_history["Prey Count"], (255,255,255), "Prey"),
                    (config.stats_history["Predator Count"], (255,0,0), "Predator"),
                    (config.stats_history["Grass Total"], (0,255,0), "Grass"),
                ]
                draw_hover_line(self.stat_screen, self.pop_chart_rect, mouse_x, pop_series, limit=pop_limit)
            
            # Draw dropdowns (last to be on top)
            self.pop_limit_dropdown.draw(self.stat_screen, mouse_pos)
            self.phase_limit_dropdown.draw(self.stat_screen, mouse_pos)

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
        return self.simulation_running
