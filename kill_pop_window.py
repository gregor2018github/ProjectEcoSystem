###############################################
# Kill Population Window
###############################################

from __future__ import annotations
import pygame
import random
import config
from ui import draw_button, register_button_click

_BG          = (30, 40, 35)
_BORDER      = (80, 160, 100)
_TITLE       = (200, 230, 200)
_LABEL       = (180, 210, 180)
_VALUE       = (220, 240, 220)
_INPUT_BG    = (20, 35, 25)
_INPUT_ACT   = (25, 50, 35)
_BRD_ACT     = (100, 200, 130)
_BRD_IDLE    = (60, 100, 70)
_CALC        = (150, 200, 150)
_CALC_NONE   = (80, 110, 80)
_ERROR       = (220, 80, 80)
_HDR         = (120, 160, 120)
_CONF_BG     = (40, 20, 20)
_CONF_BORDER = (180, 60, 60)
_CONF_TITLE  = (240, 120, 120)
_CONF_LINE   = (220, 180, 180)
_COL_PRED    = (220, 80, 80)
_COL_PREY    = (255, 255, 255)
_COL_GRASS   = (60, 180, 60)


class KillPopWindow:
    """Modal window to kill a percentage of predators, prey, and/or grass."""

    def __init__(self, screen: pygame.Surface, pred_arrays, prey_arrays, grass) -> None:
        self.screen = screen
        self.pred_arrays = pred_arrays
        self.prey_arrays = prey_arrays
        self.grass = grass

        sw, sh = screen.get_size()
        mw, mh = 500, 315
        self.modal_rect = pygame.Rect((sw - mw) // 2, (sh - mh) // 2, mw, mh)

        self.font_title = pygame.font.Font(None, 32)
        self.font       = pygame.font.Font(None, 26)
        self.font_small = pygame.font.Font(None, 22)

        self._rows = [
            {'label': 'Predators', 'color': _COL_PRED},
            {'label': 'Prey',      'color': _COL_PREY},
            {'label': 'Grass',     'color': _COL_GRASS},
        ]
        self.percents: list[str] = ['', '', '']
        self.active_row: int | None = None
        self.errors: list[bool]     = [False, False, False]
        self.input_rects: list[pygame.Rect] = []

        bw, bh = 110, 36
        bx = self.modal_rect.left + (mw - 2 * bw - 20) // 2
        by = self.modal_rect.bottom - 52
        self.btn_ok     = pygame.Rect(bx,          by, bw, bh)
        self.btn_cancel = pygame.Rect(bx + bw + 20, by, bw, bh)

        # confirm buttons are created at draw time (inside _draw_confirm_phase)
        self.btn_confirm_yes = pygame.Rect(0, 0, 0, 0)
        self.btn_confirm_no  = pygame.Rect(0, 0, 0, 0)

        self.phase    = 'input'    # 'input' | 'confirm'
        self.running  = True
        self.result   = None       # None = cancelled, 'killed' = applied

        self._pending_percents: list[float] = []
        self._pending_counts:   list[float] = []

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_counts(self) -> list[float]:
        return [
            float(self.pred_arrays.count),
            float(self.prey_arrays.count),
            float(self.grass.amounts.sum()),
        ]

    def _parse_percent(self, idx: int) -> float | None:
        text = self.percents[idx].strip()
        if text == '':
            return 0.0
        try:
            val = float(text)
            if 0.0 <= val <= 100.0:
                return val
        except ValueError:
            pass
        return None

    def _calc_label(self, idx: int, counts: list[float]) -> tuple[str, tuple]:
        val = self._parse_percent(idx)
        text = self.percents[idx].strip()
        if text == '' or val == 0.0:
            return ("— no change", _CALC_NONE)
        if val is None:
            return ("invalid %", _ERROR)
        c = counts[idx]
        if idx < 2:
            killed = int(round(c * val / 100.0))
            return (f"= {killed} animals", _CALC)
        else:
            return (f"= {val:.0f}% reduced", _CALC)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw_input_phase(self, mouse_pos: tuple) -> None:
        pygame.draw.rect(self.screen, _BG, self.modal_rect, border_radius=12)
        pygame.draw.rect(self.screen, _BORDER, self.modal_rect, 2, border_radius=12)

        # Title
        t = self.font_title.render("Kill Population", True, _TITLE)
        self.screen.blit(t, (self.modal_rect.left + (self.modal_rect.width - t.get_width()) // 2,
                             self.modal_rect.top + 14))

        # Column header positions
        lx  = self.modal_rect.left + 20   # Type label
        cx  = self.modal_rect.left + 165  # Current count
        px  = self.modal_rect.left + 255  # Kill % input
        rx  = self.modal_rect.left + 340  # Result calc
        hy  = self.modal_rect.top + 52

        for text, x in [("Type", lx), ("Current", cx), ("Kill %", px), ("Result", rx)]:
            s = self.font_small.render(text, True, _HDR)
            self.screen.blit(s, (x, hy))
        pygame.draw.line(self.screen, (60, 100, 70),
                         (self.modal_rect.left + 15, hy + 18),
                         (self.modal_rect.right - 15, hy + 18), 1)

        counts = self._get_counts()
        row_y0   = hy + 26
        row_h    = 42
        input_w  = 58
        input_h  = 28

        self.input_rects = []
        for i, row in enumerate(self._rows):
            ry = row_y0 + i * row_h

            # Label
            self.screen.blit(self.font.render(row['label'], True, row['color']),
                             (lx, ry + 5))

            # Current count
            c = counts[i]
            count_str = str(int(c)) if i < 2 else f"{c:.0f}"
            self.screen.blit(self.font.render(count_str, True, _VALUE), (cx, ry + 5))

            # Input box
            inp_rect = pygame.Rect(px, ry + 3, input_w, input_h)
            self.input_rects.append(inp_rect)
            is_active = self.active_row == i
            is_error  = self.errors[i]

            if is_error:
                brd, bg = _ERROR, (50, 20, 20)
            elif is_active:
                brd, bg = _BRD_ACT, _INPUT_ACT
            else:
                brd, bg = _BRD_IDLE, _INPUT_BG

            pygame.draw.rect(self.screen, bg,  inp_rect, border_radius=4)
            pygame.draw.rect(self.screen, brd, inp_rect, 1, border_radius=4)

            ts = self.font.render(self.percents[i], True, _VALUE)
            self.screen.blit(ts, (inp_rect.left + 5,
                                  inp_rect.top + (input_h - ts.get_height()) // 2))

            self.screen.blit(self.font_small.render("%", True, _HDR),
                             (inp_rect.right + 3, ry + 8))

            # Result
            calc_str, calc_color = self._calc_label(i, counts)
            self.screen.blit(self.font_small.render(calc_str, True, calc_color), (rx, ry + 8))

        # Buttons
        draw_button(self.screen, self.btn_ok,     "Kill!",  self.font, mouse_pos)
        draw_button(self.screen, self.btn_cancel, "Cancel", self.font, mouse_pos)

    def _draw_confirm_phase(self) -> None:
        # Fully cover the input modal with the same dimensions
        conf_rect = self.modal_rect
        cx, cy = conf_rect.left, conf_rect.top
        cw, ch = conf_rect.width, conf_rect.height

        pygame.draw.rect(self.screen, _CONF_BG,     conf_rect, border_radius=12)
        pygame.draw.rect(self.screen, _CONF_BORDER, conf_rect, 2, border_radius=12)

        t = self.font_title.render("Confirm Kill", True, _CONF_TITLE)
        self.screen.blit(t, (cx + (cw - t.get_width()) // 2, cy + 20))

        pygame.draw.line(self.screen, (120, 40, 40),
                         (cx + 15, cy + 52), (cx + cw - 15, cy + 52), 1)

        names  = ['Predators', 'Prey', 'Grass']
        counts = self._pending_counts
        lines  = []
        for i, (name, pct) in enumerate(zip(names, self._pending_percents)):
            if pct == 0.0:
                continue
            if i < 2:
                killed = int(round(counts[i] * pct / 100.0))
                lines.append(f"{name}: {pct:.0f}%  ->  {killed} killed")
            else:
                lines.append(f"Grass: {pct:.0f}% reduction")

        if not lines:
            lines = ["Nothing will be changed."]

        # Vertically center lines in the space above the buttons
        content_top    = cy + 62
        content_bottom = cy + ch - 70
        total_h = len(lines) * 30
        y = content_top + (content_bottom - content_top - total_h) // 2
        for line in lines:
            s = self.font.render(line, True, _CONF_LINE)
            self.screen.blit(s, (cx + (cw - s.get_width()) // 2, y))
            y += 30

        # Buttons aligned to the bottom of the modal
        bw, bh = 120, 36
        bx = cx + (cw - 2 * bw - 20) // 2
        by = cy + ch - 52
        self.btn_confirm_yes = pygame.Rect(bx,          by, bw, bh)
        self.btn_confirm_no  = pygame.Rect(bx + bw + 20, by, bw, bh)

        mp = pygame.mouse.get_pos()
        draw_button(self.screen, self.btn_confirm_yes, "Confirm", self.font, mp)
        draw_button(self.screen, self.btn_confirm_no,  "Go Back", self.font, mp)

    # ------------------------------------------------------------------
    # Kill application
    # ------------------------------------------------------------------

    def _apply_kills(self) -> None:
        percents = self._pending_percents

        # Predators
        pct = percents[0]
        if pct > 0 and self.pred_arrays.count > 0:
            n_kill = int(round(self.pred_arrays.count * pct / 100.0))
            n_kill = min(n_kill, self.pred_arrays.count)
            indices = random.sample(range(self.pred_arrays.count), n_kill)
            for idx in indices:
                self.pred_arrays.alive[idx] = 0
            self.pred_arrays.compact()
            config.predator_deceased += n_kill

        # Prey
        pct = percents[1]
        if pct > 0 and self.prey_arrays.count > 0:
            n_kill = int(round(self.prey_arrays.count * pct / 100.0))
            n_kill = min(n_kill, self.prey_arrays.count)
            indices = random.sample(range(self.prey_arrays.count), n_kill)
            for idx in indices:
                self.prey_arrays.alive[idx] = 0
            self.prey_arrays.compact()
            config.prey_deceased += n_kill

        # Grass — scale all amounts down
        pct = percents[2]
        if pct > 0:
            self.grass.amounts *= (1.0 - pct / 100.0)

    # ------------------------------------------------------------------
    # Main event loop
    # ------------------------------------------------------------------

    def run(self) -> str | None:
        """Run the window. Returns 'killed' if applied, None if cancelled."""
        clock = pygame.time.Clock()
        while self.running:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.result = None

                # ---- Input phase ----
                elif self.phase == 'input':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        clicked_input = False
                        for i, rect in enumerate(self.input_rects):
                            if rect.collidepoint(event.pos):
                                self.active_row = i
                                clicked_input = True
                                break

                        if not clicked_input:
                            if self.btn_ok.collidepoint(event.pos):
                                register_button_click(self.btn_ok)
                                valid = True
                                parsed = []
                                for i in range(3):
                                    v = self._parse_percent(i)
                                    if self.percents[i].strip() != '' and v is None:
                                        self.errors[i] = True
                                        valid = False
                                    else:
                                        self.errors[i] = False
                                    parsed.append(v if v is not None else 0.0)
                                if valid:
                                    self._pending_percents = parsed
                                    self._pending_counts   = self._get_counts()
                                    self.phase = 'confirm'
                            elif self.btn_cancel.collidepoint(event.pos):
                                register_button_click(self.btn_cancel)
                                self.running = False
                                self.result = None
                            else:
                                self.active_row = None

                    elif event.type == pygame.KEYDOWN and self.active_row is not None:
                        i = self.active_row
                        key = event.key
                        if key == pygame.K_BACKSPACE:
                            self.percents[i] = self.percents[i][:-1]
                            self.errors[i] = False
                        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self.active_row = (i + 1) % 3
                        elif key == pygame.K_TAB:
                            self.active_row = (i + 1) % 3
                        elif key == pygame.K_ESCAPE:
                            self.active_row = None
                        elif event.unicode.isdigit():
                            if len(self.percents[i]) < 5:
                                self.percents[i] += event.unicode
                                self.errors[i] = False
                        elif event.unicode == '.' and '.' not in self.percents[i]:
                            if len(self.percents[i]) < 5:
                                self.percents[i] += event.unicode

                # ---- Confirm phase ----
                elif self.phase == 'confirm':
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.btn_confirm_yes.collidepoint(event.pos):
                            register_button_click(self.btn_confirm_yes)
                            self._apply_kills()
                            self.running = False
                            self.result = 'killed'
                        elif self.btn_confirm_no.collidepoint(event.pos):
                            register_button_click(self.btn_confirm_no)
                            self.phase = 'input'

            # Draw
            self._draw_input_phase(mouse_pos)
            if self.phase == 'confirm':
                self._draw_confirm_phase()

            pygame.display.flip()
            clock.tick(60)

        return self.result
