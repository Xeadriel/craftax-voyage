# Description:
# Deterministically collects a given number of saplings. Saplings drop with a 10%
# chance whenever the player hits a GRASS block with DO (the grass stays). Plans the
# shortest sequence of movement/turn actions until the player faces a known grass block
# without a visible mob on it (shortest-path search over position and facing direction
# on the known map, since pressing a direction moves the player onto walkable cells and
# only turns it towards blocked ones; never-seen cells count as walkable but more
# expensive and are never the next step), then hits the grass until enough saplings
# were collected.
# Returns True on success, raises an Exception otherwise.

def collect_sapling(state, log_func, step_func, number=1, max_steps=20):
    """
    Collects `number` saplings by hitting grass blocks.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        number: Number of saplings to collect (in addition to the ones already owned)
        max_steps: Maximum number of calls to step_func before giving up
            (each hit has a 10% drop chance, so plan roughly 10-30 steps per sapling)

    Returns:
        The final EnvState (after the last step) if `number` saplings were collected

    Raises:
        Exception: If the arguments are invalid, the inventory cannot hold that many
            saplings, no known grass block is reachable (explore first), the player
            died, the player left the floor, or max_steps was reached
    """
    import heapq

    import numpy as np

    from control_primitives.knowledge import UNKNOWN, known_blocks, visible_mobs
    from craftax.craftax.constants import (
        DIRECTIONS,
        SOLID_BLOCKS,
        Action,
        BlockType,
    )

    inventory_cap = 99
    sapling_drop_chance = 0.1

    # Validate the arguments
    if isinstance(number, bool) or not isinstance(number, (int, np.integer)):
        raise Exception(f"Invalid number {number!r}: expected an integer")
    number = int(number)
    if number < 0:
        raise Exception(f"Invalid number {number}: must be non-negative")
    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    start_saplings = int(state.inventory.sapling)
    goal_saplings = start_saplings + number
    if goal_saplings > inventory_cap:
        raise Exception(
            f"Invalid number {number}: the player has {start_saplings} saplings and can hold at most {inventory_cap}"
        )

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    move_offsets = {a: (d_row, d_col) for a, d_row, d_col in moves}
    action_index = {a: index for index, (a, _, _) in enumerate(moves)}
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

    start_level = int(state.player_level)
    hits = 0
    hits_since_last_sapling = 0

    log_func(
        f"[collect_sapling] Start collecting {number} sapling(s) with a budget of {max_steps} steps "
        f"(owning {start_saplings}, drop chance {sapling_drop_chance:.0%} per hit)"
    )

    if number == 0:
        log_func("[collect_sapling] Nothing to collect")
        return state

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)
        saplings = int(state.inventory.sapling)

        if current_level != start_level:
            log_func(f"[collect_sapling] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Collecting saplings failed: player left floor {start_level}")

        log_func(
            f"[collect_sapling] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, saplings {saplings - start_saplings}/{number} "
            f"collected ({saplings} owned), {hits} hit(s) so far, health {float(state.player_health):.1f}"
        )

        if saplings >= goal_saplings:
            log_func(
                f"[collect_sapling] Successfully collected {saplings - start_saplings} sapling(s) "
                f"with {hits} hit(s) in {steps_taken} steps"
            )
            return state

        if steps_taken >= max_steps:
            log_func(
                f"[collect_sapling] Max steps ({max_steps}) reached, collected "
                f"{saplings - start_saplings}/{number} sapling(s) with {hits} hit(s)"
            )
            raise Exception(
                f"Collecting saplings failed: max steps ({max_steps}) reached after collecting "
                f"{saplings - start_saplings}/{number} sapling(s)"
            )

        # What the player knows: remembered blocks and visible mobs
        block_map = known_blocks(state)
        map_rows, map_cols = block_map.shape
        unknown = block_map == UNKNOWN
        unknown[player_row, player_col] = False
        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in visible_mobs(state):
            mob_occupied[mob_row, mob_col] = True
        walkable_cells = ~unknown & ~np.isin(block_map, list(impassable_blocks)) & ~mob_occupied
        walkable_cells[player_row, player_col] = True
        # Known grass without a visible mob on it
        grass_cells = (block_map == BlockType.GRASS.value) & ~mob_occupied

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        hitting_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            # Shortest path over (row, col, facing) until the player faces known grass
            start_facing = facing if facing in action_index else moves[0][0]
            start_state = (player_row, player_col, start_facing)

            def is_goal(node):
                row, col, state_facing = node
                ahead_row = row + move_offsets[state_facing][0]
                ahead_col = col + move_offsets[state_facing][1]
                return (
                    0 <= ahead_row < map_rows
                    and 0 <= ahead_col < map_cols
                    and bool(grass_cells[ahead_row, ahead_col])
                )

            goal_state, first_action = plan_path(start_state, walkable_cells, unknown, is_goal)

            if goal_state is None:
                log_func("[collect_sapling] No known grass block can be reached")
                raise Exception(
                    f"Collecting saplings failed: no known reachable grass, explore first "
                    f"(collected {saplings - start_saplings}/{number} sapling(s))"
                )

            grass_cell = (
                goal_state[0] + move_offsets[goal_state[2]][0],
                goal_state[1] + move_offsets[goal_state[2]][1],
            )
            if goal_state == start_state:
                action = Action.DO.value
                hitting_cell = grass_cell
                action_reason = (
                    f"hitting GRASS at {grass_cell} for a sapling (hit {hits + 1}, "
                    f"{hits_since_last_sapling} since the last drop)"
                )
            else:
                action = first_action[goal_state]
                offset = move_offsets[action]
                next_row = player_row + offset[0]
                next_col = player_col + offset[1]
                will_move = (
                    0 <= next_row < map_rows
                    and 0 <= next_col < map_cols
                    and bool(walkable_cells[next_row, next_col])
                )
                action_reason = (
                    f"{'moving to' if will_move else 'turning towards'} ({next_row}, {next_col}) "
                    f"to face GRASS at {grass_cell} from ({goal_state[0]}, {goal_state[1]})"
                )

        # ---------- Act ----------
        log_func(f"[collect_sapling] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(
                f"Collecting saplings failed: step function returned no state for action {action_names[action]}"
            )

        if float(new_state.player_health) <= 0:
            log_func("[collect_sapling] The player died")
            raise Exception(
                f"Collecting saplings failed: the player died after collecting "
                f"{saplings - start_saplings}/{number} sapling(s)"
            )

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[collect_sapling] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if hitting_cell is not None:
            hits += 1
            if int(new_state.inventory.sapling) > saplings:
                log_func(
                    f"[collect_sapling] Got a sapling from GRASS at {hitting_cell} after "
                    f"{hits_since_last_sapling + 1} hit(s), saplings {saplings} -> {int(new_state.inventory.sapling)}"
                )
                hits_since_last_sapling = 0
            else:
                hits_since_last_sapling += 1
                log_func(f"[collect_sapling] No sapling dropped from GRASS at {hitting_cell}")

        state = new_state

    raise Exception(f"Collecting saplings failed: max steps ({max_steps}) reached")
