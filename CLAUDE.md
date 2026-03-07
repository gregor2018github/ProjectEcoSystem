# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the simulation:**
```bash
source eco_envi/Scripts/activate  # Windows venv activation via bash
python main.py
```

**Install dependencies:**
```bash
pip install -r requirements.txt
# Dependencies: pygame, numpy
```

**Profile performance:**
```bash
python -m cProfile -o profile.prof main.py
snakeviz profile.prof  # installed in venv
```

There are no tests in this project.

## Architecture

This is a real-time predator-prey ecosystem simulation using Pygame and NumPy. The world is larger than the viewport (controlled by `WORLD_SIZE_MULTIPLIER`) and supports camera panning with WASD/arrow keys.

### Core data flow (per frame)

```
main.py game loop
  -> process_event()     (event_handler.py) — input, buttons, hover/click on animals
  -> update_simulation() (simulation.py)    — advance world state one tick
  -> draw_simulation()   (ui.py)            — render everything
```

### Key files

| File | Role |
|------|------|
| `config.py` | All tunable constants and global mutable state (camera pos, stats counters, `stats_history`) |
| `animals.py` | `Animal` ABC, `Predator` and `Prey` subclasses with per-instance evolutionary traits |
| `simulation.py` | `setup_simulation()` and `update_simulation()` — runs AI, handles death, reproduction, and trait inheritance |
| `grass_array.py` | `GrassArray` — NumPy 2D array replacing per-object `Grass` instances; vectorized growth and rendering |
| `spatial_hash.py` | Generic `SpatialHash[T]` — O(1) proximity queries used for hunting, fleeing, and mating |
| `ui.py` | All rendering: grass, animals, stats overlay, buttons, minimap, hover windows |
| `event_handler.py` | Pygame event dispatch, button actions, hover/lock logic for animal info windows |
| `hover_window.py` | Draws per-animal info popup (status, food, age, traits, etc.) |
| `statistics_window.py` | Separate Pygame window with population graphs, phase diagram, and trait table |
| `settings_window.py` | In-simulation settings editor (scrollable, with cursor blink and arrow-key editing) |
| `start_screen.py` | Pre-simulation configuration screen (world size, FPS, initial populations) |

### Evolutionary system

Each `Predator` and `Prey` instance holds its own copy of all evolutionary traits (speed, smell/fear distance, energy costs, max age, etc.) initialized from `config.py` defaults. When two animals mate, `inherit_traits(partner)` creates a child with:

```
child_trait = random(min(p1, p2), max(p1, p2)) ± random(0, MUTATION_RATE) × config_base_value
```

Using the config base value for mutation magnitude prevents multiplicative drift across generations.

### Performance design

- `GrassArray` uses a NumPy array for all grass; growth is a single vectorized `+=` + `clip`. Rendering builds a pixel array via a pre-computed color LUT and blits one scaled surface per frame.
- Two pre-allocated `SpatialHash` instances (one for predators, one for prey) are rebuilt each tick via `build_from_list()` and reused for all proximity queries (hunting, avoidance, mating).
- Animals only draw themselves when within the screen viewport bounds.
- The statistics window uses `UPDATE_SPEED_*` constants to throttle expensive graph/table redraws.

### Config as global state

`config.py` doubles as both constants and mutable global state. Simulation counters (`prey_born`, `predator_deceased`, etc.), `stats_history` dict, camera position (`camera_x`, `camera_y`), and `current_fps` are all module-level variables in `config.py` that are read/written throughout the codebase. Settings changed at runtime (via the settings window) write directly into `config.*` variables.
