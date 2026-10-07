# Description:
# Deterministically crafts a craftable (pickaxes, swords, armour, arrows, torches).
# Uses a crafting table / furnace that is in view, or places the missing station next
# to the player when none is in view (it never explores). Walks with a breadth-first
# search over position and facing direction until it stands next to every required
# station, then crafts until `number` items were produced. If the materials (or the
# inventory limits) run out, it crafts as many as possible before raising.
# Returns True when `number` items were crafted, raises an Exception otherwise.

def craft(state, log_func, step_func, craftable, number=1, max_steps=50):
    """
    Crafts `number` items of the craftable at the required crafting station(s).

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        craftable: The MAKE_* Action, or one of the strings "wood_pickaxe",
            "stone_pickaxe", "iron_pickaxe", "diamond_pickaxe", "wood_sword",
            "stone_sword", "iron_sword", "diamond_sword", "iron_armour",
            "diamond_armour", "arrow"/"arrows", "torch"/"torches"
        number: Number of items wanted (arrows come in 2 per craft and torches in 4 per
            craft, so e.g. 5 torches need 2 crafts); pickaxes and swords can only be 1
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if `number` items were crafted

    Raises:
        Exception: If the craftable or number is invalid, the player already has an
            equal or better tool, the materials or inventory limits do not allow
            (further) crafting, a needed station cannot be reached or placed, the
            player died, the player left the floor, or max_steps was reached
    """
    from collections import deque

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        OBS_DIM,
        SOLID_BLOCKS,
        Action,
        BlockType,
        ItemType,
    )

    # name -> (action, materials per craft, stations, kind, attribute, level or yield)
    recipes = {
        "wood_pickaxe": (Action.MAKE_WOOD_PICKAXE.value, {"wood": 1}, ["crafting_table"], "tool", "pickaxe", 1),
        "stone_pickaxe": (Action.MAKE_STONE_PICKAXE.value, {"wood": 1, "stone": 1}, ["crafting_table"], "tool", "pickaxe", 2),
        "iron_pickaxe": (
            Action.MAKE_IRON_PICKAXE.value, {"wood": 1, "stone": 1, "iron": 1, "coal": 1},
            ["crafting_table", "furnace"], "tool", "pickaxe", 3,
        ),
        "diamond_pickaxe": (Action.MAKE_DIAMOND_PICKAXE.value, {"wood": 1, "diamond": 3}, ["crafting_table"], "tool", "pickaxe", 4),
        "wood_sword": (Action.MAKE_WOOD_SWORD.value, {"wood": 1}, ["crafting_table"], "tool", "sword", 1),
        "stone_sword": (Action.MAKE_STONE_SWORD.value, {"wood": 1, "stone": 1}, ["crafting_table"], "tool", "sword", 2),
        "iron_sword": (
            Action.MAKE_IRON_SWORD.value, {"wood": 1, "stone": 1, "iron": 1, "coal": 1},
            ["crafting_table", "furnace"], "tool", "sword", 3,
        ),
        "diamond_sword": (Action.MAKE_DIAMOND_SWORD.value, {"wood": 1, "diamond": 2}, ["crafting_table"], "tool", "sword", 4),
        "iron_armour": (
            Action.MAKE_IRON_ARMOUR.value, {"iron": 3, "coal": 3},
            ["crafting_table", "furnace"], "armour", "armour", 1,
        ),
        "diamond_armour": (Action.MAKE_DIAMOND_ARMOUR.value, {"diamond": 3}, ["crafting_table"], "armour", "armour", 2),
        "arrow": (Action.MAKE_ARROW.value, {"wood": 1, "stone": 1}, ["crafting_table"], "stack", "arrows", 2),
        "torch": (Action.MAKE_TORCH.value, {"wood": 1, "coal": 1}, ["crafting_table"], "stack", "torches", 4),
    }
    aliases: dict = {name: name for name in recipes}
    aliases.update({"arrows": "arrow", "torches": "torch", "iron_armor": "iron_armour", "diamond_armor": "diamond_armour"})
    for name, recipe in recipes.items():
        aliases[Action(recipe[0])] = name
    # station -> (block, place action, materials to place it)
    stations = {
        "crafting_table": (BlockType.CRAFTING_TABLE.value, Action.PLACE_TABLE.value, {"wood": 2}),
        "furnace": (BlockType.FURNACE.value, Action.PLACE_FURNACE.value, {"stone": 1}),
    }
    stack_cap = 99

    # Resolve and validate the arguments
    key = craftable.strip().lower() if isinstance(craftable, str) else craftable
    if key not in aliases:
        raise Exception(f"Invalid craftable {craftable!r}: expected one of {', '.join(recipes)}")
    craft_name = aliases[key]
    craft_action, cost, required_stations, kind, attribute, level_or_yield = recipes[craft_name]

    if isinstance(number, bool) or not isinstance(number, (int, np.integer)):
        raise Exception(f"Invalid number {number!r}: expected an integer")
    number = int(number)
    if number < 0:
        raise Exception(f"Invalid number {number}: must be non-negative")
    if kind == "tool" and number > 1:
        raise Exception(f"Invalid number {number}: a {craft_name} can only be crafted once")
    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    if kind == "tool":
        current_level = int(getattr(state.inventory, attribute))
        if current_level >= level_or_yield:
            log_func(f"[craft] The player already has a {attribute} of level {current_level}")
            raise Exception(
                f"Crafting failed: the player already has an equal or better {attribute} "
                f"(level {current_level}) than a {craft_name} (level {level_or_yield})"
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
    liquid_blocks = {BlockType.WATER.value, BlockType.LAVA.value}
    # Cells the player cannot stand on
    impassable_blocks = solid_blocks | liquid_blocks | {
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER_VULNERABLE.value,
    }
    half_rows = OBS_DIM[0] // 2
    half_cols = OBS_DIM[1] // 2
    max_failed_attempts = 3

    start_level = int(state.player_level)
    start_armour = np.asarray(state.inventory.armour).copy()
    produced = 0
    crafts_done = 0
    failed_crafts = 0
    failed_placements = 0

    log_func(
        f"[craft] Start crafting {number} {craft_name} (cost per craft "
        + ", ".join(f"{amount} {material}" for material, amount in cost.items())
        + f", needs {' and '.join(required_stations)}) with a budget of {max_steps} steps"
    )

    if number == 0:
        log_func("[craft] Nothing to craft")
        return True

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level != start_level:
            log_func(f"[craft] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(f"Crafting failed: player left floor {start_level}")

        inventory = {
            material: int(getattr(state.inventory, material))
            for material in ("wood", "stone", "coal", "iron", "diamond")
        }

        log_func(
            f"[craft] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"facing {action_names.get(facing, facing)}, produced {produced}/{number} {craft_name}, "
            f"inventory " + ", ".join(f"{m} {v}" for m, v in inventory.items())
        )

        if produced >= number:
            log_func(
                f"[craft] Successfully crafted {produced} {craft_name} with {crafts_done} craft(s) "
                f"in {steps_taken} steps"
            )
            return True

        # Inventory limits for one more craft
        if kind == "tool":
            limit_reason = None
        elif kind == "armour":
            armour = np.asarray(state.inventory.armour)
            limit_reason = (
                None if int(np.sum(armour < level_or_yield)) > 0
                else f"all armour slots already have {craft_name.split('_')[0]} armour or better"
            )
        else:
            limit_reason = (
                None if int(getattr(state.inventory, attribute)) < stack_cap
                else f"the player already holds {stack_cap} {attribute}"
            )
        missing_materials = {
            material: amount - inventory[material]
            for material, amount in cost.items() if inventory[material] < amount
        }
        if limit_reason is not None or missing_materials:
            reason = limit_reason if limit_reason is not None else (
                "missing " + ", ".join(f"{amount} {material}" for material, amount in missing_materials.items())
            )
            log_func(f"[craft] Cannot craft another {craft_name}: {reason}")
            raise Exception(
                f"Crafting failed: crafted {produced}/{number} {craft_name}, cannot craft more because {reason}"
            )

        if steps_taken >= max_steps:
            log_func(f"[craft] Max steps ({max_steps}) reached, crafted {produced}/{number} {craft_name}")
            raise Exception(
                f"Crafting failed: max steps ({max_steps}) reached after crafting {produced}/{number} {craft_name}"
            )

        block_map = np.asarray(state.map[current_level])
        item_map = np.asarray(state.item_map[current_level])
        light_visible = np.asarray(state.light_map[current_level]) > 0.05
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape

        # Stations in the (lit) view window and the cells next to them (8-neighbourhood)
        in_view = np.zeros((map_rows, map_cols), dtype=bool)
        in_view[
            max(0, player_row - half_rows):min(map_rows, player_row + half_rows + 1),
            max(0, player_col - half_cols):min(map_cols, player_col + half_cols + 1),
        ] = True
        in_view &= light_visible
        station_visible = {}
        station_near = {}
        for station in required_stations:
            visible = (block_map == stations[station][0]) & in_view
            near = np.zeros_like(visible)
            for d_row in (-1, 0, 1):
                for d_col in (-1, 0, 1):
                    if d_row == 0 and d_col == 0:
                        continue
                    shifted = np.zeros_like(visible)
                    shifted[
                        max(0, d_row):map_rows + min(0, d_row),
                        max(0, d_col):map_cols + min(0, d_col),
                    ] = visible[
                        max(0, -d_row):map_rows + min(0, -d_row),
                        max(0, -d_col):map_cols + min(0, -d_col),
                    ]
                    near |= shifted
            station_visible[station] = visible
            station_near[station] = near

        # The game's own nearness check (8 cells around the player)
        player_near = {
            station: any(
                0 <= player_row + d_row < map_rows
                and 0 <= player_col + d_col < map_cols
                and int(block_map[player_row + d_row, player_col + d_col]) == stations[station][0]
                for d_row in (-1, 0, 1) for d_col in (-1, 0, 1) if (d_row, d_col) != (0, 0)
            )
            for station in required_stations
        }

        standable = ~np.isin(block_map, list(impassable_blocks)) & ~mob_occupied
        standable[player_row, player_col] = True
        placeable_cells = (
            ~np.isin(block_map, list(solid_blocks | liquid_blocks))
            & (item_map == ItemType.NONE.value)
            & ~mob_occupied
        )
        placeable_cells[player_row, player_col] = False

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        crafting = False
        placing = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        elif all(player_near.values()):
            action = craft_action
            crafting = True
            action_reason = (
                f"crafting {craft_name} next to {' and '.join(required_stations)} "
                f"(craft {crafts_done + 1})"
            )
        else:
            # Plan 1: walk next to every required station that is in view
            plans = []
            if all(bool(np.any(station_visible[s])) for s in required_stations):
                craft_goal = standable.copy()
                for station in required_stations:
                    craft_goal &= station_near[station]
                plans.append(("walk", None, craft_goal, None))
            # Plan 2: place the first required station that is missing (or the last one if all
            # are in view but cannot be used together) next to the stations that are in view
            missing = [s for s in required_stations if not np.any(station_visible[s])]
            place_station = missing[0] if missing else required_stations[-1]
            anchors = [s for s in required_stations if s != place_station and np.any(station_visible[s])]
            anchor_goal = standable.copy()
            for station in anchors:
                anchor_goal &= station_near[station]
            plans.append(("place", place_station, anchor_goal, placeable_cells))

            chosen = None
            for plan_kind, plan_station, stand_goal, face_goal in plans:
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
                    if stand_goal[row, col] and (
                        face_goal is None
                        or (0 <= ahead_row < map_rows and 0 <= ahead_col < map_cols and face_goal[ahead_row, ahead_col])
                    ):
                        goal_state = (row, col, state_facing)
                        break
                    for a, d_row, d_col in moves:
                        next_row = row + d_row
                        next_col = col + d_col
                        walkable = 0 <= next_row < map_rows and 0 <= next_col < map_cols and standable[next_row, next_col]
                        next_state = (next_row, next_col, a) if walkable else (row, col, a)
                        if visited[next_state[0], next_state[1], action_index[a]]:
                            continue
                        visited[next_state[0], next_state[1], action_index[a]] = True
                        first_action[next_state] = first_action.get((row, col, state_facing), a)
                        queue.append(next_state)
                if goal_state is not None:
                    chosen = (plan_kind, plan_station, goal_state, start_state, first_action)
                    break
                log_func(
                    f"[craft] Plan '{plan_kind}'"
                    + (f" ({plan_station})" if plan_station else "")
                    + " is not possible from here"
                )

            if chosen is None:
                log_func(f"[craft] Cannot get next to {' and '.join(required_stations)}")
                raise Exception(
                    f"Crafting failed: cannot reach or place {' and '.join(required_stations)} "
                    f"after crafting {produced}/{number} {craft_name}"
                )

            plan_kind, plan_station, goal_state, start_state, first_action = chosen
            if plan_kind == "place":
                _, place_action, place_cost = stations[plan_station]
                # Placing must leave enough material for at least one craft
                total_needed = dict(cost)
                for material, amount in place_cost.items():
                    total_needed[material] = total_needed.get(material, 0) + amount
                lacking = {
                    material: amount - inventory[material]
                    for material, amount in total_needed.items() if inventory[material] < amount
                }
                if lacking:
                    log_func(
                        f"[craft] No {plan_station} in view and not enough material to place one and craft: missing "
                        + ", ".join(f"{amount} {material}" for material, amount in lacking.items())
                    )
                    raise Exception(
                        f"Crafting failed: no {plan_station} in view and not enough material to place one "
                        f"and craft a {craft_name} (missing "
                        + ", ".join(f"{amount} {material}" for material, amount in lacking.items())
                        + f") after crafting {produced}/{number}"
                    )
            if plan_kind == "place" and goal_state == start_state:
                ahead = (
                    player_row + move_offsets[start_state[2]][0],
                    player_col + move_offsets[start_state[2]][1],
                )
                action = place_action
                placing = (plan_station, ahead)
                action_reason = (
                    f"no usable {plan_station} in view, placing one on "
                    f"{BlockType(int(block_map[ahead])).name} at {ahead}"
                )
            else:
                action = first_action[goal_state]
                offset = move_offsets[action]
                next_cell = (player_row + offset[0], player_col + offset[1])
                will_move = (
                    0 <= next_cell[0] < map_rows and 0 <= next_cell[1] < map_cols and standable[next_cell]
                )
                purpose = (
                    f"to stand next to {' and '.join(required_stations)} at ({goal_state[0]}, {goal_state[1]})"
                    if plan_kind == "walk"
                    else f"to get into position ({goal_state[0]}, {goal_state[1]}) for placing a {plan_station}"
                )
                action_reason = f"{'moving to' if will_move else 'turning towards'} {next_cell} {purpose}"

        # ---------- Act ----------
        log_func(f"[craft] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Crafting failed: step function returned no state for action {action_names[action]}")

        if float(new_state.player_health) <= 0 or int(new_state.timestep) <= int(state.timestep):
            log_func("[craft] The player died or the episode ended")
            raise Exception(f"Crafting failed: the player died after crafting {produced}/{number} {craft_name}")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[craft] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if placing is not None:
            station_name, cell = placing
            if int(new_state.map[current_level, cell[0], cell[1]]) == stations[station_name][0]:
                failed_placements = 0
                log_func(
                    f"[craft] Placed a {station_name} at {cell}, "
                    + ", ".join(
                        f"{material} {inventory[material]} -> {int(getattr(new_state.inventory, material))}"
                        for material in stations[station_name][2]
                    )
                )
            else:
                failed_placements += 1
                log_func(
                    f"[craft] Placing the {station_name} at {cell} had no effect "
                    f"({failed_placements}/{max_failed_attempts})"
                )
                if failed_placements >= max_failed_attempts:
                    raise Exception(f"Crafting failed: placing a {station_name} failed {max_failed_attempts} times")

        if crafting:
            if kind == "tool":
                gained = 1 if int(getattr(new_state.inventory, attribute)) >= level_or_yield else 0
            elif kind == "armour":
                gained = int(np.sum(np.asarray(new_state.inventory.armour) >= level_or_yield)) - int(
                    np.sum(np.asarray(state.inventory.armour) >= level_or_yield)
                )
            else:
                gained = int(getattr(new_state.inventory, attribute)) - int(getattr(state.inventory, attribute))
            if gained > 0:
                crafts_done += 1
                failed_crafts = 0
                produced += gained
                log_func(
                    f"[craft] Crafted {gained} {craft_name} ({produced}/{number}), "
                    + ", ".join(
                        f"{material} {inventory[material]} -> {int(getattr(new_state.inventory, material))}"
                        for material in cost
                    )
                    + (
                        f", armour {start_armour.tolist()} -> {np.asarray(new_state.inventory.armour).tolist()}"
                        if kind == "armour" else ""
                    )
                )
            else:
                failed_crafts += 1
                log_func(f"[craft] Crafting had no effect ({failed_crafts}/{max_failed_attempts})")
                if failed_crafts >= max_failed_attempts:
                    raise Exception(
                        f"Crafting failed: crafting {craft_name} had no effect {max_failed_attempts} times "
                        f"after crafting {produced}/{number}"
                    )

        state = new_state

    raise Exception(f"Crafting failed: max steps ({max_steps}) reached after crafting {produced}/{number} {craft_name}")
