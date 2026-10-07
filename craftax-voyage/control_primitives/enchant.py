# Description:
# Deterministically enchants the sword, the bow or armour with fire or ice at an
# enchantment table that is in view (enchantment tables cannot be placed, so it never
# explores and fails when no matching table is in sight). Each enchantment costs 9 mana
# and one gem (ruby for fire, sapphire for ice). Plans the shortest sequence of
# movement/turn actions until the player faces the table (breadth-first search over
# position and facing direction), then enchants exactly once: the sword, the bow, or one
# armour slot that does not have the element yet (the game picks the slot).
# Returns True when the enchantment succeeded, raises an Exception otherwise.

def enchant(state, log_func, step_func, equipment, element, max_steps=50):
    """
    Enchants one piece of equipment with fire or ice at a matching enchantment table in view.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        equipment: "sword", "bow" or "armour" (or the matching ENCHANT_* Action)
        element: "fire" or "ice" (or BlockType.ENCHANTMENT_TABLE_FIRE / _ICE)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if the enchantment succeeded (or the sword/bow, or all armour slots, already
        have the element)

    Raises:
        Exception: If the arguments are invalid, the equipment is not owned, there is not
            enough mana or no gem, no matching enchantment table is in view or reachable,
            the enchanting keeps failing, the player died, the player left the floor, or
            max_steps was reached
    """
    from collections import deque

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        OBS_DIM,
        SOLID_BLOCKS,
        Action,
        BlockType,
    )

    equipment_aliases: dict = {
        "sword": "sword",
        "bow": "bow",
        "armour": "armour",
        "armor": "armour",
        Action.ENCHANT_SWORD: "sword",
        Action.ENCHANT_BOW: "bow",
        Action.ENCHANT_ARMOUR: "armour",
    }
    element_aliases: dict = {
        "fire": "fire",
        "ice": "ice",
        BlockType.ENCHANTMENT_TABLE_FIRE: "fire",
        BlockType.ENCHANTMENT_TABLE_ICE: "ice",
    }
    enchant_actions = {
        "sword": Action.ENCHANT_SWORD.value,
        "bow": Action.ENCHANT_BOW.value,
        "armour": Action.ENCHANT_ARMOUR.value,
    }
    # element -> (enchantment value, table block, gem inventory field)
    elements = {
        "fire": (1, BlockType.ENCHANTMENT_TABLE_FIRE.value, "ruby"),
        "ice": (2, BlockType.ENCHANTMENT_TABLE_ICE.value, "sapphire"),
    }
    enchantment_names = {0: "none", 1: "fire", 2: "ice"}
    mana_cost = 9
    armour_slots = 4

    # Resolve and validate the arguments
    equipment_key = equipment.strip().lower() if isinstance(equipment, str) else equipment
    if equipment_key not in equipment_aliases:
        raise Exception(f"Invalid equipment {equipment!r}: expected 'sword', 'bow' or 'armour'")
    equipment_name = equipment_aliases[equipment_key]
    element_key = element.strip().lower() if isinstance(element, str) else element
    if element_key not in element_aliases:
        raise Exception(f"Invalid element {element!r}: expected 'fire' or 'ice'")
    element_name = element_aliases[element_key]
    enchantment_value, table_block, gem = elements[element_name]
    enchant_action = enchant_actions[equipment_name]

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

    # Cells the player cannot stand on
    impassable_blocks = set(SOLID_BLOCKS) | {
        BlockType.WATER.value,
        BlockType.LAVA.value,
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER_VULNERABLE.value,
    }
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2
    max_failed_attempts = 3

    start_level = int(state.player_level)
    enchanted = False
    failed_attempts = 0

    log_func(
        f"[enchant] Start enchanting the {equipment_name} with {element_name} "
        + ("(one armour slot) " if equipment_name == "armour" else "")
        + f"with a budget of {max_steps} steps (cost {mana_cost} mana and 1 {gem})"
    )

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)
        mana = int(state.player_mana)
        gems = int(getattr(state.inventory, gem))
        armour_enchantments = np.asarray(state.armour_enchantments)

        if current_level != start_level:
            log_func(f"[enchant] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Enchanting failed: player left floor {start_level}")

        if equipment_name == "sword":
            current_enchantment = enchantment_names.get(int(state.sword_enchantment), str(int(state.sword_enchantment)))
        elif equipment_name == "bow":
            current_enchantment = enchantment_names.get(int(state.bow_enchantment), str(int(state.bow_enchantment)))
        else:
            current_enchantment = "[" + ", ".join(enchantment_names.get(int(e), str(int(e))) for e in armour_enchantments) + "]"

        log_func(
            f"[enchant] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, {equipment_name} enchantment {current_enchantment}, "
            f"mana {mana}, {gem} {gems}"
        )

        # Goal reached?
        if equipment_name == "sword" and int(state.sword_enchantment) == enchantment_value:
            log_func(f"[enchant] The sword is enchanted with {element_name} after {steps_taken} steps")
            return True
        if equipment_name == "bow" and int(state.bow_enchantment) == enchantment_value:
            log_func(f"[enchant] The bow is enchanted with {element_name} after {steps_taken} steps")
            return True
        if equipment_name == "armour" and enchanted:
            log_func(f"[enchant] Enchanted one armour slot with {element_name} after {steps_taken} steps")
            return True
        if equipment_name == "armour" and int(np.sum(armour_enchantments == enchantment_value)) >= armour_slots:
            log_func(f"[enchant] All {armour_slots} armour slots already have {element_name}, nothing to enchant")
            return True

        # Requirements for one more enchantment
        if equipment_name == "sword" and int(state.inventory.sword) <= 0:
            problem = "the player has no sword"
        elif equipment_name == "bow" and int(state.inventory.bow) <= 0:
            problem = "the player has no bow"
        elif equipment_name == "armour" and int(np.sum(np.asarray(state.inventory.armour))) <= 0:
            problem = "the player has no armour"
        elif mana < mana_cost:
            problem = f"not enough mana ({mana}/{mana_cost})"
        elif gems < 1:
            problem = f"no {gem} (needed for a {element_name} enchantment)"
        else:
            problem = None
        if problem is not None:
            log_func(f"[enchant] Cannot enchant: {problem}")
            raise Exception(f"Enchanting failed: {problem}")

        if steps_taken >= max_steps:
            log_func(f"[enchant] Max steps ({max_steps}) reached")
            raise Exception(f"Enchanting failed: max steps ({max_steps}) reached")

        block_map = np.asarray(state.map[current_level])
        light_visible = np.asarray(state.light_map[current_level]) > 0.05
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape

        # Matching enchantment tables in the (lit) view window
        tables = np.zeros((map_rows, map_cols), dtype=bool)
        row_start = max(0, player_row - half_rows)
        row_end = min(map_rows, player_row + half_rows + 1)
        col_start = max(0, player_col - half_cols)
        col_end = min(map_cols, player_col + half_cols + 1)
        tables[row_start:row_end, col_start:col_end] = (
            (block_map[row_start:row_end, col_start:col_end] == table_block)
            & light_visible[row_start:row_end, col_start:col_end]
        )
        if not np.any(tables):
            log_func(f"[enchant] No {element_name} enchantment table is in view")
            raise Exception(f"Enchanting failed: no {element_name} enchantment table is in view")

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        enchanting = False

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
                if 0 <= ahead_row < map_rows and 0 <= ahead_col < map_cols and tables[ahead_row, ahead_col]:
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
                    )
                    next_state = (next_row, next_col, a) if walkable else (row, col, a)
                    if visited[next_state[0], next_state[1], action_index[a]]:
                        continue
                    visited[next_state[0], next_state[1], action_index[a]] = True
                    first_action[next_state] = first_action.get((row, col, state_facing), a)
                    queue.append(next_state)

            if goal_state is None:
                log_func(f"[enchant] The {element_name} enchantment table in view cannot be reached")
                raise Exception(f"Enchanting failed: the {element_name} enchantment table in view is unreachable")

            table_cell = (
                goal_state[0] + move_offsets[goal_state[2]][0],
                goal_state[1] + move_offsets[goal_state[2]][1],
            )
            if goal_state == start_state:
                action = enchant_action
                enchanting = True
                action_reason = (
                    f"enchanting the {equipment_name} at the {element_name} enchantment table at {table_cell}"
                )
            else:
                action = first_action[goal_state]
                offset = move_offsets[action]
                next_cell = (player_row + offset[0], player_col + offset[1])
                will_move = (
                    0 <= next_cell[0] < map_rows
                    and 0 <= next_cell[1] < map_cols
                    and int(block_map[next_cell]) not in impassable_blocks
                    and not mob_occupied[next_cell]
                )
                action_reason = (
                    f"{'moving to' if will_move else 'turning towards'} {next_cell} to face the "
                    f"{element_name} enchantment table at {table_cell} from ({goal_state[0]}, {goal_state[1]})"
                )

        # ---------- Act ----------
        log_func(f"[enchant] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Enchanting failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[enchant] The player died or the episode ended")
            raise Exception("Enchanting failed: the player died")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[enchant] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if enchanting:
            new_mana = int(new_state.player_mana)
            new_gems = int(getattr(new_state.inventory, gem))
            if equipment_name == "sword":
                success = int(new_state.sword_enchantment) == enchantment_value
            elif equipment_name == "bow":
                success = int(new_state.bow_enchantment) == enchantment_value
            else:
                success = int(np.sum(np.asarray(new_state.armour_enchantments) == enchantment_value)) > int(
                    np.sum(armour_enchantments == enchantment_value)
                )
            if success:
                enchanted = True
                failed_attempts = 0
                log_func(
                    f"[enchant] Enchanted the {equipment_name} with {element_name}"
                    + (
                        f", armour slots {[enchantment_names.get(int(e), int(e)) for e in armour_enchantments]} -> "
                        f"{[enchantment_names.get(int(e), int(e)) for e in np.asarray(new_state.armour_enchantments)]}"
                        if equipment_name == "armour" else ""
                    )
                    + f", mana {mana} -> {new_mana}, {gem} {gems} -> {new_gems}"
                )
            else:
                failed_attempts += 1
                log_func(f"[enchant] Enchanting had no effect ({failed_attempts}/{max_failed_attempts})")
                if failed_attempts >= max_failed_attempts:
                    raise Exception(
                        f"Enchanting failed: enchanting the {equipment_name} had no effect {max_failed_attempts} times"
                    )

        state = new_state

    raise Exception(f"Enchanting failed: max steps ({max_steps}) reached")
