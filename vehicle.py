import pygame
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from config import Config, Direction, LightState, COLORS, SIM_WIDTH, HEIGHT

if TYPE_CHECKING:
    from intersection import Intersection

LAT_STEP = 2   # px/frame khi dịch ngang sang làn mới (số nguyên)


@dataclass
class Vehicle:
    rect: pygame.Rect
    direction: Direction
    v_type: str          # 'car' or 'moto'
    speed: float = 0.0
    max_speed: float = Config.MOTO_MAX_SPEED
    accel: float = Config.MOTO_ACCEL
    decel: float = Config.MOTO_DECEL
    sub_lane: int = 0    # 0/1/2 cho moto; -1 cho ô tô (chiếm cả làn)
    follow_dist: int = Config.MOTO_FOLLOW_DIST
    lane_base: int = 0   # tọa độ mép trái/trên của làn (dùng để snap)
    lat_rem: int = 0     # quãng đường ngang còn cần dịch (số nguyên px)
    color: tuple = field(default_factory=lambda: COLORS['CAR'])

    # ------------------------------------------------------------------
    def update(self, vehicles: list, intersections: list) -> bool:
        """Cập nhật vị trí. Trả về True nếu xe ra khỏi màn hình."""
        # Thử chuyển làn trước khi tính dọc
        self.try_lane_change(vehicles, intersections)

        # Di chuyển ngang (chuyển làn dần dần – số nguyên để tránh drift)
        if self.lat_rem != 0:
            step = LAT_STEP if self.lat_rem > 0 else -LAT_STEP
            if abs(self.lat_rem) <= LAT_STEP:
                step = self.lat_rem
            self.lat_rem -= step
            if self.direction in (Direction.NORTH, Direction.SOUTH):
                self.rect.x += step
            else:
                self.rect.y += step
            # Snap về vị trí chính xác khi kết thúc chuyển làn
            if self.lat_rem == 0:
                sl_w = Config.LANE_WIDTH // 3
                lat_size = (self.rect.width if self.direction in (Direction.NORTH, Direction.SOUTH)
                            else self.rect.height)
                exact = self.lane_base + self.sub_lane * sl_w + (sl_w - lat_size) // 2
                if self.direction in (Direction.NORTH, Direction.SOUTH):
                    self.rect.x = exact
                else:
                    self.rect.y = exact

        front_blocked = self.check_front(vehicles)
        light_blocked = self.check_light(intersections)
        inter_blocked = self.check_intersection(vehicles, intersections)

        if front_blocked or light_blocked or inter_blocked:
            self.speed = max(0.0, self.speed - self.decel)
        else:
            self.speed = min(self.max_speed, self.speed + self.accel)

        if self.direction == Direction.NORTH:   self.rect.y -= self.speed
        elif self.direction == Direction.SOUTH: self.rect.y += self.speed
        elif self.direction == Direction.EAST:  self.rect.x += self.speed
        elif self.direction == Direction.WEST:  self.rect.x -= self.speed

        return self.is_off_screen()

    # ------------------------------------------------------------------
    def try_lane_change(self, vehicles: list, intersections: list) -> None:
        """Nếu bị moto cùng làn chặn, thử chuyển sang sub-lane trống.
        Không đổi làn nếu có ô tô phía trước."""
        if self.v_type != 'moto':
            return
        if self.lat_rem != 0:
            return   # đang dịch làn rồi, đợi xong

        # Không đổi làn khi đang gần/trong ngã tư
        inter = self._next_intersection(intersections)
        if inter is not None:
            cs = Config.INTERSECTION_SIZE // 2
            cx, cy = inter.cx, inter.cy
            if self.direction == Direction.NORTH:   d = self.rect.y - (cy + cs)
            elif self.direction == Direction.SOUTH: d = (cy - cs) - self.rect.bottom
            elif self.direction == Direction.EAST:  d = (cx - cs) - self.rect.right
            else:                                   d = self.rect.x - (cx + cs)
            if -Config.INTERSECTION_SIZE < d < 55:
                return

        # Có ô tô phía trước → theo sau ô tô, không tìm làn
        if self._car_ahead(vehicles):
            return

        # Chỉ đổi làn khi bị moto cùng sub-lane chặn gần
        if not self._moto_ahead_same_lane(vehicles):
            return

        # Thử sub-lane lân cận (xen kẽ hướng dựa vào id)
        candidates = []
        if self.sub_lane > 0: candidates.append(self.sub_lane - 1)
        if self.sub_lane < 2: candidates.append(self.sub_lane + 1)
        if id(self) % 2 == 0:
            candidates.reverse()

        sl_w = Config.LANE_WIDTH // 3
        for new_sl in candidates:
            if self._sublane_is_free(vehicles, new_sl):
                self.lat_rem = (new_sl - self.sub_lane) * sl_w
                self.sub_lane = new_sl
                return

    def _car_ahead(self, vehicles: list) -> bool:
        """Có ô tô nào phía trước trong tầm nhìn?"""
        for v in vehicles:
            if v is self or v.direction != self.direction: continue
            if v.v_type != 'car': continue
            if 0 < self._dist_to(v) < 150:
                return True
        return False

    def _moto_ahead_same_lane(self, vehicles: list) -> bool:
        """Có moto cùng sub-lane phía trước trong khoảng gần?"""
        for v in vehicles:
            if v is self or v.direction != self.direction: continue
            if v.sub_lane != self.sub_lane: continue
            if 0 < self._dist_to(v) < 35:
                return True
        return False

    def _sublane_is_free(self, vehicles: list, target_sl: int) -> bool:
        """Sub-lane đó có đủ trống để chuyển vào không?"""
        for v in vehicles:
            if v is self or v.direction != self.direction: continue
            if v.v_type == 'car':
                if -25 < self._dist_to(v) < 55:
                    return False
            else:
                if v.sub_lane != target_sl: continue
                if -20 < self._dist_to(v) < 50:
                    return False
        return True

    def _dist_to(self, v) -> float:
        """Khoảng cách dọc từ mũi self đến đuôi v (dương = v ở phía trước)."""
        if self.direction == Direction.NORTH:   return self.rect.y - v.rect.bottom
        elif self.direction == Direction.SOUTH: return v.rect.y - self.rect.bottom
        elif self.direction == Direction.EAST:  return v.rect.x - self.rect.right
        else:                                   return self.rect.x - v.rect.right

    def _lateral_overlap(self, v) -> bool:
        """Hai xe có giao nhau theo chiều ngang (vuông góc với hướng đi) không?"""
        if self.direction in (Direction.NORTH, Direction.SOUTH):
            return self.rect.right > v.rect.left and self.rect.left < v.rect.right
        else:
            return self.rect.bottom > v.rect.top and self.rect.top < v.rect.bottom

    # ------------------------------------------------------------------
    def check_front(self, vehicles: list) -> bool:
        """Kiểm tra xe phía trước dựa trên giao nhau ngang thực tế."""
        kin = self.speed * self.speed / (2 * self.decel + 0.01) + 2
        safe_dist = max(self.follow_dist, kin)

        for v in vehicles:
            if v is self: continue
            if self.direction != v.direction: continue

            # Bỏ qua nếu không có giao nhau ngang (đi song song lệch làn)
            if not self._lateral_overlap(v):
                continue

            dist = self._dist_to(v)
            if dist <= 0:
                continue

            # Moto phía sau ô tô: dùng khoảng cách an toàn của ô tô
            if self.v_type == 'moto' and v.v_type == 'car':
                if dist < max(safe_dist, Config.CAR_FOLLOW_DIST):
                    return True
            else:
                if dist < safe_dist:
                    return True
        return False

    # ------------------------------------------------------------------
    def check_light(self, intersections: list) -> bool:
        inter = self._next_intersection(intersections)
        if inter is None:
            return False
        state = inter.lights[self.direction]
        if state == LightState.GREEN:
            return False

        cs = Config.INTERSECTION_SIZE // 2
        cx, cy = inter.cx, inter.cy
        if self.direction == Direction.NORTH:   dist = self.rect.y - (cy + cs)
        elif self.direction == Direction.SOUTH: dist = (cy - cs) - self.rect.bottom
        elif self.direction == Direction.EAST:  dist = (cx - cs) - self.rect.right
        else:                                   dist = self.rect.x - (cx + cs)
        return 0 < dist < 40

    def _next_intersection(self, intersections: list):
        lw = Config.LANE_WIDTH
        best, best_dist = None, float('inf')
        for inter in intersections:
            cs = Config.INTERSECTION_SIZE // 2
            cx, cy = inter.cx, inter.cy
            if self.direction in (Direction.NORTH, Direction.SOUTH):
                if not (cx - lw <= self.rect.centerx <= cx + lw):
                    continue
                dist = (self.rect.y - (cy + cs) if self.direction == Direction.NORTH
                        else (cy - cs) - self.rect.bottom)
            else:
                if not (cy - lw <= self.rect.centery <= cy + lw):
                    continue
                dist = ((cx - cs) - self.rect.right if self.direction == Direction.EAST
                        else self.rect.x - (cx + cs))
            if dist > -Config.INTERSECTION_SIZE and dist < best_dist:
                best_dist = dist
                best = inter
        return best

    # ------------------------------------------------------------------
    def check_intersection(self, vehicles: list, intersections: list) -> bool:
        inter = self._next_intersection(intersections)
        if inter is None:
            return False
        cs = Config.INTERSECTION_SIZE // 2
        cx, cy = inter.cx, inter.cy
        if self.direction == Direction.NORTH:   d = self.rect.y - (cy + cs)
        elif self.direction == Direction.SOUTH: d = (cy - cs) - self.rect.bottom
        elif self.direction == Direction.EAST:  d = (cx - cs) - self.rect.right
        else:                                   d = self.rect.x - (cx + cs)
        if not (0 <= d <= 40):
            return False
        perp = ({Direction.EAST, Direction.WEST}
                if self.direction in (Direction.NORTH, Direction.SOUTH)
                else {Direction.NORTH, Direction.SOUTH})
        return any(v.direction in perp and inter.bounds.colliderect(v.rect)
                   for v in vehicles if v is not self)

    # ------------------------------------------------------------------
    def is_off_screen(self) -> bool:
        margin = 20
        return (self.rect.right < -margin or self.rect.left > SIM_WIDTH + margin
                or self.rect.bottom < -margin or self.rect.top > HEIGHT + margin)
