import pygame
import config
from ui import draw_button, register_button_click

class SettingsWindow:
    def __init__(self, screen):
        self.screen = screen
        self.modal_rect = pygame.Rect(200, 100, 600, 400)
        self.font = pygame.font.Font(None, 32)
        self.btn_rect_standard = pygame.Rect(self.modal_rect.left + 50, self.modal_rect.bottom - 60, 100, 40)
        self.btn_rect_resume = pygame.Rect(self.modal_rect.left + 250, self.modal_rect.bottom - 60, 100, 40)
        self.btn_rect_cancel = pygame.Rect(self.modal_rect.left + 450, self.modal_rect.bottom - 60, 100, 40)
        self.btn_rect_reset = pygame.Rect(self.modal_rect.left + 250, self.modal_rect.bottom - 110, 150, 30)
        
        self.settings = {
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
        self.error_fields = {}
        self.scroll_offset = 0
        self.active_key = None
        self.active_text = ""
        self.running_settings = True
        self.action = None

    def run(self):
        while self.running_settings:
            mouse_pos_settings = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running_settings = False
                    self.action = "cancel"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_rect_standard.collidepoint(event.pos):
                        register_button_click(self.btn_rect_standard)
                        if self.active_key is not None:
                            try:
                                val = float(self.active_text)
                                if val.is_integer():
                                    val = int(val)
                                self.settings[self.active_key] = val
                                self.error_fields.pop(self.active_key, None)
                            except ValueError:
                                self.error_fields[self.active_key] = True
                                continue
                        self.action = "restart"
                        self.running_settings = False
                    elif self.btn_rect_resume.collidepoint(event.pos):
                        register_button_click(self.btn_rect_resume)
                        if self.active_key is not None:
                            try:
                                val = float(self.active_text)
                                if val.is_integer():
                                    val = int(val)
                                self.settings[self.active_key] = val
                                self.error_fields.pop(self.active_key, None)
                            except ValueError:
                                self.error_fields[self.active_key] = True
                                continue
                        self.action = "resume"
                        self.running_settings = False
                    elif self.btn_rect_cancel.collidepoint(event.pos):
                        register_button_click(self.btn_rect_cancel)
                        self.action = "cancel"
                        self.running_settings = False
                    elif self.btn_rect_reset.collidepoint(event.pos):
                        register_button_click(self.btn_rect_reset)
                        for key, value in config.default_settings.items():
                            self.settings[key] = value
                            self.error_fields.pop(key, None)
                    else:
                        params_area = pygame.Rect(self.modal_rect.left + 50, self.modal_rect.top + 70, self.modal_rect.width - 100, self.modal_rect.height - 220)
                        keys_list = list(self.settings.keys())
                        for i, key in enumerate(keys_list):
                            line_rect = pygame.Rect(params_area.left, params_area.top + i*30 + self.scroll_offset, params_area.width, 30)
                            if line_rect.collidepoint(event.pos):
                                self.active_key = key
                                self.active_text = str(self.settings[key])
                                self.error_fields.pop(key, None)
                                break
                if event.type == pygame.KEYDOWN and self.active_key is not None:
                    if event.key == pygame.K_BACKSPACE:
                        self.active_text = self.active_text[:-1]
                        self.settings[self.active_key] = self.active_text
                    elif event.key == pygame.K_RETURN:
                        try:
                            val = float(self.active_text)
                            if val.is_integer():
                                val = int(val)
                            self.settings[self.active_key] = val
                            self.error_fields.pop(self.active_key, None)
                            self.active_key = None
                            self.active_text = ""
                        except ValueError:
                            self.error_fields[self.active_key] = True
                    else:
                        if event.unicode in "0123456789.-":
                            self.active_text += event.unicode
                        self.settings[self.active_key] = self.active_text
                if event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset += event.y * 20
            
            params_area = pygame.Rect(self.modal_rect.left + 50, self.modal_rect.top + 70, self.modal_rect.width - 100, self.modal_rect.height - 220)
            total_content = len(self.settings) * 30
            min_scroll = min(0, params_area.height - total_content)
            self.scroll_offset = max(min_scroll, min(0, self.scroll_offset))
            
            pygame.draw.rect(self.screen, (240,240,240), self.modal_rect)
            header = self.font.render("Simulation Settings", True, (0,0,0))
            self.screen.blit(header, (self.modal_rect.centerx - header.get_width()//2, self.modal_rect.top + 20))
            
            pygame.draw.rect(self.screen, (200, 200, 200), params_area)
            param_font = pygame.font.Font(None, 24)
            keys = list(self.settings.keys())
            for i, key in enumerate(keys):
                y = params_area.top + i * 30 + self.scroll_offset
                if y >= params_area.top and y < params_area.bottom:
                    text_val = str(self.settings[key])
                    rect = pygame.Rect(params_area.left, y - 5, params_area.width, 30)
                    if key == self.active_key:
                        if self.error_fields.get(key, False):
                            pygame.draw.rect(self.screen, (255, 0, 0), rect)
                        else:
                            pygame.draw.rect(self.screen, (180, 180, 250), rect)
                    label = f"{key} (std: {config.default_settings[key]}): {text_val}"
                    text_surface = param_font.render(label, True, (0,0,0))
                    self.screen.blit(text_surface, (rect.left + 10, rect.top + 5))
                    if key == self.active_key:
                        caret_x = rect.left + 10 + param_font.size(label)[0]
                        caret_y = rect.top + 5
                        caret_height = param_font.get_height()
                        pygame.draw.line(self.screen, (0,0,0), (caret_x, caret_y), (caret_x, caret_y + caret_height), 2)
            
            btn_font = pygame.font.Font(None, 24)
            draw_button(self.screen, self.btn_rect_standard, "Restart", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_resume, "Resume", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_cancel, "Cancel", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_reset, "Reset to std", btn_font, mouse_pos_settings)
            pygame.display.flip()

        for key in self.settings:
            if isinstance(self.settings[key], str):
                try:
                    num_val = float(self.settings[key])
                    if num_val.is_integer():
                        self.settings[key] = int(num_val)
                    else:
                        self.settings[key] = num_val
                except ValueError:
                    self.settings[key] = config.default_settings[key]
        return self.action, self.settings
