import pygame
from config import Config, Direction, LightState


class Intersection:
    """Một ngã tư độc lập: có vị trí, đèn giao thông, FSM riêng."""

    def __init__(self, cx: int, cy: int, phase_offset: int = 0):
        self.cx = cx
        self.cy = cy

        # Bắt đầu ở pha khác nhau để các ngã tư không xanh cùng lúc
        self.phase = phase_offset % 4
        self.timer = 0.0

        self.lights = {d: LightState.RED for d in Direction}
        self._apply_phase()

    # ------------------------------------------------------------------
    @property
    def cs(self) -> int:
        return Config.INTERSECTION_SIZE // 2

    @property
    def center_rect(self) -> pygame.Rect:
        """Rect điểm (0×0) tại tâm – dùng để tính stop line."""
        return pygame.Rect(self.cx, self.cy, 0, 0)

    @property
    def bounds(self) -> pygame.Rect:
        """Hình vuông ngã tư."""
        cs = self.cs
        return pygame.Rect(self.cx - cs, self.cy - cs,
                           Config.INTERSECTION_SIZE, Config.INTERSECTION_SIZE)

    # ------------------------------------------------------------------
    def update(self, dt: float):
        limits = [Config.GREEN_TIME, Config.YELLOW_TIME,
                  Config.GREEN_TIME, Config.YELLOW_TIME]
        self.timer += dt
        if self.timer >= limits[self.phase]:
            self.timer = 0.0
            self.phase = (self.phase + 1) % 4
            self._apply_phase()

    def _apply_phase(self):
        if self.phase == 0:
            self.lights[Direction.NORTH] = LightState.GREEN
            self.lights[Direction.SOUTH] = LightState.GREEN
            self.lights[Direction.EAST]  = LightState.RED
            self.lights[Direction.WEST]  = LightState.RED
        elif self.phase == 1:
            self.lights[Direction.NORTH] = LightState.YELLOW
            self.lights[Direction.SOUTH] = LightState.YELLOW
        elif self.phase == 2:
            self.lights[Direction.NORTH] = LightState.RED
            self.lights[Direction.SOUTH] = LightState.RED
            self.lights[Direction.EAST]  = LightState.GREEN
            self.lights[Direction.WEST]  = LightState.GREEN
        elif self.phase == 3:
            self.lights[Direction.EAST] = LightState.YELLOW
            self.lights[Direction.WEST] = LightState.YELLOW

    # ------------------------------------------------------------------
    def draw(self, screen: pygame.Surface):
        """Vẽ ô ngã tư và các đèn."""
        lw = Config.LANE_WIDTH
        isz = Config.INTERSECTION_SIZE
        cx, cy = self.cx, self.cy

        # Ô ngã tư (đè lên nền đường để che vạch kẻ)
        pygame.draw.rect(screen, (70, 70, 70),
                         (cx - isz // 2, cy - isz // 2, isz, isz))

        # Đèn – 4 chấm tròn nhỏ
        self._draw_light(screen, Direction.NORTH, (cx + lw // 2 + 4, cy - isz // 2 - 10))
        self._draw_light(screen, Direction.SOUTH, (cx - lw // 2 - 4, cy + isz // 2 + 10))
        self._draw_light(screen, Direction.EAST,  (cx + isz // 2 + 10, cy + lw // 2 + 4))
        self._draw_light(screen, Direction.WEST,  (cx - isz // 2 - 10, cy - lw // 2 - 4))

    def _draw_light(self, screen, direction, pos):
        from config import COLORS
        c = (COLORS['GREEN']  if self.lights[direction] == LightState.GREEN  else
             COLORS['YELLOW'] if self.lights[direction] == LightState.YELLOW else
             COLORS['RED'])
        pygame.draw.circle(screen, c, pos, 6)
        pygame.draw.circle(screen, COLORS['WHITE'], pos, 6, 1)
