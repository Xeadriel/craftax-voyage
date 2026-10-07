# Description:
# Deterministically walks to the nearest water source (water or fountain) in sight and
# drinks from it a given number of times. Plans with Dijkstra, tunnelling through
# mineable blocks (trees, stone, ores, ...) when the pickaxe allows it. Mobs are treated
# as obstacles; if mobs block every path and no path can be mined around them, it waits a
# few steps for them to move and then raises. Drinking is verified through the drink
# intrinsic. Returns True after `number` drinks, raises an Exception otherwise.

def drink(state, log_func, step_func, number=1, max_steps=100):
    """
    Drinks `number` times from the nearest water source in sight.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        number: Number of times to drink (a drink at full thirst still counts but has no effect)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if the player drank `number` times

    Raises:
        Exception: If the arguments are invalid, no water source is in sight, no water
            source is reachable (even by tunnelling), mobs keep blocking every path,
            drinking keeps failing, the player died, the player left the floor, or
            max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        OBS_DIM,
        SOLID_BLOCKS,
        Action,
        BlockType,
    )
    from craftax.craftax.util.game_logic_utils import get_max_drink

    # Validate the arguments
    if isinstance(number, bool) or not isinstance(number, (int, np.integer)):
        raise Exception(f"Invalid number {number!r}: expected an integer")
    number = int(number)
    if number < 0:
        raise Exception(f"Invalid number {number}: must be non-negative")
    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    action_names = {action.value: action.name for action in Action}

    water_blocks = {BlockType.WATER.value, BlockType.FOUNTAIN.value}
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
    max_failed_attempts = 3
    max_mob_wait_steps = 3
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2

    start_level = int(state.player_level)
    drinks = 0
    current_source = None
    failed_drinks = 0
    failed_mines = {}
    blocked_cells = set()
    mob_wait_steps = 0

    log_func(
        f"[drink] Start drinking {number} time(s) with a budget of {max_steps} steps "
        f"(drink {int(state.player_drink)}/{int(get_max_drink(state))})"
    )

    if number == 0:
        log_func("[drink] Nothing to drink")
        return True

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)
        drink_level = int(state.player_drink)
        max_drink = int(get_max_drink(state))

        if current_level != start_level:
            log_func(f"[drink] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Drinking failed: player left floor {start_level}")

        log_func(
            f"[drink] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, drank {drinks}/{number}, "
            f"drink {drink_level}/{max_drink}, health {float(state.player_health):.1f}"
        )

        if drinks >= number:
            log_func(f"[drink] Successfully drank {drinks} time(s) in {steps_taken} steps")
            return True

        if steps_taken >= max_steps:
            log_func(f"[drink] Max steps ({max_steps}) reached after drinking {drinks}/{number} time(s)")
            raise Exception(
                f"Drinking failed: max steps ({max_steps}) reached after drinking {drinks}/{number} time(s)"
            )

        block_map = np.asarray(state.map[current_level])
        light_visible = np.asarray(state.light_map[current_level]) > 0.05
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape
        pickaxe_level = int(state.inventory.pickaxe)

        # Water sources in the (lit) view window
        row_start = max(0, player_row - half_rows)
        row_end = min(map_rows, player_row + half_rows + 1)
        col_start = max(0, player_col - half_cols)
        col_end = min(map_cols, player_col + half_cols + 1)
        visible_sources = [
            (int(cell[0]) + row_start, int(cell[1]) + col_start)
            for cell in np.argwhere(
                np.isin(block_map[row_start:row_end, col_start:col_end], list(water_blocks))
                & light_visible[row_start:row_end, col_start:col_end]
            )
        ]
        if current_source is not None and int(block_map[current_source]) not in water_blocks:
            log_func(f"[drink] Water source {current_source} is gone")
            current_source = None
        if current_source is None and len(visible_sources) == 0:
            log_func("[drink] No water source is in sight")
            raise Exception(
                f"Drinking failed: no water source in sight after drinking {drinks}/{number} time(s)"
            )

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        drinking_cell = None
        mining_cell = None
        expected_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            # Dijkstra twice: first treating mobs as walls, then ignoring them to tell whether
            # mobs are what blocks the way
            plans = {}
            for mobs_block in (True, False):
                distance = np.full((map_rows, map_cols), np.inf)
                previous = {}
                distance[player_row, player_col] = 0
                heap = [(0, player_row, player_col)]
                while heap:
                    cost_so_far, row, col = heapq.heappop(heap)
                    if cost_so_far > distance[row, col]:
                        continue
                    # Water sources are path end points, never walked through
                    if (row, col) != (player_row, player_col) and int(block_map[row, col]) in water_blocks:
                        continue
                    for _, d_row, d_col in moves:
                        next_row = row + d_row
                        next_col = col + d_col
                        if not (0 <= next_row < map_rows and 0 <= next_col < map_cols):
                            continue
                        if (next_row, next_col) in blocked_cells:
                            continue
                        if mobs_block and mob_occupied[next_row, next_col]:
                            continue
                        block = int(block_map[next_row, next_col])
                        if block in water_blocks:
                            move_cost = walk_cost
                        elif block in tunnel_pickaxe_requirement:
                            if pickaxe_level < tunnel_pickaxe_requirement[block]:
                                continue
                            move_cost = tunnel_cost
                        elif block in impassable_blocks:
                            continue
                        else:
                            move_cost = walk_cost
                        new_cost = cost_so_far + move_cost
                        if new_cost < distance[next_row, next_col]:
                            distance[next_row, next_col] = new_cost
                            previous[(next_row, next_col)] = (row, col)
                            heapq.heappush(heap, (new_cost, next_row, next_col))
                plans[mobs_block] = (distance, previous)

            distance, previous = plans[True]
            if current_source is not None and not np.isfinite(distance[current_source]):
                log_func(f"[drink] Water source {current_source} is not reachable right now")
                current_source = None

            if current_source is None:
                reachable = [
                    (float(distance[cell]), cell[0], cell[1])
                    for cell in visible_sources if np.isfinite(distance[cell])
                ]
                if reachable:
                    best = min(reachable)
                    current_source = (best[1], best[2])
                    mob_wait_steps = 0
                    log_func(
                        f"[drink] Heading for {BlockType(int(block_map[current_source])).name} at "
                        f"{current_source} with path cost {best[0]:.0f}"
                    )
                else:
                    mob_free_distance = plans[False][0]
                    if any(np.isfinite(mob_free_distance[cell]) for cell in visible_sources):
                        mob_wait_steps += 1
                        if mob_wait_steps > max_mob_wait_steps:
                            log_func(
                                f"[drink] Mobs block every path to the water for {max_mob_wait_steps} steps "
                                f"and no path can be mined around them"
                            )
                            raise Exception(
                                f"Drinking failed: mobs block every path to the water source "
                                f"after drinking {drinks}/{number} time(s)"
                            )
                        action_reason = (
                            f"mobs block every path to the water, waiting for them to move "
                            f"({mob_wait_steps}/{max_mob_wait_steps})"
                        )
                    else:
                        log_func(
                            f"[drink] None of the {len(visible_sources)} water source(s) in sight is reachable, "
                            f"even by tunnelling with {['no pickaxe', 'a wood pickaxe', 'a stone pickaxe', 'an iron pickaxe', 'a diamond pickaxe'][min(pickaxe_level, 4)]}"
                        )
                        raise Exception(
                            f"Drinking failed: no water source in sight is reachable "
                            f"after drinking {drinks}/{number} time(s)"
                        )

            if current_source is not None:
                # Reconstruct the first step of the path towards the water source
                cell = current_source
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
                next_name = BlockType(next_block).name

                if facing != move_action and (next_block in water_blocks or next_block in tunnel_pickaxe_requirement):
                    action = move_action
                    action_reason = f"turning towards {next_name} at ({next_row}, {next_col})"
                elif next_block in water_blocks:
                    action = Action.DO.value
                    drinking_cell = (next_row, next_col)
                    action_reason = (
                        f"drinking from {next_name} at ({next_row}, {next_col}) "
                        f"(drink {drinks + 1}/{number}, drink level {drink_level}/{max_drink})"
                    )
                elif next_block in tunnel_pickaxe_requirement:
                    action = Action.DO.value
                    mining_cell = (next_row, next_col)
                    action_reason = (
                        f"mining {next_name} at ({next_row}, {next_col}) to tunnel towards the water at {current_source}"
                    )
                else:
                    action = move_action
                    expected_cell = (next_row, next_col)
                    action_reason = (
                        f"moving to ({next_row}, {next_col}) towards the water at {current_source} "
                        f"(path cost {float(distance[current_source]):.0f})"
                    )

        # ---------- Act ----------
        log_func(f"[drink] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Drinking failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[drink] The player died or the episode ended")
            raise Exception(f"Drinking failed: the player died after drinking {drinks}/{number} time(s)")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[drink] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if expected_cell is not None:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(f"[drink] Move to {expected_cell} did not succeed, still at {new_position}; replanning")

        if drinking_cell is not None:
            new_drink_level = int(new_state.player_drink)
            if new_drink_level > drink_level or drink_level >= max_drink:
                drinks += 1
                failed_drinks = 0
                log_func(
                    f"[drink] Drank from {drinking_cell} ({drinks}/{number}), drink {drink_level} -> {new_drink_level}"
                    + (" (already full)" if drink_level >= max_drink else "")
                )
            else:
                failed_drinks += 1
                log_func(
                    f"[drink] Drinking from {drinking_cell} had no effect, a mob may be in the way "
                    f"({failed_drinks}/{max_failed_attempts})"
                )
                if failed_drinks >= max_failed_attempts:
                    blocked_cells.add(drinking_cell)
                    current_source = None
                    failed_drinks = 0
                    log_func(f"[drink] Giving up on water source {drinking_cell}")

        if mining_cell is not None:
            old_block = int(block_map[mining_cell])
            new_block = int(new_state.map[current_level, mining_cell[0], mining_cell[1]])
            if new_block != old_block:
                failed_mines.pop(mining_cell, None)
                log_func(f"[drink] Mined {BlockType(old_block).name} at {mining_cell}, it is now {BlockType(new_block).name}")
            else:
                failed_mines[mining_cell] = failed_mines.get(mining_cell, 0) + 1
                log_func(
                    f"[drink] Mining {BlockType(old_block).name} at {mining_cell} had no effect "
                    f"({failed_mines[mining_cell]}/{max_failed_attempts})"
                )
                if failed_mines[mining_cell] >= max_failed_attempts:
                    blocked_cells.add(mining_cell)
                    current_source = None
                    log_func(f"[drink] Treating {mining_cell} as impassable from now on")

        state = new_state

    raise Exception(f"Drinking failed: max steps ({max_steps}) reached after drinking {drinks}/{number} time(s)")
