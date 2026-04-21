from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import random
import sys

import pygame
import json

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


INTERNAL_WIDTH = 320
INTERNAL_HEIGHT = 180
SCALE = 4
GAME_VIEW_WIDTH = INTERNAL_WIDTH * SCALE
GAME_VIEW_HEIGHT = INTERNAL_HEIGHT * SCALE
CAMERA_VIEW_WIDTH = 256
CAMERA_VIEW_HEIGHT = 144
WINDOW_WIDTH = GAME_VIEW_WIDTH + 320
WINDOW_HEIGHT = GAME_VIEW_HEIGHT + 180
TILE_SIZE = 16
FPS = 60

PALETTE = {
    "bg": (11, 14, 19),
    "wall": (34, 42, 53),
    "floor": (47, 58, 72),
    "dark_floor": (26, 43, 51),
    "player": (185, 135, 107),
    "player_hurt": (199, 70, 70),
    "wolf": (142, 142, 132),
    "wolf_alert": (199, 70, 70),
    "trap": (217, 122, 43),
    "trap_on": (199, 70, 70),
    "door": (217, 122, 43),
    "door_open": (83, 101, 121),
    "exit": (74, 120, 209),
    "key": (226, 190, 69),
    "battery": (92, 159, 179),
    "bandage": (215, 215, 204),
    "flashlight": (110, 157, 93),
    "text": (230, 230, 230),
    "hud_bg": (21, 26, 34),
    "health": (92, 159, 179),
    "health_mid": (226, 190, 69),
    "health_low": (199, 70, 70),
}


def clamp_channel(value: float) -> int:
    return max(0, min(255, int(value)))


def mix_color(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, amount))
    return tuple(clamp_channel(ca + (cb - ca) * t) for ca, cb in zip(a, b))


def shift_color(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(clamp_channel(channel + delta) for channel in color)

AREA_MAPS = {
    "area1": [
        "####################",
        "##########D#########",
        "#..d...............#",
        "#.............c....#",
        "#..................#",
        "#......P...........#",
        "#..b.s.............#",
        "#..................#",
        "#........S.........#",
        "#..................#",
        "####################",
    ],
    "hub": [
        "####################",
        "########....########",
        "########....########",
        "########.....#######",
        "#######.....########",
        "########S...########",
        "########.....#######",
        "########....########",
        "########..P.########",
        "########....########",
        "####################",
    ],
    "storage": [
        "####################",
        "#..............M...#",
        "#..P......f........#",
        "#..................#",
        "#.....##...........#",
        "#..................#",
        "#.......M..........#",
        "#..................#",
        "#..................#",
        "#..................#",
        "####################",
    ],
    "medbay": [
        "####################",
        "#.....H............#",
        "#..P...............#",
        "#..................#",
        "#........W.........#",
        "#..................#",
        "#.........H........#",
        "#..................#",
        "#.....S............#",
        "#..................#",
        "####################",
    ],
    "maintenance": [
        "####################",
        "#..................#",
        "#..P...............#",
        "#..................#",
        "#....R.............#",
        "#..................#",
        "#........k.........#",
        "#..................#",
        "#..................#",
        "#..................#",
        "####################",
    ],
    "area2": [
        "####################",
        "########....########",
        "########....########",
        "########....########",
        "########....########",
        "########....########",
        "########....########",
        "########....########",
        "########..P.########",
        "########....########",
        "####################",
    ],
    "area3": [
        "####################",
        "#..............G...#",
        "#..................#",
        "#.......E..........#",
        "#..................#",
        "#..................#",
        "#........P.........#",
        "#..................#",
        "#..........S.......#",
        "#..................#",
        "####################",
    ],
    "final": [
        "####################",
        "#P.................#",
        "#...............W..#",
        "#..................#",
        "#....W.............#",
        "#..................#",
        "#..............W...#",
        "#..................#",
        "#..............X...#",
        "#..................#",
        "####################",
    ],
    "l2_floor4": [
        "##################################################",
        "#P...............................................#",
        "#..B.............................................#",
        "#.......................................###.####.#",
        "####.#########.####.####.##########.#.......#....#",
        "#....................#..........#...#.......#....#",
        "#....................#..........#...#.......#....#",
        "#.....L....L....L.....#....L....#....L....L....L.#",
        "#....................#..........#...#............#",
        "#..........W.........#..........#...#.......W....#",
        "#....................#..........#...#............Z",
        "##################################################",
    ],
    "l2_floor3": [
        "###########################################################",
        "#P........................................................#",
        "#.........................................................#",
        "#.......#.....#.........#.....#.........#.....#...........#",
        "#.......#.....#.........#.....#.........#.....#...........#",
        "#.......#.1...#.........#.1...#.........#...K.#...........#",
        "#.......#.....#.........#.....#.........#.....#...........#",
        "#.........................................................#",
        "#.........................................................#",
        "#.......1.....1.........1.....1..........1.....1..........#",
        "#.........................................................Y",
        "###########################################################",
    ],
    "l2_floor2": [
        "##################################################",
        "#P...............................................#",
        "#................................................#",
        "#.......#.....#.........#.....#........#.....#...#",
        "#.......#.2...#.........#.....#........#.2...#...#",
        "#.......#.....#.........#.....#........#.....#...#",
        "#................................................#",
        "#..T..T..A...T..T..C..A..T...T..T..A..T..C.T.....#",
        "#................................................#",
        "#.......2.....2.........2.....2........2.....2..=#",
        "##################################################",
    ],
    "l2_floor1": [
        "#######################################################",
        "#P....................................................#",
        "#.....................................................#",
        "#.....................................................#",
        "#.....................................................#",
        "#...........................3.........................#",
        "#.....................................................#",
        "#.....................................................#",
        "#.....................................................#",
        "#.....................................................Z",
        "#######################################################",
    ],
}

AREA_FLOW_ORDER = ["area1", "hub", "storage", "medbay", "maintenance", "area2", "area3", "final", "l2_floor4", "l2_floor3", "l2_floor2", "l2_floor1"]
AREA_META = {
    "area1": ("B1-01", "RESIDENTIAL UNIT", "UNIT"),
    "hub": ("B1-02", "MAIN HALLWAY", "HALL"),
    "storage": ("B1-03", "STORAGE ROOM", "STOR"),
    "medbay": ("B1-04", "MED BAY", "MED"),
    "maintenance": ("B1-05", "MAINTENANCE CORRIDOR", "MNT"),
    "area2": ("B1-06", "SECURITY CHECKPOINT", "SEC"),
    "area3": ("B1-07", "ELEVATOR LOBBY", "LIFT"),
    "final": ("B1-08", "EXIT HALL", "EXIT"),
    "l2_floor4": ("B2-04", "FLICKER HALLWAY", "FL4"),
    "l2_floor3": ("B2-03", "DARK WARD", "DKW"),
    "l2_floor2": ("B2-02", "TRAP FLOOR", "TRP"),
    "l2_floor1": ("B2-01", "BASEMENT SPRINT", "BSP"),
}

AREA_THEMES: dict[str, dict[str, tuple[int, int, int]]] = {
    "area1": {
        "floor": (52, 46, 50),
        "floor_alt": (62, 55, 58),
        "floor_dark": (34, 31, 36),
        "wall": (76, 70, 74),
        "wall_hi": (118, 106, 110),
        "wall_lo": (42, 38, 42),
        "accent": (192, 146, 96),
        "danger": (185, 78, 82),
        "safe": (104, 158, 136),
        "ambient": (52, 26, 30),
    },
    "hub": {
        "floor": (44, 52, 63),
        "floor_alt": (52, 62, 74),
        "floor_dark": (28, 35, 44),
        "wall": (68, 82, 97),
        "wall_hi": (118, 134, 152),
        "wall_lo": (32, 40, 50),
        "accent": (96, 140, 188),
        "danger": (186, 82, 78),
        "safe": (96, 176, 148),
        "ambient": (18, 34, 46),
    },
    "storage": {
        "floor": (48, 54, 58),
        "floor_alt": (56, 62, 66),
        "floor_dark": (30, 36, 40),
        "wall": (72, 80, 84),
        "wall_hi": (114, 126, 130),
        "wall_lo": (36, 42, 46),
        "accent": (126, 174, 196),
        "danger": (188, 86, 82),
        "safe": (92, 170, 156),
        "ambient": (24, 40, 50),
    },
    "medbay": {
        "floor": (76, 84, 88),
        "floor_alt": (86, 94, 98),
        "floor_dark": (46, 52, 58),
        "wall": (104, 112, 118),
        "wall_hi": (146, 154, 160),
        "wall_lo": (58, 66, 72),
        "accent": (134, 182, 188),
        "danger": (174, 66, 72),
        "safe": (112, 188, 164),
        "ambient": (36, 44, 54),
    },
    "maintenance": {
        "floor": (58, 54, 46),
        "floor_alt": (68, 62, 52),
        "floor_dark": (34, 32, 28),
        "wall": (84, 78, 66),
        "wall_hi": (130, 120, 98),
        "wall_lo": (42, 38, 32),
        "accent": (216, 160, 72),
        "danger": (194, 86, 74),
        "safe": (98, 184, 146),
        "ambient": (42, 32, 18),
    },
    "area2": {
        "floor": (40, 44, 54),
        "floor_alt": (48, 54, 66),
        "floor_dark": (24, 28, 36),
        "wall": (62, 70, 84),
        "wall_hi": (102, 116, 134),
        "wall_lo": (30, 34, 42),
        "accent": (214, 84, 84),
        "danger": (224, 76, 76),
        "safe": (98, 170, 152),
        "ambient": (24, 18, 26),
    },
    "area3": {
        "floor": (50, 56, 64),
        "floor_alt": (60, 68, 78),
        "floor_dark": (30, 36, 42),
        "wall": (76, 84, 94),
        "wall_hi": (120, 132, 144),
        "wall_lo": (38, 44, 52),
        "accent": (116, 182, 204),
        "danger": (194, 90, 88),
        "safe": (110, 196, 170),
        "ambient": (20, 32, 44),
    },
    "final": {
        "floor": (42, 42, 48),
        "floor_alt": (52, 52, 58),
        "floor_dark": (26, 26, 32),
        "wall": (66, 68, 76),
        "wall_hi": (104, 106, 116),
        "wall_lo": (30, 32, 38),
        "accent": (214, 92, 82),
        "danger": (222, 70, 76),
        "safe": (120, 194, 168),
        "ambient": (44, 16, 20),
    },
    "l2_floor4": {
        "floor": (44, 42, 40),
        "floor_alt": (54, 50, 46),
        "floor_dark": (28, 26, 24),
        "wall": (68, 64, 58),
        "wall_hi": (108, 100, 90),
        "wall_lo": (34, 32, 28),
        "accent": (188, 162, 112),
        "danger": (178, 74, 68),
        "safe": (96, 164, 132),
        "ambient": (38, 24, 18),
    },
    "l2_floor3": {
        "floor": (18, 18, 22),
        "floor_alt": (24, 24, 28),
        "floor_dark": (8, 8, 12),
        "wall": (32, 32, 38),
        "wall_hi": (52, 52, 60),
        "wall_lo": (14, 14, 18),
        "accent": (62, 82, 112),
        "danger": (164, 58, 58),
        "safe": (56, 112, 96),
        "ambient": (2, 2, 4),
    },
    "l2_floor2": {
        "floor": (52, 50, 44),
        "floor_alt": (60, 56, 50),
        "floor_dark": (32, 30, 26),
        "wall": (78, 74, 66),
        "wall_hi": (122, 114, 98),
        "wall_lo": (38, 36, 32),
        "accent": (196, 148, 62),
        "danger": (192, 82, 62),
        "safe": (86, 168, 138),
        "ambient": (28, 24, 16),
    },
    "l2_floor1": {
        "floor": (28, 34, 42),
        "floor_alt": (36, 42, 50),
        "floor_dark": (14, 18, 24),
        "wall": (48, 56, 68),
        "wall_hi": (78, 88, 102),
        "wall_lo": (22, 28, 34),
        "accent": (104, 148, 188),
        "danger": (188, 68, 72),
        "safe": (108, 186, 162),
        "ambient": (14, 22, 34),
    },
}

AREA_DOORS: dict[str, list[dict[str, object]]] = {
    "area1": [
        {
            "id": "D-01",
            "tile": (10, 1),
            "to": "hub",
            "spawn": (10, 8),
            "label": "B1-02 MAIN HALLWAY",
            "requirement": "unit_door",
            "locked": "Door locked. Need unit key",
        }
    ],
    "hub": [
        {"id": "D-01R", "tile": (10, 9), "to": "area1", "spawn": (10, 2), "label": "B1-01 RESIDENTIAL UNIT", "requirement": "none"},
        {"id": "D-02", "tile": (10, 1), "to": "area2", "spawn": (10, 8), "label": "B1-06 SECURITY CHECKPOINT", "requirement": "none"},
        {"id": "D-03", "tile": (12, 3), "to": "storage", "spawn": (2, 2), "label": "B1-03 STORAGE ROOM", "requirement": "none"},
        {"id": "D-04", "tile": (12, 6), "to": "medbay", "spawn": (2, 2), "label": "B1-04 MED BAY", "requirement": "none"},
        {"id": "D-05", "tile": (7, 4), "to": "maintenance", "spawn": (2, 2), "label": "B1-05 MAINTENANCE", "requirement": "none"},
    ],
    "storage": [
        {"id": "D-03R", "tile": (10, 9), "to": "hub", "spawn": (11, 3), "label": "B1-02 MAIN HALLWAY", "requirement": "none"},
    ],
    "medbay": [
        {"id": "D-04R", "tile": (10, 9), "to": "hub", "spawn": (11, 6), "label": "B1-02 MAIN HALLWAY", "requirement": "none"},
    ],
    "maintenance": [
        {"id": "D-05R", "tile": (10, 1), "to": "hub", "spawn": (8, 4), "label": "B1-02 MAIN HALLWAY", "requirement": "none"},
    ],
    "area2": [
        {"id": "D-02R", "tile": (10, 9), "to": "hub", "spawn": (10, 2), "label": "B1-02 MAIN HALLWAY", "requirement": "none"},
        {
            "id": "D-06",
            "tile": (10, 1),
            "to": "area3",
            "spawn": (10, 9),
            "label": "B1-07 ELEVATOR LOBBY",
            "requirement": "lasers_off",
            "locked": "Checkpoint sealed. Enable maintenance breaker",
        },
    ],
    "area3": [
        {"id": "D-06R", "tile": (10, 9), "to": "area2", "spawn": (10, 2), "label": "B1-06 SECURITY CHECKPOINT", "requirement": "none"},
        {
            "id": "D-08",
            "tile": (15, 1),
            "to": "final",
            "spawn": (2, 1),
            "label": "B1-08 EXIT HALL",
            "requirement": "elevator_ready",
            "locked": "Elevator lock active. Use terminal first",
        },
    ],
    "final": [],
    "l2_floor4": [
        {
            "id": "ST-04",
            "tile": (49, 10),
            "to": "l2_floor3",
            "spawn": (1, 5),
            "label": "B2-03 DARK WARD",
            "requirement": "none",
        },
    ],
    "l2_floor3": [
        {
            "id": "ST-04R",
            "tile": (1, 5),
            "to": "l2_floor4",
            "spawn": (48, 9),
            "label": "B2-04 FLICKER HALL",
            "requirement": "none",
        },
        {
            "id": "KY-01",
            "tile": (58, 10),
            "to": "l2_floor2",
            "spawn": (1, 5),
            "label": "B2-02 TRAP FLOOR",
            "requirement": "keycard",
            "locked": "Stairwell locked. Need keycard",
        },
    ],
    "l2_floor2": [
        {
            "id": "KY-01R",
            "tile": (1, 5),
            "to": "l2_floor3",
            "spawn": (57, 9),
            "label": "B2-03 DARK WARD",
            "requirement": "none",
        },
        {
            "id": "GR-01",
            "tile": (48, 9),
            "to": "l2_floor1",
            "spawn": (1, 5),
            "label": "B2-01 BASEMENT SPRINT",
            "requirement": "knife_pry",
            "locked": "Rusted grate. Need knife to pry open",
        },
    ],
    "l2_floor1": [
        {
            "id": "GR-01R",
            "tile": (1, 5),
            "to": "l2_floor2",
            "spawn": (47, 9),
            "label": "B2-02 TRAP FLOOR",
            "requirement": "none",
        },
        {
            "id": "EXIT-L2",
            "tile": (54, 9),
            "to": "__level2_complete__",
            "spawn": (0, 0),
            "label": "LEVEL 2 EXIT",
            "requirement": "none",
        },
    ],
}


@dataclass
class ItemPickup:
    name: str
    tile_x: int
    tile_y: int

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.tile_x * TILE_SIZE + 4, self.tile_y * TILE_SIZE + 4, 8, 8)


@dataclass
class Wolf:
    x: float
    y: float
    alive: bool = True
    alert: bool = False
    facing_x: float = 1.0
    facing_y: float = 0.0
    subtype: str = "standard"
    hp: int = 1
    max_hp: int = 1
    size: int = 12
    patrol_origin_x: float = 0.0
    patrol_origin_y: float = 0.0
    stun_timer: float = 0.0
    strafe_dir: float = 1.0
    charge_timer: float = 0.0
    lunge_timer: float = 0.0
    lose_interest_timer: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    color: tuple[int, int, int]
    size: int


@dataclass
class LaserBeam:
    rect: pygame.Rect
    on_time: float
    off_time: float
    phase: float


@dataclass
class Hazard:
    kind: str
    tile_x: int
    tile_y: int
    rect: pygame.Rect
    triggered: bool = False
    active: bool = True
    crumble_timer: float = 0.0


@dataclass
class FlickerLight:
    tile_x: int
    tile_y: int
    phase: float
    on_duration: float
    off_duration: float


