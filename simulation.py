import random
import config
from animals import Predator, Prey
from grass import Grass

# Simulation setup: initialize grass grid
def setup_simulation():
    predators = [Predator(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)) for _ in range(config.NUM_PREDATORS)]
    preys = [Prey(random.uniform(0, config.XLIM), random.uniform(0, config.YLIM)) for _ in range(config.NUM_PREYS)]
    # Initialize grass chunks
    grass = {}
    cols = config.XLIM // config.CHUNKSIZE
    rows = config.YLIM // config.CHUNKSIZE
    for i in range(cols):
        for j in range(rows):
            grass[(i, j)] = Grass()
    return predators, preys, grass

def update_simulation(predators, preys, grass):
    # Update animals
    for p in predators:
        p.update(preys, grass)
    for p in preys:
        p.update(predators, grass)
    # Update grass chunks
    for g in grass.values():
        g.update()
    # Count deaths before removal
    preys_before = len(preys)
    predators_before = len(predators)
    # Remove dead animals
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

    # Compute total grass and append historic value
    total_grass = sum(g.amount for g in grass.values())

    config.stats_history["Prey Count"].append(len(preys))
    config.stats_history["Predator Count"].append(len(predators))
    config.stats_history["Grass Total"].append(total_grass)
    config.stats_history["Prey deceased"].append(config.prey_deceased)
    config.stats_history["Predator deceased"].append(config.predator_deceased)
    config.stats_history["Prey born"].append(config.prey_born)
    config.stats_history["Predator born"].append(config.predator_born)
    config.stats_history["Rounds passed"].append(config.rounds_passed)