###############################################
# Imports
###############################################

from __future__ import annotations
import pygame
import config
from ui import draw_button, register_button_click
from collections import OrderedDict

###############################################
# Settings Window Class
###############################################

class SettingsWindow:
    """A modal window for viewing and editing simulation settings.
    
    Provides a scrollable list of all configurable simulation parameters
    with inline editing, value increment/decrement controls, and options
    to restart, resume, cancel, or reset to defaults.
    
    Attributes:
        screen: The pygame display surface.
        modal_rect: Rectangle defining the modal window bounds.
        font: Font for header text.
        btn_rect_standard: Rectangle for the Restart button.
        btn_rect_resume: Rectangle for the Resume button.
        btn_rect_cancel: Rectangle for the Cancel button.
        btn_rect_reset: Rectangle for the Reset to Default button.
        settings: OrderedDict of setting names to current values.
        error_fields: Dict tracking fields with invalid input.
        scroll_offset: Current vertical scroll position.
        active_key: Currently selected setting key for editing.
        active_text: Current text value being edited.
        cursor_position: Cursor position within active text.
        running_settings: Whether the settings window is active.
        action: The action taken when closing ('restart', 'resume', 'cancel').
        cursor_timer: Timer for cursor blink animation.
    """
    
    def __init__(self, screen: pygame.Surface) -> None:
        """Initialize the settings window.
        
        Args:
            screen: The pygame display surface to render on.
        """
        self.screen = screen
        # Center the modal window on the screen
        screen_width, screen_height = screen.get_size()
        modal_width, modal_height = 600, 500
        modal_x = (screen_width - modal_width) // 2
        modal_y = (screen_height - modal_height) // 2
        self.modal_rect = pygame.Rect(modal_x, modal_y, modal_width, modal_height)
        self.font = pygame.font.Font(None, 32)
        
        # Center buttons within the modal window
        button_width = 100
        button_height = 40
        button_spacing = 20
        total_button_width = 3 * button_width + 2 * button_spacing
        start_x = self.modal_rect.left + (self.modal_rect.width - total_button_width) // 2
        
        self.btn_rect_standard = pygame.Rect(start_x, self.modal_rect.bottom - 60, button_width, button_height)
        self.btn_rect_resume = pygame.Rect(start_x + button_width + button_spacing, self.modal_rect.bottom - 60, button_width, button_height)
        self.btn_rect_cancel = pygame.Rect(start_x + 2 * (button_width + button_spacing), self.modal_rect.bottom - 60, button_width, button_height)
        
        # Center reset button
        reset_width = 150
        reset_x = self.modal_rect.left + (self.modal_rect.width - reset_width) // 2
        self.btn_rect_reset = pygame.Rect(reset_x, self.modal_rect.bottom - 110, reset_width, 30)
        
        # For trait fields, show current population averages as the editable value (rounded)
        def _avg(avg_dict, attr, fallback):
            val = avg_dict.get(attr, fallback) if avg_dict else fallback
            return round(float(val), 2) if isinstance(val, float) else val

        # Organize settings with section separators for better readability
        self.settings = OrderedDict([
            # Predator Settings
            ("Predator Speed", _avg(config.last_pred_trait_avgs, 'speed', config.PREDATOR_SPEED)),
            ("Predator Avoidance Distance", _avg(config.last_pred_trait_avgs, 'predator_avoid_distance', config.PREDATOR_PREDATOR_AVOID_DISTANCE)),
            ("Predator Smell Distance", _avg(config.last_pred_trait_avgs, 'smell_distance', config.PREDATOR_SMELL_DISTANCE)),
            ("Predator Reproduction Rate", config.PREDATOR_REPRODUCTION_RATE),
            ("Predator Health", _avg(config.last_pred_trait_avgs, 'max_food', config.PREDATOR_MAX_FOOD)),
            ("Predator Food Gain per Kill", _avg(config.last_pred_trait_avgs, 'food_gain_per_kill', config.PREDATOR_FOOD_GAIN_PER_KILL)),
            ("Predator Regular Energy Cost", _avg(config.last_pred_trait_avgs, 'regular_energy_cost', config.PREDATOR_REGULAR_ENERGY_COST)),
            ("Predator Hunting Energy Cost", _avg(config.last_pred_trait_avgs, 'hunting_energy_cost', config.PREDATOR_HUNTING_ENERGY_COST)),
            ("Predator Starvation Border", _avg(config.last_pred_trait_avgs, 'starv_border', config.PREDATOR_STARV_BORDER)),
            ("Predator Max Age", _avg(config.last_pred_trait_avgs, 'max_age', config.PREDATOR_MAX_AGE)),
            ("Predator High Age Health", _avg(config.last_pred_trait_avgs, 'high_age_health', config.PREDATOR_HIGH_AGE_HEALTH)),
            ("", ""),  # Section separator

            # Prey Settings
            ("Prey Speed", _avg(config.last_prey_trait_avgs, 'speed', config.PREY_SPEED)),
            ("Prey Fear Distance", _avg(config.last_prey_trait_avgs, 'fear_distance', config.PREY_FEAR_DISTANCE)),
            ("Prey Reproduction Rate", config.PREY_REPRODUCTION_RATE),
            ("Prey Food Gain per Grass", _avg(config.last_prey_trait_avgs, 'food_gain_per_grass', config.PREY_FOOD_GAIN_PER_GRASS)),
            ("Prey Health", _avg(config.last_prey_trait_avgs, 'max_food', config.PREY_MAX_FOOD)),
            ("Prey Starvation Border", _avg(config.last_prey_trait_avgs, 'starv_border', config.PREY_STARV_BORDER)),
            ("Prey Regular Energy Cost", config.PREY_REGULAR_ENERGY_COST),
            ("Prey Flee Energy Cost", _avg(config.last_prey_trait_avgs, 'flee_energy_cost', config.PREY_FLEE_ENERGY_COST)),
            ("Prey Max Age", _avg(config.last_prey_trait_avgs, 'max_age', config.PREY_MAX_AGE)),
            ("Prey High Age Health", _avg(config.last_prey_trait_avgs, 'high_age_health', config.PREY_HIGH_AGE_HEALTH)),
            ("", ""),  # Section separator

            # Environment Settings
            ("Grass Growth Rate", config.GRASS_GROWTH_RATE),
            ("Grass max per Field", config.GRASS_MAX_AMOUNT),
            ("Grass Start Value", config.DEFAULT_GRASS_AMOUNT),
            ("", ""),  # Section separator

            # System Settings
            ("FPS", config.FPS)
        ])

        # Reference values shown in the label: start snapshot for trait fields, std for others
        self.reference_values = {}
        for key in self.settings:
            if key in config.SETTINGS_TO_PRED_TRAIT:
                attr = config.SETTINGS_TO_PRED_TRAIT[key]
                self.reference_values[key] = config.start_pred_traits.get(attr, config.default_settings.get(key, ''))
            elif key in config.SETTINGS_TO_PREY_TRAIT:
                attr = config.SETTINGS_TO_PREY_TRAIT[key]
                self.reference_values[key] = config.start_prey_traits.get(attr, config.default_settings.get(key, ''))
            else:
                self.reference_values[key] = config.default_settings.get(key, '')
        
        self.error_fields = {}
        self.scroll_offset = 0
        self.active_key = None
        self.active_text = ""
        self.cursor_position = 0  # Position of text cursor within the active text
        self.running_settings = True
        self.action = None
        self.cursor_timer = 0  # For blinking cursor

