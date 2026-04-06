import pygame
import random
from typing import List

from config import Config, Direction, LightState, COLORS, WIDTH, HEIGHT, SIM_WIDTH, PANEL_WIDTH
from vehicle import Vehicle
from intersection import Intersection


class Simulation:
    def __init__(self):
        self._fonts = {
            'small':  pygame.font.SysFont('Arial', 15),
            'medium': pygame.font.SysFont('Arial', 18, bold=True),
            'large':  pygame.font.SysFont('Arial', 24, bold=True),
        }

        # Tạo lưới 3×3 ngã tư, offset pha để tránh tất cả xanh cùng lúc
        self.intersections: List[Intersection] = []
        for row in range(Config.GRID_ROWS):
            for col in range(Config.GRID_COLS):
                cx = Config.GRID_START_X + col * Config.GRID_SPACING_X
                cy = Config.GRID_START_Y + row * Config.GRID_SPACING_Y
                phase_offset = (row * Config.GRID_COLS + col) * 2
                self.intersections.append(Intersection(cx, cy, phase_offset))

        self.vehicles: List[Vehicle] = []
        self.stats = {'served': 0}
        self.ui_input = {'green': str(Config.GREEN_TIME), 'active': None}

    # ------------------------------------------------------------------
    def _col_cx(self, col: int) -> int:
        return Config.GRID_START_X + col * Config.GRID_SPACING_X

    def _row_cy(self, row: int) -> int:
        return Config.GRID_START_Y + row * Config.GRID_SPACING_Y

    # ------------------------------------------------------------------
    def spawn(self):
        if len(self.vehicles) >= Config.MAX_VEHICLES:
            return

        # Mỗi frame thử spawn một xe ngẫu nhiên trên một làn ngẫu nhiên
        if random.random() > Config.SPAWN_RATE:
            return

        d = random.choice(list(Direction))
        v_type = 'car' if random.random() < 0.3 else 'moto'
        size = Config.CAR_SIZE if v_type == 'car' else Config.MOTO_SIZE
        color = COLORS['CAR'] if v_type == 'car' else COLORS['MOTO']
        offset = Config.LANE_WIDTH // 3

        # Xe dọc → rect đứng; xe ngang → rect nằm ngang
        if d in (Direction.NORTH, Direction.SOUTH):
            w, h = size[1], size[0]
        else:
            w, h = size[0], size[1]

        if d == Direction.NORTH:
            col = random.randrange(Config.GRID_COLS)
            cx = self._col_cx(col)
            r = pygame.Rect(cx - offset - w, HEIGHT + 5, w, h)
        elif d == Direction.SOUTH:
            col = random.randrange(Config.GRID_COLS)
            cx = self._col_cx(col)
            r = pygame.Rect(cx + offset, -h - 5, w, h)
        elif d == Direction.EAST:
            row = random.randrange(Config.GRID_ROWS)
            cy = self._row_cy(row)
            r = pygame.Rect(-w - 5, cy + offset, w, h)
        else:  # WEST
            row = random.randrange(Config.GRID_ROWS)
            cy = self._row_cy(row)
            r = pygame.Rect(SIM_WIDTH + 5, cy - offset - h, w, h)

        self.vehicles.append(Vehicle(r, d, v_type, color=color))

    # ------------------------------------------------------------------
    def update(self, dt: float):
        self.spawn()

        for inter in self.intersections:
            inter.update(dt)

        for v in self.vehicles[:]:
            if v.update(self.vehicles, self.intersections):
                self.vehicles.remove(v)
                self.stats['served'] += 1

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        screen.fill(COLORS['GRAY'])

        lw = Config.LANE_WIDTH
        isz = Config.INTERSECTION_SIZE

        # --- Vẽ đường dọc (mỗi cột) ---
        for col in range(Config.GRID_COLS):
            cx = self._col_cx(col)
            pygame.draw.rect(screen, COLORS['ROAD'],
                             (cx - lw, 0, lw * 2, HEIGHT))

        # --- Vẽ đường ngang (mỗi hàng) ---
        for row in range(Config.GRID_ROWS):
            cy = self._row_cy(row)
            pygame.draw.rect(screen, COLORS['ROAD'],
                             (0, cy - lw, SIM_WIDTH, lw * 2))

        # --- Vạch kẻ giữa đường (giữa hai làn) ---
        for col in range(Config.GRID_COLS):
            cx = self._col_cx(col)
            self._draw_dashes_vertical(screen, cx, 0, HEIGHT, isz)

        for row in range(Config.GRID_ROWS):
            cy = self._row_cy(row)
            self._draw_dashes_horizontal(screen, cy, 0, SIM_WIDTH, isz)

        # --- Vẽ ngã tư (đè lên đường + đèn) ---
        for inter in self.intersections:
            inter.draw(screen)

        # --- Vẽ xe ---
        for v in self.vehicles:
            pygame.draw.rect(screen, v.color, v.rect, border_radius=3)
            if v.v_type == 'moto':
                pygame.draw.rect(screen, COLORS['BLACK'], v.rect, 1, border_radius=3)

        # --- Panel UI ---
        self._draw_ui(screen)

    def _draw_dashes_vertical(self, screen, cx, y_start, y_end, skip_size):
        """Vẽ vạch đứt giữa làn dọc, bỏ qua các ô ngã tư."""
        dash, gap = 12, 8
        y = y_start
        while y < y_end:
            # Kiểm tra xem y có nằm trong một ngã tư không
            in_intersection = any(
                abs(inter.cx - cx) < Config.LANE_WIDTH and
                inter.cy - inter.cs <= y <= inter.cy + inter.cs
                for inter in self.intersections
            )
            if not in_intersection:
                pygame.draw.line(screen, COLORS['LINE'],
                                 (cx, y), (cx, min(y + dash, y_end)), 1)
            y += dash + gap

    def _draw_dashes_horizontal(self, screen, cy, x_start, x_end, skip_size):
        """Vẽ vạch đứt giữa làn ngang, bỏ qua các ô ngã tư."""
        dash, gap = 12, 8
        x = x_start
        while x < x_end:
            in_intersection = any(
                abs(inter.cy - cy) < Config.LANE_WIDTH and
                inter.cx - inter.cs <= x <= inter.cx + inter.cs
                for inter in self.intersections
            )
            if not in_intersection:
                pygame.draw.line(screen, COLORS['LINE'],
                                 (x, cy), (min(x + dash, x_end), cy), 1)
            x += dash + gap

    # ------------------------------------------------------------------
    def _draw_ui(self, screen: pygame.Surface):
        panel_x = SIM_WIDTH
        pygame.draw.rect(screen, COLORS['PANEL'], (panel_x, 0, PANEL_WIDTH, HEIGHT))
        pygame.draw.line(screen, COLORS['WHITE'], (panel_x, 0), (panel_x, HEIGHT), 2)

        y = 15
        screen.blit(self._fonts['medium'].render("ĐIỀU KHIỂN", True, COLORS['TEXT']),
                    (panel_x + 10, y))
        y += 35

        for txt in [
            f"Xe đã thông: {self.stats['served']}",
            f"Xe hiện tại: {len(self.vehicles)}",
            f"Số ngã tư: {len(self.intersections)}",
        ]:
            screen.blit(self._fonts['small'].render(txt, True, COLORS['TEXT']),
                        (panel_x + 12, y))
            y += 22

        y += 8
        screen.blit(self._fonts['small'].render("Green Time (s):", True, COLORS['TEXT']),
                    (panel_x + 12, y))
        y += 22

        input_box = pygame.Rect(panel_x + 12, y, 75, 28)
        box_color = COLORS['BTN_HOVER'] if self.ui_input['active'] == 'green' else COLORS['BTN']
        pygame.draw.rect(screen, box_color, input_box, border_radius=4)
        screen.blit(self._fonts['medium'].render(self.ui_input['green'], True, COLORS['TEXT']),
                    (input_box.x + 5, input_box.y + 4))
        self.ui_input['rect'] = input_box
        y += 36

        # Trạng thái từng ngã tư
        y += 5
        screen.blit(self._fonts['small'].render("Trạng thái ngã tư:", True, COLORS['TEXT']),
                    (panel_x + 12, y))
        y += 20

        phase_names = ["NS Xanh", "NS Vàng", "EW Xanh", "EW Vàng"]
        phase_colors = [(0, 200, 0), (200, 200, 0), (0, 200, 0), (200, 200, 0)]

        for idx, inter in enumerate(self.intersections):
            row = idx // Config.GRID_COLS
            col = idx % Config.GRID_COLS
            label = f"[{row},{col}] {phase_names[inter.phase]} {inter.timer:.0f}s"
            c = phase_colors[inter.phase]
            surf = self._fonts['small'].render(label, True, c)
            screen.blit(surf, (panel_x + 12, y))
            y += 18
            if y > HEIGHT - 40:
                break

        y = HEIGHT - 55
        for txt in ["Click số để sửa", "Enter áp dụng", "ESC thoát"]:
            screen.blit(self._fonts['small'].render(txt, True, (130, 130, 130)),
                        (panel_x + 12, y))
            y += 17

    # ------------------------------------------------------------------
    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if 'rect' in self.ui_input and self.ui_input['rect'].collidepoint(event.pos):
                self.ui_input['active'] = 'green'
            else:
                self.ui_input['active'] = None

        if event.type == pygame.KEYDOWN and self.ui_input['active'] == 'green':
            if event.key == pygame.K_RETURN:
                try:
                    val = int(self.ui_input['green'])
                    if 5 <= val <= 120:
                        Config.GREEN_TIME = val
                except ValueError:
                    pass
                self.ui_input['green'] = str(Config.GREEN_TIME)
                self.ui_input['active'] = None
            elif event.key == pygame.K_BACKSPACE:
                self.ui_input['green'] = self.ui_input['green'][:-1]
            elif event.unicode.isdigit():
                self.ui_input['green'] += event.unicode
