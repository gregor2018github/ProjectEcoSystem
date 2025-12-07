################################################
# Imports
################################################

from __future__ import annotations
import pygame
import config
from ui import draw_button, register_button_click

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
    
    def __init__(self) -> None:
        """Initialize the statistics window with charts and UI elements."""
        self.stat_screen = pygame.display.set_mode((config.XLIM, config.YLIM))
        pygame.display.set_caption("Statistics")
        self.font = pygame.font.Font(None, 20)
        self.running_stats = True

        self.margin = 40
        self.chart_width = config.XLIM - 2 * self.margin
        self.chart_height = int((config.YLIM - 3 * self.margin - config.BUTTON_HEIGHT) / 2)
        self.pop_chart_rect = pygame.Rect(self.margin, self.margin, self.chart_width, self.chart_height)
        self.event_chart_rect = pygame.Rect(self.margin, self.margin + self.chart_height + self.margin, self.chart_width, self.chart_height)
        self.close_rect = pygame.Rect((config.XLIM - config.BUTTON_WIDTH) // 2, config.YLIM - self.margin - config.BUTTON_HEIGHT + 10, config.BUTTON_WIDTH, config.BUTTON_HEIGHT)

    def run(self) -> None:
        """Run the statistics window event loop.
        
        Displays population and event charts, handles user input,
        and closes when the user presses Escape or clicks the Close button.
        """
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
        
        while self.running_stats:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.running_stats = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.close_rect.collidepoint(event.pos):
                        register_button_click(self.close_rect)
                        self.running_stats = False
            
            mouse_pos = pygame.mouse.get_pos()
            
            self.stat_screen.fill((30, 30, 30))
            
            pygame.draw.rect(self.stat_screen, (200,200,200), self.pop_chart_rect, 1)
            pygame.draw.rect(self.stat_screen, (200,200,200), self.event_chart_rect, 1)
            
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
            x_offset = self.event_chart_rect.left
            y_offset = self.event_chart_rect.top - 30
            for text, color in events_header_parts:
                part = self.font.render(text, True, color)
                self.stat_screen.blit(part, (x_offset, y_offset))
                x_offset += part.get_width()
            
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Prey Count"], (255,255,255))
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Predator Count"], (255,0,0))
            draw_line_chart(self.stat_screen, self.pop_chart_rect, config.stats_history["Grass Total"], (0,255,0))
            
            draw_line_chart(self.stat_screen, self.event_chart_rect, config.stats_history["Prey deceased"], (150,150,150))
            draw_line_chart(self.stat_screen, self.event_chart_rect, config.stats_history["Predator deceased"], (255,165,0))
            draw_line_chart(self.stat_screen, self.event_chart_rect, config.stats_history["Prey born"], (0,255,0))
            draw_line_chart(self.stat_screen, self.event_chart_rect, config.stats_history["Predator born"], (0,0,255))
            
            # Draw hover lines with values when mouse is over a chart
            mouse_x, mouse_y = mouse_pos
            if self.pop_chart_rect.collidepoint(mouse_pos):
                pop_series = [
                    (config.stats_history["Prey Count"], (255,255,255), "Prey"),
                    (config.stats_history["Predator Count"], (255,0,0), "Predator"),
                    (config.stats_history["Grass Total"], (0,255,0), "Grass"),
                ]
                draw_hover_line(self.stat_screen, self.pop_chart_rect, mouse_x, pop_series)
            elif self.event_chart_rect.collidepoint(mouse_pos):
                event_series = [
                    (config.stats_history["Prey deceased"], (150,150,150), "Prey deceased"),
                    (config.stats_history["Predator deceased"], (255,165,0), "Predator deceased"),
                    (config.stats_history["Prey born"], (0,255,0), "Prey born"),
                    (config.stats_history["Predator born"], (0,0,255), "Predator born"),
                ]
                draw_hover_line(self.stat_screen, self.event_chart_rect, mouse_x, event_series)
            
            rounds_label = self.font.render(f"Rounds: {config.rounds_passed}", True, (255,255,0))
            self.stat_screen.blit(rounds_label, (self.margin, config.YLIM - self.margin - config.BUTTON_HEIGHT - 25))
            draw_button(self.stat_screen, self.close_rect, "Close", self.font, mouse_pos)
            pygame.display.flip()
            
        # Restore main screen
        pygame.display.set_mode((config.XLIM, config.YLIM))
        pygame.display.set_caption("Simulation")
