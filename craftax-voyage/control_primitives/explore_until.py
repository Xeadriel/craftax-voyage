# Description:
# Deterministically explores the current floor until a specific block type, item
# (torch or ladder) or mob becomes visible in the player's (lit) view window. Uses frontier-based exploration:
# it repeatedly walks to the cheapest reachable cell bordering unexplored territory,
# tunnelling through mineable blocks (trees, stone, ores, ...) when the equipped
# pickaxe allows it and waiting for / attacking mobs that block the path.
# Returns True when the target is seen, raises an Exception otherwise.

def explore_until(state, log_func, step_func, target, max_steps=200):
    """
    Explores the current floor until the target is visible to the player.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        target: BlockType to look for, ItemType to look for (TORCH, LADDER_UP,
            LADDER_DOWN or LADDER_DOWN_BLOCKED), MobType to look for (any mob of
            that class), or a tuple (MobType, type_id) to look for one specific mob
            type (e.g. (MobType.PASSIVE, 0) is a cow on the overworld).
            LADDER_DOWN matches the down ladder whether it is open or blocked;
            LADDER_DOWN_BLOCKED only matches it while it is still blocked (fewer
            than MONSTERS_KILLED_TO_CLEAR_LEVEL monsters killed on the floor)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if the target became visible

    Raises:
        Exception: If the target is invalid, the block does not exist on the floor,
            the floor is already cleared (LADDER_DOWN_BLOCKED), the player died, the reachable area is exhausted, or max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        MONSTERS_KILLED_TO_CLEAR_LEVEL,
        OBS_DIM,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
        MobType,
    )

    # Resolve and validate the target
    target_mob_class = None
    target_mob_type_id = None
    if (
        isinstance(target, tuple)
        and len(target) == 2
        and isinstance(target[0], MobType)
        and isinstance(target[1], (int, np.integer))
        and not isinstance(target[1], bool)
    ):
        target_kind = "mob"
        target_mob_class = target[0]
        target_mob_type_id = int(target[1])
        target_name = f"mob {target_mob_class.name} (type_id {target_mob_type_id})"
    elif isinstance(target, MobType):
        target_kind = "mob"
        target_mob_class = target
        target_name = f"mob {target_mob_class.name}"
    elif isinstance(target, BlockType):
        target_kind = "block"
        target_name = f"block {target.name}"
    elif isinstance(target, ItemType):
        target_kind = "item"
        target_name = f"item {target.name}"
    else:
        raise Exception(
            f"Invalid target {target!r}: expected BlockType, ItemType, MobType or (MobType, type_id)"
        )

    if target_kind == "mob" and target_mob_class == MobType.PROJECTILE:
        raise Exception("Invalid target: projectiles cannot be explored for")
    if target_kind == "block" and target in (
        BlockType.INVALID,
        BlockType.OUT_OF_BOUNDS,
        BlockType.DARKNESS,
    ):
        raise Exception(f"Invalid target: {target.name} is not a real map block")
    if target_kind == "item" and target == ItemType.NONE:
        raise Exception("Invalid target: ItemType.NONE is not a real item")

    # Blocked down ladders are stored as LADDER_DOWN in the item map; whether they are
    # blocked depends on the number of monsters killed on the floor
    if target_kind == "item" and target in (ItemType.LADDER_DOWN, ItemType.LADDER_DOWN_BLOCKED):
        target_item_value = ItemType.LADDER_DOWN.value
    elif target_kind == "item":
        target_item_value = target.value
    else:
        target_item_value = None

    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    action_names = {action.value: action.name for action in Action}

    # Cells the player cannot stand on
    impassable_blocks = set(SOLID_BLOCKS) | {
        BlockType.WATER.value,
        BlockType.LAVA.value,
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
    }
    # Blocks that DO turns into a walkable block, with the required pickaxe level
    tunnel_pickaxe_requirement = {
        BlockType.TREE.value: 0,
        BlockType.FIRE_TREE.value: 0,
        BlockType.ICE_SHRUB.value: 0,
        BlockType.STONE.value: 1,
        BlockType.COAL.value: 1,
        BlockType.STALAGMITE.value: 1,
        BlockType.IRON.value: 2,
        BlockType.DIAMOND.value: 3,
        BlockType.SAPPHIRE.value: 4,
        BlockType.RUBY.value: 4,
    }
    if target_kind == "block":
        tunnel_pickaxe_requirement.pop(target.value, None)

    walk_cost = 1
    tunnel_cost = 4
    mob_extra_cost = 6
    max_mine_attempts = 3
    max_mob_wait_steps = 2
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2

    level = None
    seen = None
    current_goal = None
    failed_mine_attempts = {}
    unminable_cells = set()
    mob_block_steps = 0

    log_func(
        f"[explore_until] Start exploring for {target_name} with a budget of {max_steps} steps"
    )

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)

        block_map = np.asarray(state.map[current_level])
        light_visible = np.asarray(state.light_map[current_level]) > 0.05
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape

        if current_level != level:
            log_func(f"[explore_until] Now on floor {current_level}, resetting exploration memory")
            level = current_level
            seen = np.zeros((map_rows, map_cols), dtype=bool)
            current_goal = None
            failed_mine_attempts = {}
            unminable_cells = set()
            mob_block_steps = 0
            if target_kind == "block":
                exists = bool(np.any(block_map == target.value))
                if not exists and target == BlockType.RIPE_PLANT:
                    exists = bool(np.any(block_map == BlockType.PLANT.value))
                if not exists:
                    raise Exception(
                        f"Exploration failed: no {target_name} exists on floor {current_level}"
                    )
            if target_kind == "item":
                if not bool(np.any(np.asarray(state.item_map[current_level]) == target_item_value)):
                    raise Exception(
                        f"Exploration failed: no {target_name} exists on floor {current_level}"
                    )

        floor_cleared = (
            int(state.monsters_killed[current_level]) >= MONSTERS_KILLED_TO_CLEAR_LEVEL
        )
        if target_kind == "item" and target == ItemType.LADDER_DOWN_BLOCKED and floor_cleared:
            log_func(
                f"[explore_until] Floor {current_level} is cleared "
                f"({int(state.monsters_killed[current_level])} monsters killed), the down ladder is open"
            )
            raise Exception(
                f"Exploration failed: the down ladder on floor {current_level} is not blocked anymore"
            )

        row_start = max(0, player_row - half_rows)
        row_end = min(map_rows, player_row + half_rows + 1)
        col_start = max(0, player_col - half_cols)
        col_end = min(map_cols, player_col + half_cols + 1)
        newly_seen = int(np.sum(~seen[row_start:row_end, col_start:col_end]))
        seen[row_start:row_end, col_start:col_end] = True

        log_func(
            f"[explore_until] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"floor {current_level}, facing {action_names.get(int(state.player_direction), state.player_direction)}, "
            f"health {float(state.player_health):.1f}, revealed {newly_seen} new cells, "
            f"explored {int(np.sum(seen))}/{map_rows * map_cols} cells"
        )

        # Check whether the target is visible
        if target_kind == "block":
            matches = np.argwhere(
                (block_map[row_start:row_end, col_start:col_end] == target.value)
                & light_visible[row_start:row_end, col_start:col_end]
            )
            if len(matches) > 0:
                found = min(
                    (
                        abs(int(m[0]) + row_start - player_row) + abs(int(m[1]) + col_start - player_col),
                        int(m[0]) + row_start,
                        int(m[1]) + col_start,
                    )
                    for m in matches
                )
                log_func(
                    f"[explore_until] Found {target_name} at ({found[1]}, {found[2]}), "
                    f"distance {found[0]}, after {steps_taken} steps"
                )
                return True
        elif target_kind == "item":
            item_map = np.asarray(state.item_map[current_level])
            matches = np.argwhere(
                (item_map[row_start:row_end, col_start:col_end] == target_item_value)
                & light_visible[row_start:row_end, col_start:col_end]
            )
            if len(matches) > 0:
                found = min(
                    (
                        abs(int(m[0]) + row_start - player_row) + abs(int(m[1]) + col_start - player_col),
                        int(m[0]) + row_start,
                        int(m[1]) + col_start,
                    )
                    for m in matches
                )
                ladder_state = ""
                if target_item_value == ItemType.LADDER_DOWN.value:
                    ladder_state = (
                        " (open)" if floor_cleared else
                        f" (blocked, {int(state.monsters_killed[current_level])}/"
                        f"{MONSTERS_KILLED_TO_CLEAR_LEVEL} monsters killed)"
                    )
                log_func(
                    f"[explore_until] Found {target_name}{ladder_state} at ({found[1]}, {found[2]}), "
                    f"distance {found[0]}, after {steps_taken} steps"
                )
                return True
        else:
            mobs = {
                MobType.PASSIVE: state.passive_mobs,
                MobType.MELEE: state.melee_mobs,
                MobType.RANGED: state.ranged_mobs,
            }[target_mob_class]
            mob_mask = np.asarray(mobs.mask[current_level])
            mob_positions = np.asarray(mobs.position[current_level])
            mob_type_ids = np.asarray(mobs.type_id[current_level])
            for mob_index in range(len(mob_mask)):
                if not mob_mask[mob_index]:
                    continue
                if target_mob_type_id is not None and int(mob_type_ids[mob_index]) != target_mob_type_id:
                    continue
                mob_row = int(mob_positions[mob_index][0])
                mob_col = int(mob_positions[mob_index][1])
                if (
                    abs(mob_row - player_row) <= half_rows
                    and abs(mob_col - player_col) <= half_cols
                    and 0 <= mob_row < map_rows
                    and 0 <= mob_col < map_cols
                    and light_visible[mob_row, mob_col]
                ):
                    log_func(
                        f"[explore_until] Found {target_mob_class.name} mob (type_id {int(mob_type_ids[mob_index])}) "
                        f"at ({mob_row}, {mob_col}) after {steps_taken} steps"
                    )
                    return True

        if steps_taken >= max_steps:
            log_func(f"[explore_until] Max steps ({max_steps}) reached without finding {target_name}")
            raise Exception(
                f"Exploration failed: max steps ({max_steps}) reached without finding {target_name}"
            )

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        expected_cell = None
        mining_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            pickaxe_level = int(state.inventory.pickaxe)

            # Dijkstra over explored cells; tunnelling and passing mobs cost extra
            distance = np.full((map_rows, map_cols), np.inf)
            previous = {}
            distance[player_row, player_col] = 0
            heap = [(0, player_row, player_col)]
            while heap:
                cost_so_far, row, col = heapq.heappop(heap)
                if cost_so_far > distance[row, col]:
                    continue
                for _, d_row, d_col in moves:
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < map_rows and 0 <= next_col < map_cols):
                        continue
                    if not seen[next_row, next_col] or (next_row, next_col) in unminable_cells:
                        continue
                    block = int(block_map[next_row, next_col])
                    if block in tunnel_pickaxe_requirement:
                        if pickaxe_level < tunnel_pickaxe_requirement[block]:
                            continue
                        move_cost = tunnel_cost
                    elif block in impassable_blocks:
                        continue
                    else:
                        move_cost = walk_cost
                    if mob_occupied[next_row, next_col]:
                        move_cost += mob_extra_cost
                    new_cost = cost_so_far + move_cost
                    if new_cost < distance[next_row, next_col]:
                        distance[next_row, next_col] = new_cost
                        previous[(next_row, next_col)] = (row, col)
                        heapq.heappush(heap, (new_cost, next_row, next_col))

            # Frontier: reachable cells with at least one unexplored 4-neighbour
            unseen = ~seen
            borders_unseen = np.zeros_like(seen)
            borders_unseen[1:, :] |= unseen[:-1, :]
            borders_unseen[:-1, :] |= unseen[1:, :]
            borders_unseen[:, 1:] |= unseen[:, :-1]
            borders_unseen[:, :-1] |= unseen[:, 1:]
            frontier = np.isfinite(distance) & borders_unseen
            frontier[player_row, player_col] = False

            if current_goal is not None and not frontier[current_goal]:
                log_func(f"[explore_until] Goal {current_goal} is no longer a reachable frontier, choosing a new one")
                current_goal = None

            if current_goal is None:
                frontier_cells = np.argwhere(frontier)
                if len(frontier_cells) > 0:
                    best = min(
                        (float(distance[int(c[0]), int(c[1])]), int(c[0]), int(c[1]))
                        for c in frontier_cells
                    )
                    current_goal = (best[1], best[2])
                    log_func(
                        f"[explore_until] New exploration goal {current_goal} with path cost {best[0]:.0f} "
                        f"({len(frontier_cells)} frontier cells available)"
                    )

            if current_goal is None:
                if target_kind == "block":
                    log_func(f"[explore_until] No reachable unexplored area left on floor {current_level}")
                    raise Exception(
                        f"Exploration failed: explored all reachable area on floor {current_level} "
                        f"without finding {target_name}"
                    )
                # Mobs move and spawn, so forget the explored area and sweep again
                seen[:, :] = False
                seen[row_start:row_end, col_start:col_end] = True
                action_reason = (
                    "all reachable area explored without seeing the mob, "
                    "resetting exploration memory and waiting for mobs to move/spawn"
                )
            else:
                # Reconstruct the first step of the path towards the goal
                cell = current_goal
                for _ in range(map_rows * map_cols):
                    if previous[cell] == (player_row, player_col):
                        break
                    cell = previous[cell]
                next_row, next_col = cell
                move_action = next(
                    a for a, d_row, d_col in moves
                    if player_row + d_row == next_row and player_col + d_col == next_col
                )
                next_block = int(block_map[next_row, next_col])
                facing_next = int(state.player_direction) == move_action

                if mob_occupied[next_row, next_col]:
                    mob_block_steps += 1
                    if mob_block_steps <= max_mob_wait_steps:
                        action_reason = (
                            f"mob blocks next cell ({next_row}, {next_col}), waiting "
                            f"({mob_block_steps}/{max_mob_wait_steps})"
                        )
                    elif not facing_next:
                        action = move_action
                        action_reason = f"turning towards blocking mob at ({next_row}, {next_col})"
                    else:
                        action = Action.DO.value
                        action_reason = f"attacking blocking mob at ({next_row}, {next_col})"
                else:
                    mob_block_steps = 0
                    if next_block in tunnel_pickaxe_requirement:
                        if not facing_next:
                            action = move_action
                            action_reason = (
                                f"turning towards {BlockType(next_block).name} at ({next_row}, {next_col}) to tunnel"
                            )
                        else:
                            action = Action.DO.value
                            mining_cell = (next_row, next_col)
                            action_reason = (
                                f"mining {BlockType(next_block).name} at ({next_row}, {next_col}) "
                                f"to tunnel towards goal {current_goal}"
                            )
                    else:
                        action = move_action
                        expected_cell = (next_row, next_col)
                        action_reason = f"moving to ({next_row}, {next_col}) towards goal {current_goal}"

        # ---------- Act ----------
        log_func(f"[explore_until] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Exploration failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[explore_until] The player died during exploration")
            raise Exception(f"Exploration failed: the player died while exploring for {target_name}")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[explore_until] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if expected_cell is not None and int(new_state.player_level) == current_level:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(
                    f"[explore_until] Move to {expected_cell} did not succeed, still at {new_position}; replanning"
                )

        if mining_cell is not None and int(new_state.player_level) == current_level:
            new_block = int(new_state.map[current_level, mining_cell[0], mining_cell[1]])
            if new_block == int(block_map[mining_cell]):
                failed_mine_attempts[mining_cell] = failed_mine_attempts.get(mining_cell, 0) + 1
                log_func(
                    f"[explore_until] Mining {mining_cell} had no effect "
                    f"({failed_mine_attempts[mining_cell]}/{max_mine_attempts})"
                )
                if failed_mine_attempts[mining_cell] >= max_mine_attempts:
                    unminable_cells.add(mining_cell)
                    current_goal = None
                    log_func(f"[explore_until] Treating {mining_cell} as impassable from now on")
            else:
                log_func(
                    f"[explore_until] Mined {mining_cell}, it is now {BlockType(new_block).name}"
                )

        state = new_state

    raise Exception(f"Exploration failed: max steps ({max_steps}) reached without finding {target_name}")
