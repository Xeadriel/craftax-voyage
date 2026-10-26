# Description:
# Deterministically builds (or finds) a shelter and sleeps until the energy is full.
# The shelter is a pocket of at most two non-solid cells A and B in a straight line,
# fully surrounded by solid blocks, with the player in A. Because pressing a direction
# moves the player onto walkable cells, the last wall can only be placed in the
# direction the player moves: the player walks from B into A and seals the entrance O
# in front of it (O, A, B are on one line). Side walls are placed from outside first,
# A and B are tunnelled out of rock when the pickaxe allows it, the far end behind B is
# sealed from inside B, and finally O is sealed from A. Walls are stone (or crafting
# tables when out of stone). The pocket needing the fewest placements and steps is
# chosen; if no shelter can be built the player sleeps where it stands. The shelter is
# planned only from remembered cells and visible mobs (never-seen cells count as open,
# and paths may cross them at an extra cost but never as the next step). max_steps only
# limits the steps before sleeping starts; once asleep the function keeps stepping
# until the player wakes up.
# Returns True when the player woke up with full energy, raises an Exception otherwise.

def sleep(state, log_func, step_func, max_steps=50):
    """
    Walls the player in (if possible) and sleeps until the energy is full.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        max_steps: Maximum number of calls to step_func before sleeping has started;
            ignored once the player is asleep

    Returns:
        The final EnvState (after the last step) if the player slept until its energy was full

    Raises:
        Exception: If the energy is already full, sleeping could not be started, the
            player was woken up early (e.g. by an attack), the player died (health
            dropped to 0), the player left the floor, or max_steps was reached before
            falling asleep
    """
    import heapq
    from collections import deque

    import numpy as np

    from control_primitives.knowledge import (
        UNKNOWN,
        is_visible,
        known_blocks,
        known_items,
        visible_mobs,
    )
    from craftax.craftax.constants import (
        DIRECTIONS,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
    )
    from craftax.craftax.util.game_logic_utils import get_max_energy

    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    move_offsets = {a: (d_row, d_col) for a, d_row, d_col in moves}
    action_index = {a: index for index, (a, _, _) in enumerate(moves)}
    action_names = {action.value: action.name for action in Action}

    solid_blocks = set(SOLID_BLOCKS)
    # Cells the player cannot stand on
    impassable_blocks = solid_blocks | {
        BlockType.WATER.value,
        BlockType.LAVA.value,
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER_VULNERABLE.value,
    }
    # Blocks DO turns into PATH, with the required pickaxe level and the stone gained
    tunnel_blocks = {
        BlockType.STONE.value: (1, 1),
        BlockType.COAL.value: (1, 0),
        BlockType.STALAGMITE.value: (1, 1),
        BlockType.IRON.value: (2, 0),
        BlockType.DIAMOND.value: (3, 0),
        BlockType.SAPPHIRE.value: (4, 0),
        BlockType.RUBY.value: (4, 0),
    }

    max_failed_attempts = 3
    max_mob_wait_steps = 5
    placement_cost = 3
    mining_cost = 3
    # Extra cost of walking through a never-seen cell (assumed walkable)
    unknown_cost = 2

    def plan_path(start_state, walkable, unknown, is_goal):
        # Dijkstra over (row, col, facing): pressing a direction moves the player onto a
        # walkable cell, or only turns it when that cell is blocked. Unknown cells are
        # assumed walkable at an extra cost but are never entered from the player's cell
        rows, cols = walkable.shape
        start_cell = start_state[:2]
        best_cost = {start_state: 0}
        first_action = {}
        heap = [(0, 0, start_state)]
        counter = 1
        while heap:
            cost, _, node = heapq.heappop(heap)
            if cost > best_cost[node]:
                continue
            if is_goal(node):
                return node, first_action
            row, col, _ = node
            for a, d_row, d_col in moves:
                next_row = row + d_row
                next_col = col + d_col
                inside = 0 <= next_row < rows and 0 <= next_col < cols
                if inside and unknown[next_row, next_col]:
                    if (row, col) == start_cell:
                        continue
                    next_state, step_cost = (next_row, next_col, a), 1 + unknown_cost
                elif inside and walkable[next_row, next_col]:
                    next_state, step_cost = (next_row, next_col, a), 1
                else:
                    next_state, step_cost = (row, col, a), 1
                next_cost = cost + step_cost
                if next_cost >= best_cost.get(next_state, next_cost + 1):
                    continue
                best_cost[next_state] = next_cost
                first_action[next_state] = first_action.get(node, a)
                heapq.heappush(heap, (next_cost, counter, next_state))
                counter += 1
        return None, first_action

    def block_name(value):
        value = int(value)
        return "UNKNOWN" if value == UNKNOWN else BlockType(value).name

    def material_counts(env_state):
        return tuple(
            int(getattr(env_state.inventory, name))
            for name in ("stone", "wood", "coal", "iron", "diamond", "sapphire", "ruby")
        )

    start_level = int(state.player_level)
    plan = None
    unprotected = False
    failed_attempts = 0
    mob_wait_steps = 0
    rejected_plans = set()

    log_func(
        f"[sleep] Start: energy {int(state.player_energy)}/{int(get_max_energy(state))}, "
        f"stone {int(state.inventory.stone)}, wood {int(state.inventory.wood)}, "
        f"pickaxe level {int(state.inventory.pickaxe)}, budget of {max_steps} steps before sleeping"
    )

    if not bool(state.is_sleeping) and int(state.player_energy) >= int(get_max_energy(state)):
        log_func("[sleep] Energy is already full, the player cannot fall asleep")
        raise Exception(
            f"Sleeping failed: energy is already full ({int(state.player_energy)}/{int(get_max_energy(state))})"
        )

    # ==================== Phase 1: build or find a shelter, then fall asleep ====================
    asleep = bool(state.is_sleeping)
    if asleep:
        log_func("[sleep] The player is already asleep")

    for steps_taken in range(max_steps + 1):
        if asleep:
            break

        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)
        energy = int(state.player_energy)
        max_energy = int(get_max_energy(state))
        stone = int(state.inventory.stone)
        wood = int(state.inventory.wood)
        pickaxe_level = int(state.inventory.pickaxe)

        if current_level != start_level:
            log_func(f"[sleep] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Sleeping failed: player left floor {start_level}")

        # What the player knows: remembered blocks/items and visible mobs
        block_map = known_blocks(state)
        item_memory = known_items(state)
        map_rows, map_cols = block_map.shape
        unknown = block_map == UNKNOWN
        unknown[player_row, player_col] = False
        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in visible_mobs(state):
            mob_occupied[mob_row, mob_col] = True

        # Never-seen cells count as not solid (they might be open) and as not walkable here
        solid = np.isin(block_map, list(solid_blocks))
        walkable = ~unknown & ~np.isin(block_map, list(impassable_blocks)) & ~mob_occupied
        walkable[player_row, player_col] = True

        # Region of non-solid cells connected to the player (mobs, flying mobs and projectiles
        # can only reach the player through non-solid cells)
        region = {(player_row, player_col)}
        frontier = deque([(player_row, player_col)])
        while frontier and len(region) <= 2:
            row, col = frontier.popleft()
            for _, d_row, d_col in moves:
                cell = (row + d_row, col + d_col)
                if not (0 <= cell[0] < map_rows and 0 <= cell[1] < map_cols):
                    continue
                if solid[cell] or cell in region:
                    continue
                region.add(cell)
                frontier.append(cell)
        mobs_inside = [cell for cell in region if cell != (player_row, player_col) and mob_occupied[cell]]
        sheltered = len(region) <= 2 and not mobs_inside

        log_func(
            f"[sleep] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, energy {energy}/{max_energy}, "
            f"health {float(state.player_health):.1f}, stone {stone}, wood {wood}, "
            f"{'sheltered' if sheltered else 'exposed'}"
        )

        if steps_taken >= max_steps:
            log_func(f"[sleep] Max steps ({max_steps}) reached before falling asleep")
            raise Exception(f"Sleeping failed: max steps ({max_steps}) reached before falling asleep")

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        sleeping_attempt = False
        placing_cell = None
        mining_cell = None

        if bool(state.is_resting):
            action_reason = "player is resting, actions are ignored until it stops"
        elif sheltered or unprotected:
            action = Action.SLEEP.value
            sleeping_attempt = True
            action_reason = (
                f"going to sleep in a shelter of {len(region)} cell(s)" if sheltered
                else "going to sleep without shelter (no shelter could be built)"
            )
        else:
            # Walking costs from the player (Dijkstra; never-seen cells cost extra and are
            # never the first step)
            walk_distance = np.full((map_rows, map_cols), -1, dtype=np.int64)
            walk_distance[player_row, player_col] = 0
            heap = [(0, player_row, player_col)]
            while heap:
                distance, row, col = heapq.heappop(heap)
                if distance > walk_distance[row, col]:
                    continue
                for _, d_row, d_col in moves:
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < map_rows and 0 <= next_col < map_cols):
                        continue
                    if unknown[next_row, next_col]:
                        if (row, col) == (player_row, player_col):
                            continue
                        next_distance = distance + 1 + unknown_cost
                    elif walkable[next_row, next_col]:
                        next_distance = distance + 1
                    else:
                        continue
                    if walk_distance[next_row, next_col] < 0 or next_distance < walk_distance[next_row, next_col]:
                        walk_distance[next_row, next_col] = next_distance
                        heapq.heappush(heap, (next_distance, next_row, next_col))

            # Validate the current plan (or choose a new one) from memory: pocket A-B, entrance O,
            # walls around, all of them known cells
            candidate_cells = [plan[:2]] if plan is not None else [
                (int(r), int(c), a)
                for r, c in np.argwhere((walk_distance >= 0) & ~unknown)
                for a, _, _ in moves
            ]
            if plan is None:
                # The pocket cell A may also be rock next to a reachable cell
                rock_cells = np.argwhere(np.isin(block_map, list(tunnel_blocks)))
                for r, c in rock_cells:
                    for a, _, _ in moves:
                        candidate_cells.append((int(r), int(c), a))
            best = None
            for candidate in candidate_cells:
                if plan is not None:
                    a_cell, e_action = candidate
                else:
                    a_cell, e_action = (candidate[0], candidate[1]), candidate[2]
                if (a_cell, e_action) in rejected_plans:
                    continue
                e_row, e_col = move_offsets[e_action]
                b_cell = (a_cell[0] - e_row, a_cell[1] - e_col)
                o_cell = (a_cell[0] + e_row, a_cell[1] + e_col)
                far_cell = (b_cell[0] - e_row, b_cell[1] - e_col)
                if not all(
                    0 <= cell[0] < map_rows and 0 <= cell[1] < map_cols for cell in (a_cell, b_cell, o_cell)
                ):
                    continue
                if any(unknown[cell] for cell in (a_cell, b_cell, o_cell)):
                    continue
                # The entrance must be reachable, walkable and placeable
                if walk_distance[o_cell] < 0 or int(item_memory[o_cell]) != ItemType.NONE.value:
                    continue
                pocket_ok = True
                mines = 0
                stone_gain = 0
                for cell in (a_cell, b_cell):
                    block = int(block_map[cell])
                    if block in tunnel_blocks:
                        if pickaxe_level < tunnel_blocks[block][0]:
                            pocket_ok = False
                            break
                        mines += 1
                        stone_gain += tunnel_blocks[block][1]
                    elif block in impassable_blocks:
                        pocket_ok = False
                        break
                if not pocket_ok:
                    continue
                if mob_occupied[b_cell] and b_cell != (player_row, player_col):
                    continue
                walls = [
                    (a_cell[0] + e_col, a_cell[1] + e_row),
                    (a_cell[0] - e_col, a_cell[1] - e_row),
                    (b_cell[0] + e_col, b_cell[1] + e_row),
                    (b_cell[0] - e_col, b_cell[1] - e_row),
                    far_cell,
                ]
                open_walls = []
                for cell in walls:
                    if not (0 <= cell[0] < map_rows and 0 <= cell[1] < map_cols) or solid[cell]:
                        continue
                    if unknown[cell] or int(item_memory[cell]) != ItemType.NONE.value:
                        pocket_ok = False
                        break
                    open_walls.append(cell)
                if not pocket_ok:
                    continue
                placements = len(open_walls) + (0 if solid[o_cell] else 1)
                if placements > stone + stone_gain + wood // 2:
                    continue
                cost = (
                    placements * placement_cost
                    + mines * mining_cost
                    + int(walk_distance[o_cell])
                )
                key = (cost, placements, a_cell[0], a_cell[1], action_index[e_action])
                if best is None or key < best[0]:
                    best = (key, a_cell, e_action, b_cell, o_cell, far_cell, walls[:4], cost, placements, mines)

            if best is None:
                if plan is not None:
                    log_func(f"[sleep] Shelter plan at {plan[0]} is no longer possible, choosing a new one")
                    rejected_plans.add((plan[0], plan[1]))
                    plan = None
                    action_reason = "re-planning the shelter"
                else:
                    unprotected = True
                    log_func(
                        f"[sleep] Warning: no shelter can be built here (stone {stone}, wood {wood}, "
                        f"pickaxe level {pickaxe_level}), sleeping without protection"
                    )
                    action = Action.SLEEP.value
                    sleeping_attempt = True
                    action_reason = "going to sleep without shelter"
            else:
                _, a_cell, e_action, b_cell, o_cell, far_cell, side_walls, cost, placements, mines = best
                if plan is None:
                    log_func(
                        f"[sleep] Shelter plan: sleep at {a_cell} with pocket cell {b_cell}, entrance {o_cell} "
                        f"(facing {action_names[e_action]} when sealing), {placements} wall(s) to place, "
                        f"{mines} cell(s) to tunnel, estimated cost {cost}"
                    )
                plan = (a_cell, e_action)

                # Next construction task
                open_sides = [cell for cell in side_walls if 0 <= cell[0] < map_rows and 0 <= cell[1] < map_cols and not solid[cell]]
                if open_sides:
                    task = ("place", open_sides[0], None, "side wall")
                elif not walkable[a_cell] and int(block_map[a_cell]) in tunnel_blocks:
                    task = ("mine", a_cell, None, "sleeping cell")
                elif not walkable[b_cell] and int(block_map[b_cell]) in tunnel_blocks:
                    task = ("mine", b_cell, None, "pocket cell")
                elif 0 <= far_cell[0] < map_rows and 0 <= far_cell[1] < map_cols and not solid[far_cell]:
                    task = ("place", far_cell, None, "far end wall")
                else:
                    task = ("place", o_cell, (a_cell[0], a_cell[1], e_action), "entrance")

                task_kind, target_cell, required_state, label = task

                # Shortest path over (row, col, facing) until the player faces the target
                start_facing = facing if facing in action_index else moves[0][0]
                start_state = (player_row, player_col, start_facing)

                def is_goal(node, target_cell=target_cell, required_state=required_state):
                    row, col, state_facing = node
                    ahead = (row + move_offsets[state_facing][0], col + move_offsets[state_facing][1])
                    return ahead == target_cell and (required_state is None or node == required_state)

                goal_state, first_action = plan_path(start_state, walkable, unknown, is_goal)

                if goal_state is None:
                    log_func(f"[sleep] Cannot get into position to work on the {label} at {target_cell}, re-planning")
                    rejected_plans.add(plan)
                    plan = None
                    action_reason = "re-planning the shelter"
                elif goal_state != start_state:
                    action = first_action[goal_state]
                    next_cell = (player_row + move_offsets[action][0], player_col + move_offsets[action][1])
                    will_move = 0 <= next_cell[0] < map_rows and 0 <= next_cell[1] < map_cols and walkable[next_cell]
                    action_reason = (
                        f"{'moving to' if will_move else 'turning towards'} {next_cell} to get into position "
                        f"({goal_state[0]}, {goal_state[1]}) for the {label} at {target_cell}"
                    )
                elif mob_occupied[target_cell]:
                    mob_wait_steps += 1
                    if mob_wait_steps > max_mob_wait_steps:
                        log_func(f"[sleep] A mob keeps standing on {target_cell}, re-planning")
                        rejected_plans.add(plan)
                        plan = None
                        mob_wait_steps = 0
                    action_reason = f"a mob stands on {target_cell}, waiting ({mob_wait_steps}/{max_mob_wait_steps})"
                elif task_kind == "mine":
                    mob_wait_steps = 0
                    action = Action.DO.value
                    mining_cell = target_cell
                    action_reason = f"tunnelling the {label}: mining {block_name(block_map[target_cell])} at {target_cell}"
                else:
                    mob_wait_steps = 0
                    if stone > 0:
                        action = Action.PLACE_STONE.value
                        material = "stone"
                    elif wood >= 2:
                        action = Action.PLACE_TABLE.value
                        material = "crafting table"
                    else:
                        material = None
                    if material is None:
                        log_func("[sleep] Out of stone and wood for walls, re-planning")
                        rejected_plans.add(plan)
                        plan = None
                        action_reason = "re-planning the shelter"
                    else:
                        placing_cell = target_cell
                        action_reason = (
                            f"placing a {material} as the {label} on "
                            f"{block_name(block_map[target_cell])} at {target_cell}"
                        )

        # ---------- Act ----------
        log_func(f"[sleep] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Sleeping failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0:
            log_func("[sleep] The player died")
            raise Exception("Sleeping failed: the player died before falling asleep")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[sleep] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if placing_cell is not None or mining_cell is not None:
            cell = placing_cell if placing_cell is not None else mining_cell
            old_block = int(block_map[cell])
            # Trust the memory only if the cell is in view, otherwise the inventory tells
            if is_visible(new_state, cell[0], cell[1]):
                new_block = int(known_blocks(new_state)[cell])
                changed = new_block != old_block
                change_text = f"{block_name(old_block)} -> {block_name(new_block)}"
            else:
                changed = material_counts(new_state) != material_counts(state)
                change_text = f"{block_name(old_block)} -> (not in view)"
            if changed:
                failed_attempts = 0
                log_func(
                    f"[sleep] {'Placed' if placing_cell is not None else 'Mined'} at {cell}: "
                    f"{change_text}, "
                    f"stone {stone} -> {int(new_state.inventory.stone)}, wood {wood} -> {int(new_state.inventory.wood)}"
                )
            else:
                failed_attempts += 1
                log_func(f"[sleep] Working on {cell} had no effect ({failed_attempts}/{max_failed_attempts})")
                if failed_attempts >= max_failed_attempts:
                    log_func("[sleep] Giving up on this shelter plan")
                    rejected_plans.add(plan)
                    plan = None
                    failed_attempts = 0

        if sleeping_attempt:
            if bool(new_state.is_sleeping):
                asleep = True
                log_func(
                    f"[sleep] Fell asleep at ({int(new_state.player_position[0])}, {int(new_state.player_position[1])}) "
                    f"with energy {int(new_state.player_energy)}/{int(get_max_energy(new_state))}"
                )
            else:
                failed_attempts += 1
                log_func(f"[sleep] Could not fall asleep ({failed_attempts}/{max_failed_attempts})")
                if failed_attempts >= max_failed_attempts:
                    raise Exception(
                        f"Sleeping failed: could not fall asleep (energy {int(new_state.player_energy)}/"
                        f"{int(get_max_energy(new_state))})"
                    )

        state = new_state

    if not asleep:
        raise Exception(f"Sleeping failed: max steps ({max_steps}) reached before falling asleep")

    # ==================== Phase 2: sleep until the energy is full ====================
    # Energy rises by 1 about every 11 steps while asleep; the bound only guards against an endless loop
    max_sleep_steps = (int(get_max_energy(state)) + 1) * 40 + 100
    for sleep_step in range(max_sleep_steps + 1):
        energy = int(state.player_energy)
        max_energy = int(get_max_energy(state))
        if not bool(state.is_sleeping):
            if energy >= max_energy:
                log_func(f"[sleep] Woke up rested with energy {energy}/{max_energy} after {sleep_step} sleeping steps")
                return state
            log_func(
                f"[sleep] Woke up early with energy {energy}/{max_energy} after {sleep_step} sleeping steps "
                f"(health {float(state.player_health):.1f}), probably attacked"
            )
            raise Exception(
                f"Sleeping failed: woken up early with energy {energy}/{max_energy}, probably by an attack"
            )
        if sleep_step >= max_sleep_steps:
            break

        log_func(
            f"[sleep] Sleeping step {sleep_step + 1}: energy {energy}/{max_energy}, "
            f"health {float(state.player_health):.1f}, food {int(state.player_food)}, drink {int(state.player_drink)}"
        )
        new_state = step_func(Action.NOOP.value)
        if new_state is None:
            raise Exception("Sleeping failed: step function returned no state while sleeping")
        if float(new_state.player_health) <= 0:
            log_func("[sleep] The player died while sleeping")
            raise Exception("Sleeping failed: the player died while sleeping")
        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[sleep] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f} while sleeping"
            )
        if int(new_state.player_energy) > energy:
            log_func(f"[sleep] Energy {energy} -> {int(new_state.player_energy)}")
        state = new_state

    raise Exception(f"Sleeping failed: still asleep after {max_sleep_steps} sleeping steps")
