# Level 2 — Design Document

## Overview

Level 2 is a vertical descent through a multi-floor structure, guiding the player from Floor 4 down to Floor 1. Each floor introduces a distinct gameplay mechanic — resource acquisition, darkness/battery management, stealth, and a climactic boss encounter — culminating in a final sprint through a flooded basement.

---

## Floor 4: The Start Room & The Flickering Hallway

### The Start Room (Safe Zone)
Before entering the main hallway, the player drops into a secure stairwell landing or maintenance closet. Sitting directly under a spotlight is a discarded backpack. Interacting with it populates the player's inventory and activates the HUD, granting them:

- **Flashlight**
- **Knife**
- **Bandages**

### The Hallway Environment
Once the player opens the door to leave the Start Room, they enter a long, dimly lit hallway. Overhead fluorescent lights flicker randomly.

### The Obstacle
Halfway down, a collapsed ceiling blocks the main hall. The player must detour by walking into an open side office, navigating through overturned desks, and exiting through a connecting door further down the hall.

### Enemies — Stray Wolves
- 1–2 standard wolves pacing and patrolling the open sections of the hallway.

### Exit
A stairwell door at the far right end of the hallway.

---

## Floor 3: The Dark Ward (Resource Drain)

### Environment
The power is completely cut. It is pitch black. The player must use their flashlight to see, draining their limited battery.

### Enemies — Stalker Wolves
These wolves hunt in the dark with special behavior:

- **Flashlight off** → wolves sprint directly at the player.
- **Flashlight on (beam hits wolf)** → wolf flinches, speed drops by 90%, and it attempts to slowly strafe out of the beam.
- The player must keep the beam on the wolf while backpedaling to safety.

### Objective
The stairwell at the end is electronically locked. The player must search the labyrinth of pitch-black side rooms to find a hidden **keycard** to unlock it.

---

## Floor 2: The Trap Floor (Stealth & Hazards)

### Environment
An industrial maintenance level. The lights are on, but the floor is littered with environmental hazards:

- Tripwires
- Alarms
- Crumbling floor panels

### Enemies — Hunter Wolves
- These wolves have a visible **cone of vision** (represented by glowing eyes cutting through the dim light).
- If the player steps into that cone, the wolf immediately charges.

### The Action
The player must use open side rooms to duck out of the main hallway, hide in the shadows until the wolf trots past, and then slip back out to continue moving right.

### Exit
A rusted metal grate at the far right end. The player must interact with it to pry it open with their knife.

---

## Floor 1: The Basement Sprint (The Climax)

### Environment
A flooded, overgrown basement hallway. There are no side rooms — just one wide, long horizontal stretch.

### Encounter — The Alpha Wolf
As the player walks down the final stretch, a massive Alpha Wolf steps out of the shadows.

- **High HP** and a **large hit radius**.
- The player must use precise spacing — stepping in to slash with the knife and backing up to avoid the bite.
- Whatever bandages and battery the player conserved will be critical here.

### Finish
Reaching the heavy steel door at the far right end of the hall concludes Level 2.

---

## Architecture Requirements for Level 2 Floor Generation

### 1. Single-Map Loading
Load the entire floor (hallway, side rooms, items, and enemies) simultaneously as one massive continuous 2D coordinate grid/tilemap. Do not use chunk loading or individual scene files for different rooms.

### 2. Seamless Side Rooms
The side rooms attached to the main hallway must not have interactive doors or loading screen transitions. They are simply physical extensions of the main map.

### 3. Collision Map Gaps
Implement the entrances to the side rooms as open gaps in the wall collision data. The player should be able to walk seamlessly off the hallway tiles and onto the room tiles using standard movement.

### 4. Unrestricted AI Pathfinding
Because the hallway and side rooms share the same navigation mesh/grid, enemy AI must be able to track and pursue the player continuously from the main hallway directly into the side rooms without breaking aggro due to map boundaries.