###############################################
# Settings Window Main Loop
################################################

    def run(self) -> tuple[str | None, OrderedDict[str, int | float | str]]:
        """Run the settings window event loop.
        
        Displays all simulation settings with inline editing capabilities.
        Supports the following keyboard controls:
        - Left/Right Arrow Keys: Move cursor position within the text field
        - Up/Down Arrow Keys: Increment/decrement the selected setting value
          (increments by 1 for integers, 0.1 for floating point values)
        - Home/End Keys: Move cursor to beginning/end of text
        - Delete Key: Delete character at cursor position
        - Backspace: Delete character before cursor
        - Enter: Confirm the current value
        - Escape: Cancel editing and restore original value
        
        Returns:
            A tuple containing:
                - action: The action taken ('restart', 'resume', 'cancel', or None)
                - settings: OrderedDict of all settings with their final values
        """
        clock = pygame.time.Clock()  # For cursor blinking timing
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
                            # Skip separator lines when handling clicks
                            if key == "":
                                continue
                            line_rect = pygame.Rect(params_area.left, params_area.top + i*30 + self.scroll_offset, params_area.width, 30)
                            if line_rect.collidepoint(event.pos):
                                self.active_key = key
                                self.active_text = str(self.settings[key])
                                self.cursor_position = len(self.active_text)  # Set cursor to end of text
                                self.error_fields.pop(key, None)
                                break
                if event.type == pygame.KEYDOWN and self.active_key is not None:
                    if event.key == pygame.K_BACKSPACE:
                        if self.cursor_position > 0:
                            self.active_text = self.active_text[:self.cursor_position-1] + self.active_text[self.cursor_position:]
                            self.cursor_position -= 1
                            self.settings[self.active_key] = self.active_text
                    elif event.key == pygame.K_DELETE:
                        if self.cursor_position < len(self.active_text):
                            self.active_text = self.active_text[:self.cursor_position] + self.active_text[self.cursor_position+1:]
                            self.settings[self.active_key] = self.active_text
                    elif event.key == pygame.K_LEFT:
                        # Move cursor left
                        self.cursor_position = max(0, self.cursor_position - 1)
                    elif event.key == pygame.K_RIGHT:
                        # Move cursor right
                        self.cursor_position = min(len(self.active_text), self.cursor_position + 1)
                    elif event.key == pygame.K_HOME:
                        # Move cursor to beginning
                        self.cursor_position = 0
                    elif event.key == pygame.K_END:
                        # Move cursor to end
                        self.cursor_position = len(self.active_text)
                    elif event.key == pygame.K_ESCAPE:
                        # Cancel editing and restore reference value (start stats for traits, std for others)
                        if self.active_key is not None:
                            original_val = self.reference_values.get(self.active_key, config.default_settings.get(self.active_key, self.settings[self.active_key]))
                            self.settings[self.active_key] = original_val
                            self.active_key = None
                            self.active_text = ""
                            self.cursor_position = 0
                            self.error_fields.clear()
                    elif event.key == pygame.K_UP:
                        # Increase value by 1 (or 0.1 for decimals)
                        try:
                            current_val = float(self.active_text) if self.active_text else 0
                            # Determine increment based on default setting type and current value
                            default_val = config.default_settings[self.active_key]
                            if isinstance(default_val, float) or '.' in self.active_text:
                                increment = 0.1
                                # For very small values, use smaller increments
                                if abs(current_val) < 1.0:
                                    increment = 0.01
                            else:
                                increment = 1
                            new_val = current_val + increment
                            # Round to appropriate decimal places
                            if increment == 0.01:
                                new_val = round(new_val, 3)
                            elif increment == 0.1:
                                new_val = round(new_val, 2)
                            self.active_text = str(new_val)
                            self.cursor_position = len(self.active_text)
                            self.settings[self.active_key] = self.active_text
                            self.error_fields.pop(self.active_key, None)
                        except ValueError:
                            pass  # Ignore if current text is not a valid number
                    elif event.key == pygame.K_DOWN:
                        # Decrease value by 1 (or 0.1 for decimals)
                        try:
                            current_val = float(self.active_text) if self.active_text else 0
                            # Determine increment based on default setting type and current value
                            default_val = config.default_settings[self.active_key]
                            if isinstance(default_val, float) or '.' in self.active_text:
                                increment = 0.1
                                # For very small values, use smaller increments
                                if abs(current_val) < 1.0:
                                    increment = 0.01
                            else:
                                increment = 1
                            new_val = current_val - increment
                            # Round to appropriate decimal places
                            if increment == 0.01:
                                new_val = round(new_val, 3)
                            elif increment == 0.1:
                                new_val = round(new_val, 2)
                            # Prevent negative values for most settings (but allow negative for some like energy costs)
                            if "Cost" not in self.active_key and "Rate" not in self.active_key:
                                new_val = max(0, new_val)
                            self.active_text = str(new_val)
                            self.cursor_position = len(self.active_text)
                            self.settings[self.active_key] = self.active_text
                            self.error_fields.pop(self.active_key, None)
                        except ValueError:
                            pass  # Ignore if current text is not a valid number
                    elif event.key == pygame.K_RETURN:
                        try:
                            val = float(self.active_text)
                            if val.is_integer():
                                val = int(val)
                            self.settings[self.active_key] = val
                            self.error_fields.pop(self.active_key, None)
                            self.active_key = None
                            self.active_text = ""
                            self.cursor_position = 0
                            self.cursor_position = 0
                        except ValueError:
                            self.error_fields[self.active_key] = True
                    else:
                        if event.unicode in "0123456789.-":
                            # Insert character at cursor position
                            self.active_text = self.active_text[:self.cursor_position] + event.unicode + self.active_text[self.cursor_position:]
                            self.cursor_position += 1
                            self.settings[self.active_key] = self.active_text
                if event.type == pygame.MOUSEWHEEL:
                    self.scroll_offset += event.y * 20

            params_area = pygame.Rect(self.modal_rect.left + 50, self.modal_rect.top + 70, self.modal_rect.width - 100, self.modal_rect.height - 220)
            total_content = len(self.settings) * 30
            # Add padding at both top and bottom for better visual spacing
            padding_top = 10     # Extra space at the top
            padding_bottom = 40  # Extra space to keep last line visible
            min_scroll = min(0, params_area.height - total_content - padding_bottom)
            max_scroll = padding_top  # Allow scrolling beyond 0 to create top padding
            self.scroll_offset = max(min_scroll, min(max_scroll, self.scroll_offset))
            
            # Update cursor timer for blinking effect
            self.cursor_timer += clock.get_time()
            
            pygame.draw.rect(self.screen, (240,240,240), self.modal_rect)
            header = self.font.render("Simulation Settings", True, (0,0,0))
            self.screen.blit(header, (self.modal_rect.centerx - header.get_width()//2, self.modal_rect.top + 20))
            
            pygame.draw.rect(self.screen, (200, 200, 200), params_area)
            param_font = pygame.font.Font(None, 24)
            keys = list(self.settings.keys())
            for i, key in enumerate(keys):
                y = params_area.top + i * 30 + self.scroll_offset
                # Ensure there's enough space for the full line height (30px) before the bottom of params_area
                if y >= params_area.top and y + 30 <= params_area.bottom:
                    # Skip rendering for section separators (empty lines)
                    if key == "":
                        continue
                        
                    text_val = str(self.settings[key])
                    rect = pygame.Rect(params_area.left, y - 5, params_area.width, 30)
                    if key == self.active_key:
                        if self.error_fields.get(key, False):
                            pygame.draw.rect(self.screen, (255, 0, 0), rect)
                        else:
                            pygame.draw.rect(self.screen, (180, 180, 250), rect)
                    ref_val = self.reference_values.get(key, config.default_settings.get(key, ''))
                    ref_lbl = "start" if (key in config.SETTINGS_TO_PRED_TRAIT or key in config.SETTINGS_TO_PREY_TRAIT) else "std"
                    label = f"{key} ({ref_lbl}: {ref_val}): {text_val}"
                    text_surface = param_font.render(label, True, (0,0,0))
                    # Center text vertically within the rect
                    text_y = rect.top + (rect.height - text_surface.get_height()) // 2
                    self.screen.blit(text_surface, (rect.left + 10, text_y))
                    if key == self.active_key and (self.cursor_timer // 500) % 2:  # Blink every 500ms
                        # Calculate cursor position within the text
                        label_prefix = f"{key} ({ref_lbl}: {ref_val}): "
                        text_before_cursor = label_prefix + text_val[:self.cursor_position]
                        caret_x = rect.left + 10 + param_font.size(text_before_cursor)[0]
                        caret_y = text_y
                        caret_height = param_font.get_height()
                        pygame.draw.line(self.screen, (0,0,0), (caret_x, caret_y), (caret_x, caret_y + caret_height), 2)
            
            # Draw scrollbar
            if total_content > params_area.height:
                scrollbar_width = 10
                scrollbar_x = params_area.right - scrollbar_width
                scrollbar_rect = pygame.Rect(scrollbar_x, params_area.top, scrollbar_width, params_area.height)
                pygame.draw.rect(self.screen, (150, 150, 150), scrollbar_rect)
                
                # Calculate thumb position and size
                content_ratio = params_area.height / (total_content + padding_bottom)
                thumb_height = max(20, int(params_area.height * content_ratio))
                scroll_range = max_scroll - min_scroll
                if scroll_range > 0:
                    # when scroll_offset is negative (scrolled down), thumb should be lower
                    thumb_y = params_area.top + int((max_scroll - self.scroll_offset) / scroll_range * (params_area.height - thumb_height))
                else:
                    thumb_y = params_area.top
                
                thumb_rect = pygame.Rect(scrollbar_x, thumb_y, scrollbar_width, thumb_height)
                pygame.draw.rect(self.screen, (100, 100, 100), thumb_rect)
            
            btn_font = pygame.font.Font(None, 24)
            draw_button(self.screen, self.btn_rect_standard, "Restart", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_resume, "Resume", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_cancel, "Cancel", btn_font, mouse_pos_settings)
            draw_button(self.screen, self.btn_rect_reset, "Reset to std", btn_font, mouse_pos_settings)
            pygame.display.flip()
            clock.tick(60)  # 60 FPS for smooth cursor blinking

        for key in self.settings:
            # Skip separator lines in final validation
            if key == "":
                continue
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
