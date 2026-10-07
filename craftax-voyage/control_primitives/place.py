# Description:
# Deterministically places one placeable (crafting table, furnace, stone, sapling/plant
# or torch) on the map. Checks the required material first, then either uses the given
# position or picks the nearest valid cell (not water or lava), plans the shortest
# sequence of movement/turn actions until the player faces that cell (breadth-first
# search over position and facing direction), and places it with the matching action.
# Returns True when the placement is verified, raises an Exception otherwise.

def place(state, log_func, step_func, placeable, max_steps=50, position=None):
    """
    Places one placeable on the cell in front of the player.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        placeable: What to place, given as the PLACE_* Action, BlockType.CRAFTING_TABLE,
            BlockType.FURNACE, BlockType.STONE, BlockType.PLANT, ItemType.TORCH, or one of
            the strings "crafting_table"/"table", "furnace", "stone", "plant"/"sapling", "torch"
        max_steps: Maximum number of calls to step_func before giving up
        position: Optional (row, col) cell to place on; if None the nearest valid cell
            is chosen automatically

    Returns:
        True if the placeable was placed

    Raises:
        Exception: If the placeable is invalid, the required material is missing, the
            chosen position is invalid or unreachable, no valid cell is reachable, the
            placement keeps failing, the player died, the player left the floor, or
            max_steps was reached
    """
    from collections import deque

    import numpy as np

    from craftax.craftax.constants import (
        CAN_PLACE_ITEM_BLOCKS,
        DIRECTIONS,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
    )

    # name -> (action, inventory field, amount needed)
    placeables = {
        "crafting_table": (Action.PLACE_TABLE.value, "wood", 2),
        "furnace": (Action.PLACE_FURNACE.value, "stone", 1),
        "stone": (Action.PLACE_STONE.value, "stone", 1),
        "plant": (Action.PLACE_PLANT.value, "sapling", 1),
        "torch": (Action.PLACE_TORCH.value, "torches", 1),
    }
    aliases = {
        Action.PLACE_TABLE: "crafting_table",
        Action.PLACE_FURNACE: "furnace",
        Action.PLACE_STONE: "stone",
        Action.PLACE_PLANT: "plant",
        Action.PLACE_TORCH: "torch",
        BlockType.CRAFTING_TABLE: "crafting_table",
        BlockType.FURNACE: "furnace",
        BlockType.STONE: "stone",
        BlockType.PLANT: "plant",
        ItemType.TORCH: "torch",
        "crafting_table": "crafting_table",
        "table": "crafting_table",
        "furnace": "furnace",
        "stone": "stone",
        "plant": "plant",
        "sapling": "plant",
        "torch": "torch",
    }

    # Resolve and validate the arguments
    key = placeable.strip().lower() if isinstance(placeable, str) else placeable
    if key not in aliases:
        raise Exception(
            f"Invalid placeable {placeable!r}: expected one of crafting_table, furnace, stone, plant, torch"
        )
    placeable_name = aliases[key]
    place_action, material, material_needed = placeables[placeable_name]

    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    map_rows = int(state.map.shape[1])
    map_cols = int(state.map.shape[2])
    if position is not None:
        if (
            not isinstance(position, (tuple, list, np.ndarray))
            or len(position) != 2
        ):
            raise Exception(f"Invalid position {position!r}: expected (row, col)")
        position = (int(position[0]), int(position[1]))
        if not (0 <= position[0] < map_rows and 0 <= position[1] < map_cols):
            raise Exception(f"Invalid position {position}: outside of the {map_rows}x{map_cols} map")

    material_owned = int(getattr(state.inventory, material))
    if material_owned < material_needed:
        log_func(
            f"[place] Placing a {placeable_name} needs {material_needed} {material}, "
            f"the player has {material_owned}"
        )
        raise Exception(
            f"Placing failed: a {placeable_name} needs {material_needed} {material} "
            f"but the player has {material_owned}"
        )

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    move_offsets = {a: (d_row, d_col) for a, d_row, d_col in moves}
    action_index = {a: index for index, (a, _, _) in enumerate(moves)}
    action_names = {action.value: action.name for action in Action}

    solid_blocks = set(SOLID_BLOCKS)
    item_placeable_blocks = set(CAN_PLACE_ITEM_BLOCKS)
    liquid_blocks = {BlockType.WATER.value, BlockType.LAVA.value}
    # Cells the player cannot stand on
    impassable_blocks = solid_blocks | liquid_blocks | {
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER_VULNERABLE.value,
    }

    max_place_attempts = 3
    max_mob_wait_steps = 10

    start_level = int(state.player_level)
    place_attempts = 0
    mob_wait_steps = 0

    log_func(
        f"[place] Start placing a {placeable_name} "
        + (f"at {position} " if position is not None else "at the nearest valid cell ")
        + f"with a budget of {max_steps} steps ({material} {material_owned}, needs {material_needed})"
    )

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level != start_level:
            log_func(f"[place] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Placing failed: player left floor {start_level}")

        material_owned = int(getattr(state.inventory, material))
        if material_owned < material_needed:
            log_func(f"[place] Not enough {material} anymore ({material_owned}/{material_needed})")
            raise Exception(
                f"Placing failed: a {placeable_name} needs {material_needed} {material} "
                f"but the player has {material_owned}"
            )

        block_map = np.asarray(state.map[current_level])
        item_map = np.asarray(state.item_map[current_level])
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)

        # Game rules for the cell the placeable goes on (mobs are handled separately)
        if placeable_name in ("crafting_table", "furnace"):
            valid_cells = ~np.isin(block_map, list(solid_blocks)) & (item_map == ItemType.NONE.value)
            rule = "a non-solid cell without an item"
        elif placeable_name == "stone":
            valid_cells = (block_map == BlockType.WATER.value) | (
                ~np.isin(block_map, list(solid_blocks)) & (item_map == ItemType.NONE.value)
            )
            rule = "water or a non-solid cell without an item"
        elif placeable_name == "torch":
            valid_cells = np.isin(block_map, list(item_placeable_blocks)) & (item_map == ItemType.NONE.value)
            rule = "grass, sand, path, fire grass or ice grass without an item"
        else:
            valid_cells = (block_map == BlockType.GRASS.value) & (item_map == ItemType.NONE.value)
            rule = "grass without an item"
        valid_cells[player_row, player_col] = False

        if position is not None:
            if position == (player_row, player_col):
                log_func(f"[place] Position {position} is the player's own cell")
                raise Exception(f"Placing failed: cannot place a {placeable_name} on the player's own cell {position}")
            if not valid_cells[position]:
                position_block = BlockType(int(block_map[position])).name
                position_item = ItemType(int(item_map[position])).name
                log_func(
                    f"[place] Position {position} ({position_block}, item {position_item}) is not valid, "
                    f"a {placeable_name} needs {rule}"
                )
                raise Exception(
                    f"Placing failed: position {position} ({position_block}, item {position_item}) is not "
                    f"valid for a {placeable_name}, it needs {rule}"
                )
            goal_cells = np.zeros_like(valid_cells)
            goal_cells[position] = True
        else:
            # Automatic choice: avoid cells under mobs and water/lava
            goal_cells = valid_cells & ~mob_occupied & ~np.isin(block_map, list(liquid_blocks))

        log_func(
            f"[place] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, {material} {material_owned}, "
            f"health {float(state.player_health):.1f}"
        )

        if steps_taken >= max_steps:
            log_func(f"[place] Max steps ({max_steps}) reached without placing the {placeable_name}")
            raise Exception(f"Placing failed: max steps ({max_steps}) reached without placing a {placeable_name}")

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        placing_cell = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            # Breadth-first search over (row, col, facing): pressing a direction moves the player
            # onto a walkable cell, or only turns it when that cell is blocked
            visited = np.zeros((map_rows, map_cols, len(moves)), dtype=bool)
            first_action = {}
            goal_state = None
            start_facing = facing if facing in action_index else moves[0][0]
            start_state = (player_row, player_col, start_facing)
            visited[player_row, player_col, action_index[start_facing]] = True
            queue = deque([start_state])
            while queue:
                row, col, state_facing = queue.popleft()
                ahead_row = row + move_offsets[state_facing][0]
                ahead_col = col + move_offsets[state_facing][1]
                if 0 <= ahead_row < map_rows and 0 <= ahead_col < map_cols and goal_cells[ahead_row, ahead_col]:
                    goal_state = (row, col, state_facing)
                    break
                for a, d_row, d_col in moves:
                    next_row = row + d_row
                    next_col = col + d_col
                    walkable = (
                        0 <= next_row < map_rows
                        and 0 <= next_col < map_cols
                        and int(block_map[next_row, next_col]) not in impassable_blocks
                        and not mob_occupied[next_row, next_col]
                        and not (position is not None and (next_row, next_col) == position)
                    )
                    next_state = (next_row, next_col, a) if walkable else (row, col, a)
                    if visited[next_state[0], next_state[1], action_index[a]]:
                        continue
                    visited[next_state[0], next_state[1], action_index[a]] = True
                    first_action[next_state] = first_action.get((row, col, state_facing), a)
                    queue.append(next_state)

            if goal_state is None:
                if position is not None:
                    log_func(f"[place] Position {position} cannot be faced from any reachable cell")
                    raise Exception(f"Placing failed: position {position} is unreachable")
                log_func(f"[place] No valid cell for a {placeable_name} is reachable ({rule})")
                raise Exception(
                    f"Placing failed: no reachable valid cell for a {placeable_name} on floor {current_level}"
                )

            target_cell = (
                goal_state[0] + move_offsets[goal_state[2]][0],
                goal_state[1] + move_offsets[goal_state[2]][1],
            )
            target_description = (
                f"{BlockType(int(block_map[target_cell])).name} at {target_cell}"
            )

            if goal_state == start_state:
                if mob_occupied[target_cell]:
                    mob_wait_steps += 1
                    if mob_wait_steps > max_mob_wait_steps:
                        log_func(f"[place] A mob stayed on {target_cell} for {max_mob_wait_steps} steps")
                        raise Exception(f"Placing failed: a mob keeps blocking position {target_cell}")
                    action_reason = (
                        f"a mob stands on {target_description}, waiting ({mob_wait_steps}/{max_mob_wait_steps})"
                    )
                else:
                    mob_wait_steps = 0
                    action = place_action
                    placing_cell = target_cell
                    action_reason = f"placing a {placeable_name} on {target_description}"
            else:
                action = first_action[goal_state]
                offset = move_offsets[action]
                next_row = player_row + offset[0]
                next_col = player_col + offset[1]
                will_move = (
                    0 <= next_row < map_rows
                    and 0 <= next_col < map_cols
                    and int(block_map[next_row, next_col]) not in impassable_blocks
                    and not mob_occupied[next_row, next_col]
                    and not (position is not None and (next_row, next_col) == position)
                )
                action_reason = (
                    f"{'moving to' if will_move else 'turning towards'} ({next_row}, {next_col}) "
                    f"to face {target_description} from ({goal_state[0]}, {goal_state[1]})"
                )

        # ---------- Act ----------
        log_func(f"[place] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Placing failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[place] The player died or the episode ended")
            raise Exception(f"Placing failed: the player died before placing a {placeable_name}")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[place] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if placing_cell is not None:
            new_material = int(getattr(new_state.inventory, material))
            if placeable_name == "torch":
                placed = int(new_state.item_map[current_level, placing_cell[0], placing_cell[1]]) == ItemType.TORCH.value
            else:
                expected_block = {
                    "crafting_table": BlockType.CRAFTING_TABLE.value,
                    "furnace": BlockType.FURNACE.value,
                    "stone": BlockType.STONE.value,
                    "plant": BlockType.PLANT.value,
                }[placeable_name]
                placed = int(new_state.map[current_level, placing_cell[0], placing_cell[1]]) == expected_block
            if placed and new_material < material_owned:
                log_func(
                    f"[place] Placed a {placeable_name} at {placing_cell}, {material} "
                    f"{material_owned} -> {new_material}"
                )
                log_func(f"[place] Successfully placed a {placeable_name} after {steps_taken + 1} steps")
                return True
            place_attempts += 1
            log_func(
                f"[place] Placing the {placeable_name} at {placing_cell} had no effect "
                f"({place_attempts}/{max_place_attempts})"
            )
            if place_attempts >= max_place_attempts:
                raise Exception(
                    f"Placing failed: placing a {placeable_name} at {placing_cell} failed {max_place_attempts} times"
                )

        state = new_state

    raise Exception(f"Placing failed: max steps ({max_steps}) reached without placing a {placeable_name}")