class SoundManager:
    """Procedural audio using numpy. Gracefully degrades if numpy unavailable."""

    def __init__(self) -> None:
        self.sounds: dict[str, list[pygame.mixer.Sound]] = {}
        self.enabled = HAS_NUMPY
        if not self.enabled:
            return
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._generate_all()
        except pygame.error:
            self.enabled = False

    def _make_sound(self, samples: list[float]) -> pygame.mixer.Sound:
        arr = np.array(samples, dtype=np.float64)
        arr = np.clip(arr, -1.0, 1.0)
        pcm = (arr * 32767).astype(np.int16)
        # sndarray requires a 2D array matching mixer channels
        channels = pygame.mixer.get_init()[2]
        if channels > 1:
            pcm = np.column_stack([pcm] * channels)
        return pygame.sndarray.make_sound(pcm)

    def _env(self, n: int, attack: float = 0.05, release: float = 0.3) -> list[float]:
        t = np.linspace(0, 1, n)
        env = np.ones(n)
        att_samples = max(1, int(attack * n))
        rel_samples = max(1, int(release * n))
        env[:att_samples] = np.linspace(0, 1, att_samples)
        env[-rel_samples:] = np.linspace(1, 0, rel_samples)
        return env.tolist()

    def _envelope_array(self, n: int, attack: float = 0.05, release: float = 0.3) -> np.ndarray:
        return np.array(self._env(n, attack, release))

    def _lowpass(self, arr: np.ndarray, alpha: float) -> np.ndarray:
        if len(arr) == 0:
            return arr
        out = np.empty_like(arr)
        out[0] = arr[0]
        for i in range(1, len(arr)):
            out[i] = out[i - 1] + alpha * (arr[i] - out[i - 1])
        return out

    def _highpass(self, arr: np.ndarray, alpha: float) -> np.ndarray:
        if len(arr) == 0:
            return arr
        low = self._lowpass(arr, alpha)
        return arr - low

    def _tone(
        self,
        freq_start: float,
        freq_end: float,
        duration: float,
        amplitude: float = 0.5,
        harmonics: tuple[float, ...] = (),
    ) -> np.ndarray:
        sr = 22050
        n = max(1, int(sr * duration))
        t = np.linspace(0, duration, n, endpoint=False)
        freq = np.linspace(freq_start, freq_end, n)
        base = np.sin(2 * np.pi * freq * t) * amplitude
        for idx, harmonic_amp in enumerate(harmonics, start=2):
            base += np.sin(2 * np.pi * freq * idx * t) * harmonic_amp
        return base

    def _noise(self, duration: float, amplitude: float = 0.4, color: str = "white") -> np.ndarray:
        sr = 22050
        n = max(1, int(sr * duration))
        arr = np.random.uniform(-1.0, 1.0, n) * amplitude
        if color == "low":
            arr = self._lowpass(arr, 0.06)
        elif color == "mid":
            arr = self._lowpass(arr, 0.14)
        elif color == "high":
            arr = self._highpass(arr, 0.08)
        return arr

    def _normalize(self, arr: np.ndarray, peak: float = 0.9) -> np.ndarray:
        max_val = float(np.max(np.abs(arr))) if len(arr) else 0.0
        if max_val <= 1e-6:
            return arr
        return arr * (peak / max_val)

    def _fit_length(self, arr: np.ndarray, n: int) -> np.ndarray:
        if len(arr) == n:
            return arr
        if len(arr) > n:
            return arr[:n]
        return np.pad(arr, (0, n - len(arr)))

    def _add_sound(self, name: str, wave: np.ndarray, volume: float = 1.0) -> None:
        shaped = self._normalize(wave * volume, 0.88)
        self.sounds.setdefault(name, []).append(self._make_sound(shaped.tolist()))

    def _generate_all(self) -> None:
        sr = 22050

        # Footsteps: heel thump + cloth/grit scrape, with slight variants.
        for base_freq, scrape_amt, gain in ((86, 0.16, 0.50), (94, 0.14, 0.46), (78, 0.18, 0.52)):
            duration = 0.12
            n = int(sr * duration)
            thump = self._tone(base_freq, base_freq - 18, duration, 0.65, (0.14,))
            grit = self._noise(duration, scrape_amt, "mid")
            grit = self._highpass(grit, 0.05)
            heel_click = self._noise(0.028, 0.12, "high")
            heel_pad = np.pad(heel_click, (0, max(0, n - len(heel_click))))
            env = self._envelope_array(n, 0.01, 0.72)
            footstep = (thump * 0.72 + grit * 0.34 + heel_pad[:n] * 0.7) * env
            self._add_sound("footstep", footstep, gain)

        # Pickup: subtle metallic utility pickup rather than arcade chirp.
        n = int(sr * 0.17)
        pickup = self._fit_length(self._tone(620, 980, 0.17, 0.34, (0.10,)), n)
        pickup += self._fit_length(self._tone(930, 1460, 0.12, 0.14), n)
        pickup += self._fit_length(self._noise(0.05, 0.04, "high"), n)
        pickup *= self._envelope_array(n, 0.02, 0.48)
        self._add_sound("pickup", pickup, 0.55)

        # Damage: body hit with bass thud and tearing transient.
        n = int(sr * 0.18)
        body_hit = self._tone(120, 58, 0.18, 0.58, (0.22,))
        crack = self._noise(0.08, 0.24, "high")
        crack = np.pad(crack, (0, max(0, n - len(crack))))
        pain = self._tone(210, 150, 0.07, 0.16)
        pain = np.pad(pain, (0, max(0, n - len(pain))))
        damage = (body_hit + crack[:n] * 0.9 + pain[:n] * 0.55) * self._envelope_array(n, 0.01, 0.52)
        self._add_sound("damage", damage, 0.64)

        # Slash: fast blade whoosh.
        n = int(sr * 0.11)
        slash = self._fit_length(self._noise(0.11, 0.20, "high"), n)
        slash += self._fit_length(self._tone(900, 420, 0.11, 0.12), n)
        slash *= self._envelope_array(n, 0.01, 0.82)
        self._add_sound("slash", slash, 0.48)

        # Stab: slash transient plus wet impact.
        n = int(sr * 0.14)
        stab_body = self._tone(180, 96, 0.14, 0.44, (0.16,))
        stab_noise = self._noise(0.09, 0.20, "mid")
        stab_noise = np.pad(stab_noise, (0, max(0, n - len(stab_noise))))
        stab_click = self._noise(0.025, 0.16, "high")
        stab_click = np.pad(stab_click, (0, max(0, n - len(stab_click))))
        stab = (stab_body + stab_noise[:n] * 0.55 + stab_click[:n] * 0.7) * self._envelope_array(n, 0.01, 0.5)
        self._add_sound("stab", stab, 0.62)

        # Door: latch click, hinge scrape, and a hollow panel thud.
        n = int(sr * 0.24)
        latch = self._noise(0.035, 0.22, "high")
        latch = np.pad(latch, (0, max(0, n - len(latch))))
        hinge = self._fit_length(self._tone(320, 210, 0.14, 0.18), n)
        hinge += self._fit_length(self._noise(0.14, 0.08, "mid"), n)
        thud = self._tone(96, 58, 0.18, 0.42, (0.12,))
        thud = np.pad(thud, (0, max(0, n - len(thud))))
        door = (latch[:n] * 0.8 + hinge[:n] * 0.7 + thud[:n]) * self._envelope_array(n, 0.01, 0.44)
        self._add_sound("door", door, 0.56)

        # Wolf growl: layered rumble with a rough snarl edge.
        n = int(sr * 0.38)
        t = np.linspace(0, 0.38, n, endpoint=False)
        tremolo = 0.72 + 0.28 * np.sin(2 * np.pi * 7.4 * t)
        rumble = self._tone(72, 58, 0.38, 0.34, (0.22,))
        snarl = self._noise(0.38, 0.16, "mid")
        snarl = self._highpass(snarl, 0.04)
        growl = (rumble + snarl * 0.55) * tremolo * self._envelope_array(n, 0.04, 0.36)
        self._add_sound("growl", growl, 0.58)

        # Save chime: still synthetic, but softer and less toy-like.
        notes = [523.25, 659.25, 783.99]
        samples_per = int(sr * 0.12)
        all_samples = []
        for freq in notes:
            wave = self._tone(freq, freq * 1.01, 0.12, 0.24, (0.08,))
            all_samples.extend((wave * self._envelope_array(samples_per, 0.02, 0.3)).tolist())
        gap = [0.0] * int(sr * 0.02)
        self._add_sound("save", np.array(all_samples + gap + all_samples[:samples_per]), 0.52)

    def play(self, name: str) -> None:
        if not self.enabled or name not in self.sounds:
            return
        random.choice(self.sounds[name]).play()


