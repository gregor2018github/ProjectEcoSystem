import pygame
import config
from ui import draw_button, register_button_click

class StatisticsWindow:
    def __init__(self):
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

    def run(self):
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
            
            rounds_label = self.font.render(f"Rounds: {config.rounds_passed}", True, (255,255,0))
            self.stat_screen.blit(rounds_label, (self.margin, config.YLIM - self.margin - config.BUTTON_HEIGHT - 25))
            draw_button(self.stat_screen, self.close_rect, "Close", self.font, mouse_pos)
            pygame.display.flip()
            
        # Restore main screen
        pygame.display.set_mode((config.XLIM, config.YLIM))
        pygame.display.set_caption("Simulation")
