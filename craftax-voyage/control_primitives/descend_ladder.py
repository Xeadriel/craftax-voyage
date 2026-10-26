# Description:
# Deterministically walks onto the down ladder of the current floor and descends it to the next
# floor. The ladder must be open (enough monsters killed on this floor, shown as "Ladder Open")
# and known: it is taken from the player's memory of the floor, so it must have been seen before
# (explore for ItemType.LADDER_DOWN first). Plans with Dijkstra over the known floor (never-seen
# cells are assumed walkable at an extra cost but are never stepped into directly), tunnelling
# through mineable blocks (trees, stone, ores, ...) when the pickaxe allows it and waiting for /
# attacking mobs that block the path. The descent is verified through the player's floor.
# Returns the final state on the new floor (standing on its up ladder), raises an Exception otherwise.

def descend_ladder(state, log_func, step_func, max_steps=20):
    """
    Walks onto the down ladder of the current floor and descends it.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        The final EnvState (after the last step) once the player is on the next
        floor, standing on that floor's up ladder

    Raises:
        Exception: If max_steps is invalid, the player is on the boss floor (it has
            no down ladder), the down ladder is closed (kill more monsters on this
            floor first), the down ladder was never seen (explore first), it cannot
            be reached over the known map (even by tunnelling), descending keeps
            failing, the player died, or max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        MONSTERS_KILLED_TO_CLEAR_LEVEL,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
    )
    from control_primitives.knowledge import (
        UNKNOWN,
        is_visible,
        known_blocks,
        known_items,
        ladder_open,
        visible_mobs,
    )

    # Validate the arguments
    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    start_level = int(state.player_level)
    boss_level = int(state.map.shape[0]) - 1

    if start_level >= boss_level:
        log_func(f"[descend_ladder] Floor {start_level} is the boss floor, it has no down ladder")
        raise Exception(
            f"Descending failed: floor {start_level} is the boss floor (the deepest floor), it has no down ladder"
        )

    if not ladder_open(state):
        killed = int(state.monsters_killed[start_level])
        log_func(
            f"[descend_ladder] The down ladder on floor {start_level} is closed "
            f"({killed}/{MONSTERS_KILLED_TO_CLEAR_LEVEL} monsters killed)"
        )
        raise Exception(
            f"Descending failed: the down ladder on floor {start_level} is closed, kill "
            f"{MONSTERS_KILLED_TO_CLEAR_LEVEL - killed} more monster(s) on this floor first "
            f"({killed}/{MONSTERS_KILLED_TO_CLEAR_LEVEL} killed)"
        )

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
        BlockType.NECROMANCER_VULNERABLE.value,
    }
    # Blocks DO turns into a walkable block, with the required pickaxe level
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

    walk_cost = 1
    tunnel_cost = 4
    unknown_cost = 2
    mob_extra_cost = 6
    max_failed_attempts = 3
    max_mob_wait_steps = 2

    failed_descents = 0
    failed_mines = {}
    blocked_cells = set()
    mob_block_steps = 0

    log_func(f"[descend_ladder] Start descending from floor {start_level} with a budget of {max_steps} steps")

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level == start_level + 1:
            log_func(
                f"[descend_ladder] Successfully descended to floor {current_level} in {steps_taken} steps, "
                f"now at ({player_row}, {player_col})"
            )
            return state
        if current_level != start_level:
            log_func(f"[descend_ladder] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Descending failed: player moved from floor {start_level} to floor {current_level}")

        log_func(
            f"[descend_ladder] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"floor {current_level}, facing {action_names.get(facing, facing)}, "
            f"health {float(state.player_health):.1f}"
        )

        if steps_taken >= max_steps:
            log_func(f"[descend_ladder] Max steps ({max_steps}) reached without descending")
            raise Exception(f"Descending failed: max steps ({max_steps}) reached without descending")

        # The player's memory of the floor and the mobs in view
        block_map = known_blocks(state)
        map_rows, map_cols = block_map.shape
        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in visible_mobs(state):
            mob_occupied[mob_row, mob_col] = True
        pickaxe_level = int(state.inventory.pickaxe)

        ladder_cells = np.argwhere(known_items(state) == ItemType.LADDER_DOWN.value)
        if len(ladder_cells) == 0:
            log_func(f"[descend_ladder] The down ladder on floor {current_level} has not been seen yet")
            raise Exception(
                f"Descending failed: the down ladder on floor {current_level} has not been seen yet, "
                f"explore for ItemType.LADDER_DOWN first"
            )
        ladder = (int(ladder_cells[0][0]), int(ladder_cells[0][1]))

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        descending = False
        mining_cell = None
        expected_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        elif (player_row, player_col) == ladder:
            action = Action.DESCEND.value
            descending = True
            action_reason = f"descending the down ladder at {ladder} to floor {current_level + 1}"
        else:
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
                    if (next_row, next_col) in blocked_cells:
                        continue
                    block = int(block_map[next_row, next_col])
                    if block == UNKNOWN:
                        if is_start:
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

            if not np.isfinite(distance[ladder]):
                log_func(
                    f"[descend_ladder] The down ladder at {ladder} cannot be reached over the known map, "
                    f"even by tunnelling with "
                    f"{['no pickaxe', 'a wood pickaxe', 'a stone pickaxe', 'an iron pickaxe', 'a diamond pickaxe'][min(pickaxe_level, 4)]}"
                )
                raise Exception(f"Descending failed: the down ladder at {ladder} cannot be reached")

            # Reconstruct the first step of the path towards the ladder
            cell = ladder
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
            facing_next = facing == move_action

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
                            f"to tunnel towards the down ladder at {ladder}"
                        )
                else:
                    action = move_action
                    expected_cell = (next_row, next_col)
                    action_reason = (
                        f"moving to ({next_row}, {next_col}) towards the down ladder at {ladder} "
                        f"(path cost {float(distance[ladder]):.0f})"
                    )

        # ---------- Act ----------
        log_func(f"[descend_ladder] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Descending failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0:
            log_func("[descend_ladder] The player died")
            raise Exception("Descending failed: the player died")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[descend_ladder] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if descending and int(new_state.player_level) == start_level:
            failed_descents += 1
            log_func(
                f"[descend_ladder] Descending at {ladder} had no effect "
                f"({failed_descents}/{max_failed_attempts})"
            )
            if failed_descents >= max_failed_attempts:
                raise Exception(
                    f"Descending failed: descending the down ladder at {ladder} failed {max_failed_attempts} times"
                )

        if expected_cell is not None and int(new_state.player_level) == start_level:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(f"[descend_ladder] Move to {expected_cell} did not succeed, still at {new_position}; replanning")

        if mining_cell is not None and int(new_state.player_level) == start_level:
            # Only trust the mined cell's new block type if it can be seen
            old_block = int(block_map[mining_cell])
            new_block = old_block
            if is_visible(new_state, mining_cell[0], mining_cell[1]):
                new_block = int(known_blocks(new_state)[mining_cell])
            if new_block != old_block:
                failed_mines.pop(mining_cell, None)
                log_func(
                    f"[descend_ladder] Mined {BlockType(old_block).name} at {mining_cell}, "
                    f"it is now {BlockType(new_block).name}"
                )
            else:
                failed_mines[mining_cell] = failed_mines.get(mining_cell, 0) + 1
                log_func(
                    f"[descend_ladder] Mining {BlockType(old_block).name} at {mining_cell} had no visible effect "
                    f"({failed_mines[mining_cell]}/{max_failed_attempts})"
                )
                if failed_mines[mining_cell] >= max_failed_attempts:
                    blocked_cells.add(mining_cell)
                    log_func(f"[descend_ladder] Treating {mining_cell} as impassable from now on")

        state = new_state

    raise Exception(f"Descending failed: max steps ({max_steps}) reached without descending")
