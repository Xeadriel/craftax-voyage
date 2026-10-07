# Description:
# Deterministically mines a given number of blocks of one type that are in sight.
# Picks the cheapest visible target block with Dijkstra path planning, tunnels through
# mineable blocks on the way and bridges water and lava by placing a stone and mining
# it again. Faces each target block and mines it with DO, counting every target block
# that gets removed. Returns True once enough blocks are mined, raises otherwise.

def mine_block(state, log_func, step_func, target, number=1, max_steps=200):
    """
    Mines `number` blocks of the target type that are visible to the player.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        target: BlockType to mine (TREE, FIRE_TREE, ICE_SHRUB, STONE, COAL, STALAGMITE,
            IRON, DIAMOND, SAPPHIRE, RUBY, CRAFTING_TABLE or FURNACE)
        number: Number of target blocks to mine
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if `number` target blocks were mined

    Raises:
        Exception: If the target is invalid, the required pickaxe is missing, no target
            block is in sight, no more target blocks are in sight while more are needed,
            no visible target block is reachable, the player died, the player left the
            floor, or max_steps was reached
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

    pickaxe_names = ["no pickaxe", "wood pickaxe", "stone pickaxe", "iron pickaxe", "diamond pickaxe"]

    # Blocks DO removes, with the required pickaxe level and the inventory item they give
    mineable_blocks = {
        BlockType.TREE.value: (0, "wood"),
        BlockType.FIRE_TREE.value: (0, "wood"),
        BlockType.ICE_SHRUB.value: (0, "wood"),
        BlockType.STONE.value: (1, "stone"),
        BlockType.COAL.value: (1, "coal"),
        BlockType.STALAGMITE.value: (1, "stone"),
        BlockType.IRON.value: (2, "iron"),
        BlockType.DIAMOND.value: (3, "diamond"),
        BlockType.SAPPHIRE.value: (4, "sapphire"),
        BlockType.RUBY.value: (4, "ruby"),
        BlockType.CRAFTING_TABLE.value: (0, None),
        BlockType.FURNACE.value: (0, None),
    }

    # Validate the arguments
    if not isinstance(target, BlockType) or target.value not in mineable_blocks:
        raise Exception(
            f"Invalid target {target!r}: expected one of "
            + ", ".join(BlockType(value).name for value in mineable_blocks)
        )
    if isinstance(number, bool) or not isinstance(number, (int, np.integer)):
        raise Exception(f"Invalid number {number!r}: expected an integer")
    number = int(number)
    if number < 0:
        raise Exception(f"Invalid number {number}: must be non-negative")
    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    required_pickaxe, yielded_item = mineable_blocks[target.value]
    pickaxe_level = int(state.inventory.pickaxe)
    if pickaxe_level < required_pickaxe:
        log_func(
            f"[mine_block] Mining {target.name} needs a {pickaxe_names[required_pickaxe]}, "
            f"the player has {pickaxe_names[min(pickaxe_level, len(pickaxe_names) - 1)]}"
        )
        raise Exception(
            f"Mining failed: {target.name} requires a {pickaxe_names[required_pickaxe]} "
            f"but the player has {pickaxe_names[min(pickaxe_level, len(pickaxe_names) - 1)]}"
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
    # Blocks that may be mined away to tunnel (useful structures are never destroyed)
    tunnel_blocks = {
        value for value, (_, item) in mineable_blocks.items() if item is not None
    } | {target.value}
    # Blocks that can be bridged by placing a stone and mining it again
    bridge_blocks = {BlockType.WATER.value, BlockType.LAVA.value}

    walk_cost = 1
    tunnel_cost = 4
    bridge_cost = 5
    mob_extra_cost = 6
    max_failed_attempts = 3
    max_mob_wait_steps = 2
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2

    start_level = int(state.player_level)
    mined_count = 0
    current_target = None
    placed_stone_cells = set()
    failed_attempts = {}
    blocked_cells = set()
    mob_block_steps = 0

    log_func(
        f"[mine_block] Start mining {number} {target.name} block(s) with a budget of {max_steps} steps "
        f"({pickaxe_names[min(pickaxe_level, len(pickaxe_names) - 1)]}, {int(state.inventory.stone)} stone)"
    )

    if number == 0:
        log_func("[mine_block] Nothing to mine")
        return True

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level != start_level:
            log_func(f"[mine_block] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Mining failed: player left floor {start_level}")

        block_map = np.asarray(state.map[current_level])
        light_visible = np.asarray(state.light_map[current_level]) > 0.05
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape
        pickaxe_level = int(state.inventory.pickaxe)
        stone_count = int(state.inventory.stone)
        can_bridge = pickaxe_level >= 1 and stone_count >= 1

        # Target blocks in the (lit) view window
        row_start = max(0, player_row - half_rows)
        row_end = min(map_rows, player_row + half_rows + 1)
        col_start = max(0, player_col - half_cols)
        col_end = min(map_cols, player_col + half_cols + 1)
        visible_targets = [
            (int(cell[0]) + row_start, int(cell[1]) + col_start)
            for cell in np.argwhere(
                (block_map[row_start:row_end, col_start:col_end] == target.value)
                & light_visible[row_start:row_end, col_start:col_end]
            )
        ]
        visible_targets = [
            cell for cell in visible_targets
            if cell not in placed_stone_cells and cell not in blocked_cells
        ]

        if current_target is not None and (
            int(block_map[current_target]) != target.value or current_target in blocked_cells
        ):
            log_func(f"[mine_block] Target block {current_target} is no longer a {target.name}")
            current_target = None

        log_func(
            f"[mine_block] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, mined {mined_count}/{number}, "
            f"{len(visible_targets)} {target.name} block(s) in sight, stone {stone_count}, "
            f"health {float(state.player_health):.1f}"
        )

        if current_target is None and len(visible_targets) == 0:
            if mined_count == 0:
                log_func(f"[mine_block] No {target.name} block is in sight")
                raise Exception(f"Mining failed: no {target.name} block is in sight")
            log_func(
                f"[mine_block] No more {target.name} blocks in sight, mined {mined_count}/{number}"
            )
            raise Exception(
                f"Mining failed: no more {target.name} blocks in sight after mining {mined_count}/{number}"
            )

        if steps_taken >= max_steps:
            log_func(f"[mine_block] Max steps ({max_steps}) reached, mined {mined_count}/{number}")
            raise Exception(
                f"Mining failed: max steps ({max_steps}) reached after mining {mined_count}/{number} {target.name}"
            )

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        expected_cell = None
        mining_cell = None
        placing_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            # Dijkstra over the floor; tunnelling, bridging and passing mobs cost extra
            distance = np.full((map_rows, map_cols), np.inf)
            previous = {}
            distance[player_row, player_col] = 0
            heap = [(0, player_row, player_col)]
            while heap:
                cost_so_far, row, col = heapq.heappop(heap)
                if cost_so_far > distance[row, col]:
                    continue
                # Target blocks are path end points, never walked through
                if (row, col) != (player_row, player_col) and int(block_map[row, col]) == target.value and (row, col) not in placed_stone_cells:
                    continue
                for _, d_row, d_col in moves:
                    next_row = row + d_row
                    next_col = col + d_col
                    if not (0 <= next_row < map_rows and 0 <= next_col < map_cols):
                        continue
                    if (next_row, next_col) in blocked_cells:
                        continue
                    block = int(block_map[next_row, next_col])
                    if block in tunnel_blocks and pickaxe_level >= mineable_blocks[block][0]:
                        move_cost = tunnel_cost
                    elif block in bridge_blocks and can_bridge:
                        move_cost = bridge_cost
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

            if current_target is not None and not np.isfinite(distance[current_target]):
                log_func(f"[mine_block] Target block {current_target} became unreachable")
                current_target = None

            if current_target is None:
                reachable = [
                    (float(distance[cell]), cell[0], cell[1])
                    for cell in visible_targets if np.isfinite(distance[cell])
                ]
                if len(reachable) == 0:
                    log_func(
                        f"[mine_block] None of the {len(visible_targets)} {target.name} block(s) in sight is reachable"
                    )
                    raise Exception(
                        f"Mining failed: no {target.name} block in sight is reachable "
                        f"after mining {mined_count}/{number}"
                    )
                best = min(reachable)
                current_target = (best[1], best[2])
                log_func(
                    f"[mine_block] New target {target.name} at {current_target} with path cost {best[0]:.0f}"
                )

            # Reconstruct the first step of the path towards the target block
            cell = current_target
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

            if mob_occupied[next_row, next_col]:
                mob_block_steps += 1
                if mob_block_steps <= max_mob_wait_steps:
                    action_reason = (
                        f"a mob blocks next cell ({next_row}, {next_col}), waiting "
                        f"({mob_block_steps}/{max_mob_wait_steps})"
                    )
                elif facing != move_action:
                    action = move_action
                    action_reason = f"turning towards blocking mob at ({next_row}, {next_col})"
                else:
                    action = Action.DO.value
                    action_reason = f"attacking blocking mob at ({next_row}, {next_col})"
            else:
                mob_block_steps = 0
                if next_block in tunnel_blocks or next_block in bridge_blocks:
                    if facing != move_action:
                        action = move_action
                        action_reason = f"turning towards {next_name} at ({next_row}, {next_col})"
                    elif next_block in bridge_blocks:
                        action = Action.PLACE_STONE.value
                        placing_cell = (next_row, next_col)
                        action_reason = (
                            f"placing stone on {next_name} at ({next_row}, {next_col}) to bridge it"
                        )
                    else:
                        action = Action.DO.value
                        mining_cell = (next_row, next_col)
                        if (next_row, next_col) == current_target:
                            action_reason = (
                                f"mining target {next_name} at ({next_row}, {next_col}) "
                                f"({mined_count + 1}/{number})"
                            )
                        elif (next_row, next_col) in placed_stone_cells:
                            action_reason = (
                                f"mining placed stone at ({next_row}, {next_col}) to finish the bridge"
                            )
                        else:
                            action_reason = (
                                f"mining {next_name} at ({next_row}, {next_col}) to tunnel towards {current_target}"
                            )
                else:
                    action = move_action
                    expected_cell = (next_row, next_col)
                    action_reason = (
                        f"moving to ({next_row}, {next_col}) towards {target.name} at {current_target} "
                        f"(path cost {float(distance[current_target]):.0f})"
                    )

        # ---------- Act ----------
        log_func(f"[mine_block] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Mining failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[mine_block] The player died or the episode ended")
            raise Exception(
                f"Mining failed: the player died after mining {mined_count}/{number} {target.name}"
            )

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[mine_block] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if expected_cell is not None:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(
                    f"[mine_block] Move to {expected_cell} did not succeed, still at {new_position}; replanning"
                )

        if placing_cell is not None:
            new_block = int(new_state.map[current_level, placing_cell[0], placing_cell[1]])
            if new_block == BlockType.STONE.value:
                placed_stone_cells.add(placing_cell)
                failed_attempts.pop(placing_cell, None)
                log_func(
                    f"[mine_block] Placed stone at {placing_cell}, stone "
                    f"{int(state.inventory.stone)} -> {int(new_state.inventory.stone)}"
                )
            else:
                failed_attempts[placing_cell] = failed_attempts.get(placing_cell, 0) + 1
                log_func(
                    f"[mine_block] Placing stone at {placing_cell} had no effect "
                    f"({failed_attempts[placing_cell]}/{max_failed_attempts})"
                )
                if failed_attempts[placing_cell] >= max_failed_attempts:
                    blocked_cells.add(placing_cell)
                    log_func(f"[mine_block] Treating {placing_cell} as impassable from now on")

        if mining_cell is not None:
            old_block = int(block_map[mining_cell])
            new_block = int(new_state.map[current_level, mining_cell[0], mining_cell[1]])
            if new_block != old_block:
                failed_attempts.pop(mining_cell, None)
                was_placed = mining_cell in placed_stone_cells
                placed_stone_cells.discard(mining_cell)
                log_func(
                    f"[mine_block] Mined {BlockType(old_block).name} at {mining_cell}, it is now "
                    f"{BlockType(new_block).name}"
                )
                if old_block == target.value and not was_placed:
                    mined_count += 1
                    if yielded_item is not None:
                        log_func(
                            f"[mine_block] Mined {target.name} {mined_count}/{number}, {yielded_item} "
                            f"{int(getattr(state.inventory, yielded_item))} -> "
                            f"{int(getattr(new_state.inventory, yielded_item))}"
                        )
                    else:
                        log_func(f"[mine_block] Mined {target.name} {mined_count}/{number}")
                    if mining_cell == current_target:
                        current_target = None
                    if mined_count >= number:
                        log_func(
                            f"[mine_block] Successfully mined {mined_count} {target.name} block(s) "
                            f"after {steps_taken + 1} steps"
                        )
                        return True
            else:
                failed_attempts[mining_cell] = failed_attempts.get(mining_cell, 0) + 1
                log_func(
                    f"[mine_block] Mining {BlockType(old_block).name} at {mining_cell} had no effect "
                    f"({failed_attempts[mining_cell]}/{max_failed_attempts})"
                )
                if failed_attempts[mining_cell] >= max_failed_attempts:
                    blocked_cells.add(mining_cell)
                    if mining_cell == current_target:
                        current_target = None
                    log_func(f"[mine_block] Giving up on {mining_cell}, treating it as impassable")

        state = new_state

    raise Exception(
        f"Mining failed: max steps ({max_steps}) reached after mining {mined_count}/{number} {target.name}"
    )
