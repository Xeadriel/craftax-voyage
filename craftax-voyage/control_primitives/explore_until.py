# Description:
# Deterministically explores the current floor until a specific block type, item
# (torch or ladder) or mob becomes visible in the player's (lit) view window. If a block or item target was
# seen before but is out of view, it walks back towards the nearest remembered one, so it also works on a
# fully explored floor. Otherwise it uses frontier-based exploration over the player's memory of the floor:
# it repeatedly walks to the cheapest reachable known cell bordering never-seen territory, tunnelling
# through mineable blocks (trees, stone, ores, ...) when the equipped pickaxe allows it and waiting for /
# attacking mobs that block the path. Dark cells cannot be seen and are not explored. Mobs are not
# remembered, so mob targets are always explored for.
# Returns the final state when the target is seen, raises an Exception otherwise.

def explore_until(state, log_func, step_func, target, max_steps=20):
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
            RIPE_PLANT only matches ripe plants, PLANT only young plants.
            LADDER_DOWN matches the down ladder whether it is open or blocked;
            LADDER_DOWN_BLOCKED only matches it while it is still blocked
            (the ladder is not open yet)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        The final EnvState (after the last step) if the target became visible

    Raises:
        Exception: If the target is invalid, the down ladder is already open
            (LADDER_DOWN_BLOCKED), the player died, the target is neither in sight
            nor remembered at a reachable place and no reachable unexplored area
            is left, or max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        OBS_DIM,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
        MobType,
    )
    from control_primitives.knowledge import (
        UNKNOWN,
        is_visible,
        known_blocks,
        known_items,
        ladder_open,
        visible_mask,
        visible_mobs,
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
    # blocked is shown by the "Ladder Open" indicator
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
    unknown_cost = 2
    mob_extra_cost = 6
    max_mine_attempts = 3
    max_mob_wait_steps = 2
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2

    level = None
    dark_cells = None
    known_count = 0
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

        block_map = known_blocks(state)
        visible = visible_mask(state)
        map_rows, map_cols = block_map.shape
        mobs_in_view = visible_mobs(state)
        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in mobs_in_view:
            mob_occupied[mob_row, mob_col] = True

        if current_level != level:
            log_func(f"[explore_until] Now on floor {current_level}, resetting exploration goal")
            level = current_level
            # Cells that were in view but dark: they cannot be seen, so they are not explored
            dark_cells = np.zeros((map_rows, map_cols), dtype=bool)
            known_count = int(np.sum(block_map != UNKNOWN))
            current_goal = None
            failed_mine_attempts = {}
            unminable_cells = set()
            mob_block_steps = 0

        if target_kind == "item" and target == ItemType.LADDER_DOWN_BLOCKED and ladder_open(state):
            log_func(f"[explore_until] The down ladder on floor {current_level} is open")
            raise Exception(
                f"Exploration failed: the down ladder on floor {current_level} is not blocked anymore"
            )

        row_start = max(0, player_row - half_rows)
        row_end = min(map_rows, player_row + half_rows + 1)
        col_start = max(0, player_col - half_cols)
        col_end = min(map_cols, player_col + half_cols + 1)
        dark_cells[row_start:row_end, col_start:col_end] |= ~visible[row_start:row_end, col_start:col_end]
        unknown = block_map == UNKNOWN
        dark_cells &= unknown

        new_known_count = int(np.sum(~unknown))
        newly_seen = new_known_count - known_count
        known_count = new_known_count

        log_func(
            f"[explore_until] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"floor {current_level}, facing {action_names.get(int(state.player_direction), state.player_direction)}, "
            f"health {float(state.player_health):.1f}, revealed {newly_seen} new cells, "
            f"known {known_count}/{map_rows * map_cols} cells"
        )

        # Check whether the target is visible
        if target_kind in ("block", "item"):
            if target_kind == "block":
                matches = np.argwhere((block_map == target.value) & visible)
            else:
                matches = np.argwhere((known_items(state) == target_item_value) & visible)
            if len(matches) > 0:
                found = min(
                    (
                        abs(int(m[0]) - player_row) + abs(int(m[1]) - player_col),
                        int(m[0]),
                        int(m[1]),
                    )
                    for m in matches
                )
                ladder_state = ""
                if target_item_value == ItemType.LADDER_DOWN.value:
                    ladder_state = " (open)" if ladder_open(state) else " (blocked)"
                log_func(
                    f"[explore_until] Found {target_name}{ladder_state} at ({found[1]}, {found[2]}), "
                    f"distance {found[0]}, after {steps_taken} steps"
                )
                return state
        else:
            for mob_class, mob_type_id, mob_row, mob_col, _ in mobs_in_view:
                if mob_class != target_mob_class:
                    continue
                if target_mob_type_id is not None and mob_type_id != target_mob_type_id:
                    continue
                log_func(
                    f"[explore_until] Found {target_mob_class.name} mob (type_id {mob_type_id}) "
                    f"at ({mob_row}, {mob_col}) after {steps_taken} steps"
                )
                return state

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

            # Dijkstra over the known floor; never-seen cells are assumed walkable at an extra
            # cost (but never as the next step), tunnelling and passing mobs cost extra
            distance = np.full((map_rows, map_cols), np.inf)
            previous = {}
            distance[player_row, player_col] = 0
            heap = [(0, player_row, player_col)]
            while heap:
                cost_so_far, row, col = heapq.heappop(heap)
                if cost_so_far > distance[row, col]:
                    continue
                is_start = (row, col) == (player_row, player_col)
                for _, d_row, d_col in moves:
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < map_rows and 0 <= next_col < map_cols):
                        continue
                    if (next_row, next_col) in unminable_cells:
                        continue
                    block = int(block_map[next_row, next_col])
                    if block == UNKNOWN:
                        if is_start or dark_cells[next_row, next_col]:
                            continue
                        move_cost = walk_cost + unknown_cost
                    elif block in tunnel_pickaxe_requirement:
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

            # Frontier: reachable known cells with at least one never-seen (and not dark) 4-neighbour
            explorable = unknown & ~dark_cells
            borders_unknown = np.zeros_like(explorable)
            borders_unknown[1:, :] |= explorable[:-1, :]
            borders_unknown[:-1, :] |= explorable[1:, :]
            borders_unknown[:, 1:] |= explorable[:, :-1]
            borders_unknown[:, :-1] |= explorable[:, 1:]
            frontier = np.isfinite(distance) & ~unknown & borders_unknown
            frontier[player_row, player_col] = False

            # Targets remembered from earlier but out of view: walking back towards the nearest
            # one brings it into view, which beats exploring (the floor may be fully explored).
            # Remembered targets inside the view window are dark and cannot be confirmed
            remembered_count = 0
            approach = np.zeros_like(frontier)
            if target_kind in ("block", "item"):
                if target_kind == "block":
                    remembered = block_map == target.value
                else:
                    remembered = known_items(state) == target_item_value
                in_window = np.zeros_like(remembered)
                in_window[row_start:row_end, col_start:col_end] = True
                remembered &= ~in_window
                remembered_count = int(np.sum(remembered))
                # Stand on the target or next to it (blocks like water cannot be stood on)
                approach |= remembered
                approach[1:, :] |= remembered[:-1, :]
                approach[:-1, :] |= remembered[1:, :]
                approach[:, 1:] |= remembered[:, :-1]
                approach[:, :-1] |= remembered[:, 1:]
                approach &= np.isfinite(distance) & ~unknown
                approach[player_row, player_col] = False

            if approach.any():
                goal_cells, goal_kind = approach, "remembered"
            else:
                goal_cells, goal_kind = frontier, "frontier"

            if current_goal is not None and not goal_cells[current_goal]:
                log_func(f"[explore_until] Goal {current_goal} is no longer a reachable {goal_kind} goal, choosing a new one")
                current_goal = None

            if current_goal is None:
                candidates = np.argwhere(goal_cells)
                if len(candidates) > 0:
                    best = min(
                        (float(distance[int(c[0]), int(c[1])]), int(c[0]), int(c[1]))
                        for c in candidates
                    )
                    current_goal = (best[1], best[2])
                    if goal_kind == "remembered":
                        log_func(
                            f"[explore_until] {target_name} was seen before but is out of view, heading back "
                            f"to {current_goal} with path cost {best[0]:.0f} ({remembered_count} remembered)"
                        )
                    else:
                        log_func(
                            f"[explore_until] New exploration goal {current_goal} with path cost {best[0]:.0f} "
                            f"({len(candidates)} frontier cells available)"
                        )

            if current_goal is None:
                log_func(f"[explore_until] No reachable unexplored area left on floor {current_level}")
                if remembered_count > 0:
                    raise Exception(
                        f"Exploration failed: {remembered_count} remembered {target_name} cell(s) on floor "
                        f"{current_level} cannot be reached, even by tunnelling, and no reachable "
                        f"unexplored area is left"
                    )
                raise Exception(
                    f"Exploration failed: no reachable unexplored area left on floor {current_level} "
                    f"and no {target_name} in sight or remembered"
                )

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

        if float(new_state.player_health) <= 0:
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
            # Only trust the mined cell's new block type if it can be seen
            new_block = int(block_map[mining_cell])
            if is_visible(new_state, mining_cell[0], mining_cell[1]):
                new_block = int(known_blocks(new_state)[mining_cell])
            if new_block == int(block_map[mining_cell]):
                failed_mine_attempts[mining_cell] = failed_mine_attempts.get(mining_cell, 0) + 1
                log_func(
                    f"[explore_until] Mining {mining_cell} had no visible effect "
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
