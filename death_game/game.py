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
}

AREA_FLOW_ORDER = ["area1", "hub", "storage", "medbay", "maintenance", "area2", "area3", "final"]
AREA_META = {
    "area1": ("B1-01", "RESIDENTIAL UNIT", "UNIT"),
    "hub": ("B1-02", "MAIN HALLWAY", "HALL"),
    "storage": ("B1-03", "STORAGE ROOM", "STOR"),
    "medbay": ("B1-04", "MED BAY", "MED"),
    "maintenance": ("B1-05", "MAINTENANCE CORRIDOR", "MNT"),
    "area2": ("B1-06", "SECURITY CHECKPOINT", "SEC"),
    "area3": ("B1-07", "ELEVATOR LOBBY", "LIFT"),
    "final": ("B1-08", "EXIT HALL", "EXIT"),
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

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), 12, 12)


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


class SoundManager:
    """Procedural audio using numpy. Gracefully degrades if numpy unavailable."""

    def __init__(self) -> None:
        self.sounds: dict[str, pygame.mixer.Sound] = {}
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

    def _generate_all(self) -> None:
        sr = 22050

        # Footstep: 50ms noise burst
        n = int(sr * 0.05)
        noise = np.random.uniform(-0.3, 0.3, n).tolist()
        self.sounds["footstep"] = self._make_sound([s * e for s, e in zip(noise, self._env(n, 0.1, 0.6))])

        # Pickup: 200ms ascending sine 440->880Hz
        n = int(sr * 0.2)
        t = np.linspace(0, 0.2, n)
        freq = np.linspace(440, 880, n)
        wave = np.sin(2 * np.pi * freq * t) * 0.4
        self.sounds["pickup"] = self._make_sound((wave * np.array(self._env(n, 0.05, 0.3))).tolist())

        # Damage: 150ms low sine 80Hz + noise
        n = int(sr * 0.15)
        t = np.linspace(0, 0.15, n)
        wave = (np.sin(2 * np.pi * 80 * t) * 0.5 + np.random.uniform(-0.2, 0.2, n) * 0.3)
        self.sounds["damage"] = self._make_sound((wave * np.array(self._env(n, 0.02, 0.4))).tolist())

        # Door: 100ms click + 80ms scrape
        n1 = int(sr * 0.1)
        n2 = int(sr * 0.08)
        click = np.random.uniform(-0.5, 0.5, n1) * np.array(self._env(n1, 0.01, 0.5))
        scrape = np.random.uniform(-0.15, 0.15, n2) * np.sin(2 * np.pi * 200 * np.linspace(0, 0.08, n2))
        combined = np.concatenate([click, scrape])
        self.sounds["door"] = self._make_sound(combined.tolist())

        # Wolf growl: 300ms low rumble 60Hz + noise with tremolo
        n = int(sr * 0.3)
        t = np.linspace(0, 0.3, n)
        tremolo = 0.5 + 0.5 * np.sin(2 * np.pi * 8 * t)
        wave = (np.sin(2 * np.pi * 60 * t) * 0.4 + np.random.uniform(-0.1, 0.1, n) * 0.2) * tremolo
        self.sounds["growl"] = self._make_sound((wave * np.array(self._env(n, 0.05, 0.3))).tolist())

        # Save chime: C5->E5->G5 ascending, repeated with gap
        notes = [523.25, 659.25, 783.99]
        samples_per = int(sr * 0.12)
        all_samples = []
        for freq in notes:
            t = np.linspace(0, 0.12, samples_per)
            wave = np.sin(2 * np.pi * freq * t) * 0.3
            all_samples.extend((wave * np.array(self._env(samples_per, 0.02, 0.3))).tolist())
        gap = [0.0] * int(sr * 0.02)
        self.sounds["save"] = self._make_sound(all_samples + gap + all_samples[:samples_per])

    def play(self, name: str) -> None:
        if not self.enabled or name not in self.sounds:
            return
        self.sounds[name].play()


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
        self.intro_hint = "Press SPACE or E to start"
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
        self.zone_card_title = ""
        self.zone_card_subtitle = ""
        self.zone_card_timer = 0.0
        self.visited_areas: set[str] = set()

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

    def load_sprite(self, path: Path, size: tuple[int, int]) -> pygame.Surface:
        if path.exists():
            sprite = pygame.image.load(path.as_posix()).convert_alpha()
            if sprite.get_size() != size:
                sprite = pygame.transform.scale(sprite, size)
            return sprite

        # Fallback placeholder keeps game playable when pipeline assets are not present yet.
        placeholder = pygame.Surface(size, pygame.SRCALPHA)
        placeholder.fill((0, 0, 0, 0))
        pygame.draw.rect(placeholder, (22, 30, 40), placeholder.get_rect())
        pygame.draw.rect(placeholder, (120, 140, 164), placeholder.get_rect(), 1)
        return placeholder

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
                self.attack_speed_mult = 1.7
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
                elif cell == "X":
                    self.final_exit_tile = (x, y)
                elif cell == "S":
                    self.save_tiles.append((x, y))

        self.checkpoints[area_id] = spawn
        spawn_tile = spawn_override if spawn_override is not None else spawn
        self.player.x = spawn_tile[0] * TILE_SIZE + 3
        self.player.y = spawn_tile[1] * TILE_SIZE + 2
        self.player_pos.update(float(self.player.x), float(self.player.y))
        self.player_vel.update(0, 0)

        if area_id == "area2":
            self.setup_area2_lasers()

        if area_id == "final":
            self.final_exit_unlocked = False

        zone_code, zone_name, _ = self.get_area_meta(area_id)
        self.zone_card_title = f"LEVEL 1  |  {zone_code}"
        self.zone_card_subtitle = zone_name
        self.zone_card_timer = 2.2

        self.set_objective_for_area()

    def get_area_meta(self, area_id: str | None = None) -> tuple[str, str, str]:
        key = area_id if area_id is not None else self.current_area
        return AREA_META.get(key, ("B1-??", "UNKNOWN ZONE", "???"))

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
                    pygame.quit()
                    sys.exit(0)

                if self.intro_timer > 0 and event.key in (pygame.K_SPACE, pygame.K_e, pygame.K_RETURN):
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
                        self.inventory_selected = min(7, self.inventory_selected + 1)
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        self.inventory_selected = max(0, self.inventory_selected - self.inventory_cols)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.inventory_selected = min(7, self.inventory_selected + self.inventory_cols)
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

        self.intro_timer = max(0.0, self.intro_timer - dt)
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

        self.collect_pickups()
        self.check_traps()
        self.update_wolves(dt)
        self.update_flashlight(dt)
        self.update_area2_hazards()
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
                    self.message = "You escaped Level 1."
                    self.message_timer = 1000.0
                else:
                    self.message = "Defeat all enemies first"
                    self.message_timer = 1.1
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

            wolf_vec = pygame.Vector2(wolf.x + 6, wolf.y + 6)
            to_player = player_center - wolf_vec
            dist = to_player.length()

            was_alert = wolf.alert
            wolf.alert = dist < 64
            if wolf.alert and not was_alert:
                self.sound.play("growl")
            if dist < 90:
                if dist > 0:
                    move = to_player.normalize() * (42 if wolf.alert else 30) * dt
                    wolf.x += move.x
                    wolf.y += move.y

                if self.player.colliderect(wolf.rect) and self.hit_cooldown <= 0:
                    self.health = max(0, self.health - 12)
                    self.sound.play("damage")
                    self.damage_flash = 0.16
                    self.hit_cooldown = 0.5
                    self.message = "Wolf attack"
                    self.message_timer = 0.8
                    self.trigger_shake(2.0, 0.15)
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

        for wolf in self.wolves:
            if wolf.alive and attack_rect.colliderect(wolf.rect):
                wolf.alive = False
                self.message = "Wolf neutralized"
                self.message_timer = 0.9
                self.trigger_shake(1.8, 0.12)
                self.emit_particles(wolf.rect.centerx, wolf.rect.centery, 12, PALETTE["wolf_alert"])

        slash_x = self.player.centerx + self.attack_dir.x * 10
        slash_y = self.player.centery + self.attack_dir.y * 10
        self.emit_particles(slash_x, slash_y, 6, (232, 232, 224))

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
        slots: list[str | None] = [None] * 8
        slots[0] = "knife" if self.has_knife else None
        slots[1] = "flashlight" if self.has_flashlight else None
        slots[2] = "bandage" if self.bandages > 0 else None
        slots[3] = "key" if self.has_key else None
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
            self.attack_speed_mult = 1.7
            self.choice_result = "arm"
            self.message = "Arm sacrificed: attack speed reduced"
            self.message_timer = 2.2

        self.set_objective_for_area()

    def draw(self) -> None:
        self.draw_atmosphere_back()

        self.draw_world()
        self.draw_entities()
        self.draw_particles()
        self.draw_darkness_overlay()
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

        scaled = pygame.transform.scale(self.canvas, (GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT))

        window_w, window_h = self.screen.get_size()
        view_x = (window_w - GAME_VIEW_WIDTH) // 2
        view_y = (window_h - GAME_VIEW_HEIGHT) // 2
        view_rect = pygame.Rect(view_x, view_y, GAME_VIEW_WIDTH, GAME_VIEW_HEIGHT)

        self.screen.fill((8, 11, 16))
        frame_rect = pygame.Rect(view_x - 8, view_y - 8, GAME_VIEW_WIDTH + 16, GAME_VIEW_HEIGHT + 16)
        pygame.draw.rect(self.screen, (22, 28, 38), frame_rect)
        pygame.draw.rect(self.screen, (62, 78, 96), frame_rect, 2)

        if self.shake_strength > 0:
            ox = int(random.uniform(-self.shake_strength, self.shake_strength) * SCALE)
            oy = int(random.uniform(-self.shake_strength, self.shake_strength) * SCALE)
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

    def draw_intro_overlay(self) -> None:
        if self.intro_timer <= 0 or self.state != "explore":
            return

        fade_t = 1.0
        if self.intro_timer < self.intro_fade_duration:
            fade_t = max(0.0, min(1.0, self.intro_timer / self.intro_fade_duration))
        panel_alpha = int(218 * fade_t)
        text_alpha = int(255 * fade_t)

        panel_w = 274
        panel_h = 112
        x = (INTERNAL_WIDTH - panel_w) // 2
        y = (INTERNAL_HEIGHT - panel_h) // 2 + 8

        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((10, 16, 25, panel_alpha))
        self.canvas.blit(panel, (x, y))
        pygame.draw.rect(self.canvas, (104, 126, 150), pygame.Rect(x, y, panel_w, panel_h), 1)

        title = self.fit_text(self.intro_title, self.big_font, panel_w - 18)
        title_w, _ = self.big_font.size(title)
        self.blit_pixel_text_on(self.canvas, title, x + (panel_w - title_w) // 2, y + 8, self.big_font, (236, 243, 250))

        line_y = y + 30
        for line in self.intro_lines:
            draw_line = self.fit_text(line, self.font, panel_w - 16)
            line_w, _ = self.font.size(draw_line)
            self.blit_pixel_text_on(self.canvas, draw_line, x + (panel_w - line_w) // 2, line_y, self.font, (218, 230, 240))
            line_y += self.font.get_height() + 1

        hint = self.fit_text(self.intro_hint, self.small_font, panel_w - 16)
        hint_w, _ = self.small_font.size(hint)
        self.blit_pixel_text_on(self.canvas, hint, x + (panel_w - hint_w) // 2, y + panel_h - 13, self.small_font, (190, 208, 226))

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
        info_w = 160
        info_h = 28
        info_x = view_rect.right - info_w - 8
        info_y = view_rect.y + 8
        info_surf = pygame.Surface((info_w, info_h), pygame.SRCALPHA)
        info_surf.fill((10, 14, 22, 160))
        self.screen.blit(info_surf, (info_x, info_y))
        pygame.draw.rect(self.screen, (26, 42, 58), pygame.Rect(info_x, info_y, info_w, info_h), 1)
        self.blit_pixel_text_on(self.screen, f"{zone_code}  {zone_name}", info_x + 6, info_y + 2, self.ui_small_font, (58, 90, 122))
        self.blit_pixel_text_on(self.screen, self.objective, info_x + 6, info_y + 14, self.ui_small_font, (90, 122, 154))

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

        player_screen_x = view_rect.x + self.player.centerx * SCALE
        player_screen_y = view_rect.y + self.player.y * SCALE
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
            sx = view_rect.x + cx * SCALE
            sy = view_rect.y + cy * SCALE
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

    def draw_world(self) -> None:
        for y, row in enumerate(self.current_map):
            for x, cell in enumerate(row):
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                color = PALETTE["floor"]
                if (x, y) in self.dark_tiles:
                    color = PALETTE["dark_floor"]
                if cell == "#":
                    color = PALETTE["wall"]
                self.canvas.fill(color, tile_rect)

                # Subtle pixel variation to avoid flat-looking walls/floors.
                if cell != "#" and (x + y) % 3 == 0:
                    self.canvas.fill((color[0] + 6, color[1] + 6, color[2] + 6), pygame.Rect(tile_rect.x + 2, tile_rect.y + 2, 2, 2))
                if cell == "#":
                    pygame.draw.line(self.canvas, (54, 68, 84), (tile_rect.x, tile_rect.y), (tile_rect.right - 1, tile_rect.y))
                    pygame.draw.line(self.canvas, (20, 26, 34), (tile_rect.x, tile_rect.bottom - 1), (tile_rect.right - 1, tile_rect.bottom - 1))

        for door in self.current_doors:
            dx, dy = door["tile"]
            door_rect = pygame.Rect(dx * TILE_SIZE, dy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            locked = self.is_door_locked(door)
            fill = (92, 70, 60) if locked else (72, 94, 116)
            border = (214, 126, 96) if locked else (138, 178, 228)
            self.canvas.fill(fill, door_rect)
            pygame.draw.rect(self.canvas, border, door_rect, 1)
            pulse = int((math.sin(self.time_alive * 2.7) + 1.0) * 0.5 * 26)
            light_col = (208 + pulse // 2, 74, 74) if locked else (98, 202 + pulse // 3, 158)
            self.canvas.fill(light_col, pygame.Rect(door_rect.x + 6, door_rect.y + 6, 3, 3))

        if self.current_area == "final" and self.final_exit_tile != (0, 0):
            final_rect = pygame.Rect(self.final_exit_tile[0] * TILE_SIZE, self.final_exit_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            col = PALETTE["exit"] if self.final_exit_unlocked else (52, 64, 86)
            self.canvas.fill(col, final_rect)
            pulse = int((math.sin(self.time_alive * 2.1) + 1.0) * 0.5 * 36)
            border_col = (120 + pulse, 170 + pulse // 2, 255) if self.final_exit_unlocked else (92, 104, 122)
            pygame.draw.rect(self.canvas, border_col, final_rect, 1)

        if self.current_area == "area2":
            for laser in self.lasers:
                active = self.laser_is_active(laser)
                col = (220, 62, 62) if active else (90, 50, 50)
                if self.area2_cleared:
                    col = (50, 86, 104)
                self.canvas.fill(col, laser.rect)
                if active:
                    self.canvas.fill((255, 170, 170), pygame.Rect(laser.rect.x, laser.rect.y, max(1, laser.rect.width), 1))

        for (tx, ty), kind in self.furniture.items():
            item_rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if kind == "desk":
                self.canvas.fill((86, 70, 60), item_rect)
                self.canvas.fill((40, 46, 56), pygame.Rect(item_rect.x + 2, item_rect.y + 3, 12, 7))
            elif kind == "cabinet":
                self.canvas.fill((76, 74, 80), item_rect)
                self.canvas.fill((180, 170, 136), pygame.Rect(item_rect.x + 11, item_rect.y + 7, 2, 2))
            elif kind == "bed":
                self.canvas.fill((82, 62, 56), item_rect)
                self.canvas.fill((185, 185, 175), pygame.Rect(item_rect.x + 1, item_rect.y + 2, 14, 9))
            elif kind == "freezer":
                self.canvas.fill((70, 88, 104), item_rect)
                pygame.draw.rect(self.canvas, (136, 170, 198), item_rect, 1)
                freezer_key = (self.current_area, tx, ty)
                charges = self.freezer_charges.get(freezer_key, 0)
                light_col = (88, 220, 160) if charges > 0 else (120, 128, 138)
                self.canvas.fill(light_col, pygame.Rect(item_rect.x + 6, item_rect.y + 3, 4, 4))
            else:
                self.canvas.fill((95, 78, 66), item_rect)

        if self.current_area == "maintenance" and self.breaker_tile != (0, 0):
            br = pygame.Rect(self.breaker_tile[0] * TILE_SIZE, self.breaker_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            self.canvas.fill((70, 84, 98), br)
            light_col = (80, 210, 140) if self.area2_cleared else (220, 170, 70)
            self.canvas.fill(light_col, pygame.Rect(br.x + 5, br.y + 4, 6, 6))

        if self.current_area == "area3" and self.elevator_terminal_tile != (0, 0):
            tr = pygame.Rect(self.elevator_terminal_tile[0] * TILE_SIZE, self.elevator_terminal_tile[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            self.canvas.fill((68, 74, 88), tr)
            light_col = (80, 210, 140) if self.elevator_choice_made else (210, 92, 92)
            self.canvas.fill(light_col, pygame.Rect(tr.x + 5, tr.y + 4, 6, 6))

    def draw_entities(self) -> None:
        if self.can_reveal_pickups():
            for pickup in self.pickups:
                if not self.is_pickup_in_flashlight_range(pickup):
                    continue
                color_name = {
                    "key": "key",
                    "battery": "battery",
                    "bandage": "bandage",
                    "flashlight": "flashlight",
                    "knife": "door",
                }.get(pickup.name, "bandage")
                self.draw_pickup_icon(pickup.rect, pickup.name, PALETTE[color_name], self.sprite_cache.get(pickup.name))

        for wolf in self.wolves:
            if not wolf.alive:
                continue
            self.draw_wolf_sprite(wolf)

        self.draw_player_sprite()

    def draw_darkness_overlay(self) -> None:
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 6, 10, 120))

        tile_x = self.player.centerx // TILE_SIZE
        tile_y = self.player.centery // TILE_SIZE
        in_dark_zone = (tile_x, tile_y) in self.dark_tiles

        if self.flashlight_on and self.battery > 0:
            radius = 56 if self.battery > 20 else 46
            center = (self.player.centerx, self.player.centery)
            for i in range(4):
                pygame.draw.circle(overlay, (0, 0, 0, max(0, 75 - i * 24)), center, radius + i * 10)
            pygame.draw.circle(overlay, (0, 0, 0, 0), center, radius)
        elif in_dark_zone:
            radius = 18
            center = (self.player.centerx, self.player.centery)
            pygame.draw.circle(overlay, (0, 0, 0, 0), center, radius)

        self.canvas.blit(overlay, (0, 0))

    def draw_inventory_overlay(self) -> None:
        # Dark scrim behind the panel
        scrim = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        scrim.fill((0, 0, 0, 128))
        self.canvas.blit(scrim, (0, 0))

        panel = pygame.Surface((236, 138), pygame.SRCALPHA)
        panel.fill((11, 16, 24, 240))
        px = (INTERNAL_WIDTH - panel.get_width()) // 2
        py_base = (INTERNAL_HEIGHT - panel.get_height()) // 2
        py = int(py_base + (1.0 - self.inventory_anim) * 24)
        panel.set_alpha(int(240 * self.inventory_anim))
        self.canvas.blit(panel, (px, py))
        pygame.draw.rect(self.canvas, (122, 142, 162), pygame.Rect(px, py, 236, 138), 1)
        pygame.draw.rect(self.canvas, (65, 80, 98), pygame.Rect(px + 2, py + 2, 232, 134), 1)

        self.blit_pixel_text_centered("ITEMS", pygame.Rect(px + 8, py + 4, 220, 12), self.inventory_title_font)
        self.blit_pixel_text_centered("TAB/ESC CLOSE", pygame.Rect(px + 8, py + 17, 220, 11), self.inventory_font)

        slots = self.get_inventory_slots()
        for idx, item in enumerate(slots):
            row = idx // self.inventory_cols
            col = idx % self.inventory_cols
            sx = px + 16 + col * 52
            sy = py + 36 + row * 42
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
                self.blit_pixel_text_centered(item.upper(), pygame.Rect(sx + 2, sy + 20, slot_rect.width - 4, 9), self.inventory_small_font)
                if item == "bandage":
                    self.blit_pixel_text(str(self.bandages), sx + 34, sy + 1, self.inventory_small_font)

        # Description panel
        selected_item = slots[self.inventory_selected] if self.inventory_selected < len(slots) else None
        desc_text = self.ITEM_DESCRIPTIONS.get(selected_item, "Empty slot") if selected_item else "Empty slot"
        desc_rect = pygame.Rect(px + 12, py + 102, 212, 14)
        self.draw_panel(desc_rect, (16, 20, 28), (50, 62, 78))
        self.blit_pixel_text_centered(desc_text, pygame.Rect(desc_rect.x + 4, desc_rect.y + 2, desc_rect.width - 8, desc_rect.height - 4), self.inventory_font)

        footer = pygame.Rect(px + 10, py + 122, 216, 12)
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
        self.blit_text_shadow("Attack speed 1.0s -> 1.7s (+70%)", px + 14, py + 78, text_w)

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
        else:
            self.canvas.fill(color, pygame.Rect(rect.x + 2, rect.y + 2, 5, 4))
            self.canvas.fill((240, 240, 240), pygame.Rect(rect.x + 4, rect.y + 3, 1, 2))

    def draw_wolf_sprite(self, wolf: Wolf) -> None:
        body = wolf.rect
        sprite = self.sprite_cache.get("wolf")
        if sprite is not None:
            draw_x = body.centerx - sprite.get_width() // 2
            draw_y = body.bottom - sprite.get_height() + 1
            self.canvas.blit(sprite, (draw_x, draw_y))
            if wolf.alert:
                self.canvas.fill((220, 80, 80), pygame.Rect(draw_x + 11, draw_y + 5, 2, 2), special_flags=pygame.BLEND_ADD)
            return

        color = PALETTE["wolf_alert"] if wolf.alert else PALETTE["wolf"]
        self.canvas.fill((10, 14, 20), pygame.Rect(body.x + 1, body.y + 11, 10, 2))
        self.canvas.fill(color, pygame.Rect(body.x + 2, body.y + 3, 8, 7))
        self.canvas.fill((220, 220, 220), pygame.Rect(body.x + 9, body.y + 4, 2, 2))
        eye_col = (240, 90, 90) if wolf.alert else (220, 220, 220)
        self.canvas.fill(eye_col, pygame.Rect(body.x + 9, body.y + 5, 1, 1))

    def draw_player_sprite(self) -> None:
        base = self.player
        player_color = PALETTE["player_hurt"] if self.damage_flash > 0 else PALETTE["player"]
        moving = self.player_vel.length() > 8.0
        stride = int(math.sin(self.walk_cycle * 7.4) * 2) if moving else 0
        bob = int(abs(math.sin(self.walk_cycle * 7.4)) * 1.4) if moving else 0

        facing = self.last_dir if self.last_dir.length_squared() > 0 else pygame.Vector2(1, 0)
        facing = facing.normalize()

        head_y = base.y + 1 - bob
        torso_y = base.y + 5 - bob
        leg_y = base.y + 9

        # Grounded shadow keeps movement readable.
        self.canvas.fill((10, 14, 20), pygame.Rect(base.x + 1, base.y + 11, 8, 2))

        # Legs animate with stride to show walking direction.
        self.canvas.fill((42, 52, 68), pygame.Rect(base.x + 2 + stride, leg_y, 2, 3))
        self.canvas.fill((42, 52, 68), pygame.Rect(base.x + 6 - stride, leg_y, 2, 3))

        self.canvas.fill(player_color, pygame.Rect(base.x + 1, torso_y, 8, 5))
        self.canvas.fill((141, 96, 75), pygame.Rect(base.x + 2, head_y, 6, 4))

        arm_y = torso_y + 1
        self.canvas.fill((126, 84, 66), pygame.Rect(base.x + 1, arm_y, 1, 3))
        self.canvas.fill((126, 84, 66), pygame.Rect(base.x + 8, arm_y, 1, 3))

        eye_col = (236, 236, 232)
        if abs(facing.x) > abs(facing.y):
            eye_x = base.x + (6 if facing.x > 0 else 3)
            self.canvas.fill(eye_col, pygame.Rect(eye_x, head_y + 2, 1, 1))
            self.canvas.fill(eye_col, pygame.Rect(eye_x, head_y + 3, 1, 1))
        elif facing.y < 0:
            self.canvas.fill(eye_col, pygame.Rect(base.x + 3, head_y + 1, 1, 1))
            self.canvas.fill(eye_col, pygame.Rect(base.x + 6, head_y + 1, 1, 1))
        else:
            self.canvas.fill(eye_col, pygame.Rect(base.x + 3, head_y + 3, 1, 1))
            self.canvas.fill(eye_col, pygame.Rect(base.x + 6, head_y + 3, 1, 1))

        if self.attack_anim > 0:
            t = 1.0 - (self.attack_anim / max(0.001, self.attack_duration))
            swing = math.sin(t * math.pi)
            start = pygame.Vector2(base.centerx, torso_y + 2)
            swing_dir = self.attack_dir if self.attack_dir.length_squared() > 0 else facing
            tip = start + swing_dir * (5.0 + swing * 5.0)
            knife_tip = tip + swing_dir * 2.2
            pygame.draw.line(self.canvas, (220, 224, 232), (int(start.x), int(start.y)), (int(tip.x), int(tip.y)))
            pygame.draw.line(self.canvas, (245, 245, 238), (int(tip.x), int(tip.y)), (int(knife_tip.x), int(knife_tip.y)))
            spark = knife_tip + pygame.Vector2(-swing_dir.y, swing_dir.x) * 1.2
            self.canvas.fill((250, 248, 212), pygame.Rect(int(spark.x), int(spark.y), 1, 1))

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
        # Vertical gradient builds mood and separates play-space from UI layers.
        for y in range(INTERNAL_HEIGHT):
            t = y / INTERNAL_HEIGHT
            r = int(7 + 12 * t)
            g = int(10 + 14 * t)
            b = int(17 + 20 * t)
            pygame.draw.line(self.canvas, (r, g, b), (0, y), (INTERNAL_WIDTH, y))

    def draw_atmosphere_front(self) -> None:
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

        self.canvas.blit(vignette, (0, 0))


def main() -> None:
    game = Game()
    game.run()
