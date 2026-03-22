################################################
# Imports
################################################

from __future__ import annotations
import random
import config
from animal_arrays import PredatorArrays, PreyArrays
from grass_array import GrassArray
from vectorized_update import (
    update_predators, update_prey,
    process_deaths, process_reproduction,
)

################################################
# Simulation Setup and Update Functions
################################################

def setup_simulation() -> tuple[PredatorArrays, PreyArrays, GrassArray]:
    """Initialize the simulation with predators, prey, and grass.

    Returns:
        A tuple containing:
            - PredatorArrays (SoA)
            - PreyArrays (SoA)
            - GrassArray for efficient grass management
    """
    pred = PredatorArrays(max(256, config.NUM_PREDATORS * 2))
    prey = PreyArrays(max(1024, config.NUM_PREYS * 2))

    for _ in range(config.NUM_PREDATORS):
        pred.add_default(
            random.uniform(0, config.WORLD_WIDTH),
            random.uniform(0, config.WORLD_HEIGHT),
        )
    for _ in range(config.NUM_PREYS):
        prey.add_default(
            random.uniform(0, config.WORLD_WIDTH),
            random.uniform(0, config.WORLD_HEIGHT),
        )

    # Initialize grass array
    cols = int(config.WORLD_WIDTH // config.CHUNKSIZE)
    rows = int(config.WORLD_HEIGHT // config.CHUNKSIZE)
    grass = GrassArray(cols, rows)

    config.total_grass = grass.get_total()

    return pred, prey, grass


def update_simulation(
    pred: PredatorArrays,
    prey: PreyArrays,
    grass: GrassArray,
) -> None:
    """Advance the simulation by one tick using vectorized operations.

    Args:
        pred: PredatorArrays SoA (modified in place).
        prey: PreyArrays SoA (modified in place).
        grass: GrassArray for grass management.
    """
    # Vectorized animal updates
    update_predators(pred, prey, grass)
    update_prey(pred, prey, grass)

    # Count and remove dead animals
    pred_deaths, prey_deaths = process_deaths(pred, prey)
    config.predator_deceased += pred_deaths
    config.prey_deceased += prey_deaths

    # Reproduction
    process_reproduction(pred, prey)

    # Increment round
    config.rounds_passed += 1

    # Vectorized grass update
    grass.update()
    config.total_grass = grass.get_total()

    # Update stats history
    config.stats_history["Prey Count"].append(prey.count)
    config.stats_history["Predator Count"].append(pred.count)
    config.stats_history["Grass Total"].append(config.total_grass)
    config.stats_history["Prey deceased"].append(config.prey_deceased)
    config.stats_history["Predator deceased"].append(config.predator_deceased)
    config.stats_history["Prey born"].append(config.prey_born)
    config.stats_history["Predator born"].append(config.predator_born)
    config.stats_history["Rounds passed"].append(config.rounds_passed)
    config.stats_history["Prey dead by hunting"].append(config.prey_dead_by_hunting)
    config.stats_history["Prey dead by starvation"].append(config.prey_dead_by_starvation)
    config.stats_history["Predator dead by starvation"].append(config.predator_dead_by_starvation)
    config.stats_history["Prey dead by age"].append(config.prey_dead_by_age)
    config.stats_history["Predator dead by age"].append(config.predator_dead_by_age)
