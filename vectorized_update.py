###############################################
# Vectorized simulation update functions
# Replaces per-animal Python loops with bulk
# NumPy operations for 5-15x speedup.
###############################################

from __future__ import annotations
import numpy as np
import random
import config
from animal_arrays import PredatorArrays, PreyArrays, _alloc_uid
from grass_array import GrassArray


def _find_nearest_chunked(
    src_x: np.ndarray, src_y: np.ndarray, src_count: int,
    tgt_x: np.ndarray, tgt_y: np.ndarray, tgt_count: int,
    max_dist: float,
) -> tuple[np.ndarray, np.ndarray]:
    """For each source entity, find the nearest target within max_dist.

    Returns (nearest_idx, nearest_dist_sq) arrays of length src_count.
    nearest_idx[i] = -1 if no target found within range.
    Uses chunked processing to avoid N×M memory explosion.
    """
    CHUNK = 256
    nearest_idx = np.full(src_count, -1, dtype=np.int32)
    nearest_dist_sq = np.full(src_count, np.inf, dtype=np.float32)
    max_dist_sq = np.float32(max_dist * max_dist)

    sx = src_x[:src_count]
    sy = src_y[:src_count]

    for start in range(0, tgt_count, CHUNK):
        end = min(start + CHUNK, tgt_count)
        tx = tgt_x[start:end]
        ty = tgt_y[start:end]

        # (src_count, chunk_size) distance matrices
        dx = tx[np.newaxis, :] - sx[:, np.newaxis]
        dy = ty[np.newaxis, :] - sy[:, np.newaxis]
        dist_sq = dx * dx + dy * dy

        # Mask out-of-range
        dist_sq[dist_sq > max_dist_sq] = np.inf

        # Per-source minimum in this chunk
        chunk_min_idx = np.argmin(dist_sq, axis=1)
        chunk_min_dist = dist_sq[np.arange(src_count), chunk_min_idx]

        # Update global nearest
        better = chunk_min_dist < nearest_dist_sq
        nearest_idx[better] = chunk_min_idx[better] + start
        nearest_dist_sq[better] = chunk_min_dist[better]

    return nearest_idx, nearest_dist_sq


