################################################
# Imports
################################################

from __future__ import annotations
import random
import config
from animals import Predator, Prey
from grass_array import GrassArray

################################################
# Simulation Setup and Update Functions
################################################

def setup_simulation() -> tuple[list[Predator], list[Prey], GrassArray]:
    """Initialize the simulation with predators, prey, and grass.
    
    Creates the initial population of predators and prey at random positions
    within the simulation boundaries, and initializes the grass grid.
    
    Returns:
        A tuple containing:
            - List of Predator objects
            - List of Prey objects
            - GrassArray for efficient grass management
    """
    predators = [Predator(random.uniform(0, config.WORLD_WIDTH), random.uniform(0, config.WORLD_HEIGHT)) for _ in range(config.NUM_PREDATORS)]
    preys = [Prey(random.uniform(0, config.WORLD_WIDTH), random.uniform(0, config.WORLD_HEIGHT)) for _ in range(config.NUM_PREYS)]
    
    # Initialize grass array (much faster than dict of objects)
    cols = config.WORLD_WIDTH // config.CHUNKSIZE
    rows = config.WORLD_HEIGHT // config.CHUNKSIZE
    grass = GrassArray(cols, rows)
    
    # Initialize total grass tracking
    config.total_grass = grass.get_total()
    
    return predators, preys, grass

def update_simulation(
    predators: list[Predator],
    preys: list[Prey],
    grass: GrassArray
) -> None:
    """Advance the simulation by one tick.
    
    Updates all animals and grass, removes dead animals, handles reproduction,
    and records statistics history.
    
    Args:
        predators: List of predator objects to update (modified in place).
        preys: List of prey objects to update (modified in place).
        grass: GrassArray for grass management.
    """
    # Update animals - pass separate lists to avoid isinstance() calls
    for p in predators:
        p.update(predators, preys, grass)
    for p in preys:
        p.update(predators, grass)
        
    # Count deaths before removal
    preys_before = len(preys)
    predators_before = len(predators)
    
    # Remove dead animals (using the original separate lists)
    predators[:] = [p for p in predators if p.alive]
    preys[:] = [p for p in preys if p.alive]
    
    config.predator_deceased += (predators_before - len(predators))
    config.prey_deceased += (preys_before - len(preys))
    
    # Reproduction: Preys still reproduce randomly
    new_preys = []
    for p in preys:
        if random.random() < config.PREY_REPRODUCTION_RATE:
            new_preys.append(Prey(p.x, p.y))
            config.prey_born += 1
    preys.extend(new_preys)
    
    # Reproduction: Predators now reproduce only if they killed a prey
    new_predators = []
    for p in predators:
        if p.killed:
            rand_x_dist = random.uniform(10, 15)*random.choice([-1, 1])
            rand_y_dist = random.uniform(10, 15)*random.choice([-1, 1])
            new_predators.append(Predator(p.x + rand_x_dist, p.y + rand_y_dist))
            config.predator_born += 1
            p.killed = False  # Reset flag after reproduction
    predators.extend(new_predators)
    
    # Increment simulation round
    config.rounds_passed += 1

    # Update all grass in one vectorized operation (MUCH faster than individual updates)
    grass_growth = grass.update()
    config.total_grass += grass_growth

    # Update stats history (using the updated separate lists)
    config.stats_history["Prey Count"].append(len(preys))
    config.stats_history["Predator Count"].append(len(predators))
    config.stats_history["Grass Total"].append(config.total_grass)
    config.stats_history["Prey deceased"].append(config.prey_deceased)
    config.stats_history["Predator deceased"].append(config.predator_deceased)
    config.stats_history["Prey born"].append(config.prey_born)
    config.stats_history["Predator born"].append(config.predator_born)
    config.stats_history["Rounds passed"].append(config.rounds_passed)