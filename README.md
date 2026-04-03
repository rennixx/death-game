# Escape Room (Prototype)

A playable first implementation of the Escape Room concept using Python and pygame.

## Setup

```powershell
python -m pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Controls

- `WASD`: Move
- `E`: Interact (doors)
- `Q`: Toggle flashlight
- `SPACE`: Strike (neutralize wolves)
- `TAB`: Open/close inventory
- `H`: Use bandage (in inventory)
- `1` / `2`: Choose elevator dilemma option

## Current Playable Features

- Exploration state and inventory state
- Tile collisions and blocked locked door
- Auto pickup for key, battery, bandage, flashlight
- Trap damage and wolf enemy damage
- Flashlight + battery drain in dark area
- Elevator dilemma with persistent consequence
- Sleep Meter style health HUD and objective strip
- Exit condition after clearing wolves

## Next Suggested Coding Steps

- Replace placeholder shapes with real pixel sprites from `assets/art`
- Split world into separate level files (`.tmx`) and add camera dead-zone
- Add proper enemy AI states and attack telegraph timing
- Add audio integration and hit/alert feedback polish