def _sum_repulsion_vectors(
    src_x: np.ndarray, src_y: np.ndarray, src_count: int,
    tgt_x: np.ndarray, tgt_y: np.ndarray, tgt_count: int,
    max_dist_per_src: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """For each source, sum normalized repulsion vectors from all targets within range.

    max_dist_per_src: per-source maximum distance (length src_count).
    Returns (repulse_dx, repulse_dy) of shape (src_count,).
    """
    CHUNK = 256
    repulse_dx = np.zeros(src_count, dtype=np.float32)
    repulse_dy = np.zeros(src_count, dtype=np.float32)

    sx = src_x[:src_count]
    sy = src_y[:src_count]
    max_dist_sq = max_dist_per_src ** 2

    for start in range(0, tgt_count, CHUNK):
        end = min(start + CHUNK, tgt_count)
        tx = tgt_x[start:end]
        ty = tgt_y[start:end]

        # (src_count, chunk_size)
        dx = sx[:, np.newaxis] - tx[np.newaxis, :]  # points AWAY from target
        dy = sy[:, np.newaxis] - ty[np.newaxis, :]
        dist_sq = dx * dx + dy * dy

        within = dist_sq < max_dist_sq[:, np.newaxis]
        within &= dist_sq > 0  # exclude self or zero-distance

        dist = np.sqrt(np.where(within, dist_sq, 1.0))
        repulse_dx += np.sum(np.where(within, dx / dist, 0.0), axis=1)
        repulse_dy += np.sum(np.where(within, dy / dist, 0.0), axis=1)

    return repulse_dx, repulse_dy


def update_predators(pred: PredatorArrays, prey: PreyArrays, grass: GrassArray) -> None:
    """Vectorized predator update for one tick."""
    n = pred.count
    if n == 0:
        return

    s = np.s_[:n]  # slice for active range

    # Reset per-tick flags
    pred.killed[s] = 0
    pred.reproduced[s] = 0
    pred.avoiding[s] = 0

    # --- Age & death by old age ---
    pred.age[s] += 1
    over_age_mask = pred.age[s] > pred.max_age[s]
    if np.any(over_age_mask):
        over_age_idx = np.where(over_age_mask)[0]
        rolls = np.random.random(len(over_age_idx)).astype(np.float32)
        die = rolls > pred.high_age_health[over_age_idx]
        dead_idx = over_age_idx[die]
        pred.alive[dead_idx] = 0
        config.predator_dead_by_age += int(die.sum())

    # --- Energy consumption ---
    cost = np.where(
        pred.hunting[s].astype(bool),
        pred.hunting_energy_cost[s],
        pred.regular_energy_cost[s],
    )
    pred.cur_consumption[s] = cost
    pred.food[s] -= cost

    starve_mask = pred.food[s] <= 0
    starve_alive = starve_mask & pred.alive[s].astype(bool)
    if np.any(starve_alive):
        starve_idx = np.where(starve_alive)[0]
        pred.alive[starve_idx] = 0
        config.predator_dead_by_starvation += int(starve_alive.sum())

    # Update starving flag for survivors
    alive_mask = pred.alive[s].astype(bool)
    pred.starving[s] = (
        (pred.food[s] < pred.starv_border[s] * pred.max_food[s]) & alive_mask
    ).astype(np.uint8)

    # Starving predators lose mating flag
    pred.mating[s] = (pred.mating[s].astype(bool) & ~pred.starving[s].astype(bool)).astype(np.uint8)

    # Recompute alive mask after deaths
    alive_mask = pred.alive[s].astype(bool)
    alive_idx = np.where(alive_mask)[0]
    n_alive = len(alive_idx)
    if n_alive == 0:
        return

    # --- Predator-predator avoidance ---
    avoid_dx = np.zeros(n, dtype=np.float32)
    avoid_dy = np.zeros(n, dtype=np.float32)
    predator_too_close = np.zeros(n, dtype=bool)

    if config.PRED_AVOID_PRED and n_alive > 1:
        # Use alive predators only for avoidance computation
        ax = pred.x[alive_idx]
        ay = pred.y[alive_idx]
        avoid_dist = pred.predator_avoid_distance[alive_idx]

        rdx, rdy = _sum_repulsion_vectors(
            ax, ay, n_alive, ax, ay, n_alive, avoid_dist
        )
        # Map back to full array
        avoid_dx[alive_idx] = rdx
        avoid_dy[alive_idx] = rdy
        predator_too_close[alive_idx] = (rdx != 0) | (rdy != 0)

    # Determine which predators should avoid (not starving, not mating, predator too close)
    should_avoid = (
        predator_too_close
        & alive_mask
        & ~pred.starving[s].astype(bool)
        & ~pred.mating[s].astype(bool)
        & (config.PRED_AVOID_PRED == True)
    )

    # Apply avoidance movement
    if np.any(should_avoid):
        av_idx = np.where(should_avoid)[0]
        pred.hunting[av_idx] = 0
        pred.avoiding[av_idx] = 1
        adx = avoid_dx[av_idx]
        ady = avoid_dy[av_idx]
        norm = np.sqrt(adx * adx + ady * ady)
        norm[norm == 0] = 1
        pred.x[av_idx] += (adx / norm) * pred.speed[av_idx]
        pred.y[av_idx] += (ady / norm) * pred.speed[av_idx]

    # --- Mating behavior ---
    not_avoiding = alive_mask & ~should_avoid
    wants_mate = not_avoiding & pred.mating[s].astype(bool)

    if np.any(wants_mate):
        mate_idx = np.where(wants_mate)[0]
        pred.hunting[mate_idx] = 0

        # Find nearest mating partner among all mating predators
        mating_pool = np.where(pred.mating[s].astype(bool) & alive_mask)[0]
        if len(mating_pool) > 1:
            pool_x = pred.x[mating_pool]
            pool_y = pred.y[mating_pool]

            for mi in mate_idx:
                if not pred.mating[mi]:
                    continue  # already paired by a previous seeker
                dx = pool_x - pred.x[mi]
                dy = pool_y - pred.y[mi]
                dist_sq = dx * dx + dy * dy
                dist_sq[mating_pool == mi] = np.inf  # exclude self
                # Exclude already-paired partners
                for pi in range(len(mating_pool)):
                    if not pred.mating[mating_pool[pi]]:
                        dist_sq[pi] = np.inf
                msd = pred.mating_search_distance[mi]
                dist_sq[dist_sq > msd * msd] = np.inf

                best = np.argmin(dist_sq)
                if dist_sq[best] < np.inf:
                    best_global = mating_pool[best]
                    if dist_sq[best] <= config.PREDATOR_MATING_CLOSE_DISTANCE ** 2:
                        # Mating successful
                        pred.reproduced[mi] = 1
                        pred.mating_partner_idx[mi] = best_global
                        pred.mating[mi] = 0
                        pred.mating[best_global] = 0
                    else:
                        # Move towards mate
                        d = np.sqrt(dist_sq[best]) or 1
                        pred.x[mi] += (dx[best] / d) * pred.speed[mi]
                        pred.y[mi] += (dy[best] / d) * pred.speed[mi]

    # --- Hunting behavior ---
    not_mating_or_avoiding = not_avoiding & ~pred.mating[s].astype(bool)
    hunters = not_mating_or_avoiding

    if np.any(hunters) and prey.count > 0:
        hunt_idx = np.where(hunters)[0]
        n_hunt = len(hunt_idx)

        # Get max smell distance for query range
        max_smell = float(pred.smell_distance[hunt_idx].max())

        # Find nearest alive prey for each hunting predator
        alive_prey_mask = prey.alive[:prey.count].astype(bool)
        alive_prey_idx = np.where(alive_prey_mask)[0]
        n_alive_prey = len(alive_prey_idx)

        if n_alive_prey > 0:
            nearest_prey, nearest_dist_sq = _find_nearest_chunked(
                pred.x[hunt_idx], pred.y[hunt_idx], n_hunt,
                prey.x[alive_prey_idx], prey.y[alive_prey_idx], n_alive_prey,
                max_smell,
            )

            # Filter by individual smell distance
            has_target = nearest_prey >= 0
            individual_smell_sq = pred.smell_distance[hunt_idx] ** 2
            in_smell = has_target & (nearest_dist_sq <= individual_smell_sq)

            # Map prey indices back to global prey indices
            global_prey_idx = np.where(has_target, alive_prey_idx[np.clip(nearest_prey, 0, n_alive_prey - 1)], -1)
            global_prey_idx[~in_smell] = -1

            # Split into: has target vs no target
            has_tgt = global_prey_idx >= 0
            no_tgt = ~has_tgt

            # Move towards target
            if np.any(has_tgt):
                tgt_hunt_idx = hunt_idx[has_tgt]
                tgt_prey_idx = global_prey_idx[has_tgt]
                tgt_dist_sq = nearest_dist_sq[has_tgt]

                pred.hunting[tgt_hunt_idx] = 1
                dx = prey.x[tgt_prey_idx] - pred.x[tgt_hunt_idx]
                dy = prey.y[tgt_prey_idx] - pred.y[tgt_hunt_idx]
                dist = np.sqrt(tgt_dist_sq)
                dist[dist == 0] = 1
                pred.x[tgt_hunt_idx] += (dx / dist) * pred.speed[tgt_hunt_idx]
                pred.y[tgt_hunt_idx] += (dy / dist) * pred.speed[tgt_hunt_idx]

                # Check for kills
                kill_dist = (PredatorArrays.SIZE + PreyArrays.SIZE) ** 2
                close_enough = tgt_dist_sq < kill_dist

                if np.any(close_enough):
                    killer_hunt = np.where(close_enough)[0]
                    killer_global = tgt_hunt_idx[killer_hunt]
                    victim_global = tgt_prey_idx[killer_hunt]

                    # Deduplicate: one prey can only be killed once
                    unique_victims, first_occ = np.unique(victim_global, return_index=True)
                    actual_killers = killer_global[first_occ]

                    prey.alive[unique_victims] = 0
                    pred.killed[actual_killers] = 1
                    pred.mating[actual_killers] = 1
                    pred.prey_eaten[actual_killers] += 1
                    pred.food[actual_killers] = np.minimum(
                        pred.max_food[actual_killers],
                        pred.food[actual_killers] + pred.food_gain_per_kill[actual_killers],
                    )
                    config.prey_dead_by_hunting += len(unique_victims)

            # Random movement for predators with no target
            if np.any(no_tgt):
                idle_idx = hunt_idx[no_tgt]
                pred.hunting[idle_idx] = 0
                pred.x[idle_idx] += np.random.uniform(-1, 1, size=len(idle_idx)).astype(np.float32)
                pred.y[idle_idx] += np.random.uniform(-1, 1, size=len(idle_idx)).astype(np.float32)
        else:
            # No prey alive, random movement
            pred.hunting[hunt_idx] = 0
            pred.x[hunt_idx] += np.random.uniform(-1, 1, size=n_hunt).astype(np.float32)
            pred.y[hunt_idx] += np.random.uniform(-1, 1, size=n_hunt).astype(np.float32)

    # --- Boundary clamp ---
    np.clip(pred.x[s], 0, config.WORLD_WIDTH, out=pred.x[s])
    np.clip(pred.y[s], 0, config.WORLD_HEIGHT, out=pred.y[s])


def update_prey(pred: PredatorArrays, prey: PreyArrays, grass: GrassArray) -> None:
    """Vectorized prey update for one tick."""
    n = prey.count
    if n == 0:
        return

    s = np.s_[:n]

    # Reset per-tick status flags
    prey.is_fleeing[s] = 0
    prey.is_eating[s] = 0

    # --- Age & death by old age ---
    prey.age[s] += 1
    over_age_mask = prey.age[s] > prey.max_age[s]
    if np.any(over_age_mask):
        over_age_idx = np.where(over_age_mask)[0]
        rolls = np.random.random(len(over_age_idx)).astype(np.float32)
        die = rolls > prey.high_age_health[over_age_idx]
        dead_idx = over_age_idx[die]
        prey.alive[dead_idx] = 0
        config.prey_dead_by_age += int(die.sum())

    # --- Fleeing from predators ---
    alive_mask = prey.alive[s].astype(bool)
    alive_idx = np.where(alive_mask)[0]
    n_alive = len(alive_idx)

    flee_dx = np.zeros(n, dtype=np.float32)
    flee_dy = np.zeros(n, dtype=np.float32)

    # Count alive predators for flee computation
    pred_alive_mask = pred.alive[:pred.count].astype(bool) if pred.count > 0 else np.array([], dtype=bool)
    pred_alive_idx = np.where(pred_alive_mask)[0] if len(pred_alive_mask) > 0 else np.array([], dtype=np.int32)
    n_pred_alive = len(pred_alive_idx)

    if n_alive > 0 and n_pred_alive > 0:
        rdx, rdy = _sum_repulsion_vectors(
            prey.x[alive_idx], prey.y[alive_idx], n_alive,
            pred.x[pred_alive_idx], pred.y[pred_alive_idx], n_pred_alive,
            prey.fear_distance[alive_idx],
        )
        flee_dx[alive_idx] = rdx
        flee_dy[alive_idx] = rdy

    is_fleeing = (flee_dx != 0) | (flee_dy != 0)
    is_fleeing &= alive_mask

    # Apply flee movement
    if np.any(is_fleeing):
        fl_idx = np.where(is_fleeing)[0]
        fdx = flee_dx[fl_idx]
        fdy = flee_dy[fl_idx]
        norm = np.sqrt(fdx * fdx + fdy * fdy)
        norm[norm == 0] = 1
        prey.x[fl_idx] += (fdx / norm) * prey.speed[fl_idx]
        prey.y[fl_idx] += (fdy / norm) * prey.speed[fl_idx]
        prey.is_fleeing[fl_idx] = 1

    # Random movement for non-fleeing alive prey
    idle = alive_mask & ~is_fleeing
    if np.any(idle):
        idle_idx = np.where(idle)[0]
        prey.x[idle_idx] += np.random.uniform(-1, 1, size=len(idle_idx)).astype(np.float32)
        prey.y[idle_idx] += np.random.uniform(-1, 1, size=len(idle_idx)).astype(np.float32)

    # --- Energy consumption ---
    cost = np.where(
        prey.is_fleeing[s].astype(bool),
        prey.flee_energy_cost[s],
        config.PREY_REGULAR_ENERGY_COST,
    )
    prey.cur_consumption[s] = cost
    prey.food[s] -= cost

    starve_dead = (prey.food[s] <= 0) & prey.alive[s].astype(bool)
    if np.any(starve_dead):
        starve_idx = np.where(starve_dead)[0]
        prey.alive[starve_idx] = 0
        config.prey_dead_by_starvation += int(starve_dead.sum())

    # Starving flag
    alive_mask = prey.alive[s].astype(bool)
    prey.starving[s] = (
        (prey.food[s] < prey.starv_border[s] * prey.max_food[s]) & alive_mask
    ).astype(np.uint8)

    # --- Grass seeking & eating ---
    alive_idx = np.where(alive_mask)[0]
    n_alive = len(alive_idx)

    if n_alive > 0:
        px = prey.x[alive_idx]
        py = prey.y[alive_idx]
        chunk_i = (px.astype(np.int32)) // config.CHUNKSIZE
        chunk_j = (py.astype(np.int32)) // config.CHUNKSIZE

        # Clamp to valid grass grid range
        np.clip(chunk_i, 0, grass.cols - 1, out=chunk_i)
        np.clip(chunk_j, 0, grass.rows - 1, out=chunk_j)

        # Grass gradient for seeking: use np.gradient precomputed
        grad_i, grad_j = np.gradient(grass.amounts)

        # Look up gradient at each prey's cell
        gi = grad_i[chunk_i, chunk_j]
        gj = grad_j[chunk_i, chunk_j]

        # Move towards higher grass (half speed)
        has_gradient = (gi != 0) | (gj != 0)
        if np.any(has_gradient):
            grad_idx = np.where(has_gradient)[0]
            gdx = gi[grad_idx]
            gdy = gj[grad_idx]
            gnorm = np.sqrt(gdx * gdx + gdy * gdy)
            gnorm[gnorm == 0] = 1
            prey.x[alive_idx[grad_idx]] += (gdx / gnorm) * (prey.speed[alive_idx[grad_idx]] * 0.5)
            prey.y[alive_idx[grad_idx]] += (gdy / gnorm) * (prey.speed[alive_idx[grad_idx]] * 0.5)

        # Boundary clamp after grass movement
        np.clip(prey.x[s], 0, config.WORLD_WIDTH, out=prey.x[s])
        np.clip(prey.y[s], 0, config.WORLD_HEIGHT, out=prey.y[s])

        # Recalculate chunk after movement
        px2 = prey.x[alive_idx]
        py2 = prey.y[alive_idx]
        chunk_i2 = (px2.astype(np.int32)) // config.CHUNKSIZE
        chunk_j2 = (py2.astype(np.int32)) // config.CHUNKSIZE
        np.clip(chunk_i2, 0, grass.cols - 1, out=chunk_i2)
        np.clip(chunk_j2, 0, grass.rows - 1, out=chunk_j2)

        # Eat grass — approximate the original sequential consumption.
        # In the original, k prey on a cell with g grass process one-by-one:
        # prey i sees max(0, g-i) grass. The average grass seen across k prey is:
        #   avg = min(k,g) * (2g - min(k,g) + 1) / (2k)
        # This formula gives the exact average of the sequential behavior.
        prey_per_cell = np.zeros((grass.cols, grass.rows), dtype=np.int32)
        np.add.at(prey_per_cell, (chunk_i2, chunk_j2), 1)

        k = prey_per_cell[chunk_i2, chunk_j2].astype(np.float32)
        k[k == 0] = 1  # avoid div-by-zero
        raw_grass = grass.amounts[chunk_i2, chunk_j2]
        g = raw_grass.astype(np.float32)
        m = np.minimum(k, g)
        # Average grass seen per prey (exact match to sequential average)
        effective_grass = m * (2.0 * g - m + 1.0) / (2.0 * k)
        gain = effective_grass * prey.food_gain_per_grass[alive_idx]

        # Track eating status
        eating = (gain > 0) & (prey.food[alive_idx] < prey.max_food[alive_idx]) & (raw_grass > 0)
        prey.is_eating[alive_idx[eating]] = 1
        prey.grass_eaten[alive_idx[eating]] += gain[eating]

        prey.food[alive_idx] = np.minimum(
            prey.max_food[alive_idx],
            prey.food[alive_idx] + gain,
        )

        # Consume grass (safe for multiple prey on same cell)
        np.subtract.at(grass.amounts, (chunk_i2, chunk_j2), 1)
        np.clip(grass.amounts, 0, config.GRASS_MAX_AMOUNT, out=grass.amounts)
    else:
        # Boundary clamp even if no alive prey (for consistency)
        np.clip(prey.x[s], 0, config.WORLD_WIDTH, out=prey.x[s])
        np.clip(prey.y[s], 0, config.WORLD_HEIGHT, out=prey.y[s])

    # --- Mating ---
    alive_mask = prey.alive[s].astype(bool)

    # Simple reproduction (non-mating-simulation prey)
    simple_mask = alive_mask & ~prey.mating_simulation[s].astype(bool)
    if np.any(simple_mask):
        simple_idx = np.where(simple_mask)[0]
        prey.reproduced[simple_idx] = 0
        rolls = np.random.random(len(simple_idx))
        reproduce = rolls / 4 < config.PREY_REPRODUCTION_RATE
        prey.reproduced[simple_idx[reproduce]] = 1

    # Complex mating simulation
    complex_mask = alive_mask & prey.mating_simulation[s].astype(bool)
    if np.any(complex_mask):
        complex_idx = np.where(complex_mask)[0]
        prey.reproduced[complex_idx] = 0

        # Prey that are mating and not fleeing look for a partner
        mating_and_not_fleeing = (
            prey.mating[complex_idx].astype(bool)
            & ~prey.is_fleeing[complex_idx].astype(bool)
        )

        if np.any(mating_and_not_fleeing):
            seeker_local = np.where(mating_and_not_fleeing)[0]
            seeker_idx = complex_idx[seeker_local]

            # Mating pool: all complex prey that are mating and alive
            mating_pool = np.where(
                prey.mating[s].astype(bool) & alive_mask & prey.mating_simulation[s].astype(bool)
            )[0]

            if len(mating_pool) > 1:
                pool_x = prey.x[mating_pool]
                pool_y = prey.y[mating_pool]

                for si in seeker_idx:
                    if not prey.mating[si]:
                        continue  # already paired by a previous seeker
                    dx = pool_x - prey.x[si]
                    dy = pool_y - prey.y[si]
                    dist_sq = dx * dx + dy * dy
                    dist_sq[mating_pool == si] = np.inf  # exclude self
                    # Exclude already-paired partners
                    for pi in range(len(mating_pool)):
                        if not prey.mating[mating_pool[pi]]:
                            dist_sq[pi] = np.inf
                    msd = prey.mating_search_distance[si]
                    dist_sq[dist_sq > msd * msd] = np.inf

                    best = np.argmin(dist_sq)
                    if dist_sq[best] < np.inf:
                        best_global = mating_pool[best]
                        if dist_sq[best] <= config.PREY_MATING_CLOSE_DISTANCE ** 2:
                            prey.reproduced[si] = 1
                            prey.mating_partner_idx[si] = best_global
                            prey.mating[si] = 0
                            prey.mating[best_global] = 0
                        else:
                            d = np.sqrt(dist_sq[best]) or 1.0
                            prey.x[si] += (dx[best] / d) * prey.speed[si]
                            prey.y[si] += (dy[best] / d) * prey.speed[si]
                            prey.x[si] = max(0, min(config.WORLD_WIDTH, float(prey.x[si])))
                            prey.y[si] = max(0, min(config.WORLD_HEIGHT, float(prey.y[si])))

        # Random chance to enter mating mode
        not_mating = complex_mask & ~prey.mating[s].astype(bool)
        if np.any(not_mating):
            nm_idx = np.where(not_mating)[0]
            rolls = np.random.random(len(nm_idx))
            enter = rolls < config.PREY_REPRODUCTION_RATE
            prey.mating[nm_idx[enter]] = 1


def process_deaths(pred: PredatorArrays, prey: PreyArrays) -> tuple[int, int]:
    """Compact arrays, removing dead animals. Returns (pred_deaths, prey_deaths)."""
    pred_before = pred.count
    prey_before = prey.count

    pred.compact()
    prey.compact()

    return pred_before - pred.count, prey_before - prey.count


def process_reproduction(pred: PredatorArrays, prey: PreyArrays) -> None:
    """Handle reproduction: create children with inherited traits."""

    # --- Prey reproduction ---
    repro_mask = prey.reproduced[:prey.count].astype(bool)
    if np.any(repro_mask):
        repro_idx = np.where(repro_mask)[0]
        for ri in repro_idx:
            num_born = random.randint(1, 4)
            partner_idx = int(prey.mating_partner_idx[ri])

            for _ in range(num_born):
                if prey.count >= prey.capacity:
                    prey._grow(prey.count + 1)
                ci = prey.count
                prey.uid[ci] = _alloc_uid()
                prey.alive[ci] = 1
                prey.mating[ci] = 0
                prey.reproduced[ci] = 0
                prey.starving[ci] = 0
                prey.killed[ci] = 0
                prey.is_fleeing[ci] = 0
                prey.is_eating[ci] = 0
                prey.age[ci] = 0
                prey.grass_eaten[ci] = 0
                prey.offspring_created[ci] = 0
                prey.cur_consumption[ci] = 0.0
                prey.mating_partner_idx[ci] = -1

                if partner_idx >= 0 and partner_idx < prey.count:
                    # Inherit traits from both parents
                    gen = max(int(prey.generation[ri]), int(prey.generation[partner_idx])) + 1
                    prey.generation[ci] = gen
                    _inherit_prey_traits(prey, ci, ri, partner_idx)
                else:
                    prey.generation[ci] = int(prey.generation[ri]) + 1
                    _copy_default_prey_traits(prey, ci)

                prey.x[ci] = prey.x[ri] + random.uniform(-5, 5)
                prey.y[ci] = prey.y[ri] + random.uniform(-5, 5)
                prey.food[ci] = prey.max_food[ci]
                prey.count += 1

            config.prey_born += num_born
            prey.offspring_created[ri] += num_born
            prey.mating_partner_idx[ri] = -1

    # --- Predator reproduction ---
    repro_mask = pred.reproduced[:pred.count].astype(bool)
    if np.any(repro_mask):
        repro_idx = np.where(repro_mask)[0]
        for ri in repro_idx:
            num_born = random.randint(1, 4)
            partner_idx = int(pred.mating_partner_idx[ri])

            for _ in range(num_born):
                if pred.count >= pred.capacity:
                    pred._grow(pred.count + 1)
                ci = pred.count
                pred.uid[ci] = _alloc_uid()
                pred.alive[ci] = 1
                pred.hunting[ci] = 0
                pred.mating[ci] = 0
                pred.reproduced[ci] = 0
                pred.starving[ci] = 0
                pred.killed[ci] = 0
                pred.avoiding[ci] = 0
                pred.age[ci] = 0
                pred.prey_eaten[ci] = 0
                pred.offspring_created[ci] = 0
                pred.cur_consumption[ci] = 0.0
                pred.mating_partner_idx[ci] = -1

                rx = random.uniform(10, 15) * random.choice([-1, 1])
                ry = random.uniform(10, 15) * random.choice([-1, 1])

                if partner_idx >= 0 and partner_idx < pred.count:
                    gen = max(int(pred.generation[ri]), int(pred.generation[partner_idx])) + 1
                    pred.generation[ci] = gen
                    _inherit_pred_traits(pred, ci, ri, partner_idx)
                else:
                    pred.generation[ci] = int(pred.generation[ri]) + 1
                    _copy_default_pred_traits(pred, ci)

                pred.x[ci] = pred.x[ri] + rx
                pred.y[ci] = pred.y[ri] + ry
                pred.food[ci] = pred.max_food[ci]
                pred.count += 1

            config.predator_born += num_born
            pred.reproduced[ri] = 0
            pred.offspring_created[ri] += num_born
            pred.mating_partner_idx[ri] = -1


def _inherit_trait(p1: float, p2: float, base: float) -> float:
    """Inherit a trait from two parents with mutation."""
    inherited = random.uniform(min(p1, p2), max(p1, p2))
    mutation = random.uniform(-config.MUTATION_RATE, config.MUTATION_RATE) * base
    return max(0.001, inherited + mutation)


def _inherit_pred_traits(pred: PredatorArrays, ci: int, p1: int, p2: int) -> None:
    """Set child predator traits via inheritance from parents p1 and p2."""
    pred.speed[ci] = _inherit_trait(
        float(pred.speed[p1]), float(pred.speed[p2]), config.PREDATOR_SPEED)
    pred.predator_avoid_distance[ci] = _inherit_trait(
        float(pred.predator_avoid_distance[p1]), float(pred.predator_avoid_distance[p2]),
        config.PREDATOR_PREDATOR_AVOID_DISTANCE)
    pred.smell_distance[ci] = _inherit_trait(
        float(pred.smell_distance[p1]), float(pred.smell_distance[p2]),
        config.PREDATOR_SMELL_DISTANCE)
    pred.max_food[ci] = _inherit_trait(
        float(pred.max_food[p1]), float(pred.max_food[p2]), config.PREDATOR_MAX_FOOD)
    pred.food_gain_per_kill[ci] = _inherit_trait(
        float(pred.food_gain_per_kill[p1]), float(pred.food_gain_per_kill[p2]),
        config.PREDATOR_FOOD_GAIN_PER_KILL)
    pred.regular_energy_cost[ci] = _inherit_trait(
        float(pred.regular_energy_cost[p1]), float(pred.regular_energy_cost[p2]),
        config.PREDATOR_REGULAR_ENERGY_COST)
    pred.hunting_energy_cost[ci] = _inherit_trait(
        float(pred.hunting_energy_cost[p1]), float(pred.hunting_energy_cost[p2]),
        config.PREDATOR_HUNTING_ENERGY_COST)
    pred.starv_border[ci] = _inherit_trait(
        float(pred.starv_border[p1]), float(pred.starv_border[p2]),
        config.PREDATOR_STARV_BORDER)
    pred.max_age[ci] = _inherit_trait(
        float(pred.max_age[p1]), float(pred.max_age[p2]), config.PREDATOR_MAX_AGE)
    pred.high_age_health[ci] = min(1.0, _inherit_trait(
        float(pred.high_age_health[p1]), float(pred.high_age_health[p2]),
        config.PREDATOR_HIGH_AGE_HEALTH))
    pred.mating_search_distance[ci] = _inherit_trait(
        float(pred.mating_search_distance[p1]), float(pred.mating_search_distance[p2]),
        config.PREDATOR_MATING_SEARCH_DISTANCE)


def _inherit_prey_traits(prey: PreyArrays, ci: int, p1: int, p2: int) -> None:
    """Set child prey traits via inheritance from parents p1 and p2."""
    prey.speed[ci] = _inherit_trait(
        float(prey.speed[p1]), float(prey.speed[p2]), config.PREY_SPEED)
    prey.fear_distance[ci] = _inherit_trait(
        float(prey.fear_distance[p1]), float(prey.fear_distance[p2]),
        config.PREY_FEAR_DISTANCE)
    prey.mating_simulation[ci] = random.choice([
        int(prey.mating_simulation[p1]), int(prey.mating_simulation[p2])])
    prey.mating_search_distance[ci] = _inherit_trait(
        float(prey.mating_search_distance[p1]), float(prey.mating_search_distance[p2]),
        config.PREY_MATING_SEARCH_DISTANCE)
    prey.max_food[ci] = _inherit_trait(
        float(prey.max_food[p1]), float(prey.max_food[p2]), config.PREY_MAX_FOOD)
    prey.food_gain_per_grass[ci] = _inherit_trait(
        float(prey.food_gain_per_grass[p1]), float(prey.food_gain_per_grass[p2]),
        config.PREY_FOOD_GAIN_PER_GRASS)
    prey.starv_border[ci] = _inherit_trait(
        float(prey.starv_border[p1]), float(prey.starv_border[p2]),
        config.PREY_STARV_BORDER)
    prey.flee_energy_cost[ci] = _inherit_trait(
        float(prey.flee_energy_cost[p1]), float(prey.flee_energy_cost[p2]),
        config.PREY_FLEE_ENERGY_COST)
    prey.max_age[ci] = _inherit_trait(
        float(prey.max_age[p1]), float(prey.max_age[p2]), config.PREY_MAX_AGE)
    prey.high_age_health[ci] = min(1.0, _inherit_trait(
        float(prey.high_age_health[p1]), float(prey.high_age_health[p2]),
        config.PREY_HIGH_AGE_HEALTH))


def _copy_default_pred_traits(pred: PredatorArrays, ci: int) -> None:
    """Set default config traits for a new predator (no partner)."""
    pred.speed[ci] = config.PREDATOR_SPEED
    pred.smell_distance[ci] = config.PREDATOR_SMELL_DISTANCE
    pred.predator_avoid_distance[ci] = config.PREDATOR_PREDATOR_AVOID_DISTANCE
    pred.max_food[ci] = config.PREDATOR_MAX_FOOD
    pred.food_gain_per_kill[ci] = config.PREDATOR_FOOD_GAIN_PER_KILL
    pred.regular_energy_cost[ci] = config.PREDATOR_REGULAR_ENERGY_COST
    pred.hunting_energy_cost[ci] = config.PREDATOR_HUNTING_ENERGY_COST
    pred.starv_border[ci] = config.PREDATOR_STARV_BORDER
    pred.max_age[ci] = config.PREDATOR_MAX_AGE
    pred.high_age_health[ci] = config.PREDATOR_HIGH_AGE_HEALTH
    pred.mating_search_distance[ci] = config.PREDATOR_MATING_SEARCH_DISTANCE


def _copy_default_prey_traits(prey: PreyArrays, ci: int) -> None:
    """Set default config traits for a new prey (no partner)."""
    prey.speed[ci] = config.PREY_SPEED
    prey.fear_distance[ci] = config.PREY_FEAR_DISTANCE
    prey.mating_simulation[ci] = 1 if config.PREY_MATING_SIMULATION else 0
    prey.mating_search_distance[ci] = config.PREY_MATING_SEARCH_DISTANCE
    prey.max_food[ci] = config.PREY_MAX_FOOD
    prey.food_gain_per_grass[ci] = config.PREY_FOOD_GAIN_PER_GRASS
    prey.starv_border[ci] = config.PREY_STARV_BORDER
    prey.flee_energy_cost[ci] = config.PREY_FLEE_ENERGY_COST
    prey.max_age[ci] = config.PREY_MAX_AGE
    prey.high_age_health[ci] = config.PREY_HIGH_AGE_HEALTH
