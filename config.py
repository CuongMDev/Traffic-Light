from enum import Enum

WIDTH, HEIGHT = 1000, 700
FPS = 60
PANEL_WIDTH = 220
SIM_WIDTH = WIDTH - PANEL_WIDTH   # vùng mô phỏng (không kể panel)

COLORS = {
    'WHITE': (255, 255, 255), 'BLACK': (0, 0, 0), 'GRAY': (50, 50, 50),
    'ROAD': (70, 70, 70), 'LINE': (200, 200, 200),
    'RED': (200, 0, 0), 'YELLOW': (200, 200, 0), 'GREEN': (0, 200, 0),
    'CAR': (50, 120, 200), 'MOTO': (200, 100, 50),
    'PANEL': (30, 30, 40), 'TEXT': (220, 220, 220),
    'BTN': (60, 100, 60), 'BTN_HOVER': (80, 140, 80)
}


class Config:
    # Lưới ngã tư
    GRID_COLS = 3
    GRID_ROWS = 3
    GRID_SPACING_X = 250        # khoảng cách tâm-tâm theo chiều ngang
    GRID_SPACING_Y = 220        # khoảng cách tâm-tâm theo chiều dọc
    GRID_START_X = 130          # tâm ngã tư cột 0
    GRID_START_Y = 130          # tâm ngã tư hàng 0

    # Kích thước
    INTERSECTION_SIZE = 70
    LANE_WIDTH = 22

    # Thời gian đèn
    GREEN_TIME = 15
    YELLOW_TIME = 3

    # Xe cộ
    SPAWN_RATE = 0.015          # xác suất spawn mỗi frame (mỗi làn)
    MAX_VEHICLES = 300

    # Vật lý
    MAX_SPEED = 3.0
    ACCEL = 0.15
    DECEL = 0.25
    CAR_SIZE = (24, 12)         # (dài, rộng)
    MOTO_SIZE = (16, 8)         # (dài, rộng)


class Direction(Enum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3


class LightState(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2
