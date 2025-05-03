import random
from config import *
from animals import Predator, Prey
from grass import Grass

# Simulation setup: initialize grass grid
def setup_simulation():
    predators = [Predator(random.uniform(0, XLIM), random.uniform(0, YLIM)) for _ in range(NUM_PREDATORS)]
    preys = [Prey(random.uniform(0, XLIM), random.uniform(0, YLIM)) for _ in range(NUM_PREYS)]
    # Initialize grass chunks
    grass = {}
    cols = XLIM // CHUNKSIZE
    rows = YLIM // CHUNKSIZE
    for i in range(cols):
        for j in range(rows):
            grass[(i, j)] = Grass()
    return predators, preys, grass

def update_simulation(predators, preys, grass):
    global prey_deceased, predator_deceased, prey_born, predator_born, rounds_passed
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
    predator_deceased += (predators_before - len(predators))
    prey_deceased += (preys_before - len(preys))
    # Reproduction: Preys still reproduce randomly
    new_preys = []
    for p in preys:
        if random.random() < PREY_REPRODUCTION_RATE:
            new_preys.append(Prey(p.x, p.y))
            prey_born += 1
    preys.extend(new_preys)
    # Reproduction: Predators now reproduce only if they killed a prey
    new_predators = []
    for p in predators:
        if p.killed:
            rand_x_dist = random.uniform(10, 15)*random.choice([-1, 1])
            rand_y_dist = random.uniform(10, 15)*random.choice([-1, 1])
            new_predators.append(Predator(p.x + rand_x_dist, p.y + rand_y_dist))
            predator_born += 1
            p.killed = False  # Reset flag after reproduction
    predators.extend(new_predators)
    # Increment simulation round
    rounds_passed += 1

    # NEW: Compute total grass and append historic value
    total_grass = sum(g.amount for g in grass.values())

    stats_history["Prey Count"].append(len(preys))
    stats_history["Predator Count"].append(len(predators))
    stats_history["Grass Total"].append(total_grass)
    stats_history["Prey deceased"].append(prey_deceased)
    stats_history["Predator deceased"].append(predator_deceased)
    stats_history["Prey born"].append(prey_born)
    stats_history["Predator born"].append(predator_born)
    stats_history["Rounds passed"].append(rounds_passed)