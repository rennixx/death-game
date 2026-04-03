from pathlib import Path

import pygame


def save(surface: pygame.Surface, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, str(path))


def main() -> None:
    pygame.init()
    root = Path("assets/art")

    player = pygame.Surface((16, 16), pygame.SRCALPHA)
    player.fill((0, 0, 0, 0))
    player.fill((12, 16, 24), (3, 14, 10, 1))
    player.fill((121, 86, 64), (6, 2, 4, 1))
    player.fill((160, 112, 88), (5, 3, 6, 4))
    player.fill((24, 28, 36), (6, 4, 1, 1))
    player.fill((24, 28, 36), (9, 4, 1, 1))
    player.fill((180, 135, 107), (4, 7, 8, 5))
    player.fill((145, 102, 80), (4, 10, 8, 2))
    player.fill((202, 166, 140), (6, 12, 2, 2))
    player.fill((202, 166, 140), (8, 12, 2, 2))
    pygame.draw.rect(player, (34, 44, 58), player.get_rect(), 1)
    save(player, root / "characters/player/char_player_idle_f01.png")

    wolf = pygame.Surface((16, 16), pygame.SRCALPHA)
    wolf.fill((0, 0, 0, 0))
    wolf.fill((10, 14, 20), (3, 14, 11, 1))
    wolf.fill((84, 92, 98), (5, 5, 8, 6))
    wolf.fill((128, 139, 145), (4, 6, 6, 4))
    wolf.fill((170, 182, 190), (6, 6, 3, 2))
    wolf.fill((228, 228, 228), (12, 7, 2, 1))
    wolf.fill((236, 90, 90), (12, 7, 1, 1))
    wolf.fill((54, 60, 66), (3, 10, 2, 2))
    wolf.fill((54, 60, 66), (9, 10, 2, 2))
    pygame.draw.rect(wolf, (26, 30, 36), wolf.get_rect(), 1)
    save(wolf, root / "characters/wolves/char_wolf_patrol_f01.png")

    key = pygame.Surface((8, 8), pygame.SRCALPHA)
    key.fill((0, 0, 0, 0))
    pygame.draw.circle(key, (226, 190, 69), (2, 3), 2)
    key.fill((226, 190, 69), (4, 2, 3, 2))
    key.fill((226, 190, 69), (6, 4, 1, 1))
    key.fill((255, 230, 145), (1, 2, 2, 1))
    save(key, root / "items/item_key_a01.png")

    battery = pygame.Surface((8, 8), pygame.SRCALPHA)
    battery.fill((0, 0, 0, 0))
    battery.fill((92, 159, 179), (2, 1, 4, 6))
    battery.fill((215, 215, 204), (3, 0, 2, 1))
    battery.fill((130, 200, 215), (3, 2, 1, 3))
    battery.fill((63, 105, 118), (5, 2, 1, 4))
    save(battery, root / "items/item_battery_a01.png")

    bandage = pygame.Surface((8, 8), pygame.SRCALPHA)
    bandage.fill((0, 0, 0, 0))
    bandage.fill((215, 215, 204), (1, 2, 6, 4))
    bandage.fill((236, 170, 140), (3, 3, 2, 2))
    bandage.fill((190, 190, 180), (2, 2, 1, 4))
    bandage.fill((190, 190, 180), (5, 2, 1, 4))
    bandage.fill((245, 245, 235), (2, 2, 3, 1))
    save(bandage, root / "items/item_bandage_a01.png")

    flashlight = pygame.Surface((8, 8), pygame.SRCALPHA)
    flashlight.fill((0, 0, 0, 0))
    flashlight.fill((110, 157, 93), (1, 3, 5, 2))
    flashlight.fill((216, 216, 200), (6, 3, 1, 2))
    flashlight.fill((75, 110, 64), (2, 2, 2, 1))
    flashlight.fill((145, 188, 121), (1, 3, 2, 1))
    save(flashlight, root / "items/item_flashlight_a01.png")

    print("Created starter sprite assets.")


if __name__ == "__main__":
    main()