class Game:
    HINT_DEFS = {
        "interact_door": "Press E to interact",
        "flashlight_dark": "Press Q for flashlight",
        "attack_wolf": "Press SPACE to attack",
        "use_bandage": "Press H to use bandage",
        "open_inventory": "Press TAB for inventory",
        "save_terminal": "Press E to save",
    }

    ITEM_DESCRIPTIONS = {
        "knife": "Sharp blade. Press SPACE to strike.",
        "flashlight": "Illuminates dark areas. Press Q to toggle.",
        "bandage": "Restores 25 HP. Press H to use.",
        "key": "Opens locked doors. Press E near a door.",
        "keycard": "Electronic keycard. Unlocks secured stairwells.",
    }

    def __init__(self) -> None:
        # Force nearest-neighbor scaling for crisp pixel output.
        os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "0")
        pygame.init()
        pygame.display.set_caption("DEATH GAME")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.DOUBLEBUF | pygame.RESIZABLE)
        self.canvas = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 9, bold=True)
        self.big_font = pygame.font.SysFont("consolas", 14, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 8, bold=True)
        self.inventory_title_font = pygame.font.SysFont("consolas", 10, bold=True)
        self.inventory_font = pygame.font.SysFont("consolas", 9, bold=True)
        self.inventory_small_font = pygame.font.SysFont("consolas", 8, bold=True)
        self.ui_font = pygame.font.SysFont("consolas", 11, bold=True)
        self.ui_small_font = pygame.font.SysFont("consolas", 10, bold=True)
        self.assets_root = Path(__file__).resolve().parents[1] / "assets" / "art"

        self.current_area = "area1"
        self.current_map: list[str] = AREA_MAPS[self.current_area]
        self.world_width = len(self.current_map[0]) * TILE_SIZE
        self.world_height = len(self.current_map) * TILE_SIZE

        self.walls: list[pygame.Rect] = []
        self.traps: dict[tuple[int, int], bool] = {}
        self.pickups: list[ItemPickup] = []
        self.wolves: list[Wolf] = []
        self.dark_tiles: set[tuple[int, int]] = set()
        self.furniture: dict[tuple[int, int], str] = {}
        self.lasers: list[LaserBeam] = []
        self.current_doors: list[dict[str, object]] = []
        self.hazards: list[Hazard] = []
        self.flicker_lights: list[FlickerLight] = []

        self.player = pygame.Rect(16, 16, 10, 12)
        self.player_speed = 70.0
        self.base_player_speed = 70.0
        self.player_accel = 360.0
        self.player_drag = 8.0
        self.player_pos = pygame.Vector2(float(self.player.x), float(self.player.y))
        self.player_vel = pygame.Vector2(0, 0)
        self.last_dir = pygame.Vector2(1, 0)
        self.walk_cycle = 0.0
        self.attack_anim = 0.0
        self.attack_duration = 0.18
        self.attack_dir = pygame.Vector2(1, 0)

        self.has_key = False
        self.has_flashlight = False
        self.flashlight_on = False
        self.battery = 50
        self.flashlight_drain_interval = 0.8
        self.bandages = 0
        self.health = 100
        self.max_health = 100
        self.has_knife = False
        self.freezer_charges: dict[tuple[str, int, int], int] = {}

        self.inventory_selected = 0
        self.inventory_cols = 4
        self.inventory_rows = 2
        self.equipped_item = "knife"
        self.show_labels = True

        self.state = "explore"
        self.objective = "Find key"
        self.message = ""
        self.message_timer = 0.0
        self.intro_title = "LEVEL 1: ESCAPE"
        self.intro_lines = [
            "Wake up in B1. Find the key and escape.",
            "WASD Move   E Interact",
            "Q Flashlight   SPACE Attack",
            "TAB Inventory   F Equip",
            "L Labels   H Use Bandage",
        ]
        self.intro_hint = "Press ENTER to start"
        self.intro_timer = 8.5
        self.intro_fade_duration = 1.0
        self.damage_flash = 0.0
        self.hit_cooldown = 0.0
        self.battery_tick = 0.0
        self.attack_cooldown = 0.0
        self.attack_speed_mult = 1.0
        self.inventory_anim = 0.0
        self.dilemma_anim = 0.0
        self.banner_anim = 0.0
        self.zone_card_anim = 0.0
        self.shake_strength = 0.0
        self.shake_time = 0.0
        self.particles: list[Particle] = []
        self.sprite_cache: dict[str, pygame.Surface] = {}
        self.entity_sprites: dict[str, dict[str, pygame.Surface]] = {}
        self.zone_card_title = ""
        self.zone_card_subtitle = ""
        self.zone_card_timer = 0.0
        self.visited_areas: set[str] = set()
        self.current_viewport_world = pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.current_render_scale = float(SCALE)
        self.camera_center = pygame.Vector2(INTERNAL_WIDTH * 0.5, INTERNAL_HEIGHT * 0.5)

        self.locked_door_tile = (10, 1)
        self.exit_tile = (10, 1)
        self.transition_tile = (0, 0)
        self.breaker_tile = (0, 0)
        self.elevator_terminal_tile = (0, 0)
        self.final_exit_tile = (0, 0)
        self.door_unlocked = False
        self.desk_searched = False
        self.cabinet_searched = False
        self.bed_searched = False
        self.dilemma_triggered = False
        self.area2_cleared = False
        self.lasers_disabled_timer = 0.0
        self.elevator_choice_made = False
        self.choice_result = ""
        self.final_exit_unlocked = False
        self.time_alive = 0.0
        self.has_keycard = False
        self.backpack_collected = False
        self.l2_boss_defeated = False

        self.checkpoints: dict[str, tuple[int, int]] = {}
        self.sound = SoundManager()
        self.footstep_timer = 0.0
        self.save_tiles: list[tuple[int, int]] = []
        self.hints_shown: set[str] = set()
        self.active_hint: str = ""
        self.active_hint_timer: float = 0.0
        self.active_hint_fade: float = 0.0
        self.low_hp_pulse_phase: float = 0.0
        self.dilemma_selection: int = 0  # 0=none, 1=leg, 2=arm
        self.pause_selected = 0
        self.area_fade_alpha: float = 0.0
        self.area_fade_phase: str = "none"  # "none", "fadeOut", "fadeIn"
        self.area_fade_target: str = ""
        self.area_fade_spawn: tuple[int, int] | None = None

        self.load_visual_assets()
        self.load_area(self.current_area)

    def load_visual_assets(self) -> None:
        self.sprite_cache["player"] = self.load_sprite(
            self.assets_root / "characters" / "player" / "char_player_idle_f01.png",
            (16, 16),
        )
        self.sprite_cache["wolf"] = self.load_sprite(
            self.assets_root / "characters" / "wolves" / "char_wolf_patrol_f01.png",
            (16, 16),
        )
        self.sprite_cache["key"] = self.load_sprite(self.assets_root / "items" / "item_key_a01.png", (8, 8))
        self.sprite_cache["battery"] = self.load_sprite(self.assets_root / "items" / "item_battery_a01.png", (8, 8))
        self.sprite_cache["bandage"] = self.load_sprite(self.assets_root / "items" / "item_bandage_a01.png", (8, 8))
        self.sprite_cache["flashlight"] = self.load_sprite(self.assets_root / "items" / "item_flashlight_a01.png", (8, 8))
        self.sprite_cache["knife"] = self.load_sprite(self.assets_root / "items" / "item_knife_pickup_a01.png", (8, 8))
        self.build_entity_sprites()

    def load_sprite(self, path: Path, size: tuple[int, int]) -> pygame.Surface | None:
        if path.exists():
            sprite = pygame.image.load(path.as_posix()).convert_alpha()
            if sprite.get_size() != size:
                sprite = pygame.transform.scale(sprite, size)
            return sprite

        return None

    def sprite_from_pattern(
        self,
        pattern: list[str],
        palette: dict[str, tuple[int, int, int] | tuple[int, int, int, int]],
    ) -> pygame.Surface:
        height = len(pattern)
        width = max((len(row) for row in pattern), default=0)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        for y, row in enumerate(pattern):
            for x, code in enumerate(row):
                if code == ".":
                    continue
                color = palette.get(code)
                if color is None:
                    continue
                surface.set_at((x, y), color)
        return surface

    def mirror_sprite(self, sprite: pygame.Surface) -> pygame.Surface:
        return pygame.transform.flip(sprite, True, False)

    def build_entity_sprites(self) -> None:
        player_palette = {
            "a": (46, 34, 30),
            "s": (176, 130, 105),
            "h": (226, 212, 192),
            "j": (56, 69, 82),
            "c": (88, 108, 122),
            "g": (112, 90, 72),
            "p": (50, 58, 72),
            "b": (32, 34, 40),
            "f": (112, 160, 118),
            "m": (170, 174, 182),
            "k": (226, 228, 232),
            "r": (186, 82, 82),
        }
        wolf_palette = {
            "o": (24, 22, 26),
            "w": (102, 104, 108),
            "g": (140, 142, 144),
            "l": (176, 178, 180),
            "e": (232, 236, 240),
            "r": (228, 82, 82),
            "n": (42, 32, 30),
        }

        player_patterns = {
            "down_idle": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcggcj......",
                ".....jccj.......",
                "....pp..pp......",
                "...bpp..ppb.....",
                "...bb....bb.....",
                "................",
            ],
            "down_walk_a": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcggcj......",
                ".....jccj.......",
                ".....pp.pp......",
                "...bbp...pb.....",
                "...b.....bb.....",
                "................",
            ],
            "down_walk_b": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcggcj......",
                ".....jccj.......",
                "....pp.pp.......",
                "...bp...pbb.....",
                "...bb.....b.....",
                "................",
            ],
            "up_idle": [
                "................",
                "......aa........",
                ".....ajja.......",
                ".....jjjj.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcgccj......",
                ".....jccj.......",
                "....pp..pp......",
                "...bpp..ppb.....",
                "...bb....bb.....",
                "................",
            ],
            "up_walk_a": [
                "................",
                "......aa........",
                ".....ajja.......",
                ".....jjjj.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcgccj......",
                ".....jccj.......",
                ".....pp.pp......",
                "...bbp...pb.....",
                "...b.....bb.....",
                "................",
            ],
            "up_walk_b": [
                "................",
                "......aa........",
                ".....ajja.......",
                ".....jjjj.......",
                "....jjccjj......",
                "....jccccj......",
                "....jcgccj......",
                ".....jccj.......",
                "....pp.pp.......",
                "...bp...pbb.....",
                "...bb.....b.....",
                "................",
            ],
            "side_idle": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccjj.....",
                "....jcgccfk.....",
                ".....jccjj......",
                "....pppp........",
                "...bp.pmb.......",
                "...bb..bb.......",
                "................",
            ],
            "side_walk_a": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccjj.....",
                "....jcgccfk.....",
                ".....jccjj......",
                ".....ppp........",
                "...bbp.pmb......",
                "...b...bb.......",
                "................",
            ],
            "side_walk_b": [
                "................",
                "......aa........",
                ".....assh.......",
                ".....shhs.......",
                "....jjccjj......",
                "....jccccjj.....",
                "....jcgccfk.....",
                ".....jccjj......",
                "....pppp........",
                "...bp..pmb......",
                "...bb...bb......",
                "................",
            ],
            "side_hurt": [
                "................",
                "......aa........",
                ".....arrh.......",
                ".....shhs.......",
                "....jjccjj......",
                "...jjccccjj.....",
                "...jjcgccfk.....",
                "....jjccjj......",
                "....pppp........",
                "...bp.pmb.......",
                "..bb...bb.......",
                "................",
            ],
        }

        wolf_patterns = {
            "side_idle": [
                "................",
                "................",
                "....oo..........",
                "...owggwwo......",
                "..owwwwwwwwo....",
                "..owwwwwwwwe....",
                "...owwwwwwwo....",
                "..oo.ww.ww......",
                "..o..ww.ww......",
                ".....o...o......",
                "................",
                "................",
            ],
            "side_walk_a": [
                "................",
                "................",
                "....oo..........",
                "...owggwwo......",
                "..owwwwwwwwo....",
                "..owwwwwwwwe....",
                "...owwwwwwwo....",
                "...o.ww..ww.....",
                "..o..ww.ww......",
                ".....o...o......",
                "................",
                "................",
            ],
            "side_walk_b": [
                "................",
                "................",
                "....oo..........",
                "...owggwwo......",
                "..owwwwwwwwo....",
                "..owwwwwwwwe....",
                "...owwwwwwwo....",
                "..oo..ww.ww.....",
                "...o.ww..ww.....",
                "......o...o.....",
                "................",
                "................",
            ],
            "side_alert": [
                "................",
                "................",
                "....oo..........",
                "...owllwwo......",
                "..owwwwwwwwo....",
                "..owwwwwwwwr....",
                "...owwwwwwwo....",
                "..oo.ww.ww......",
                "..o..ww.ww......",
                ".....o...o......",
                "................",
                "................",
            ],
            "up_idle": [
                "................",
                "................",
                ".....owwo.......",
                "....owwwwo......",
                "...owwllwwo.....",
                "...owwwwwwo.....",
                "...owwwwwwo.....",
                "...o.wwww.o.....",
                "..o..w..w..o....",
                ".....o..o.......",
                "................",
                "................",
            ],
            "up_alert": [
                "................",
                "................",
                ".....owwo.......",
                "....owrrwo......",
                "...owwllwwo.....",
                "...owwwwwwo.....",
                "...owwwwwwo.....",
                "...o.wwww.o.....",
                "..o..w..w..o....",
                ".....o..o.......",
                "................",
                "................",
            ],
            "down_idle": [
                "................",
                "................",
                ".....owwo.......",
                "....owggwo......",
                "...owwwwwwo.....",
                "...owweewwo.....",
                "...owwwwwwo.....",
                "...o.wwww.o.....",
                "..o..w..w..o....",
                ".....o..o.......",
                "................",
                "................",
            ],
            "down_alert": [
                "................",
                "................",
                ".....owwo.......",
                "....owllwo......",
                "...owwwwwwo.....",
                "...owwrrwwo.....",
                "...owwwwwwo.....",
                "...o.wwww.o.....",
                "..o..w..w..o....",
                ".....o..o.......",
                "................",
                "................",
            ],
            "corpse": [
                "................",
                "................",
                "................",
                "...owwwww.......",
                "..owwwwwww......",
                "..owwwggwo......",
                "...owwwwwo......",
                "....owwwwo......",
                ".....o..oo......",
                "................",
                "................",
                "................",
            ],
        }

        self.entity_sprites["player"] = {}
        for key, pattern in player_patterns.items():
            sprite = self.sprite_from_pattern(pattern, player_palette)
            self.entity_sprites["player"][key] = sprite
            if key.startswith("side_"):
                self.entity_sprites["player"][key.replace("side_", "left_")] = self.mirror_sprite(sprite)
                self.entity_sprites["player"][key.replace("side_", "right_")] = sprite

        self.entity_sprites["wolf"] = {}
        for key, pattern in wolf_patterns.items():
            sprite = self.sprite_from_pattern(pattern, wolf_palette)
            self.entity_sprites["wolf"][key] = sprite
            if key.startswith("side_"):
                self.entity_sprites["wolf"][key.replace("side_", "left_")] = self.mirror_sprite(sprite)
                self.entity_sprites["wolf"][key.replace("side_", "right_")] = sprite

    def save_game(self) -> None:
        data = {
            "area": self.current_area,
            "player_x": self.player_pos.x,
            "player_y": self.player_pos.y,
            "health": self.health,
            "battery": self.battery,
            "bandages": self.bandages,
            "has_flashlight": self.has_flashlight,
            "has_knife": self.has_knife,
            "has_key": self.has_key,
            "flashlight_on": self.flashlight_on,
            "visited_areas": list(self.visited_areas),
            "area2_cleared": self.area2_cleared,
            "dilemma_chosen": getattr(self, "choice_result", None),
            "final_exit_unlocked": self.final_exit_unlocked,
            "has_keycard": self.has_keycard,
            "backpack_collected": self.backpack_collected,
            "l2_boss_defeated": self.l2_boss_defeated,
            "hints_shown": list(self.hints_shown),
        }
        save_path = Path(__file__).resolve().parents[1] / "save.json"
        with open(save_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_game(self) -> bool:
        save_path = Path(__file__).resolve().parents[1] / "save.json"
        if not save_path.exists():
            return False
        try:
            with open(save_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return False
        self.current_area = data["area"]
        spawn_tile = (int(data["player_x"]) // TILE_SIZE, int(data["player_y"]) // TILE_SIZE)
        self.load_area(self.current_area, spawn_override=spawn_tile)
        self.health = data["health"]
        self.battery = data["battery"]
        self.bandages = data["bandages"]
        self.has_flashlight = data["has_flashlight"]
        self.has_knife = data["has_knife"]
        self.has_key = data["has_key"]
        self.flashlight_on = data["flashlight_on"]
        self.visited_areas = set(data.get("visited_areas", []))
        self.area2_cleared = data.get("area2_cleared", False)
        self.final_exit_unlocked = data.get("final_exit_unlocked", False)
        self.hints_shown = set(data.get("hints_shown", []))
        choice = data.get("dilemma_chosen")
        if choice:
            self.choice_result = choice
            self.elevator_choice_made = True
            if choice == "leg":
                self.player_speed = self.base_player_speed * 0.65
            elif choice == "arm":
                # Attack speed -70% means attack interval is about 3.33x longer.
                self.attack_speed_mult = 10.0 / 3.0
        self.has_keycard = data.get("has_keycard", False)
        self.backpack_collected = data.get("backpack_collected", False)
        self.l2_boss_defeated = data.get("l2_boss_defeated", False)
        return True

    def try_save_at_terminal(self) -> None:
        tile_x = self.player.centerx // TILE_SIZE
        tile_y = self.player.centery // TILE_SIZE
        for sx, sy in self.save_tiles:
            if abs(tile_x - sx) + abs(tile_y - sy) <= 1:
                self.save_game()
                self.sound.play("save")
                self.message = "Progress saved"
                self.message_timer = 1.4
                return

    def trigger_hint(self, hint_id: str) -> None:
        if hint_id in self.hints_shown:
            return
        self.hints_shown.add(hint_id)
        self.active_hint = self.HINT_DEFS.get(hint_id, "")
        self.active_hint_timer = 3.0
        self.active_hint_fade = 0.0

    def check_contextual_hints(self) -> None:
        tile_x = self.player.centerx // TILE_SIZE
        tile_y = self.player.centery // TILE_SIZE

        if "interact_door" not in self.hints_shown:
            for door in self.current_doors:
                dx, dy = door["tile"]
                if abs(tile_x - dx) + abs(tile_y - dy) <= 2:
                    self.trigger_hint("interact_door")
                    break

        if "flashlight_dark" not in self.hints_shown and not self.flashlight_on:
            if (tile_x, tile_y) in self.dark_tiles:
                self.trigger_hint("flashlight_dark")

        if "attack_wolf" not in self.hints_shown:
            for wolf in self.wolves:
                if wolf.alive:
                    dist = math.hypot(self.player.centerx - wolf.rect.centerx, self.player.centery - wolf.rect.centery)
                    if dist < 48:
                        self.trigger_hint("attack_wolf")
                        break

        if "use_bandage" not in self.hints_shown and self.health < 50 and self.bandages > 0:
            self.trigger_hint("use_bandage")

        if "save_terminal" not in self.hints_shown:
            for sx, sy in self.save_tiles:
                if abs(tile_x - sx) + abs(tile_y - sy) <= 2:
                    self.trigger_hint("save_terminal")
                    break

    def load_area(self, area_id: str, spawn_override: tuple[int, int] | None = None) -> None:
        self.current_area = area_id
        self.visited_areas.add(area_id)
        self.current_map = AREA_MAPS[area_id]
        self.world_width = len(self.current_map[0]) * TILE_SIZE
        self.world_height = len(self.current_map) * TILE_SIZE
        self.current_doors = AREA_DOORS.get(area_id, [])

        self.walls.clear()
        self.traps.clear()
        self.pickups.clear()
        self.wolves.clear()
        self.save_tiles = []
        self.dark_tiles.clear()
        self.furniture.clear()
        self.lasers.clear()
        self.hazards.clear()
        self.flicker_lights.clear()
        self.lasers_disabled_timer = 0.0
        self.breaker_tile = (0, 0)
        self.transition_tile = (0, 0)
        self.elevator_terminal_tile = (0, 0)
        self.final_exit_tile = (0, 0)

        spawn = (1, 1)
        for y, row in enumerate(self.current_map):
            for x, cell in enumerate(row):
                world_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

                if cell == "#":
                    self.walls.append(world_rect)
                elif cell == "P":
                    spawn = (x, y)
                elif cell == "D":
                    self.locked_door_tile = (x, y)
                    self.exit_tile = (x, y)
                elif cell == "d":
                    self.furniture[(x, y)] = "desk"
                elif cell == "c":
                    self.furniture[(x, y)] = "cabinet"
                elif cell == "b":
                    self.furniture[(x, y)] = "bed"
                elif cell == "s":
                    self.furniture[(x, y)] = "stool"
                elif cell == "f":
                    self.furniture[(x, y)] = "freezer"
                    freezer_key = (area_id, x, y)
                    if freezer_key not in self.freezer_charges:
                        self.freezer_charges[freezer_key] = 4
                elif cell == "R":
                    self.breaker_tile = (x, y)
                elif cell == "G":
                    self.transition_tile = (x, y)
                elif cell == "M":
                    self.pickups.append(ItemPickup("battery", x, y))
                elif cell == "H":
                    self.pickups.append(ItemPickup("bandage", x, y))
                elif cell == "E":
                    self.elevator_terminal_tile = (x, y)
                elif cell == "k":
                    self.pickups.append(ItemPickup("knife", x, y))
                elif cell == "W":
                    self.wolves.append(Wolf(x * TILE_SIZE + 2, y * TILE_SIZE + 2))
                elif cell == "1":
                    w = Wolf(x * TILE_SIZE + 2, y * TILE_SIZE + 2, subtype="stalker")
                    self.wolves.append(w)
                elif cell == "2":
                    w = Wolf(x * TILE_SIZE + 2, y * TILE_SIZE + 2, subtype="hunter",
                             patrol_origin_x=x * TILE_SIZE + 2, patrol_origin_y=y * TILE_SIZE + 2)
                    self.wolves.append(w)
                elif cell == "3":
                    w = Wolf(x * TILE_SIZE - 4, y * TILE_SIZE - 4, subtype="alpha",
                             hp=5, max_hp=5, size=20)
                    self.wolves.append(w)
                elif cell == "X":
                    self.final_exit_tile = (x, y)
                elif cell == "S":
                    self.save_tiles.append((x, y))
                elif cell == "B":
                    self.furniture[(x, y)] = "backpack"
                elif cell == "K":
                    self.pickups.append(ItemPickup("keycard", x, y))
                elif cell == "T":
                    self.hazards.append(Hazard("tripwire", x, y,
                                               pygame.Rect(x * TILE_SIZE + 4, y * TILE_SIZE, 8, TILE_SIZE)))
                elif cell == "A":
                    self.hazards.append(Hazard("alarm", x, y,
                                               pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)))
                elif cell == "C":
                    self.hazards.append(Hazard("crumble", x, y,
                                               pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)))
                elif cell == "L":
                    self.flicker_lights.append(FlickerLight(
                        x, y,
                        random.uniform(0, 5.0),
                        random.uniform(1.5, 4.0),
                        random.uniform(0.1, 0.6),
                    ))

        self.checkpoints[area_id] = spawn
        spawn_tile = spawn_override if spawn_override is not None else spawn
        self.player.x = spawn_tile[0] * TILE_SIZE + 3
        self.player.y = spawn_tile[1] * TILE_SIZE + 2
        self.player_pos.update(float(self.player.x), float(self.player.y))
        self.player_vel.update(0, 0)
        self.reset_camera(immediate=True)

        if area_id == "area2":
            self.setup_area2_lasers()

        if area_id == "final":
            self.final_exit_unlocked = False

        if area_id == "l2_floor3":
            for fy, row in enumerate(self.current_map):
                for fx, cell in enumerate(row):
                    if cell != "#":
                        self.dark_tiles.add((fx, fy))

        zone_code, zone_name, _ = self.get_area_meta(area_id)
        level_prefix = "LEVEL 2" if area_id.startswith("l2_") else "LEVEL 1"
        self.zone_card_title = f"{level_prefix}  |  {zone_code}"
        self.zone_card_subtitle = zone_name
        self.zone_card_timer = 2.2

        self.set_objective_for_area()

    def get_area_meta(self, area_id: str | None = None) -> tuple[str, str, str]:
        key = area_id if area_id is not None else self.current_area
        return AREA_META.get(key, ("B1-??", "UNKNOWN ZONE", "???"))

    def get_area_theme(self, area_id: str | None = None) -> dict[str, tuple[int, int, int]]:
        key = area_id if area_id is not None else self.current_area
        return AREA_THEMES.get(key, AREA_THEMES["hub"])

    def get_area_doors(self, area_id: str | None = None) -> list[dict[str, object]]:
        key = area_id if area_id is not None else self.current_area
        return AREA_DOORS.get(key, [])

    def get_nearby_door(self, tile_x: int, tile_y: int) -> dict[str, object] | None:
        for door in self.current_doors:
            dx, dy = door["tile"]
            if abs(tile_x - dx) + abs(tile_y - dy) <= 1:
                return door
        return None

    def is_door_locked(self, door: dict[str, object]) -> bool:
        requirement = str(door.get("requirement", "none"))
        if requirement == "unit_door":
            return not self.door_unlocked
        if requirement == "lasers_off":
            return not self.area2_cleared
        if requirement == "elevator_ready":
            return not self.elevator_choice_made
        if requirement == "keycard":
            return not self.has_keycard
        if requirement == "knife_pry":
            return not self.has_knife
        return False

    def get_door_prompt(self, door: dict[str, object]) -> str:
        requirement = str(door.get("requirement", "none"))
        door_id = str(door.get("id", "D-??"))
        label = str(door.get("label", "UNKNOWN ZONE"))
        if requirement == "unit_door" and not self.door_unlocked:
            return "Press E to unlock unit door" if self.has_key else str(door.get("locked", "Door locked"))
        if requirement == "lasers_off" and not self.area2_cleared:
            return str(door.get("locked", "Door sealed"))
        if requirement == "elevator_ready" and not self.elevator_choice_made:
            return str(door.get("locked", "Terminal authorization required"))
        if requirement == "keycard" and not self.has_keycard:
            return str(door.get("locked", "Need keycard"))
        if requirement == "knife_pry" and not self.has_knife:
            return str(door.get("locked", "Need knife"))
        return f"Press E: {door_id} -> {label}"

    def interact_door(self, door: dict[str, object]) -> bool:
        requirement = str(door.get("requirement", "none"))
        if requirement == "unit_door" and not self.door_unlocked:
            if self.has_key:
                self.door_unlocked = True
                self.set_objective_for_area()
                self.message = "Unit door unlocked. Press E to enter hallway"
                self.message_timer = 1.3
            else:
                self.message = str(door.get("locked", "Door locked"))
                self.message_timer = 1.1
            return True

        if requirement == "lasers_off" and not self.area2_cleared:
            self.message = str(door.get("locked", "Checkpoint sealed"))
            self.message_timer = 1.2
            return True

        if requirement == "elevator_ready" and not self.elevator_choice_made:
            self.message = str(door.get("locked", "Terminal authorization required"))
            self.message_timer = 1.2
            return True

        if requirement == "keycard" and not self.has_keycard:
            self.message = str(door.get("locked", "Need keycard"))
            self.message_timer = 1.2
            return True

        if requirement == "knife_pry" and not self.has_knife:
            self.message = str(door.get("locked", "Need knife"))
            self.message_timer = 1.2
            return True

        target_area = str(door.get("to", self.current_area))
        if target_area == "__level2_complete__":
            if not self.l2_boss_defeated:
                self.message = "Defeat the Alpha Wolf first"
                self.message_timer = 1.2
                return True
            self.state = "won"
            self.message = "Level 2 complete. You escaped the descent."
            self.message_timer = 1000.0
            return True

        target_area = str(door.get("to", self.current_area))
        spawn = door.get("spawn", None)
        spawn_override = spawn if isinstance(spawn, tuple) else None
        self.sound.play("door")
        self.start_area_transition(target_area, spawn_override)
        zone_code, zone_name, _ = self.get_area_meta(target_area)
        self.message = f"Entering {zone_code} {zone_name}"
        self.message_timer = 1.4
        return True

    def setup_area2_lasers(self) -> None:
        self.lasers = [
            LaserBeam(pygame.Rect(8 * TILE_SIZE, 3 * TILE_SIZE + 7, 4 * TILE_SIZE, 2), 1.25, 0.7, 0.0),
            LaserBeam(pygame.Rect(8 * TILE_SIZE, 5 * TILE_SIZE + 7, 4 * TILE_SIZE, 2), 1.15, 0.75, 0.35),
            LaserBeam(pygame.Rect(8 * TILE_SIZE, 7 * TILE_SIZE + 7, 4 * TILE_SIZE, 2), 1.1, 0.8, 0.7),
            LaserBeam(pygame.Rect(9 * TILE_SIZE + 7, 2 * TILE_SIZE, 2, 6 * TILE_SIZE), 0.95, 0.85, 1.05),
        ]

    def get_flashlight_radius(self) -> float:
        if not self.flashlight_on or self.battery <= 0:
            return 0.0
        return 56.0 if self.battery > 20 else 46.0

    def can_reveal_pickups(self) -> bool:
        return self.get_flashlight_radius() > 0

    def is_pickup_in_flashlight_range(self, pickup: ItemPickup) -> bool:
        radius = self.get_flashlight_radius()
        if radius <= 0:
            return False
        player_center = pygame.Vector2(self.player.centerx, self.player.centery)
        pickup_center = pygame.Vector2(pickup.rect.centerx, pickup.rect.centery)
        return player_center.distance_to(pickup_center) <= radius + 2.0

    def interact_freezer(self, tile: tuple[int, int]) -> bool:
        freezer_key = (self.current_area, tile[0], tile[1])
        charges = self.freezer_charges.get(freezer_key, 0)
        if charges <= 0:
            self.message = "Freezer is empty"
            self.message_timer = 1.0
            return True

        if self.battery >= 100:
            self.message = "Battery already full"
            self.message_timer = 1.0
            return True

        self.freezer_charges[freezer_key] = charges - 1
        self.battery = min(100, self.battery + 24)
        self.emit_particles(tile[0] * TILE_SIZE + TILE_SIZE // 2, tile[1] * TILE_SIZE + TILE_SIZE // 2, 8, PALETTE["battery"])
        self.message = f"Energy drink used (+BAT). Left: {self.freezer_charges[freezer_key]}"
        self.message_timer = 1.3
        return True

    def set_objective_for_area(self) -> None:
        if self.current_area == "area1":
            if not self.has_key:
                self.objective = "Locate unit key"
            elif not self.door_unlocked:
                self.objective = "Unlock unit door"
            else:
                self.objective = "Enter main hallway"
        elif self.current_area == "hub":
            if not self.area2_cleared:
                self.objective = "Explore rooms and reach security checkpoint"
            elif not self.elevator_choice_made:
                self.objective = "Reach elevator lobby"
            else:
                self.objective = "Route to exit hall"
        elif self.current_area == "storage":
            self.objective = "Search storage and return to hallway"
        elif self.current_area == "medbay":
            self.objective = "Collect supplies and return to hallway"
        elif self.current_area == "maintenance":
            if not self.area2_cleared:
                self.objective = "Activate maintenance breaker"
            elif not self.has_knife:
                self.objective = "Find knife then head to elevator"
            else:
                self.objective = "Return to checkpoint gate"
        elif self.current_area == "area2":
            if not self.area2_cleared:
                self.objective = "Lasers active. Use maintenance breaker"
            else:
                self.objective = "Proceed to elevator lobby"
        elif self.current_area == "area3":
            if not self.has_knife:
                self.objective = "Need knife from maintenance"
            elif not self.elevator_choice_made:
                self.objective = "Use elevator terminal and choose"
            else:
                self.objective = "Ride elevator to exit hall"
        elif self.current_area == "l2_floor4":
            if not self.backpack_collected:
                self.objective = "Collect the backpack"
            else:
                self.objective = "Navigate hallway to stairwell"
        elif self.current_area == "l2_floor3":
            if not self.has_keycard:
                self.objective = "Find keycard in dark rooms"
            else:
                self.objective = "Unlock stairwell with keycard"
        elif self.current_area == "l2_floor2":
            self.objective = "Avoid traps and wolves. Reach the grate"
        elif self.current_area == "l2_floor1":
            if not self.l2_boss_defeated:
                self.objective = "Defeat the Alpha Wolf"
            else:
                self.objective = "Reach the steel door"
        else:
            if not self.final_exit_unlocked:
                self.objective = "Clear hostiles in exit hall"
            else:
                self.objective = "Reach building exit"

    def run(self) -> None:
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.time_alive += dt
            self.handle_events()
            self.update_visual_fx(dt)
            if self.state == "explore":
                self.update_explore(dt)
            self.draw()

    def update_visual_fx(self, dt: float) -> None:
        inv_target = 1.0 if self.state == "inventory" else 0.0
        dil_target = 1.0 if self.state == "dilemma" else 0.0
        banner_target = 1.0 if self.message_timer > 0 else 0.0
        zone_target = 1.0 if self.zone_card_timer > 0 else 0.0

        self.inventory_anim += (inv_target - self.inventory_anim) * min(1.0, dt * 12.0)
        self.dilemma_anim += (dil_target - self.dilemma_anim) * min(1.0, dt * 12.0)
        self.banner_anim += (banner_target - self.banner_anim) * min(1.0, dt * 9.0)
        self.zone_card_anim += (zone_target - self.zone_card_anim) * min(1.0, dt * 8.0)
        self.zone_card_timer = max(0.0, self.zone_card_timer - dt)

        self.shake_time = max(0.0, self.shake_time - dt)
        if self.shake_time <= 0:
            self.shake_strength = 0.0
        else:
            self.shake_strength *= 0.9

        if self.health < self.max_health * 0.3:
            self.low_hp_pulse_phase += dt * 5.2
        else:
            self.low_hp_pulse_phase = 0.0

        for p in self.particles[:]:
            p.life -= dt
            if p.life <= 0:
                self.particles.remove(p)
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += 20.0 * dt

    def laser_is_active(self, laser: LaserBeam) -> bool:
        if self.area2_cleared:
            return False
        period = laser.on_time + laser.off_time
        return ((self.time_alive + laser.phase) % period) < laser.on_time

    def update_area2_hazards(self) -> None:
        if self.current_area != "area2":
            return
        if self.area2_cleared:
            return
        if self.hit_cooldown > 0:
            return

        for laser in self.lasers:
            if self.laser_is_active(laser) and self.player.colliderect(laser.rect):
                self.health = max(0, self.health - 12)
                self.sound.play("damage")
                self.damage_flash = 0.14
                self.hit_cooldown = 0.45
                self.message = "Laser burn"
                self.message_timer = 0.9
                self.trigger_shake(1.6, 0.12)
                self.emit_particles(self.player.centerx, self.player.centery, 8, PALETTE["trap_on"])
                if self.health <= 0:
                    self.respawn_at_checkpoint()
                break

    def respawn_at_checkpoint(self) -> None:
        spawn = self.checkpoints.get(self.current_area, (1, 1))
        self.player.x = spawn[0] * TILE_SIZE + 3
        self.player.y = spawn[1] * TILE_SIZE + 2
        self.player_pos.update(float(self.player.x), float(self.player.y))
        self.player_vel.update(0, 0)
        self.health = self.max_health
        self.flashlight_on = False
        self.hit_cooldown = 0.6
        self.message = "You collapsed. Respawned at checkpoint."
        self.message_timer = 1.8
        self.damage_flash = 0.0

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            if event.type == pygame.VIDEORESIZE:
                # Keep a larger outer window while preserving centered gameplay viewport.
                min_w = GAME_VIEW_WIDTH + 220
                min_h = GAME_VIEW_HEIGHT + 160
                new_w = max(min_w, event.w)
                new_h = max(min_h, event.h)
                self.screen = pygame.display.set_mode((new_w, new_h), pygame.DOUBLEBUF | pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "inventory":
                        self.state = "explore"
                        continue
                    elif self.state == "explore":
                        self.state = "pause"
                        self.pause_selected = 0
                        continue
                    elif self.state == "pause":
                        self.state = "explore"
                        continue
                    pygame.quit()
                    sys.exit(0)

                if self.state == "dead" and event.key:
                    save_path = Path(__file__).resolve().parents[1] / "save.json"
                    if save_path.exists():
                        save_path.unlink()
                    self.__init__()
                    continue
                if self.state == "won" and event.key:
                    if self.current_area == "final":
                        self.health = 100
                        self.battery = 50
                        self.bandages = 2
                        self.current_area = "l2_floor4"
                        self.load_area("l2_floor4")
                        self.state = "explore"
                        self.intro_title = "LEVEL 2: DESCENT"
                        self.intro_lines = [
                            "You escaped B1. But the building goes deeper.",
                            "WASD Move   E Interact",
                            "Q Flashlight   SPACE Attack",
                            "TAB Inventory   F Equip",
                        ]
                        self.intro_hint = "Press ENTER to start"
                        self.intro_timer = 8.5
                    else:
                        pygame.quit()
                        sys.exit(0)
                    continue

                if self.intro_timer > 0 and self.state == "explore":
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.intro_timer = 0.0
                    continue

                if event.key == pygame.K_l:
                    self.show_labels = not self.show_labels
                    self.message = "Labels ON" if self.show_labels else "Labels OFF"
                    self.message_timer = 1.0

                if event.key == pygame.K_TAB:
                    if self.state == "explore":
                        self.state = "inventory"
                    elif self.state == "inventory":
                        self.state = "explore"

                if self.state == "explore":
                    if event.key == pygame.K_e:
                        self.try_interact()
                    if event.key == pygame.K_q:
                        self.toggle_flashlight()
                    if event.key == pygame.K_SPACE:
                        self.attack()
                elif self.state == "inventory":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.inventory_selected = max(0, self.inventory_selected - 1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.inventory_selected = min(self.inventory_cols * self.inventory_rows - 1, self.inventory_selected + 1)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.inventory_selected = max(0, self.inventory_selected - self.inventory_cols)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.inventory_selected = min(self.inventory_cols * self.inventory_rows - 1, self.inventory_selected + self.inventory_cols)
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self.inventory_use_selected()
                    elif event.key == pygame.K_f:
                        self.inventory_equip_selected()
                    if event.key == pygame.K_h:
                        self.use_bandage()

                if self.state == "dilemma":
                    if event.key == pygame.K_1:
                        self.dilemma_selection = 1
                    elif event.key == pygame.K_2:
                        self.dilemma_selection = 2
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self.dilemma_selection == 1:
                            self.choose_dilemma("leg")
                        elif self.dilemma_selection == 2:
                            self.choose_dilemma("arm")
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "explore"
                        self.dilemma_selection = 0

                if self.state == "pause":
                    if event.key == pygame.K_UP:
                        self.pause_selected = (self.pause_selected - 1) % 3
                    elif event.key == pygame.K_DOWN:
                        self.pause_selected = (self.pause_selected + 1) % 3
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if self.pause_selected == 0:
                            self.state = "explore"
                        elif self.pause_selected == 1:
                            self.save_game()
                            pygame.quit()
                            sys.exit(0)
                        elif self.pause_selected == 2:
                            pygame.quit()
                            sys.exit(0)

    def update_explore(self, dt: float) -> None:
        if self.area_fade_phase == "fadeOut":
            self.area_fade_alpha = min(255, self.area_fade_alpha + dt * 850)
            if self.area_fade_alpha >= 255:
                self.load_area(self.area_fade_target, self.area_fade_spawn)
                self.area_fade_phase = "fadeIn"
            return
        if self.area_fade_phase == "fadeIn":
            self.area_fade_alpha = max(0, self.area_fade_alpha - dt * 850)
            if self.area_fade_alpha <= 0:
                self.area_fade_phase = "none"
            return

        self.message_timer = max(0.0, self.message_timer - dt)
        self.damage_flash = max(0.0, self.damage_flash - dt)
        self.hit_cooldown = max(0.0, self.hit_cooldown - dt)
        self.attack_cooldown = max(0.0, self.attack_cooldown - dt)
        self.attack_anim = max(0.0, self.attack_anim - dt)
        self.lasers_disabled_timer = max(0.0, self.lasers_disabled_timer - dt)

        move = pygame.Vector2(0, 0)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1

        if move.length_squared() > 0:
            move = move.normalize()
            self.last_dir = move

        accel = self.player_accel
        if move.length_squared() > 0:
            self.player_vel += move * accel * dt
        else:
            drag = max(0.0, 1.0 - self.player_drag * dt)
            self.player_vel *= drag

        if self.player_vel.length_squared() > 0:
            max_speed = max(20.0, self.player_speed)
            if self.player_vel.length() > max_speed:
                self.player_vel.scale_to_length(max_speed)

        if self.player_vel.length_squared() < 3.0:
            self.player_vel.update(0, 0)

        self.walk_cycle += self.player_vel.length() * dt * 0.22
        if self.player_vel.length_squared() > 9:
            self.footstep_timer -= dt
            if self.footstep_timer <= 0:
                self.sound.play("footstep")
                self.footstep_timer = 0.3
        else:
            self.footstep_timer = 0.0
        self.move_player(self.player_vel.x * dt, self.player_vel.y * dt)
        self.update_camera(dt)

        self.collect_pickups()
        self.check_traps()
        self.update_wolves(dt)
        self.update_flashlight(dt)
        self.update_area2_hazards()
        self.update_hazards(dt)
        self.check_contextual_hints()

        if self.active_hint_timer > 0:
            self.active_hint_timer -= dt
            self.active_hint_fade = min(1.0, self.active_hint_fade + dt * 4.0)
            if self.active_hint_timer <= 0:
                self.active_hint = ""
        else:
            self.active_hint_fade = max(0.0, self.active_hint_fade - dt * 2.0)

        if self.current_area == "final" and not self.final_exit_unlocked and not any(w.alive for w in self.wolves):
            self.final_exit_unlocked = True
            self.objective = "Reach building exit"
            self.message = "Exit unlocked"
            self.message_timer = 1.4

        tile_x = (self.player.centerx // TILE_SIZE)
        tile_y = (self.player.centery // TILE_SIZE)

        nearby_door = self.get_nearby_door(tile_x, tile_y)
        if nearby_door is not None and self.message_timer <= 0.15:
            self.message = self.get_door_prompt(nearby_door)
            self.message_timer = 0.8
        elif self.current_area == "final" and (tile_x, tile_y) == self.final_exit_tile and self.final_exit_unlocked and self.message_timer <= 0.15:
            self.message = "Final exit ready. Press E"
            self.message_timer = 0.8

    def move_player(self, dx: float, dy: float) -> None:
        self.player_pos.x += dx
        self.player.x = int(round(self.player_pos.x))
        self.resolve_collisions("x")
        self.player_pos.x = float(self.player.x)
        self.player_pos.y += dy
        self.player.y = int(round(self.player_pos.y))
        self.resolve_collisions("y")
        self.player_pos.y = float(self.player.y)
        self.player.clamp_ip(pygame.Rect(0, 0, self.world_width, self.world_height))
        self.player_pos.update(float(self.player.x), float(self.player.y))

    def resolve_collisions(self, axis: str) -> None:
        for wall in self.walls:
            if self.player.colliderect(wall):
                if axis == "x":
                    if self.player.centerx < wall.centerx:
                        self.player.right = wall.left
                    else:
                        self.player.left = wall.right
                else:
                    if self.player.centery < wall.centery:
                        self.player.bottom = wall.top
                    else:
                        self.player.top = wall.bottom

    def collect_pickups(self) -> None:
        if not self.can_reveal_pickups():
            return

        for pickup in self.pickups[:]:
            if self.player.colliderect(pickup.rect) and self.is_pickup_in_flashlight_range(pickup):
                self.emit_particles(pickup.rect.centerx, pickup.rect.centery, 8, PALETTE["battery"])
                self.sound.play("pickup")
                if pickup.name == "key":
                    self.has_key = True
                    self.message = "Picked up a key"
                elif pickup.name == "battery":
                    self.battery = min(100, self.battery + 35)
                    self.message = "Battery restored"
                elif pickup.name == "bandage":
                    self.bandages += 1
                    self.message = "Bandage added to inventory"
                elif pickup.name == "flashlight":
                    self.has_flashlight = True
                    self.message = "Flashlight acquired (Q to toggle)"
                elif pickup.name == "knife":
                    self.has_knife = True
                    self.equipped_item = "knife"
                    self.message = "Knife acquired"
                elif pickup.name == "keycard":
                    self.has_keycard = True
                    self.message = "Keycard acquired"

                self.set_objective_for_area()
                self.message_timer = 1.5
                self.pickups.remove(pickup)
                self.trigger_hint("open_inventory")

    def check_traps(self) -> None:
        px = self.player.centerx // TILE_SIZE
        py = self.player.centery // TILE_SIZE
        if (px, py) in self.traps and self.traps[(px, py)] and self.hit_cooldown <= 0:
            self.health = max(0, self.health - 15)
            self.damage_flash = 0.18
            self.hit_cooldown = 0.6
            self.message = "You stepped on a trap"
            self.message_timer = 1.1
            self.trigger_shake(2.8, 0.18)
            self.emit_particles(self.player.centerx, self.player.centery, 14, PALETTE["trap_on"])

            if self.health <= 0:
                self.respawn_at_checkpoint()

    def update_hazards(self, dt: float) -> None:
        for hazard in self.hazards:
            if not hazard.active:
                continue

            if hazard.kind == "tripwire":
                if not hazard.triggered and self.player.colliderect(hazard.rect):
                    hazard.triggered = True
                    hazard.active = False
                    if self.hit_cooldown <= 0:
                        self.health = max(0, self.health - 10)
                        self.damage_flash = 0.16
                        self.hit_cooldown = 0.5
                        self.sound.play("damage")
                        self.trigger_shake(2.0, 0.12)
                        self.emit_particles(hazard.tile_x * TILE_SIZE + 8, hazard.tile_y * TILE_SIZE + 8, 8, PALETTE["trap_on"])
                        self.message = "Tripwire!"
                        self.message_timer = 1.0
                        if self.health <= 0:
                            self.respawn_at_checkpoint()

            elif hazard.kind == "alarm":
                if not hazard.triggered and self.player.colliderect(hazard.rect):
                    hazard.triggered = True
                    hazard.active = False
                    for wolf in self.wolves:
                        if wolf.alive:
                            wolf.alert = True
                    self.sound.play("damage")
                    self.message = "Alarm triggered!"
                    self.message_timer = 1.5

            elif hazard.kind == "crumble":
                if not hazard.triggered and self.player.colliderect(hazard.rect):
                    hazard.triggered = True
                    hazard.crumble_timer = 0.8
                    self.message = "Floor cracking!"
                    self.message_timer = 0.8

                if hazard.triggered and hazard.active:
                    hazard.crumble_timer -= dt
                    if hazard.crumble_timer <= 0:
                        hazard.active = False
                        pit_rect = pygame.Rect(hazard.tile_x * TILE_SIZE, hazard.tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        self.walls.append(pit_rect)
                        if self.player.colliderect(pit_rect):
                            self.health = max(0, self.health - 20)
                            self.damage_flash = 0.16
                            self.hit_cooldown = 0.5
                            self.sound.play("damage")
                            self.trigger_shake(3.0, 0.2)
                            if self.health <= 0:
                                self.respawn_at_checkpoint()

    def try_interact(self) -> None:
        px = self.player.centerx // TILE_SIZE
        py = self.player.centery // TILE_SIZE
        is_near = lambda tile: abs(px - tile[0]) + abs(py - tile[1]) <= 1

        nearby_door = self.get_nearby_door(px, py)
        if nearby_door is not None:
            self.interact_door(nearby_door)
            return

        for (tx, ty), kind in self.furniture.items():
            if abs(px - tx) + abs(py - ty) > 1:
                continue
            if kind == "freezer":
                self.interact_freezer((tx, ty))
                return

        if self.current_area == "area1":
            for (tx, ty), kind in self.furniture.items():
                if abs(px - tx) + abs(py - ty) > 1:
                    continue

                if kind == "desk":
                    if not self.desk_searched:
                        self.desk_searched = True
                        self.has_flashlight = True
                        self.objective = "Search cabinet for key"
                        self.message = "Found flashlight. Note hints key in cabinet"
                    else:
                        self.message = "Desk has old papers and dead monitor"
                    self.message_timer = 1.8
                    return

                if kind == "cabinet":
                    if not self.desk_searched:
                        self.message = "Cabinet jammed. Check desk first"
                        self.message_timer = 1.5
                        return
                    if not self.cabinet_searched:
                        self.cabinet_searched = True
                        self.has_key = True
                        self.bandages += 1
                        self.set_objective_for_area()
                        self.message = "You found the key and a bandage"
                    else:
                        self.message = "Cabinet is empty"
                    self.message_timer = 1.6
                    return

                if kind == "bed":
                    if not self.bed_searched:
                        self.bed_searched = True
                        self.bandages += 1
                        self.message = "Found a bandage under the bed"
                    else:
                        self.message = "Nothing else under the bed"
                    self.message_timer = 1.4
                    return

                if kind == "stool":
                    self.message = "A small stool. Not useful right now"
                    self.message_timer = 1.0
                    return

        elif self.current_area == "maintenance":
            if self.breaker_tile != (0, 0) and is_near(self.breaker_tile):
                if not self.area2_cleared:
                    self.area2_cleared = True
                    self.set_objective_for_area()
                    self.message = "Main breaker engaged. Security lasers offline"
                else:
                    self.message = "Breaker already powered"
                self.message_timer = 1.2
                return

        elif self.current_area == "area3":
            if self.elevator_terminal_tile != (0, 0) and is_near(self.elevator_terminal_tile):
                if not self.has_knife:
                    self.message = "Need knife before terminal authorization"
                    self.message_timer = 1.2
                    return
                if not self.elevator_choice_made:
                    self.state = "dilemma"
                    self.dilemma_selection = 0
                    return

                self.message = "Terminal authorized. Elevator unlocked"
                self.message_timer = 1.5
                return

        elif self.current_area == "final":
            if self.final_exit_tile != (0, 0) and is_near(self.final_exit_tile):
                if self.final_exit_unlocked:
                    self.state = "won"
                    self.message = "Level 1 complete!"
                    self.message_timer = 1000.0
                else:
                    self.message = "Defeat all enemies first"
                    self.message_timer = 1.1
                return

        elif self.current_area == "l2_floor4":
            for (tx, ty), kind in self.furniture.items():
                if abs(px - tx) + abs(py - ty) > 1:
                    continue
                if kind == "backpack":
                    if not self.backpack_collected:
                        self.backpack_collected = True
                        self.has_flashlight = True
                        self.has_knife = True
                        self.equipped_item = "knife"
                        self.bandages += 2
                        self.battery = 75
                        self.message = "Found backpack: flashlight, knife, 2 bandages"
                        self.set_objective_for_area()
                    else:
                        self.message = "Empty backpack"
                    self.message_timer = 2.0
                    return

        self.try_save_at_terminal()

    def toggle_flashlight(self) -> None:
        if not self.has_flashlight:
            self.message = "No flashlight yet"
            self.message_timer = 1.0
            return

        if self.battery <= 0:
            self.flashlight_on = False
            self.message = "Battery empty"
            self.message_timer = 1.0
            return

        self.flashlight_on = not self.flashlight_on
        self.message = "Flashlight on" if self.flashlight_on else "Flashlight off"
        self.message_timer = 0.8

    def update_flashlight(self, dt: float) -> None:
        if not self.flashlight_on:
            return

        self.battery_tick += dt
        if self.battery_tick >= self.flashlight_drain_interval:
            self.battery_tick = 0.0
            self.battery = max(0, self.battery - 1)
            if self.battery == 0:
                self.flashlight_on = False
                self.message = "Battery depleted"
                self.message_timer = 1.0

    def update_wolves(self, dt: float) -> None:
        player_center = pygame.Vector2(self.player.centerx, self.player.centery)
        for wolf in self.wolves:
            if not wolf.alive:
                continue

            half = wolf.size // 2
            wolf_vec = pygame.Vector2(wolf.x + half, wolf.y + half)
            to_player = player_center - wolf_vec
            dist = to_player.length()

            if wolf.subtype == "stalker":
                self._update_stalker_wolf(wolf, dt, player_center, wolf_vec, to_player, dist)
                continue
            elif wolf.subtype == "hunter":
                self._update_hunter_wolf(wolf, dt, player_center, wolf_vec, to_player, dist)
                continue
            elif wolf.subtype == "alpha":
                self._update_alpha_wolf(wolf, dt, player_center, wolf_vec, to_player, dist)
                continue

            was_alert = wolf.alert
            wolf.alert = dist < 64
            if wolf.alert and not was_alert:
                self.sound.play("growl")
                if dist > 0:
                    snap_dir = to_player.normalize()
                    wolf.facing_x = snap_dir.x
                    wolf.facing_y = snap_dir.y
            if dist < 90:
                if dist > 0:
                    heading = to_player.normalize()
                    wolf.facing_x = heading.x
                    wolf.facing_y = heading.y
                    move = heading * (42 if wolf.alert else 30) * dt
                    wolf.x += move.x
                    wolf.y += move.y

                if self.player.colliderect(wolf.rect) and self.hit_cooldown <= 0:
                    self.health = max(0, self.health - 12)
                    self.sound.play("damage")
                    self.damage_flash = 0.16
                    self.hit_cooldown = 0.5
                    self.trigger_shake(2.0, 0.15)
                    self.emit_particles(self.player.centerx, self.player.centery, 10, PALETTE["health_low"])
                    if self.health <= 0:
                        self.respawn_at_checkpoint()

    def _update_stalker_wolf(self, wolf: Wolf, dt: float, player_center: pygame.Vector2,
                              wolf_vec: pygame.Vector2, to_player: pygame.Vector2, dist: float) -> None:
        beam_hitting = False
        if self.flashlight_on and self.battery > 0:
            flashlight_radius = self.get_flashlight_radius()
            if dist <= flashlight_radius and dist > 0:
                to_wolf_norm = to_player.normalize()
                dot = self.last_dir.dot(to_wolf_norm)
                if dot > 0.707:
                    beam_hitting = True

        if beam_hitting:
            wolf.stun_timer = 0.5
            if dist > 0:
                heading = to_player.normalize()
                wolf.facing_x = heading.x
                wolf.facing_y = heading.y
                perp = pygame.Vector2(-heading.y, heading.x)
                strafe_move = perp * wolf.strafe_dir * 4.2 * dt
                wolf.x += strafe_move.x
                wolf.y += strafe_move.y
                if random.random() < 0.02:
                    wolf.strafe_dir *= -1
        else:
            if wolf.stun_timer > 0:
                wolf.stun_timer -= dt
                return
            if dist > 0:
                heading = to_player.normalize()
                wolf.facing_x = heading.x
                wolf.facing_y = heading.y
                move = heading * 63.0 * dt
                wolf.x += move.x
                wolf.y += move.y

        if self.player.colliderect(wolf.rect) and self.hit_cooldown <= 0:
            self.health = max(0, self.health - 12)
            self.sound.play("damage")
            self.damage_flash = 0.16
            self.hit_cooldown = 0.5
            self.trigger_shake(2.0, 0.15)
            self.emit_particles(self.player.centerx, self.player.centery, 10, PALETTE["health_low"])
            if self.health <= 0:
                self.respawn_at_checkpoint()

    def _update_hunter_wolf(self, wolf: Wolf, dt: float, player_center: pygame.Vector2,
                             wolf_vec: pygame.Vector2, to_player: pygame.Vector2, dist: float) -> None:
        facing = pygame.Vector2(wolf.facing_x, wolf.facing_y)
        if facing.length_squared() == 0:
            facing = pygame.Vector2(1, 0)
        facing = facing.normalize()

        half_angle = math.pi / 3
        cone_range = 64.0

        player_in_cone = False
        if dist <= cone_range and dist > 0:
            to_player_norm = to_player.normalize()
            dot = facing.dot(to_player_norm)
            if dot > math.cos(half_angle):
                player_in_cone = self._has_line_of_sight(wolf_vec, player_center)

        if player_in_cone:
            wolf.alert = True
            wolf.lose_interest_timer = 0.0
            if dist > 0:
                heading = to_player.normalize()
                wolf.facing_x = heading.x
                wolf.facing_y = heading.y
                move = heading * 75.0 * dt
                wolf.x += move.x
                wolf.y += move.y
        else:
            if wolf.alert:
                wolf.lose_interest_timer += dt
                if wolf.lose_interest_timer > 2.0:
                    wolf.alert = False
                    wolf.lose_interest_timer = 0.0
                elif dist > 0:
                    heading = to_player.normalize()
                    wolf.facing_x = heading.x
                    wolf.facing_y = heading.y
                    move = heading * 75.0 * dt
                    wolf.x += move.x
                    wolf.y += move.y
            else:
                patrol_speed = 20.0
                origin = pygame.Vector2(wolf.patrol_origin_x, wolf.patrol_origin_y)
                offset = wolf_vec.x - origin.x
                if abs(offset) > 40:
                    facing.x = -1 if offset > 0 else 1
                    facing.y = 0
                    wolf.facing_x = facing.x
                    wolf.facing_y = 0
                wolf.x += wolf.facing_x * patrol_speed * dt

        if self.player.colliderect(wolf.rect) and self.hit_cooldown <= 0:
            self.health = max(0, self.health - 12)
            self.sound.play("damage")
            self.damage_flash = 0.16
            self.hit_cooldown = 0.5
            self.trigger_shake(2.0, 0.15)
            self.emit_particles(self.player.centerx, self.player.centery, 10, PALETTE["health_low"])
            if self.health <= 0:
                self.respawn_at_checkpoint()

    def _has_line_of_sight(self, from_pos: pygame.Vector2, to_pos: pygame.Vector2) -> bool:
        delta = to_pos - from_pos
        dist = delta.length()
        if dist == 0:
            return True
        steps = int(dist / 8)
        direction = delta.normalize()
        for i in range(1, steps):
            check = from_pos + direction * (i * 8)
            for wall in self.walls:
                if wall.collidepoint(int(check.x), int(check.y)):
                    return False
        return True

    def _update_alpha_wolf(self, wolf: Wolf, dt: float, player_center: pygame.Vector2,
                            wolf_vec: pygame.Vector2, to_player: pygame.Vector2, dist: float) -> None:
        half = wolf.size // 2
        if wolf.charge_timer > 0:
            wolf.charge_timer -= dt

        if dist < 80 and not wolf.alert:
            wolf.alert = True
            self.sound.play("growl")

        if wolf.alert:
            if wolf.lunge_timer > 0:
                wolf.lunge_timer -= dt
                if dist > 0:
                    heading = to_player.normalize()
                    wolf.facing_x = heading.x
                    wolf.facing_y = heading.y
                    move = heading * 120.0 * dt
                    wolf.x += move.x
                    wolf.y += move.y
            else:
                if dist > 0:
                    heading = to_player.normalize()
                    wolf.facing_x = heading.x
                    wolf.facing_y = heading.y
                    move = heading * 28.0 * dt
                    wolf.x += move.x
                    wolf.y += move.y

                if dist < 24 and wolf.charge_timer <= 0:
                    wolf.lunge_timer = 0.3
                    wolf.charge_timer = 1.5

        if self.player.colliderect(wolf.rect) and self.hit_cooldown <= 0:
            damage = 20 if wolf.lunge_timer > 0 else 12
            self.health = max(0, self.health - damage)
            self.sound.play("damage")
            self.damage_flash = 0.16
            self.hit_cooldown = 0.5
            self.trigger_shake(3.0, 0.2)
            self.emit_particles(self.player.centerx, self.player.centery, 10, PALETTE["health_low"])
            if self.health <= 0:
                self.respawn_at_checkpoint()

    def attack(self) -> None:
        if not self.has_knife:
            self.message = "Need a weapon first"
            self.message_timer = 0.8
            return

        if self.attack_cooldown > 0:
            return

        if self.last_dir.length_squared() > 0:
            self.attack_dir = self.last_dir.normalize()
        else:
            self.attack_dir = pygame.Vector2(1, 0)
        self.attack_anim = self.attack_duration

        reach = 20
        attack_rect = self.player.copy()
        attack_rect.width = 16
        attack_rect.height = 16
        attack_rect.center = (
            int(self.player.centerx + self.last_dir.x * reach),
            int(self.player.centery + self.last_dir.y * reach),
        )

        hit_any = False
        for wolf in self.wolves:
            if wolf.alive and attack_rect.colliderect(wolf.rect):
                if wolf.subtype == "alpha":
                    wolf.hp -= 1
                    if wolf.hp <= 0:
                        wolf.alive = False
                        self.l2_boss_defeated = True
                        self.message = "Alpha Wolf defeated!"
                    else:
                        self.message = f"Alpha Wolf hit ({wolf.hp}/{wolf.max_hp})"
                    self.trigger_shake(1.8, 0.12)
                    self.emit_particles(wolf.rect.centerx, wolf.rect.centery, 12, PALETTE["wolf_alert"])
                else:
                    wolf.alive = False
                    self.message = "Wolf neutralized"
                    self.trigger_shake(1.8, 0.12)
                    self.emit_particles(wolf.rect.centerx, wolf.rect.centery, 12, PALETTE["wolf_alert"])
                hit_any = True
                self.message_timer = 0.9

        slash_x = self.player.centerx + self.attack_dir.x * 10
        slash_y = self.player.centery + self.attack_dir.y * 10
        self.emit_particles(slash_x, slash_y, 6, (232, 232, 224))
        self.sound.play("stab" if hit_any else "slash")

        self.attack_cooldown = 0.45 * self.attack_speed_mult

    def use_bandage(self) -> None:
        if self.bandages <= 0:
            self.message = "No bandages"
            self.message_timer = 1.0
            return

        if self.health >= self.max_health:
            self.message = "Health already full"
            self.message_timer = 1.0
            return

        self.bandages -= 1
        self.health = min(self.max_health, self.health + 30)
        self.message = "Bandage used (+30 HP)"
        self.message_timer = 1.0

    def get_inventory_slots(self) -> list[str | None]:
        slots: list[str | None] = [None] * (self.inventory_cols * self.inventory_rows)
        slots[0] = "knife" if self.has_knife else None
        slots[1] = "flashlight" if self.has_flashlight else None
        slots[2] = "bandage" if self.bandages > 0 else None
        slots[3] = "key" if self.has_key else None
        slots[4] = "keycard" if self.has_keycard else None
        return slots

    def inventory_use_selected(self) -> None:
        item = self.get_inventory_slots()[self.inventory_selected]
        if item == "bandage":
            self.use_bandage()
            return
        if item == "flashlight":
            self.toggle_flashlight()
            return
        if item == "knife":
            self.message = "Knife is an equip item (press F)"
            self.message_timer = 1.0
            return
        if item == "key":
            self.message = "Key is used automatically at the door"
            self.message_timer = 1.0
            return
        if item == "keycard":
            self.message = "Keycard is used automatically at locked stairwells"
            self.message_timer = 1.0
            return

        self.message = "Empty slot"
        self.message_timer = 0.8

    def inventory_equip_selected(self) -> None:
        item = self.get_inventory_slots()[self.inventory_selected]
        if item in ("knife", "flashlight"):
            self.equipped_item = item
            self.message = f"Equipped: {item}"
            self.message_timer = 1.0
            return

        if item is None:
            self.message = "Empty slot"
        else:
            self.message = "This item cannot be equipped"
        self.message_timer = 0.9

    def choose_dilemma(self, choice: str) -> None:
        if self.elevator_choice_made:
            self.state = "explore"
            return

        self.dilemma_triggered = True
        self.elevator_choice_made = True
        self.state = "explore"

        if choice == "leg":
            self.player_speed = self.base_player_speed * 0.65
            self.choice_result = "leg"
            self.message = "Leg sacrificed: move speed reduced"
            self.message_timer = 2.2
        else:
            # Attack speed -70% means attack interval is about 3.33x longer.
            self.attack_speed_mult = 10.0 / 3.0
            self.choice_result = "arm"
            self.message = "Arm sacrificed: attack speed -70%"
            self.message_timer = 2.2

        self.set_objective_for_area()

    def draw(self) -> None:
        cam_viewport = self.get_camera_world_rect()
        wide_world = self.world_width > INTERNAL_WIDTH

        # For wide maps (Level 2), draw world-space content onto a
        # world-sized surface so tiles beyond 320px are actually rendered.
        world_surf = None
        if wide_world:
            world_surf = pygame.Surface((self.world_width, self.world_height))
            self._saved_canvas = self.canvas
            self.canvas = world_surf

        self.draw_atmosphere_back()
        self.draw_world()
        self.draw_entities()
        self.draw_particles()
        self.draw_darkness_overlay()
        self.draw_player_sprite()

        # Restore the normal canvas and blit the camera viewport onto it.
        if wide_world:
            self.canvas = self._saved_canvas
            scaled_vp = pygame.transform.scale(
                world_surf.subsurface(cam_viewport),
                (INTERNAL_WIDTH, INTERNAL_HEIGHT),
            )
            self.canvas.blit(scaled_vp, (0, 0))

        self.draw_atmosphere_front()
        self.draw_intro_overlay()

        if self.inventory_anim > 0.01:
            self.draw_inventory_overlay()
        if self.dilemma_anim > 0.01:
            self.draw_dilemma_overlay()

        if self.damage_flash > 0:
            alpha = int(140 * (self.damage_flash / 0.18))
            flash = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            flash.fill((199, 70, 70, alpha))
            self.canvas.blit(flash, (0, 0))

        zoom_gameplay = (
            self.state in {"explore", "pause", "dead", "won"}
            and self.intro_timer <= 0
            and self.inventory_anim <= 0.01
            and self.dilemma_anim <= 0.01
        )

        if zoom_gameplay:
            if wide_world:
                # Extract zoomed viewport directly from the world surface
                view_surface = pygame.Surface((cam_viewport.width, cam_viewport.height))
                view_surface.blit(world_surf, (0, 0), cam_viewport)
                viewport_world = cam_viewport
            else:
                viewport_world = self.get_camera_world_rect()
                view_surface = pygame.Surface((viewport_world.width, viewport_world.height))
                view_surface.blit(self.canvas, (0, 0), viewport_world)
        else:
            viewport_world = pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT)
            view_surface = self.canvas

        self.current_viewport_world = cam_viewport if wide_world else viewport_world
        self.current_render_scale = GAME_VIEW_WIDTH / viewport_world.width
        scaled = pygame.transform.scale(view_surface, (GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT))

        window_w, window_h = self.screen.get_size()
        view_x = (window_w - GAME_VIEW_WIDTH) // 2
        view_y = (window_h - GAME_VIEW_HEIGHT) // 2
        view_rect = pygame.Rect(view_x, view_y, GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT)

        self.screen.fill((8, 11, 16))
        frame_rect = pygame.Rect(view_x - 8, view_y - 8, GAME_VIEW_WIDTH + 16, GAME_VIEW_HEIGHT + 16)
        pygame.draw.rect(self.screen, (22, 28, 38), frame_rect)
        pygame.draw.rect(self.screen, (62, 78, 96), frame_rect, 2)

        if self.shake_strength > 0:
            ox = int(random.uniform(-self.shake_strength, self.shake_strength) * self.current_render_scale)
            oy = int(random.uniform(-self.shake_strength, self.shake_strength) * self.current_render_scale)
            self.screen.blit(scaled, (view_x + ox, view_y + oy))
        else:
            self.screen.blit(scaled, (view_x, view_y))

        if self.area_fade_alpha > 0:
            fade_surf = pygame.Surface((GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT), pygame.SRCALPHA)
            fade_surf.fill((0, 0, 0, int(self.area_fade_alpha)))
            self.screen.blit(fade_surf, (view_x, view_y))

        self.draw_immersive_hud(view_rect)
        self.draw_low_hp_pulse(view_rect)
        self.draw_player_popup_screen(view_rect)

        if self.state == "dead":
            self.draw_death_screen(view_rect)
        elif self.state == "won":
            self.draw_victory_screen(view_rect)

        if self.state == "pause":
            self.draw_pause_menu(view_rect)

        pygame.display.flip()

    def get_camera_target_center(self) -> pygame.Vector2:
        look_ahead = self.last_dir if self.last_dir.length_squared() > 0 else pygame.Vector2(0, 0)
        return pygame.Vector2(
            self.player.centerx + look_ahead.x * 12,
            self.player.centery + look_ahead.y * 8,
        )

    def clamp_camera_center(self, center: pygame.Vector2) -> pygame.Vector2:
        view_w = min(CAMERA_VIEW_WIDTH, self.world_width)
        view_h = min(CAMERA_VIEW_HEIGHT, self.world_height)
        half_w = view_w * 0.5
        half_h = view_h * 0.5

        if self.world_width <= view_w:
            clamped_x = self.world_width * 0.5
        else:
            clamped_x = max(half_w, min(self.world_width - half_w, center.x))

        if self.world_height <= view_h:
            clamped_y = self.world_height * 0.5
        else:
            clamped_y = max(half_h, min(self.world_height - half_h, center.y))

        return pygame.Vector2(clamped_x, clamped_y)

    def reset_camera(self, immediate: bool = False) -> None:
        target = self.clamp_camera_center(self.get_camera_target_center())
        if immediate:
            self.camera_center.update(target)
        else:
            self.camera_center += (target - self.camera_center) * 0.6
            self.camera_center.update(self.clamp_camera_center(self.camera_center))

    def update_camera(self, dt: float) -> None:
        target = self.clamp_camera_center(self.get_camera_target_center())
        desired = pygame.Vector2(self.camera_center)
        deadzone_x = 18.0
        deadzone_y = 10.0

        if target.x < self.camera_center.x - deadzone_x:
            desired.x = target.x + deadzone_x
        elif target.x > self.camera_center.x + deadzone_x:
            desired.x = target.x - deadzone_x

        if target.y < self.camera_center.y - deadzone_y:
            desired.y = target.y + deadzone_y
        elif target.y > self.camera_center.y + deadzone_y:
            desired.y = target.y - deadzone_y

        follow = min(1.0, dt * 7.0)
        self.camera_center += (desired - self.camera_center) * follow
        self.camera_center.update(self.clamp_camera_center(self.camera_center))

    def get_camera_world_rect(self) -> pygame.Rect:
        view_w = min(CAMERA_VIEW_WIDTH, self.world_width)
        view_h = min(CAMERA_VIEW_HEIGHT, self.world_height)
        x = int(round(self.camera_center.x - view_w * 0.5))
        y = int(round(self.camera_center.y - view_h * 0.5))
        x = max(0, min(self.world_width - view_w, x))
        y = max(0, min(self.world_height - view_h, y))
        return pygame.Rect(x, y, view_w, view_h)

    def world_to_screen(self, world_x: float, world_y: float, view_rect: pygame.Rect) -> tuple[int, int]:
        scale = self.current_render_scale
        sx = int(view_rect.x + (world_x - self.current_viewport_world.x) * scale)
        sy = int(view_rect.y + (world_y - self.current_viewport_world.y) * scale)
        return sx, sy

    def draw_intro_overlay(self) -> None:
        if self.intro_timer <= 0 or self.state != "explore":
            return

        fade_t = 1.0
        if self.intro_timer < self.intro_fade_duration:
            fade_t = max(0.0, min(1.0, self.intro_timer / self.intro_fade_duration))
        panel_alpha = int(218 * fade_t)
        text_alpha = int(255 * fade_t)

        panel_w = 300
        panel_h = 132
        x = (INTERNAL_WIDTH - panel_w) // 2
        y = (INTERNAL_HEIGHT - panel_h) // 2 + 4

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 16, 25, panel_alpha))
        self.canvas.blit(panel, (x, y))
        pygame.draw.rect(self.canvas, (104, 126, 150), pygame.Rect(x, y, panel_w, panel_h), 1)

        title = self.fit_text(self.intro_title, self.big_font, panel_w - 18)
        title_w, _ = self.big_font.size(title)
        self.blit_pixel_text_on(self.canvas, title, x + (panel_w - title_w) // 2, y + 10, self.big_font, (236, 243, 250))

        line_y = y + 36
        for line in self.intro_lines:
            draw_line = self.fit_text(line, self.font, panel_w - 16)
            line_w, _ = self.font.size(draw_line)
            self.blit_pixel_text_on(self.canvas, draw_line, x + (panel_w - line_w) // 2, line_y, self.font, (218, 230, 240))
            line_y += self.font.get_height() + 1

        hint = self.fit_text(self.intro_hint, self.small_font, panel_w - 16)
        hint_w, _ = self.small_font.size(hint)
        self.blit_pixel_text_on(self.canvas, hint, x + (panel_w - hint_w) // 2, y + panel_h - 14, self.small_font, (190, 208, 226))

        if text_alpha < 255:
            fade_surface = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, 255 - text_alpha))
            self.canvas.blit(fade_surface, (x, y), special_flags=pygame.BLEND_RGBA_SUB)


    def draw_immersive_hud(self, view_rect: pygame.Rect) -> None:
        if self.state in ("won", "dead"):
            return

        # --- BOTTOM-LEFT: Health + Battery + Bandages ---
        panel_w, panel_h = 170, 40
        panel_x = view_rect.x + 8
        panel_y = view_rect.bottom - panel_h - 8
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((10, 14, 22, 210))
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, (42, 58, 82), pygame.Rect(panel_x, panel_y, panel_w, panel_h), 1)

        health_ratio = self.health / self.max_health
        fill_color = PALETTE["health"]
        if health_ratio < 0.3:
            fill_color = PALETTE["health_low"]
        elif health_ratio < 0.6:
            fill_color = PALETTE["health_mid"]

        # Health label + bar
        self.blit_pixel_text_on(self.screen, "HP", panel_x + 6, panel_y + 4, self.ui_small_font, fill_color)
        bar_x = panel_x + 26
        bar_w = 100
        bar_h = 6
        bar_y = panel_y + 5
        pygame.draw.rect(self.screen, (11, 14, 19), pygame.Rect(bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, fill_color, pygame.Rect(bar_x, bar_y, int(bar_w * health_ratio), bar_h))

        # Battery bar below
        bat_color = PALETTE["battery"]
        bat_y = bar_y + bar_h + 3
        self.blit_pixel_text_on(self.screen, "BAT", panel_x + 6, bat_y, self.ui_small_font, bat_color)
        bat_bar_x = bar_x + 8
        bat_bar_w = bar_w - 8
        bat_ratio = self.battery / 100.0
        pygame.draw.rect(self.screen, (11, 14, 19), pygame.Rect(bat_bar_x, bat_y, bat_bar_w, 4))
        pygame.draw.rect(self.screen, bat_color, pygame.Rect(bat_bar_x, bat_y, int(bat_bar_w * bat_ratio), 4))

        # Bandages
        self.blit_pixel_text_on(self.screen, f"BAND x{self.bandages}", panel_x + 6, bat_y + 8, self.ui_small_font, PALETTE["bandage"])

        # --- BOTTOM-CENTER: Quick Slots ---
        slot_size = 36
        slot_gap = 4
        quick_items = ["knife", "flashlight", "bandage"]
        total_w = len(quick_items) * slot_size + (len(quick_items) - 1) * slot_gap
        slots_x = view_rect.centerx - total_w // 2
        slots_y = view_rect.bottom - slot_size - 8

        for idx, item_name in enumerate(quick_items):
            sx = slots_x + idx * (slot_size + slot_gap)
            has_item = (item_name == "knife" and self.has_knife) or \
                       (item_name == "flashlight" and self.has_flashlight) or \
                       (item_name == "bandage" and self.bandages > 0)
            is_active = self.equipped_item == item_name

            if has_item:
                border = (90, 170, 200) if is_active else (58, 74, 94)
                fill_alpha = 210
            else:
                border = (26, 34, 46)
                fill_alpha = 80

            slot_surf = pygame.Surface((slot_size, slot_size), pygame.SRCALPHA)
            slot_surf.fill((10, 14, 22, fill_alpha))
            self.screen.blit(slot_surf, (sx, slots_y))
            pygame.draw.rect(self.screen, border, pygame.Rect(sx, slots_y, slot_size, slot_size), 1)

            if is_active and has_item:
                glow_surf = pygame.Surface((slot_size + 4, slot_size + 4), pygame.SRCALPHA)
                glow_surf.fill((92, 159, 179, 30))
                self.screen.blit(glow_surf, (sx - 2, slots_y - 2))

            if has_item and item_name in self.sprite_cache and self.sprite_cache[item_name] is not None:
                icon = pygame.transform.scale(self.sprite_cache[item_name], (18, 18))
                self.screen.blit(icon, (sx + (slot_size - 18) // 2, slots_y + 4))

            num_text = str(idx + 1)
            self.blit_pixel_text_on(self.screen, num_text, sx + slot_size - 10, slots_y + 2, self.ui_small_font, (130, 148, 168) if has_item else (50, 60, 74))

        # --- TOP-RIGHT: Zone + Objective ---
        zone_code, zone_name, _ = self.get_area_meta()
        info_w = 186
        info_h = 28
        info_x = view_rect.right - info_w - 8
        info_y = view_rect.y + 8
        info_surf = pygame.Surface((info_w, info_h), pygame.SRCALPHA)
        info_surf.fill((10, 14, 22, 160))
        self.screen.blit(info_surf, (info_x, info_y))
        pygame.draw.rect(self.screen, (26, 42, 58), pygame.Rect(info_x, info_y, info_w, info_h), 1)
        zone_text = self.fit_text(f"{zone_code}  {zone_name}", self.ui_small_font, info_w - 12)
        objective_text = self.fit_text(self.objective, self.ui_small_font, info_w - 12)
        self.blit_pixel_text_on(self.screen, zone_text, info_x + 6, info_y + 2, self.ui_small_font, (58, 90, 122))
        self.blit_pixel_text_on(self.screen, objective_text, info_x + 6, info_y + 14, self.ui_small_font, (90, 122, 154))

        # --- TOP-LEFT: Contextual Hint ---
        if self.active_hint and self.active_hint_fade > 0.01:
            hint_alpha = int(210 * self.active_hint_fade)
            hint_w = self.ui_small_font.size(self.active_hint)[0] + 16
            hint_h = 18
            hint_x = view_rect.x + 8
            hint_y = view_rect.y + 8
            hint_surf = pygame.Surface((hint_w, hint_h), pygame.SRCALPHA)
            hint_surf.fill((10, 14, 22, hint_alpha))
            self.screen.blit(hint_surf, (hint_x, hint_y))
            pygame.draw.rect(self.screen, (42, 74, 58), pygame.Rect(hint_x, hint_y, hint_w, hint_h), 1)
            self.blit_pixel_text_on(self.screen, self.active_hint, hint_x + 8, hint_y + 3, self.ui_small_font, (74, 138, 90))

    def draw_low_hp_pulse(self, view_rect: pygame.Rect) -> None:
        if self.low_hp_pulse_phase <= 0:
            return
        pulse = 0.5 + 0.5 * math.sin(self.low_hp_pulse_phase)
        alpha = int(pulse * 60)
        pulse_surf = pygame.Surface((view_rect.width, view_rect.height), pygame.SRCALPHA)
        for i in range(3):
            border_w = 20 + i * 15
            border_alpha = max(0, alpha - i * 15)
            pygame.draw.rect(pulse_surf, (199, 70, 70, border_alpha), pygame.Rect(0, 0, view_rect.width, border_w))
            pygame.draw.rect(pulse_surf, (199, 70, 70, border_alpha), pygame.Rect(0, view_rect.height - border_w, view_rect.width, border_w))
            pygame.draw.rect(pulse_surf, (199, 70, 70, border_alpha), pygame.Rect(0, 0, border_w, view_rect.height))
            pygame.draw.rect(pulse_surf, (199, 70, 70, border_alpha), pygame.Rect(view_rect.width - border_w, 0, border_w, view_rect.height))
        self.screen.blit(pulse_surf, (view_rect.x, view_rect.y))

    def draw_player_popup_screen(self, view_rect: pygame.Rect) -> None:
        if self.message_timer <= 0 or not self.message:
            return
        if self.state in ("won", "dead"):
            return

        max_width = min(280, view_rect.width - 16)
        line_width = max_width - 12
        lines = self.wrap_text(self.message, self.ui_font, line_width)
        max_lines = 3
        if len(lines) > max_lines:
            clipped = lines[: max_lines - 1]
            clipped.append(self.fit_text(" ".join(lines[max_lines - 1 :]), self.ui_font, line_width))
            lines = clipped

        line_h = self.ui_font.get_height()
        bubble_w = max(self.ui_font.size(line)[0] for line in lines) + 12
        bubble_h = line_h * len(lines) + 7

        player_screen_x, player_screen_y = self.world_to_screen(self.player.centerx, self.player.y, view_rect)
        rise = int((1.0 - self.banner_anim) * 10)

        bubble_x = player_screen_x - bubble_w // 2
        bubble_x = max(view_rect.x + 4, min(bubble_x, view_rect.right - bubble_w - 4))
        bubble_y = player_screen_y - bubble_h - 24 - rise
        bubble_y = max(view_rect.y + 4, bubble_y)

        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_w, bubble_h)
        self.screen.fill((8, 12, 18), bubble_rect)
        pygame.draw.rect(self.screen, (86, 104, 126), bubble_rect, 1)

        tip_x = max(bubble_rect.x + 6, min(player_screen_x, bubble_rect.right - 6))
        tip = [(tip_x - 4, bubble_rect.bottom), (tip_x + 4, bubble_rect.bottom), (tip_x, bubble_rect.bottom + 5)]
        pygame.draw.polygon(self.screen, (8, 12, 18), tip)
        pygame.draw.polygon(self.screen, (86, 104, 126), tip, 1)

        text_y = bubble_rect.y + 3
        for line in lines:
            self.blit_text_shadow_on(self.screen, line, bubble_rect.x + 6, text_y, line_width)
            text_y += line_h

    def collect_world_labels(self) -> list[tuple[str, int, int]]:
        labels: list[tuple[str, int, int]] = []
        if not self.show_labels:
            return labels

        player_center = pygame.Vector2(self.player.centerx, self.player.centery)

        for door in self.current_doors:
            dx, dy = door["tile"]
            center = pygame.Vector2(dx * TILE_SIZE + TILE_SIZE // 2, dy * TILE_SIZE + TILE_SIZE // 2)
            if player_center.distance_to(center) < 96:
                door_id = str(door.get("id", "D-??"))
                target_area = str(door.get("to", ""))
                target_code, _, target_short = self.get_area_meta(target_area)
                state = "LOCKED" if self.is_door_locked(door) else "OPEN"
                labels.append((f"{door_id} -> {target_code} {target_short} {state}", int(center.x), int(center.y - 16)))

        if self.current_area == "maintenance" and self.breaker_tile != (0, 0):
            center = pygame.Vector2(self.breaker_tile[0] * TILE_SIZE + TILE_SIZE // 2, self.breaker_tile[1] * TILE_SIZE + TILE_SIZE // 2)
            if player_center.distance_to(center) < 72:
                text = "Main Breaker ON" if self.area2_cleared else "Main Breaker"
                labels.append((text, int(center.x), int(center.y - 16)))

        if self.current_area == "area3" and self.elevator_terminal_tile != (0, 0):
            center = pygame.Vector2(
                self.elevator_terminal_tile[0] * TILE_SIZE + TILE_SIZE // 2,
                self.elevator_terminal_tile[1] * TILE_SIZE + TILE_SIZE // 2,
            )
            if player_center.distance_to(center) < 72:
                labels.append(("Elevator Terminal", int(center.x), int(center.y - 16)))

        if self.current_area == "final" and self.final_exit_tile != (0, 0):
            center = pygame.Vector2(self.final_exit_tile[0] * TILE_SIZE + TILE_SIZE // 2, self.final_exit_tile[1] * TILE_SIZE + TILE_SIZE // 2)
            if player_center.distance_to(center) < 82:
                labels.append(("Level Exit", int(center.x), int(center.y - 16)))

        furniture_labels = {
            "desk": "Desk",
            "cabinet": "Cabinet",
            "bed": "Bed",
            "stool": "Stool",
            "freezer": "Freezer",
        }
        for (tx, ty), kind in self.furniture.items():
            center = pygame.Vector2(tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2)
            if player_center.distance_to(center) < 64:
                labels.append((furniture_labels.get(kind, kind.title()), int(center.x), int(center.y - 16)))

        pickup_labels = {
            "key": "Key",
            "battery": "Battery",
            "bandage": "Bandage",
            "flashlight": "Flashlight",
            "knife": "Knife",
        }
        if self.can_reveal_pickups():
            for pickup in self.pickups:
                if not self.is_pickup_in_flashlight_range(pickup):
                    continue
                center = pygame.Vector2(pickup.rect.centerx, pickup.rect.centery)
                if player_center.distance_to(center) < 60:
                    labels.append((pickup_labels.get(pickup.name, pickup.name.title()), int(center.x), int(center.y - 14)))

        for wolf in self.wolves:
            if not wolf.alive:
                continue
            center = pygame.Vector2(wolf.rect.centerx, wolf.rect.centery)
            if player_center.distance_to(center) < 90:
                text = "Wolf (Alert)" if wolf.alert else "Wolf"
                labels.append((text, int(center.x), int(center.y - 16)))

        return labels

    def draw_world_labels_screen(self, view_rect: pygame.Rect) -> None:
        for text, cx, cy in self.collect_world_labels():
            sx, sy = self.world_to_screen(cx, cy, view_rect)
            self.draw_label_on_screen(text, sx, sy)

    def draw_label_on_screen(self, text: str, center_x: int, y: int) -> None:
        w = self.ui_small_font.size(text)[0] + 12
        h = self.ui_small_font.get_height() + 7
        x = center_x - w // 2
        bg = pygame.Rect(x, y, w, h)
        self.screen.fill((8, 12, 18), bg)
        pygame.draw.rect(self.screen, (78, 96, 120), bg, 1)
        self.blit_pixel_text_on(self.screen, text, x + 6, y + 3, self.ui_small_font)

    def draw_screen_panel(self, rect: pygame.Rect, fill: tuple[int, int, int], border: tuple[int, int, int]) -> None:
        self.screen.fill(fill, rect)
        pygame.draw.rect(self.screen, border, rect, 1)
        inner = rect.inflate(-2, -2)
        pygame.draw.rect(self.screen, (30, 40, 53), inner, 1)

    def blit_text_shadow_on(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        max_width: int | None = None,
    ) -> None:
        draw_text = self.fit_text(text, self.ui_font, max_width) if max_width is not None else text
        self.blit_pixel_text_on(surface, draw_text, x, y, self.ui_font)

    def blit_text_centered_shadow_on(self, surface: pygame.Surface, text: str, rect: pygame.Rect) -> None:
        draw_text = self.fit_text(text, self.ui_font, rect.width)
        if not draw_text:
            return
        text_w, text_h = self.ui_font.size(draw_text)
        x = rect.x + (rect.width - text_w) // 2
        y = rect.y + (rect.height - text_h) // 2
        self.blit_text_shadow_on(surface, draw_text, x, y)

    def blit_multiline_left_shadow_on(self, surface: pygame.Surface, text: str, rect: pygame.Rect) -> None:
        line_height = self.ui_font.get_height()
        lines = self.wrap_text(text, self.ui_font, rect.width)
        max_lines = max(1, rect.height // line_height)

        if len(lines) > max_lines:
            head = lines[: max_lines - 1]
            tail_joined = " ".join(lines[max_lines - 1 :])
            head.append(self.fit_text(tail_joined, self.ui_font, rect.width))
            lines = head

        y = rect.y
        for line in lines:
            self.blit_text_shadow_on(surface, line, rect.x, y, rect.width)
            y += line_height

    def get_map_cell(self, tile_x: int, tile_y: int) -> str:
        if tile_y < 0 or tile_y >= len(self.current_map):
            return "#"
        row = self.current_map[tile_y]
        if tile_x < 0 or tile_x >= len(row):
            return "#"
        return row[tile_x]

    def draw_floor_tile(
        self,
        tile_x: int,
        tile_y: int,
        tile_rect: pygame.Rect,
        theme: dict[str, tuple[int, int, int]],
        is_dark: bool,
    ) -> None:
        base = theme["floor_dark"] if is_dark else theme["floor"]
        alt = mix_color(base, theme["floor_alt"], 0.65 if not is_dark else 0.3)
        self.canvas.fill(base, tile_rect)

        if (tile_x * 3 + tile_y * 5) % 4 in (0, 3):
            self.canvas.fill(alt, pygame.Rect(tile_rect.x + 1, tile_rect.y + 1, 6, 6))
        if (tile_x + tile_y) % 2 == 0:
            self.canvas.fill(shift_color(base, 8), pygame.Rect(tile_rect.x + 9, tile_rect.y + 3, 4, 4))

        for nx, ny, seam_rect in (
            (tile_x, tile_y - 1, pygame.Rect(tile_rect.x, tile_rect.y, tile_rect.width, 2)),
            (tile_x - 1, tile_y, pygame.Rect(tile_rect.x, tile_rect.y, 2, tile_rect.height)),
        ):
            if self.get_map_cell(nx, ny) == "#":
                self.canvas.fill(theme["floor_dark"], seam_rect)

        if self.current_area == "maintenance" and (tile_x + tile_y) % 5 == 0:
            stripe = pygame.Rect(tile_rect.x + 3, tile_rect.y + 6, 10, 2)
            self.canvas.fill(theme["accent"], stripe)
            self.canvas.fill((24, 24, 24), pygame.Rect(stripe.x + 1, stripe.y, 2, 2))
            self.canvas.fill((24, 24, 24), pygame.Rect(stripe.x + 5, stripe.y, 2, 2))
        elif self.current_area == "medbay" and tile_y % 2 == 0:
            self.canvas.fill(shift_color(base, 12), pygame.Rect(tile_rect.x + 7, tile_rect.y, 1, tile_rect.height))
        elif self.current_area == "final" and (tile_x + tile_y) % 6 == 0:
            self.canvas.fill(theme["danger"], pygame.Rect(tile_rect.x + 2, tile_rect.y + 11, 9, 1))

    def draw_wall_tile(
        self,
        tile_x: int,
        tile_y: int,
        tile_rect: pygame.Rect,
        theme: dict[str, tuple[int, int, int]],
    ) -> None:
        self.canvas.fill(theme["wall"], tile_rect)
        self.canvas.fill(theme["wall_hi"], pygame.Rect(tile_rect.x, tile_rect.y, tile_rect.width, 2))
        self.canvas.fill(theme["wall_lo"], pygame.Rect(tile_rect.x, tile_rect.bottom - 3, tile_rect.width, 3))
        self.canvas.fill(shift_color(theme["wall_lo"], -6), pygame.Rect(tile_rect.x, tile_rect.y + 3, 2, tile_rect.height - 5))
        if tile_x % 2 == 0:
            self.canvas.fill(shift_color(theme["wall"], -10), pygame.Rect(tile_rect.x + 6, tile_rect.y + 2, 1, tile_rect.height - 5))
        if (tile_x + tile_y) % 3 == 0:
            self.canvas.fill(shift_color(theme["wall_hi"], 8), pygame.Rect(tile_rect.x + 10, tile_rect.y + 4, 3, 2))
        if self.get_map_cell(tile_x, tile_y + 1) != "#":
            self.canvas.fill((12, 16, 22), pygame.Rect(tile_rect.x, tile_rect.bottom - 2, tile_rect.width, 2))

    def draw_door_tile(
        self,
        tile_rect: pygame.Rect,
        locked: bool,
        theme: dict[str, tuple[int, int, int]],
    ) -> None:
        pulse = int((math.sin(self.time_alive * 3.1) + 1.0) * 0.5 * 24)
        slab_fill = mix_color(theme["accent"], (220, 220, 220), 0.18 if locked else 0.32)
        slab_border = theme["danger"] if locked else theme["safe"]

        # Glow behind the door so it stands out from adjacent walls.
        glow_pad = 10
        glow = pygame.Surface((tile_rect.width + glow_pad * 2, tile_rect.height + glow_pad * 2), pygame.SRCALPHA)
        glow_col = theme["danger"] if locked else theme["safe"]
        glow.fill((glow_col[0], glow_col[1], glow_col[2], 52))
        self.canvas.blit(glow, (tile_rect.x - glow_pad, tile_rect.y - glow_pad))

        frame_color = mix_color(theme["accent"], theme["wall"], 0.35)
        jamb_color = shift_color(frame_color, 12)
        self.canvas.fill(frame_color, tile_rect)
        self.canvas.fill(jamb_color, pygame.Rect(tile_rect.x, tile_rect.y, 2, tile_rect.height))
        self.canvas.fill(jamb_color, pygame.Rect(tile_rect.right - 2, tile_rect.y, 2, tile_rect.height))
        self.canvas.fill(shift_color(frame_color, -8), pygame.Rect(tile_rect.x + 2, tile_rect.y + 1, tile_rect.width - 4, 2))

        door_rect = pygame.Rect(tile_rect.x + 3, tile_rect.y + 1, 10, tile_rect.height - 2)
        self.canvas.fill(slab_fill, door_rect)
        pygame.draw.rect(self.canvas, slab_border, door_rect, 2)
        self.canvas.fill(shift_color(slab_fill, 18), pygame.Rect(door_rect.x + 1, door_rect.y + 1, door_rect.width - 2, 2))
        self.canvas.fill(shift_color(slab_fill, -18), pygame.Rect(door_rect.x + 1, door_rect.bottom - 3, door_rect.width - 2, 2))
        self.canvas.fill((18, 24, 32), pygame.Rect(door_rect.centerx - 1, door_rect.y + 2, 2, door_rect.height - 4))

        if locked:
            for offset in range(-2, 10, 3):
                pygame.draw.line(
                    self.canvas,
                    shift_color(theme["danger"], 28),
                    (door_rect.x + offset, door_rect.bottom - 1),
                    (door_rect.x + offset + 5, door_rect.y + 1),
                )
        else:
            self.canvas.fill(shift_color(theme["safe"], 28), pygame.Rect(door_rect.x + 1, door_rect.y + 6, door_rect.width - 2, 1))
        light = theme["danger"] if locked else theme["safe"]
        self.canvas.fill(shift_color(light, pulse // 2), pygame.Rect(door_rect.right - 2, door_rect.y + 3, 1, 4))

    def draw_laser_beam(self, laser: LaserBeam, theme: dict[str, tuple[int, int, int]], active: bool) -> None:
        emitter = mix_color(theme["wall"], theme["accent"], 0.42)
        horizontal = laser.rect.width > laser.rect.height
        if horizontal:
            left_post = pygame.Rect(laser.rect.x - 2, laser.rect.y - 2, 3, laser.rect.height + 4)
            right_post = pygame.Rect(laser.rect.right - 1, laser.rect.y - 2, 3, laser.rect.height + 4)
            self.canvas.fill(emitter, left_post)
            self.canvas.fill(emitter, right_post)
        else:
            top_post = pygame.Rect(laser.rect.x - 2, laser.rect.y - 2, laser.rect.width + 4, 3)
            bottom_post = pygame.Rect(laser.rect.x - 2, laser.rect.bottom - 1, laser.rect.width + 4, 3)
            self.canvas.fill(emitter, top_post)
            self.canvas.fill(emitter, bottom_post)

        if active:
            glow = pygame.Surface((laser.rect.width + 6, laser.rect.height + 6), pygame.SRCALPHA)
            glow.fill((theme["danger"][0], theme["danger"][1], theme["danger"][2], 56))
            self.canvas.blit(glow, (laser.rect.x - 3, laser.rect.y - 3))
            self.canvas.fill(theme["danger"], laser.rect)
            if horizontal:
                self.canvas.fill((255, 212, 212), pygame.Rect(laser.rect.x, laser.rect.y, laser.rect.width, 1))
            else:
                self.canvas.fill((255, 212, 212), pygame.Rect(laser.rect.x, laser.rect.y, 1, laser.rect.height))
        else:
            dim = mix_color(theme["danger"], theme["wall_lo"], 0.65)
            self.canvas.fill(dim, laser.rect)

    def draw_terminal_tile(
        self,
        tile: tuple[int, int],
        active: bool,
        theme: dict[str, tuple[int, int, int]],
        glow_color: tuple[int, int, int],
    ) -> None:
        rect = pygame.Rect(tile[0] * TILE_SIZE, tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pulse = int((math.sin(self.time_alive * 2.2 + tile[0]) + 1.0) * 0.5 * 28)
        screen_color = shift_color(glow_color, pulse // 3) if active else mix_color(glow_color, theme["wall_lo"], 0.6)
        self.canvas.fill((20, 24, 30), pygame.Rect(rect.x + 2, rect.y + 11, 12, 3))
        self.canvas.fill(mix_color(theme["wall"], theme["accent"], 0.28), pygame.Rect(rect.x + 4, rect.y + 7, 8, 5))
        self.canvas.fill((12, 16, 20), pygame.Rect(rect.x + 3, rect.y + 2, 10, 6))
        self.canvas.fill(screen_color, pygame.Rect(rect.x + 4, rect.y + 3, 8, 4))
        self.canvas.fill(shift_color(screen_color, 22), pygame.Rect(rect.x + 4, rect.y + 3, 8, 1))
        floor_glow = pygame.Surface((16, 10), pygame.SRCALPHA)
        floor_glow.fill((screen_color[0], screen_color[1], screen_color[2], 46 if active else 20))
        self.canvas.blit(floor_glow, (rect.x, rect.y + 9))

    def draw_furniture_tile(
        self,
        tile_x: int,
        tile_y: int,
        kind: str,
        theme: dict[str, tuple[int, int, int]],
    ) -> None:
        rect = pygame.Rect(tile_x * TILE_SIZE, tile_y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        shadow_y = rect.y + 12
        if kind == "desk":
            top = pygame.Rect(rect.x - 1, rect.y + 6, 18, 4)
            self.canvas.fill((12, 16, 20), pygame.Rect(rect.x + 1, shadow_y, 14, 2))
            self.canvas.fill((96, 74, 62), top)
            self.canvas.fill((42, 50, 60), pygame.Rect(rect.x + 4, rect.y + 1, 9, 6))
            self.canvas.fill(theme["accent"], pygame.Rect(rect.x + 11, rect.y + 3, 1, 1))
            self.canvas.fill((80, 58, 48), pygame.Rect(rect.x + 1, rect.y + 10, 2, 4))
            self.canvas.fill((80, 58, 48), pygame.Rect(rect.x + 13, rect.y + 10, 2, 4))
            self.canvas.fill((148, 120, 86), pygame.Rect(top.x + 2, top.y + 1, 12, 1))
        elif kind == "cabinet":
            cab = pygame.Rect(rect.x + 2, rect.y, 12, 15)
            self.canvas.fill((12, 16, 20), pygame.Rect(rect.x + 3, shadow_y, 10, 2))
            self.canvas.fill((86, 84, 92), cab)
            self.canvas.fill((124, 122, 130), pygame.Rect(cab.x + 1, cab.y + 1, cab.width - 2, 2))
            self.canvas.fill((54, 52, 58), pygame.Rect(cab.centerx - 1, cab.y + 3, 1, cab.height - 5))
            self.canvas.fill((190, 178, 136), pygame.Rect(cab.right - 3, cab.y + 6, 1, 2))
            self.canvas.fill((190, 178, 136), pygame.Rect(cab.x + 2, cab.y + 6, 1, 2))
        elif kind == "bed":
            bed = pygame.Rect(rect.x - 3, rect.y + 2, 22, 11)
            self.canvas.fill((12, 16, 20), pygame.Rect(bed.x + 2, bed.bottom - 1, bed.width - 4, 2))
            self.canvas.fill((82, 58, 56), bed)
            self.canvas.fill((64, 42, 40), pygame.Rect(bed.x, bed.y + 1, 2, bed.height - 2))
            self.canvas.fill((206, 206, 194), pygame.Rect(bed.x + 2, bed.y + 1, bed.width - 4, 8))
            self.canvas.fill((228, 228, 218), pygame.Rect(bed.x + 2, bed.y + 1, 6, 4))
            self.canvas.fill((186, 180, 172), pygame.Rect(bed.x + 9, bed.y + 2, 8, 5))
            self.canvas.fill((170, 132, 126), pygame.Rect(bed.x + 5, bed.y + 8, 10, 2))
            self.canvas.fill(theme["danger"], pygame.Rect(bed.x + 15, bed.y + 8, 3, 1))
        elif kind == "freezer":
            freezer_key = (self.current_area, tile_x, tile_y)
            charges = self.freezer_charges.get(freezer_key, 0)
            light_col = theme["safe"] if charges > 0 else (118, 126, 136)
            body = pygame.Rect(rect.x + 1, rect.y, 14, 15)
            self.canvas.fill((12, 16, 20), pygame.Rect(rect.x + 2, shadow_y, 12, 2))
            self.canvas.fill((76, 92, 108), body)
            pygame.draw.rect(self.canvas, (150, 178, 198), body, 1)
            self.canvas.fill((220, 232, 240), pygame.Rect(body.x + 1, body.y + 1, body.width - 2, 1))
            self.canvas.fill(light_col, pygame.Rect(body.x + 5, body.y + 5, 4, 3))
            self.canvas.fill((196, 210, 226), pygame.Rect(body.x + 2, body.y + 3, 3, 1))
        else:
            seat = pygame.Rect(rect.x + 3, rect.y + 6, 10, 4)
            self.canvas.fill((12, 16, 20), pygame.Rect(rect.x + 4, shadow_y, 8, 2))
            self.canvas.fill((108, 84, 66), seat)
            self.canvas.fill((132, 104, 82), pygame.Rect(seat.x + 1, seat.y + 1, seat.width - 2, 1))
            self.canvas.fill((84, 62, 46), pygame.Rect(rect.x + 5, rect.y + 10, 1, 4))
            self.canvas.fill((84, 62, 46), pygame.Rect(rect.x + 10, rect.y + 10, 1, 4))

    def draw_pickup_entity(self, pickup: ItemPickup) -> None:
        base_rect = pickup.rect
        shadow_rect = pygame.Rect(base_rect.x, base_rect.y + 5, base_rect.width, 3)
        self.canvas.fill((10, 12, 18), shadow_rect)
        bob = int(math.sin(self.time_alive * 4.3 + base_rect.x * 0.11 + base_rect.y * 0.07) * 1.5)
        draw_rect = base_rect.move(0, bob)
        color_name = {
            "key": "key",
            "battery": "battery",
            "bandage": "bandage",
            "flashlight": "flashlight",
            "knife": "door",
            "keycard": "key",
        }.get(pickup.name, "bandage")
        self.draw_pickup_icon(draw_rect, pickup.name, PALETTE[color_name], self.sprite_cache.get(pickup.name))
        glint_phase = (self.time_alive * 2.1 + base_rect.x * 0.03 + base_rect.y * 0.05) % 2.2
        if glint_phase < 0.18:
            glint = draw_rect.inflate(4, 4)
            pygame.draw.line(self.canvas, (255, 250, 224), (glint.centerx - 2, glint.centery), (glint.centerx + 2, glint.centery))
            pygame.draw.line(self.canvas, (255, 250, 224), (glint.centerx, glint.centery - 2), (glint.centerx, glint.centery + 2))
        if pickup.name == "key":
            glow = pygame.Surface((draw_rect.width + 8, draw_rect.height + 8), pygame.SRCALPHA)
            glow.fill((226, 190, 69, 48))
            self.canvas.blit(glow, (draw_rect.x - 4, draw_rect.y - 4))

    def get_direction_key(self, vec: pygame.Vector2) -> str:
        if vec.length_squared() <= 0:
            return "right"
        if abs(vec.x) > abs(vec.y):
            return "right" if vec.x >= 0 else "left"
        return "down" if vec.y >= 0 else "up"

    def draw_centered_sprite(self, rect: pygame.Rect, sprite: pygame.Surface, y_offset: int = 0) -> None:
        draw_x = rect.centerx - sprite.get_width() // 2
        draw_y = rect.bottom - sprite.get_height() + y_offset
        self.canvas.blit(sprite, (draw_x, draw_y))

    def draw_world(self) -> None:
        theme = self.get_area_theme()
        for y, row in enumerate(self.current_map):
            for x, cell in enumerate(row):
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if cell == "#":
                    self.draw_wall_tile(x, y, tile_rect, theme)
                else:
                    self.draw_floor_tile(x, y, tile_rect, theme, (x, y) in self.dark_tiles)

        for door in self.current_doors:
            dx, dy = door["tile"]
            door_rect = pygame.Rect(dx * TILE_SIZE, dy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            self.draw_door_tile(door_rect, self.is_door_locked(door), theme)

        if self.current_area == "final" and self.final_exit_tile != (0, 0):
            final_rect = pygame.Rect(self.final_exit_tile[0] * TILE_SIZE, self.final_exit_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pulse = int((math.sin(self.time_alive * 2.1) + 1.0) * 0.5 * 36)
            exit_fill = mix_color(theme["wall"], PALETTE["exit"], 0.42 if self.final_exit_unlocked else 0.18)
            exit_border = (120 + pulse, 170 + pulse // 2, 255) if self.final_exit_unlocked else (92, 104, 122)
            self.canvas.fill(exit_fill, final_rect)
            pygame.draw.rect(self.canvas, exit_border, final_rect, 1)
            self.canvas.fill((18, 22, 30), pygame.Rect(final_rect.x + 4, final_rect.y + 1, 8, 12))
            self.canvas.fill(shift_color(exit_border, 18 if self.final_exit_unlocked else -12), pygame.Rect(final_rect.x + 6, final_rect.y + 4, 4, 4))

        if self.current_area == "area2":
            for laser in self.lasers:
                self.draw_laser_beam(laser, theme, self.laser_is_active(laser))

        for (tx, ty), kind in self.furniture.items():
            self.draw_furniture_tile(tx, ty, kind, theme)

        for trap_tile, is_active in self.traps.items():
            rect = pygame.Rect(trap_tile[0] * TILE_SIZE, trap_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            spike = theme["danger"] if is_active else shift_color(theme["wall_lo"], 20)
            self.canvas.fill((18, 20, 24), pygame.Rect(rect.x + 2, rect.y + 11, 12, 2))
            for offset in (2, 5, 8, 11):
                pygame.draw.line(self.canvas, spike, (rect.x + offset, rect.y + 11), (rect.x + offset + 1, rect.y + 5))

        if self.current_area == "maintenance" and self.breaker_tile != (0, 0):
            rect = pygame.Rect(self.breaker_tile[0] * TILE_SIZE, self.breaker_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            switch_on = self.area2_cleared
            switch_light = theme["safe"] if switch_on else theme["accent"]
            self.canvas.fill((20, 24, 28), pygame.Rect(rect.x + 2, rect.y + 12, 12, 2))
            self.canvas.fill((88, 96, 104), pygame.Rect(rect.x + 4, rect.y + 2, 8, 10))
            self.canvas.fill((54, 58, 64), pygame.Rect(rect.x + 5, rect.y + 3, 6, 8))
            lever_y = rect.y + (3 if switch_on else 7)
            pygame.draw.line(self.canvas, shift_color(switch_light, 22), (rect.x + 8, lever_y), (rect.x + 11, lever_y - 2 if switch_on else lever_y + 2))
            self.canvas.fill(switch_light, pygame.Rect(rect.x + 5, rect.y + 10, 6, 2))

        if self.current_area == "area3" and self.elevator_terminal_tile != (0, 0):
            self.draw_terminal_tile(self.elevator_terminal_tile, self.elevator_choice_made, theme, theme["safe"])

        for tile in self.save_tiles:
            self.draw_terminal_tile(tile, True, theme, theme["safe"])

        self.draw_hazards(theme)
        self.draw_flicker_lights(theme)

    def draw_entities(self) -> None:
        if self.can_reveal_pickups():
            for pickup in self.pickups:
                if not self.is_pickup_in_flashlight_range(pickup):
                    continue
                self.draw_pickup_entity(pickup)

        for wolf in self.wolves:
            self.draw_vision_cone(wolf)

        for wolf in self.wolves:
            self.draw_wolf_sprite(wolf)

    def draw_darkness_overlay(self) -> None:
        theme = self.get_area_theme()
        ambient = theme["ambient"]
        cam = self.get_camera_world_rect()
        wide = self.world_width > INTERNAL_WIDTH

        if wide:
            overlay = pygame.Surface((cam.width, cam.height), pygame.SRCALPHA)
            pcx = float(self.player.centerx - cam.x)
            pcy = float(self.player.centery - cam.y)
        else:
            overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            pcx = float(self.player.centerx)
            pcy = float(self.player.centery)

        overlay.fill((ambient[0], ambient[1], ambient[2], 124))

        tile_x = self.player.centerx // TILE_SIZE
        tile_y = self.player.centery // TILE_SIZE
        in_dark_zone = (tile_x, tile_y) in self.dark_tiles

        if self.flashlight_on and self.battery > 0:
            radius = 56 if self.battery > 20 else 46
            center = pygame.Vector2(pcx, pcy)
            direction = self.last_dir if self.last_dir.length_squared() > 0 else pygame.Vector2(1, 0)
            direction = direction.normalize()
            perpendicular = pygame.Vector2(-direction.y, direction.x)

            local_radius = 34 if self.battery > 20 else 28
            pygame.draw.circle(overlay, (ambient[0], ambient[1], ambient[2], 40), (int(center.x), int(center.y)), local_radius)
            pygame.draw.circle(overlay, (ambient[0], ambient[1], ambient[2], 58), (int(center.x), int(center.y)), local_radius + 10)

            beam_nodes = 5
            for idx in range(beam_nodes):
                t = idx / max(1, beam_nodes - 1)
                node_center = center + direction * (local_radius - 4 + t * (radius - 2))
                node_radius = int(12 + (1.0 - t) * 6 + t * 12)
                core_alpha = int(34 - t * 12)
                pygame.draw.circle(
                    overlay,
                    (ambient[0], ambient[1], ambient[2], core_alpha),
                    (int(node_center.x), int(node_center.y)),
                    node_radius,
                )

                side_spread = perpendicular * (3 + t * 9)
                side_radius = max(7, node_radius - 8)
                edge_alpha = int(60 - t * 10)
                pygame.draw.circle(
                    overlay,
                    (ambient[0], ambient[1], ambient[2], edge_alpha),
                    (int((node_center + side_spread).x), int((node_center + side_spread).y)),
                    side_radius,
                )
                pygame.draw.circle(
                    overlay,
                    (ambient[0], ambient[1], ambient[2], edge_alpha),
                    (int((node_center - side_spread).x), int((node_center - side_spread).y)),
                    side_radius,
                )
        elif in_dark_zone:
            radius = 18
            center = (int(pcx), int(pcy))
            pygame.draw.circle(overlay, (ambient[0], ambient[1], ambient[2], 44), center, radius)

        if wide:
            self.canvas.blit(overlay, (cam.x, cam.y))
        else:
            self.canvas.blit(overlay, (0, 0))

    def draw_inventory_overlay(self) -> None:
        # Dark scrim behind the panel
        scrim = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        scrim.fill((0, 0, 0, 128))
        self.canvas.blit(scrim, (0, 0))

        panel_w, panel_h = 236, 144
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((11, 16, 24, 240))
        px = (INTERNAL_WIDTH - panel_w) // 2
        py_base = (INTERNAL_HEIGHT - panel_h) // 2
        py = int(py_base + (1.0 - self.inventory_anim) * 24)
        panel.set_alpha(int(240 * self.inventory_anim))
        self.canvas.blit(panel, (px, py))
        pygame.draw.rect(self.canvas, (122, 142, 162), pygame.Rect(px, py, panel_w, panel_h), 1)
        pygame.draw.rect(self.canvas, (65, 80, 98), pygame.Rect(px + 2, py + 2, panel_w - 4, panel_h - 4), 1)

        self.blit_pixel_text_centered("ITEMS", pygame.Rect(px + 8, py + 4, 220, 12), self.inventory_title_font)
        self.blit_pixel_text_centered("TAB/ESC CLOSE", pygame.Rect(px + 8, py + 17, 220, 11), self.inventory_font)

        slots = self.get_inventory_slots()
        for idx, item in enumerate(slots):
            row = idx // self.inventory_cols
            col = idx % self.inventory_cols
            sx = px + 16 + col * 52
            sy = py + 32 + row * 40
            slot_rect = pygame.Rect(sx, sy, 44, 34)
            is_selected = idx == self.inventory_selected

            if item is None:
                # Empty slots dimmed
                self.draw_panel(slot_rect, (20, 24, 32), (26, 34, 46))
            else:
                border_color = (90, 138, 184) if is_selected else (78, 96, 116)
                self.draw_panel(slot_rect, (34, 44, 58), border_color)

                if item in self.sprite_cache and self.sprite_cache[item] is not None:
                    sprite = pygame.transform.scale(self.sprite_cache[item], (14, 14))
                    self.canvas.blit(sprite, (sx + (slot_rect.width - 14) // 2, sy + 4))
                elif item == "knife":
                    ix = sx + (slot_rect.width - 14) // 2
                    iy = sy + 3
                    handle_col = (139, 90, 43)
                    self.canvas.fill(handle_col, pygame.Rect(ix + 3, iy + 8, 5, 5))
                    self.canvas.fill(shift_color(handle_col, 22), pygame.Rect(ix + 3, iy + 8, 2, 3))
                    self.canvas.fill((170, 160, 140), pygame.Rect(ix + 2, iy + 7, 7, 1))
                    blade = (210, 214, 220)
                    self.canvas.fill(blade, pygame.Rect(ix + 4, iy + 2, 5, 5))
                    self.canvas.fill(blade, pygame.Rect(ix + 5, iy, 4, 2))
                    self.canvas.fill(shift_color(blade, 18), pygame.Rect(ix + 5, iy + 2, 2, 3))
                    self.canvas.fill((235, 238, 242), pygame.Rect(ix + 8, iy + 2, 1, 3))
                elif item == "keycard":
                    ix = sx + (slot_rect.width - 14) // 2
                    iy = sy + 3
                    self.canvas.fill(PALETTE["key"], pygame.Rect(ix + 2, iy + 2, 10, 8))
                    self.canvas.fill((200, 200, 195), pygame.Rect(ix + 3, iy + 3, 3, 3))
                    self.canvas.fill(shift_color(PALETTE["key"], -50), pygame.Rect(ix + 2, iy + 8, 10, 2))
                    self.canvas.fill((220, 220, 215), pygame.Rect(ix + 8, iy + 3, 2, 1))
                    self.canvas.fill((220, 220, 215), pygame.Rect(ix + 8, iy + 6, 2, 1))
                self.blit_pixel_text_centered(item.upper(), pygame.Rect(sx + 2, sy + 20, slot_rect.width - 4, 9), self.inventory_small_font)
                if item == "bandage":
                    self.blit_pixel_text(str(self.bandages), sx + 34, sy + 1, self.inventory_small_font)

        # Description panel
        selected_item = slots[self.inventory_selected] if self.inventory_selected < len(slots) else None
        desc_text = self.ITEM_DESCRIPTIONS.get(selected_item, "Empty slot") if selected_item else "Empty slot"
        desc_rect = pygame.Rect(px + 12, py + 112, 212, 14)
        self.draw_panel(desc_rect, (16, 20, 28), (50, 62, 78))
        self.blit_pixel_text_centered(desc_text, pygame.Rect(desc_rect.x + 4, desc_rect.y + 2, desc_rect.width - 8, desc_rect.height - 4), self.inventory_font)

        footer = pygame.Rect(px + 10, py + 130, 216, 12)
        self.draw_panel(footer, (26, 34, 45), (95, 112, 132))
        self.blit_pixel_text_centered("ENTER USE  |  F EQUIP", pygame.Rect(footer.x + 2, footer.y + 1, footer.width - 4, footer.height - 2), self.inventory_font)

    def draw_dilemma_overlay(self) -> None:
        panel_h = 130
        panel = pygame.Surface((280, panel_h), pygame.SRCALPHA)
        panel.fill((18, 15, 18, 245))
        px = (INTERNAL_WIDTH - panel.get_width()) // 2
        py_base = (INTERNAL_HEIGHT - panel.get_height()) // 2
        py = int(py_base + (1.0 - self.dilemma_anim) * 18)
        panel.set_alpha(int(245 * self.dilemma_anim))
        self.canvas.blit(panel, (px, py))
        pygame.draw.rect(self.canvas, (150, 98, 98), pygame.Rect(px, py, 280, panel_h), 1)

        text_w = 280 - 24
        self.blit_text_shadow("ELEVATOR LIMIT: 60KG", px + 12, py + 10, text_w)
        self.blit_text_shadow("Choose your sacrifice", px + 12, py + 24, text_w)

        # Option 1: Leg
        opt1_selected = self.dilemma_selection == 1
        opt1_border = (199, 144, 70) if opt1_selected else (58, 42, 42)
        opt1_rect = pygame.Rect(px + 8, py + 40, 264, 22)
        self.draw_panel(opt1_rect, (28, 20, 20) if opt1_selected else (22, 18, 18), opt1_border)
        self.blit_text_shadow("[1] Cut leg", px + 14, py + 42, text_w)
        self.blit_text_shadow("Move speed 70 -> 45 (-36%)", px + 14, py + 52, text_w)

        # Option 2: Arm
        opt2_selected = self.dilemma_selection == 2
        opt2_border = (199, 144, 70) if opt2_selected else (58, 42, 42)
        opt2_rect = pygame.Rect(px + 8, py + 66, 264, 22)
        self.draw_panel(opt2_rect, (28, 20, 20) if opt2_selected else (22, 18, 18), opt2_border)
        self.blit_text_shadow("[2] Cut arm", px + 14, py + 68, text_w)
        self.blit_text_shadow("Attack speed 1.0x -> 0.3x (-70%)", px + 14, py + 78, text_w)

        # Warning and footer
        self.blit_text_shadow("This cannot be undone", px + 12, py + 94, text_w)
        self.blit_pixel_text_centered("1/2 select | ENTER confirm | ESC cancel", pygame.Rect(px + 8, py + 112, 264, 12), self.inventory_font)

    def draw_center_banner(self, text: str) -> None:
        box = pygame.Surface((180, 44), pygame.SRCALPHA)
        box.fill((18, 24, 33, 242))
        x = (INTERNAL_WIDTH - 180) // 2
        y = (INTERNAL_HEIGHT - 44) // 2
        self.canvas.blit(box, (x, y))
        pygame.draw.rect(self.canvas, (133, 156, 178), pygame.Rect(x, y, 180, 44), 1)
        text_w, text_h = self.big_font.size(text)
        self.blit_pixel_text_on(self.canvas, text, x + (180 - text_w) // 2, y + (44 - text_h) // 2, self.big_font)

    def start_area_transition(self, target_area: str, spawn_override: tuple[int, int] | None = None) -> None:
        self.area_fade_phase = "fadeOut"
        self.area_fade_target = target_area
        self.area_fade_spawn = spawn_override
        self.area_fade_alpha = 0.0

    def draw_pause_menu(self, view_rect: pygame.Rect) -> None:
        scrim = pygame.Surface((view_rect.width, view_rect.height), pygame.SRCALPHA)
        scrim.fill((0, 0, 0, 160))
        self.screen.blit(scrim, (view_rect.x, view_rect.y))

        menu_w, menu_h = 220, 140
        menu_x = view_rect.centerx - menu_w // 2
        menu_y = view_rect.centery - menu_h // 2

        panel = pygame.Surface((menu_w, menu_h), pygame.SRCALPHA)
        panel.fill((12, 16, 24, 240))
        self.screen.blit(panel, (menu_x, menu_y))
        pygame.draw.rect(self.screen, (42, 58, 82), pygame.Rect(menu_x, menu_y, menu_w, menu_h), 1)

        # Title
        title_text = self.big_font.render("PAUSED", True, (180, 196, 216))
        title_x = menu_x + (menu_w - title_text.get_width()) // 2
        self.screen.blit(title_text, (title_x, menu_y + 10))

        items = ["Resume", "Save & Quit", "Quit"]
        for idx, label in enumerate(items):
            item_y = menu_y + 40 + idx * 28
            is_selected = idx == self.pause_selected
            item_rect = pygame.Rect(menu_x + 20, item_y, menu_w - 40, 22)

            if is_selected:
                item_surf = pygame.Surface((item_rect.width, item_rect.height), pygame.SRCALPHA)
                item_surf.fill((18, 22, 32, 200))
                self.screen.blit(item_surf, (item_rect.x, item_rect.y))
                border = (138, 64, 64) if idx >= 1 else (90, 138, 184)
                text_color = (184, 106, 106) if idx >= 1 else (220, 232, 244)
            else:
                border = (42, 52, 66)
                text_color = (106, 118, 134)

            pygame.draw.rect(self.screen, border, item_rect, 1)
            lbl = self.ui_font.render(label, True, text_color)
            lbl_x = item_rect.x + (item_rect.width - lbl.get_width()) // 2
            lbl_y = item_rect.y + (item_rect.height - lbl.get_height()) // 2
            self.screen.blit(lbl, (lbl_x, lbl_y))

    def draw_death_screen(self, view_rect: pygame.Rect) -> None:
        vignette = pygame.Surface((view_rect.width, view_rect.height), pygame.SRCALPHA)
        vignette.fill((80, 10, 10, 120))
        self.screen.blit(vignette, (view_rect.x, view_rect.y))

        text = self.big_font.render("YOU DIED", True, (199, 70, 70))
        tx = view_rect.centerx - text.get_width() // 2
        ty = view_rect.centery - text.get_height() // 2 - 10
        self.screen.blit(text, (tx, ty))

        prompt = self.ui_small_font.render("Press any key to restart", True, (106, 74, 74))
        px = view_rect.centerx - prompt.get_width() // 2
        py = ty + 30
        self.screen.blit(prompt, (px, py))

    def draw_victory_screen(self, view_rect: pygame.Rect) -> None:
        text = self.big_font.render("YOU ESCAPED", True, (92, 179, 130))
        tx = view_rect.centerx - text.get_width() // 2
        ty = view_rect.centery - text.get_height() // 2 - 20
        self.screen.blit(text, (tx, ty))

        time_str = f"Time: {self.time_alive:.0f}s"
        hp_str = f"HP remaining: {self.health}"
        stats = self.ui_small_font.render(f"{time_str}  |  {hp_str}", True, (122, 154, 138))
        sx = view_rect.centerx - stats.get_width() // 2
        sy = ty + 24
        self.screen.blit(stats, (sx, sy))

        prompt = self.ui_small_font.render("Press any key to exit", True, (90, 122, 106))
        px = view_rect.centerx - prompt.get_width() // 2
        py = sy + 20
        self.screen.blit(prompt, (px, py))

    def blit_text(self, text: str, x: int, y: int) -> None:
        self.blit_pixel_text_on(self.canvas, text, x, y, self.font)

    def blit_pixel_text_on(
        self,
        surface: pygame.Surface,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = (236, 243, 250),
    ) -> None:
        if not text:
            return
        outline = font.render(text, False, (6, 9, 14))
        label = font.render(text, False, color)
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            surface.blit(outline, (x + ox, y + oy))
        surface.blit(label, (x, y))

    def blit_pixel_text(
        self,
        text: str,
        x: int,
        y: int,
        font: pygame.font.Font,
        color: tuple[int, int, int] = (236, 243, 250),
    ) -> None:
        self.blit_pixel_text_on(self.canvas, text, x, y, font, color)

    def blit_pixel_text_centered(self, text: str, rect: pygame.Rect, font: pygame.font.Font) -> None:
        draw_text = self.fit_text(text, font, rect.width)
        if not draw_text:
            return
        label = font.render(draw_text, False, (236, 243, 250))
        x = rect.x + (rect.width - label.get_width()) // 2
        y = rect.y + (rect.height - label.get_height()) // 2
        self.blit_pixel_text(draw_text, x, y, font)

    def fit_text(self, text: str, font: pygame.font.Font, max_width: int) -> str:
        if max_width <= 0:
            return ""
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        if font.size(ellipsis)[0] > max_width:
            return ""

        trimmed = text
        while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
            trimmed = trimmed[:-1]
        return trimmed + ellipsis

    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]

        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            trial = f"{current} {word}"
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def blit_text_shadow(self, text: str, x: int, y: int, max_width: int | None = None) -> None:
        draw_text = self.fit_text(text, self.font, max_width) if max_width is not None else text
        self.blit_pixel_text_on(self.canvas, draw_text, x, y, self.font)

    def blit_text_centered_shadow(self, text: str, rect: pygame.Rect) -> None:
        draw_text = self.fit_text(text, self.font, rect.width)
        if not draw_text:
            return
        text_w, text_h = self.font.size(draw_text)
        x = rect.x + (rect.width - text_w) // 2
        y = rect.y + (rect.height - text_h) // 2
        self.blit_text_shadow(draw_text, x, y)

    def blit_small_text_centered(self, text: str, rect: pygame.Rect) -> None:
        draw_text = self.fit_text(text, self.small_font, rect.width)
        if not draw_text:
            return
        text_w, text_h = self.small_font.size(draw_text)
        x = rect.x + (rect.width - text_w) // 2
        y = rect.y + (rect.height - text_h) // 2
        self.blit_pixel_text_on(self.canvas, draw_text, x, y, self.small_font)

    def blit_multiline_left_shadow(self, text: str, rect: pygame.Rect) -> None:
        line_height = self.font.get_height()
        lines = self.wrap_text(text, self.font, rect.width)
        max_lines = max(1, rect.height // line_height)

        if len(lines) > max_lines:
            head = lines[: max_lines - 1]
            tail_joined = " ".join(lines[max_lines - 1 :])
            head.append(self.fit_text(tail_joined, self.font, rect.width))
            lines = head

        y = rect.y
        for line in lines:
            self.blit_text_shadow(line, rect.x, y, rect.width)
            y += line_height

    def draw_panel(self, rect: pygame.Rect, fill: tuple[int, int, int], border: tuple[int, int, int]) -> None:
        self.canvas.fill(fill, rect)
        pygame.draw.rect(self.canvas, border, rect, 1)
        inner = rect.inflate(-2, -2)
        pygame.draw.rect(self.canvas, (30, 40, 53), inner, 1)

    def draw_pickup_icon(
        self,
        rect: pygame.Rect,
        name: str,
        color: tuple[int, int, int],
        sprite: pygame.Surface | None,
    ) -> None:
        if sprite is not None:
            sx = rect.x + (rect.width - sprite.get_width()) // 2
            sy = rect.y + (rect.height - sprite.get_height()) // 2
            self.canvas.blit(sprite, (sx, sy))
            return

        self.canvas.fill((18, 24, 33), rect)
        if name == "key":
            pygame.draw.circle(self.canvas, color, (rect.x + 3, rect.y + 3), 2)
            self.canvas.fill(color, pygame.Rect(rect.x + 5, rect.y + 2, 2, 5))
            self.canvas.fill(color, pygame.Rect(rect.x + 6, rect.y + 5, 2, 1))
        elif name == "battery":
            self.canvas.fill(color, pygame.Rect(rect.x + 2, rect.y + 1, 4, 6))
            self.canvas.fill((220, 220, 220), pygame.Rect(rect.x + 3, rect.y, 2, 1))
        elif name == "flashlight":
            self.canvas.fill(color, pygame.Rect(rect.x + 2, rect.y + 2, 5, 3))
            self.canvas.fill((216, 216, 200), pygame.Rect(rect.x + 6, rect.y + 3, 2, 1))
        elif name == "knife":
            # Handle
            handle_col = (139, 90, 43)
            self.canvas.fill(handle_col, pygame.Rect(rect.x + 1, rect.y + 4, 3, 3))
            self.canvas.fill(shift_color(handle_col, 22), pygame.Rect(rect.x + 1, rect.y + 4, 1, 2))
            # Guard
            self.canvas.fill((170, 160, 140), pygame.Rect(rect.x + 1, rect.y + 3, 4, 1))
            # Blade
            blade = (210, 214, 220)
            self.canvas.fill(blade, pygame.Rect(rect.x + 2, rect.y + 1, 3, 2))
            self.canvas.fill(blade, pygame.Rect(rect.x + 3, rect.y, 2, 1))
            self.canvas.fill(shift_color(blade, 20), pygame.Rect(rect.x + 3, rect.y + 1, 1, 1))
            # Edge highlight
            self.canvas.fill((235, 238, 242), pygame.Rect(rect.x + 4, rect.y + 1, 1, 1))
        elif name == "keycard":
            # Card body
            self.canvas.fill(color, pygame.Rect(rect.x + 1, rect.y + 1, 6, 5))
            # Chip
            self.canvas.fill((200, 200, 195), pygame.Rect(rect.x + 2, rect.y + 2, 2, 2))
            # Stripe
            self.canvas.fill(shift_color(color, -40), pygame.Rect(rect.x + 1, rect.y + 5, 6, 1))
            # Contact dots
            self.canvas.fill((220, 220, 215), pygame.Rect(rect.x + 5, rect.y + 2, 1, 1))
            self.canvas.fill((220, 220, 215), pygame.Rect(rect.x + 5, rect.y + 4, 1, 1))
        else:
            self.canvas.fill(color, pygame.Rect(rect.x + 2, rect.y + 2, 5, 4))
            self.canvas.fill((240, 240, 240), pygame.Rect(rect.x + 4, rect.y + 3, 1, 2))

    def draw_wolf_sprite(self, wolf: Wolf) -> None:
        body = wolf.rect
        shadow_w = 13 if wolf.alive else 14
        shadow = pygame.Rect(body.centerx - shadow_w // 2, body.y + 11, shadow_w, 2)
        self.canvas.fill((10, 12, 16), shadow)

        sprite_set = self.entity_sprites.get("wolf", {})
        if not sprite_set:
            color = PALETTE["wolf_alert"] if wolf.alert else PALETTE["wolf"]
            self.canvas.fill(color, pygame.Rect(body.x + 2, body.y + 3, 8, 7))
            return

        if not wolf.alive:
            corpse = sprite_set.get("corpse")
            if corpse is not None:
                self.draw_centered_sprite(body, corpse, 0)
            self.canvas.fill((150, 92, 92), pygame.Rect(body.x + 3, body.y + 9, 2, 1))
            return

        direction = self.get_direction_key(pygame.Vector2(wolf.facing_x, wolf.facing_y))
        moving = (abs(wolf.facing_x) + abs(wolf.facing_y)) > 0.01

        if direction in {"left", "right"}:
            frame = "walk_a" if int(self.time_alive * 8.0) % 2 == 0 and moving else "walk_b"
            if not moving:
                frame = "idle"
            if wolf.alert:
                frame = "alert"
            sprite = sprite_set.get(f"{direction}_{frame}", sprite_set.get(f"{direction}_idle"))
        else:
            frame = "alert" if wolf.alert else "idle"
            sprite = sprite_set.get(f"{direction}_{frame}", sprite_set.get("down_idle"))

        if sprite is not None:
            bob = -1 if wolf.alert and int(self.time_alive * 12.0) % 2 == 0 else 0
            self.draw_centered_sprite(body, sprite, bob)
            if wolf.alert:
                self.canvas.fill((84, 24, 24), pygame.Rect(body.x + 1, body.y + 11, 12, 1))

        if wolf.subtype == "alpha" and wolf.alive:
            bar_w = 24
            bar_h = 3
            x = int(wolf.x + wolf.size // 2 - bar_w // 2)
            y = int(wolf.y - 6)
            ratio = wolf.hp / wolf.max_hp
            self.canvas.fill((40, 10, 10), pygame.Rect(x, y, bar_w, bar_h))
            self.canvas.fill((199, 70, 70), pygame.Rect(x, y, int(bar_w * ratio), bar_h))

    def draw_vision_cone(self, wolf: Wolf) -> None:
        if wolf.subtype != "hunter" or not wolf.alive:
            return
        center = pygame.Vector2(wolf.x + wolf.size // 2, wolf.y + wolf.size // 2)
        facing = pygame.Vector2(wolf.facing_x, wolf.facing_y)
        if facing.length_squared() == 0:
            facing = pygame.Vector2(1, 0)
        facing = facing.normalize()
        half_angle = math.pi / 6
        cone_range = 64
        perp = pygame.Vector2(-facing.y, facing.x)
        tip_a = center + (facing * math.cos(half_angle) + perp * math.sin(half_angle)) * cone_range
        tip_b = center + (facing * math.cos(half_angle) - perp * math.sin(half_angle)) * cone_range
        cone_surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        color = (220, 80, 60, 40) if wolf.alert else (180, 220, 140, 25)
        points = [(int(center.x), int(center.y)), (int(tip_a.x), int(tip_a.y)), (int(tip_b.x), int(tip_b.y))]
        pygame.draw.polygon(cone_surf, color, points)
        self.canvas.blit(cone_surf, (0, 0))

    def draw_hazards(self, theme: dict[str, tuple[int, int, int]]) -> None:
        for hazard in self.hazards:
            x = hazard.tile_x * TILE_SIZE
            y = hazard.tile_y * TILE_SIZE
            if hazard.kind == "tripwire":
                if not hazard.triggered:
                    wire_color = shift_color(theme["accent"], -20)
                    pygame.draw.line(self.canvas, wire_color, (x + 2, y + 8), (x + 14, y + 8), 1)
                    self.canvas.fill(wire_color, pygame.Rect(x + 6, y + 6, 4, 4))
            elif hazard.kind == "alarm":
                if not hazard.triggered:
                    color = theme["danger"] if int(self.time_alive * 3) % 2 == 0 else shift_color(theme["danger"], -40)
                    self.canvas.fill((24, 24, 28), pygame.Rect(x + 4, y + 4, 8, 8))
                    self.canvas.fill(color, pygame.Rect(x + 5, y + 5, 6, 6))
            elif hazard.kind == "crumble":
                if hazard.active:
                    if hazard.triggered:
                        crack_color = theme["danger"]
                        for offset in (3, 7, 11):
                            pygame.draw.line(self.canvas, crack_color,
                                             (x + offset, y + 2), (x + offset + 2, y + 14), 1)
                    else:
                        alt = theme["floor_alt"]
                        self.canvas.fill(alt, pygame.Rect(x, y, TILE_SIZE, TILE_SIZE))
                        self.canvas.fill(shift_color(theme["floor"], -8), pygame.Rect(x + 2, y + 2, 6, 2))
                        self.canvas.fill(shift_color(theme["floor"], -8), pygame.Rect(x + 9, y + 8, 5, 2))

    def draw_flicker_lights(self, theme: dict[str, tuple[int, int, int]]) -> None:
        for light in self.flicker_lights:
            cycle = light.on_duration + light.off_duration
            t = (self.time_alive + light.phase) % cycle
            is_on = t < light.on_duration
            cx = light.tile_x * TILE_SIZE + TILE_SIZE // 2
            cy = light.tile_y * TILE_SIZE + TILE_SIZE // 2
            if is_on:
                glow = pygame.Surface((48, 48), pygame.SRCALPHA)
                glow.fill((240, 220, 160, 30))
                self.canvas.blit(glow, (cx - 24, cy - 24))
                self.canvas.fill((240, 220, 160), pygame.Rect(cx - 1, cy - 3, 2, 2))
            else:
                self.canvas.fill((60, 55, 35), pygame.Rect(cx - 1, cy - 3, 2, 2))

    def draw_player_sprite(self) -> None:
        base = self.player
        moving = self.player_vel.length() > 8.0
        facing = self.last_dir if self.last_dir.length_squared() > 0 else pygame.Vector2(1, 0)
        facing = facing.normalize()
        direction = self.get_direction_key(facing)
        sprite_set = self.entity_sprites.get("player", {})

        self.canvas.fill((10, 12, 18), pygame.Rect(base.centerx - 5, base.y + 11, 10, 2))
        if moving:
            self.canvas.fill((10, 12, 18), pygame.Rect(base.centerx + 3, base.y + 11, 3, 1))

        if sprite_set:
            if self.damage_flash > 0 and direction in {"left", "right"}:
                frame = f"{direction}_hurt"
            else:
                cycle = "walk_a" if int(self.time_alive * 8.0) % 2 == 0 else "walk_b"
                if not moving:
                    cycle = "idle"
                frame = f"{direction}_{cycle}"
            sprite = sprite_set.get(frame, sprite_set.get("right_idle"))
            if sprite is not None:
                hurt_shift = -1 if self.damage_flash > 0 else 0
                limp = 1 if self.health < self.max_health * 0.3 and int(self.time_alive * 5.0) % 2 == 0 else 0
                self.draw_centered_sprite(base, sprite, hurt_shift + limp)

        gear_y = base.y + 6
        if self.has_flashlight and self.equipped_item != "flashlight":
            belt_x = base.centerx + 2 if direction != "left" else base.centerx - 4
            self.canvas.fill((106, 118, 126), pygame.Rect(belt_x, gear_y + 2, 1, 3))
            self.canvas.fill(PALETTE["flashlight"], pygame.Rect(belt_x, gear_y + 1, 1, 1))
        if self.has_knife and self.equipped_item != "knife":
            knife_x = base.centerx - 5 if direction != "right" else base.centerx + 2
            # Sheath
            self.canvas.fill((80, 60, 40), pygame.Rect(knife_x, gear_y + 1, 2, 4))
            # Pommel
            self.canvas.fill((139, 90, 43), pygame.Rect(knife_x, gear_y, 2, 1))
            # Blade peeking out
            self.canvas.fill((200, 204, 210), pygame.Rect(knife_x, gear_y - 1, 1, 1))

        hand_point = pygame.Vector2(base.centerx + facing.x * 3, base.y + 7 + facing.y * 2)
        if self.equipped_item == "flashlight" and self.has_flashlight:
            flash_body = pygame.Rect(int(hand_point.x), int(hand_point.y), 3, 2)
            self.canvas.fill((118, 132, 144), flash_body)
            lens_x = flash_body.right if facing.x >= 0 else flash_body.x - 1
            self.canvas.fill(PALETTE["flashlight"], pygame.Rect(lens_x, flash_body.y, 1, 2))
            if self.flashlight_on and self.battery > 0:
                beam_tip = hand_point + facing * 7
                pygame.draw.line(self.canvas, (242, 232, 178), (int(hand_point.x + 1), int(hand_point.y + 1)), (int(beam_tip.x), int(beam_tip.y)))

        if self.attack_anim > 0:
            t = 1.0 - (self.attack_anim / max(0.001, self.attack_duration))
            swing = math.sin(t * math.pi)
            start = pygame.Vector2(base.centerx, base.y + 7)
            swing_dir = self.attack_dir if self.attack_dir.length_squared() > 0 else facing
            perp = pygame.Vector2(-swing_dir.y, swing_dir.x)

            grip = start + swing_dir * 2.0
            guard = grip + swing_dir * 1.0
            blade_base = guard + swing_dir * (2.0 + swing * 4.0)
            blade_tip = blade_base + swing_dir * 2.5

            # Handle
            pygame.draw.line(self.canvas, (139, 90, 43), (int(start.x), int(start.y)), (int(grip.x), int(grip.y)), 2)
            # Guard
            guard_l = guard + perp * 1.5
            guard_r = guard - perp * 1.5
            pygame.draw.line(self.canvas, (170, 160, 140), (int(guard_l.x), int(guard_l.y)), (int(guard_r.x), int(guard_r.y)))
            # Blade edges
            blade_l = blade_base + perp * 1.2
            blade_r = blade_base - perp * 1.2
            pygame.draw.line(self.canvas, (200, 204, 212), (int(blade_l.x), int(blade_l.y)), (int(blade_tip.x), int(blade_tip.y)))
            pygame.draw.line(self.canvas, (200, 204, 212), (int(blade_r.x), int(blade_r.y)), (int(blade_tip.x), int(blade_tip.y)))
            # Blade fill
            pygame.draw.line(self.canvas, (228, 232, 240), (int(guard.x), int(guard.y)), (int(blade_base.x), int(blade_base.y)))
            pygame.draw.line(self.canvas, (238, 240, 245), (int(blade_base.x), int(blade_base.y)), (int(blade_tip.x), int(blade_tip.y)))
            # Edge shine
            pygame.draw.line(self.canvas, (248, 250, 252), (int(blade_base.x), int(blade_base.y)), (int(blade_tip.x), int(blade_tip.y)))
            # Tip sparkle
            if swing > 0.5:
                self.canvas.fill((255, 252, 230), pygame.Rect(int(blade_tip.x), int(blade_tip.y), 1, 1))

    def draw_particles(self) -> None:
        for p in self.particles:
            alpha = max(0, min(255, int(255 * min(1.0, p.life / 0.45))))
            dot = pygame.Surface((p.size, p.size), pygame.SRCALPHA)
            dot.fill((p.color[0], p.color[1], p.color[2], alpha))
            self.canvas.blit(dot, (int(p.x), int(p.y)))

    def emit_particles(self, x: float, y: float, count: int, color: tuple[int, int, int]) -> None:
        for _ in range(count):
            angle = random.uniform(0.0, math.pi * 2.0)
            speed = random.uniform(15.0, 60.0)
            self.particles.append(
                Particle(
                    x=x,
                    y=y,
                    vx=math.cos(angle) * speed,
                    vy=math.sin(angle) * speed - 8.0,
                    life=random.uniform(0.2, 0.5),
                    color=color,
                    size=random.randint(1, 3),
                )
            )

    def trigger_shake(self, strength: float, duration: float) -> None:
        self.shake_strength = max(self.shake_strength, strength)
        self.shake_time = max(self.shake_time, duration)

    def draw_atmosphere_back(self) -> None:
        theme = self.get_area_theme()
        top = shift_color(theme["ambient"], -6)
        bottom = mix_color(theme["floor"], theme["wall"], 0.4)
        cw = self.canvas.get_width()
        ch = self.canvas.get_height()
        for y in range(ch):
            t = y / ch
            pygame.draw.line(self.canvas, mix_color(top, bottom, t), (0, y), (cw, y))

    def draw_atmosphere_front(self) -> None:
        theme = self.get_area_theme()
        vignette = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        for i in range(9):
            alpha = 14 + i * 3
            pygame.draw.rect(
                vignette,
                (0, 0, 0, alpha),
                pygame.Rect(i, i, INTERNAL_WIDTH - i * 2, INTERNAL_HEIGHT - i * 2),
                1,
            )

        # Subtle scanlines keep a pixel-horror feel without hurting readability.
        line_alpha = 12 + int((math.sin(self.time_alive * 1.5) + 1.0) * 0.5 * 6)
        for y in range(0, INTERNAL_HEIGHT, 2):
            pygame.draw.line(vignette, (0, 0, 0, line_alpha), (0, y), (INTERNAL_WIDTH, y))

        edge_glow = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        edge_color = theme["danger"] if self.current_area in {"area2", "final"} else theme["accent"]
        pygame.draw.rect(edge_glow, (edge_color[0], edge_color[1], edge_color[2], 18), pygame.Rect(1, 1, INTERNAL_WIDTH - 2, INTERNAL_HEIGHT - 2), 1)
        vignette.blit(edge_glow, (0, 0))
        self.canvas.blit(vignette, (0, 0))


def main() -> None:
    game = Game()
    game.run()
