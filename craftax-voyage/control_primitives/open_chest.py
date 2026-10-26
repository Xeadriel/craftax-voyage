# Description:
# Deterministically walks to known chests and opens them. A chest is opened by facing it and pressing
# DO, which gives random loot (torches, ores, potions, arrows, sometimes a pickaxe or sword; the first
# chest on floor 1 also gives a bow, the first chests on floors 3 and 4 a book) and turns the chest into
# a PATH block. The chests are taken from the player's memory of the floor, so they must have been seen
# before (explore for BlockType.CHEST first). Plans with Dijkstra over the known floor towards the
# cheapest chest (never-seen cells are assumed walkable at an extra cost but are never stepped into
# directly), tunnelling through mineable blocks (trees, stone, ores, ...) when the pickaxe allows it and
# waiting for / attacking mobs that block the path. Every opening is verified by seeing the chest gone.
# Returns the final state once enough chests were opened, raises an Exception otherwise.

def open_chest(state, log_func, step_func, number=1, max_steps=30):
    """
    Walks to `number` known chests on the current floor and opens them.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        number: Number of chests to open
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        The final EnvState (after the last step) if `number` chests were opened

    Raises:
        Exception: If the arguments are invalid, no chest was seen on this floor
            (explore first), no more known chests are left while more are needed,
            no known chest can be reached over the known map (even by tunnelling),
            opening a chest keeps failing, the player died, the player left the
            floor, or max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        SOLID_BLOCKS,
        Action,
        BlockType,
    )
    from control_primitives.knowledge import (
        UNKNOWN,
        is_visible,
        known_blocks,
        visible_mobs,
    )

    pickaxe_names = ["no pickaxe", "a wood pickaxe", "a stone pickaxe", "an iron pickaxe", "a diamond pickaxe"]
    potion_names = ["red", "green", "blue", "pink", "cyan", "yellow"]
    loot_fields = [
        "torches", "coal", "iron", "diamond", "sapphire", "ruby",
        "arrows", "pickaxe", "sword", "bow", "books",
    ]

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

    def describe_loot(old_inventory, new_inventory):
        loot = []
        for field in loot_fields:
            gained = int(getattr(new_inventory, field)) - int(getattr(old_inventory, field))
            if gained > 0:
                loot.append(f"{field} +{gained}")
        old_potions = np.asarray(old_inventory.potions)
        new_potions = np.asarray(new_inventory.potions)
        for index, name in enumerate(potion_names):
            gained = int(new_potions[index]) - int(old_potions[index])
            if gained > 0:
                loot.append(f"{name} potion +{gained}")
        return ", ".join(loot) if loot else "nothing"

    start_level = int(state.player_level)
    opened = 0
    failed_opens = {}
    failed_mines = {}
    blocked_cells = set()
    mob_block_steps = 0

    log_func(
        f"[open_chest] Start opening {number} chest(s) on floor {start_level} "
        f"with a budget of {max_steps} steps"
    )

    if number == 0:
        log_func("[open_chest] Nothing to open")
        return state

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level != start_level:
            log_func(f"[open_chest] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Opening chests failed: player left floor {start_level}")

        log_func(
            f"[open_chest] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, chests {opened}/{number} opened, "
            f"health {float(state.player_health):.1f}"
        )

        if opened >= number:
            log_func(f"[open_chest] Successfully opened {opened} chest(s) in {steps_taken} steps")
            return state

        if steps_taken >= max_steps:
            log_func(f"[open_chest] Max steps ({max_steps}) reached, opened {opened}/{number} chest(s)")
            raise Exception(
                f"Opening chests failed: max steps ({max_steps}) reached after opening {opened}/{number} chest(s)"
            )

        # The player's memory of the floor and the mobs in view
        block_map = known_blocks(state)
        map_rows, map_cols = block_map.shape
        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in visible_mobs(state):
            mob_occupied[mob_row, mob_col] = True
        pickaxe_level = int(state.inventory.pickaxe)

        chest_cells = {
            (int(row), int(col))
            for row, col in np.argwhere(block_map == BlockType.CHEST.value)
            if (int(row), int(col)) not in blocked_cells
        }
        if not chest_cells:
            if opened == 0:
                log_func(f"[open_chest] No chest has been seen on floor {current_level} yet")
                raise Exception(
                    f"Opening chests failed: no chest has been seen on floor {current_level}, "
                    f"explore for BlockType.CHEST first"
                )
            log_func(f"[open_chest] No more known chests on floor {current_level}")
            raise Exception(
                f"Opening chests failed: no more known chests on floor {current_level} "
                f"after opening {opened}/{number} chest(s), explore for BlockType.CHEST first"
            )

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        opening_cell = None
        mining_cell = None
        expected_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            # Dijkstra over the known floor; chests are only path end points, never-seen cells
            # are assumed walkable at an extra cost (but never as the next step), tunnelling and
            # passing mobs cost extra
            distance = np.full((map_rows, map_cols), np.inf)
            previous = {}
            distance[player_row, player_col] = 0
            heap = [(0, player_row, player_col)]
            while heap:
                cost_so_far, row, col = heapq.heappop(heap)
                if cost_so_far > distance[row, col]:
                    continue
                if (row, col) in chest_cells:
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
                    if (next_row, next_col) in chest_cells:
                        move_cost = walk_cost
                    elif block == UNKNOWN:
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

            reachable_chests = sorted(
                (float(distance[cell]), cell) for cell in chest_cells if np.isfinite(distance[cell])
            )
            if not reachable_chests:
                log_func(
                    f"[open_chest] None of the {len(chest_cells)} known chest(s) can be reached over the "
                    f"known map, even by tunnelling with {pickaxe_names[min(pickaxe_level, 4)]}"
                )
                raise Exception(
                    f"Opening chests failed: no known chest can be reached "
                    f"(opened {opened}/{number} chest(s))"
                )
            chest_cost, chest = reachable_chests[0]

            # Reconstruct the first step of the path towards the chest
            cell = chest
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

            if (next_row, next_col) == chest:
                mob_block_steps = 0
                if not facing_next:
                    # The chest is solid, so pressing its direction only turns the player
                    action = move_action
                    action_reason = f"turning towards the chest at {chest}"
                else:
                    action = Action.DO.value
                    opening_cell = chest
                    action_reason = f"opening the chest at {chest}"
            elif mob_occupied[next_row, next_col]:
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
                            f"to tunnel towards the chest at {chest}"
                        )
                else:
                    action = move_action
                    expected_cell = (next_row, next_col)
                    action_reason = (
                        f"moving to ({next_row}, {next_col}) towards the chest at {chest} "
                        f"(path cost {chest_cost:.0f})"
                    )

        # ---------- Act ----------
        log_func(f"[open_chest] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Opening chests failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0:
            log_func("[open_chest] The player died")
            raise Exception(f"Opening chests failed: the player died after opening {opened}/{number} chest(s)")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[open_chest] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if expected_cell is not None and int(new_state.player_level) == start_level:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(f"[open_chest] Move to {expected_cell} did not succeed, still at {new_position}; replanning")

        if opening_cell is not None and int(new_state.player_level) == start_level:
            # Only count the chest as opened once it can be seen to be gone
            chest_gone = (
                is_visible(new_state, opening_cell[0], opening_cell[1])
                and int(known_blocks(new_state)[opening_cell]) != BlockType.CHEST.value
            )
            if chest_gone:
                opened += 1
                failed_opens.pop(opening_cell, None)
                log_func(
                    f"[open_chest] Opened the chest at {opening_cell} ({opened}/{number}), "
                    f"loot: {describe_loot(state.inventory, new_state.inventory)}"
                )
            else:
                failed_opens[opening_cell] = failed_opens.get(opening_cell, 0) + 1
                log_func(
                    f"[open_chest] Opening the chest at {opening_cell} had no visible effect "
                    f"({failed_opens[opening_cell]}/{max_failed_attempts})"
                )
                if failed_opens[opening_cell] >= max_failed_attempts:
                    blocked_cells.add(opening_cell)
                    log_func(f"[open_chest] Ignoring the chest at {opening_cell} from now on")

        if mining_cell is not None and int(new_state.player_level) == start_level:
            # Only trust the mined cell's new block type if it can be seen
            old_block = int(block_map[mining_cell])
            new_block = old_block
            if is_visible(new_state, mining_cell[0], mining_cell[1]):
                new_block = int(known_blocks(new_state)[mining_cell])
            if new_block != old_block:
                failed_mines.pop(mining_cell, None)
                log_func(
                    f"[open_chest] Mined {BlockType(old_block).name} at {mining_cell}, "
                    f"it is now {BlockType(new_block).name}"
                )
            else:
                failed_mines[mining_cell] = failed_mines.get(mining_cell, 0) + 1
                log_func(
                    f"[open_chest] Mining {BlockType(old_block).name} at {mining_cell} had no visible effect "
                    f"({failed_mines[mining_cell]}/{max_failed_attempts})"
                )
                if failed_mines[mining_cell] >= max_failed_attempts:
                    blocked_cells.add(mining_cell)
                    log_func(f"[open_chest] Treating {mining_cell} as impassable from now on")

        state = new_state

    raise Exception(f"Opening chests failed: max steps ({max_steps}) reached")
