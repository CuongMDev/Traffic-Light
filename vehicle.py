import pygame
from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING
from config import Config, Direction, LightState, COLORS, SIM_WIDTH, HEIGHT

if TYPE_CHECKING:
    from intersection import Intersection


@dataclass
class Vehicle:
    rect: pygame.Rect
    direction: Direction
    v_type: str          # 'car' or 'moto'
    speed: float = 0.0
    max_speed: float = Config.MAX_SPEED
    color: tuple = field(default_factory=lambda: COLORS['CAR'])

    # ------------------------------------------------------------------
    def update(self, vehicles: list, intersections: list) -> bool:
        """Cập nhật vị trí. Trả về True nếu xe ra khỏi màn hình."""
        front_blocked = self.check_front(vehicles)
        light_blocked = self.check_light(intersections)

        if front_blocked or light_blocked:
            self.speed = max(0.0, self.speed - Config.DECEL)
        else:
            self.speed = min(self.max_speed, self.speed + Config.ACCEL)

        if self.direction == Direction.NORTH:   self.rect.y -= self.speed
        elif self.direction == Direction.SOUTH: self.rect.y += self.speed
        elif self.direction == Direction.EAST:  self.rect.x += self.speed
        elif self.direction == Direction.WEST:  self.rect.x -= self.speed

        return self.is_off_screen()

    # ------------------------------------------------------------------
    def check_front(self, vehicles: list) -> bool:
        """Kiểm tra xe phía trước cùng chiều."""
        for v in vehicles:
            if v is self: continue
            if self.direction != v.direction: continue
            dist = 999
            if self.direction == Direction.NORTH:
                x_ov = v.rect.right > self.rect.left and v.rect.left < self.rect.right
                if x_ov and v.rect.y < self.rect.y:
                    dist = self.rect.y - v.rect.bottom
            elif self.direction == Direction.SOUTH:
                x_ov = v.rect.right > self.rect.left and v.rect.left < self.rect.right
                if x_ov and v.rect.y > self.rect.y:
                    dist = v.rect.y - self.rect.bottom
            elif self.direction == Direction.EAST:
                y_ov = v.rect.bottom > self.rect.top and v.rect.top < self.rect.bottom
                if y_ov and v.rect.x > self.rect.x:
                    dist = v.rect.x - self.rect.right
            elif self.direction == Direction.WEST:
                y_ov = v.rect.bottom > self.rect.top and v.rect.top < self.rect.bottom
                if y_ov and v.rect.x < self.rect.x:
                    dist = self.rect.x - v.rect.right
            if dist < 30:
                return True
        return False

    # ------------------------------------------------------------------
    def check_light(self, intersections: list) -> bool:
        """Tìm ngã tư gần nhất phía trước, kiểm tra đèn."""
        inter = self._next_intersection(intersections)
        if inter is None:
            return False

        state = inter.lights[self.direction]
        if state == LightState.GREEN:
            return False

        cs = Config.INTERSECTION_SIZE // 2
        cx, cy = inter.cx, inter.cy

        if self.direction == Direction.NORTH:
            stop_line = cy + cs
            dist = self.rect.y - stop_line
        elif self.direction == Direction.SOUTH:
            stop_line = cy - cs
            dist = stop_line - self.rect.bottom
        elif self.direction == Direction.EAST:
            stop_line = cx - cs
            dist = stop_line - self.rect.right
        else:  # WEST
            stop_line = cx + cs
            dist = self.rect.x - stop_line

        # dist > 0 : chưa vào ngã tư → dừng nếu < 40px
        # dist <= 0: đã vào → tiếp tục
        return 0 < dist < 40

    def _next_intersection(self, intersections: list):
        """Trả về ngã tư gần nhất phía trước trong làn của xe."""
        lw = Config.LANE_WIDTH
        best = None
        best_dist = float('inf')

        for inter in intersections:
            cs = Config.INTERSECTION_SIZE // 2
            cx, cy = inter.cx, inter.cy

            if self.direction in (Direction.NORTH, Direction.SOUTH):
                # Xe đi dọc: kiểm tra làn theo x
                if not (cx - lw <= self.rect.centerx <= cx + lw):
                    continue
                if self.direction == Direction.NORTH:
                    stop_line = cy + cs
                    dist = self.rect.y - stop_line   # > 0 nếu chưa vào
                else:
                    stop_line = cy - cs
                    dist = stop_line - self.rect.bottom
            else:
                # Xe đi ngang: kiểm tra làn theo y
                if not (cy - lw <= self.rect.centery <= cy + lw):
                    continue
                if self.direction == Direction.EAST:
                    stop_line = cx - cs
                    dist = stop_line - self.rect.right
                else:
                    stop_line = cx + cs
                    dist = self.rect.x - stop_line

            # Chỉ quan tâm ngã tư phía trước (dist > -INTERSECTION_SIZE)
            if dist > -Config.INTERSECTION_SIZE and dist < best_dist:
                best_dist = dist
                best = inter

        return best

    # ------------------------------------------------------------------
    def is_off_screen(self) -> bool:
        margin = 20
        return (self.rect.right < -margin or self.rect.left > SIM_WIDTH + margin
                or self.rect.bottom < -margin or self.rect.top > HEIGHT + margin)
