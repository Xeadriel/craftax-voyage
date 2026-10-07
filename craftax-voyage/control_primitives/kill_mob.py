# Description:
# Deterministically hunts down and kills a mob (any mob of a class, one specific mob
# type, or the necromancer boss) on the current floor. Uses melee attacks, arrows
# (bow + arrows), fireballs and iceballs (learned spells + mana), always picking the
# attack that deals the most damage to the mob's defenses. Moves with Dijkstra path
# planning to the cheapest cell from which the mob can be attacked (next to it, or in
# a clear straight line within range for projectiles), tunnelling through mineable
# blocks when the pickaxe allows it, and defends itself against adjacent monsters.
# For the boss it clears every spawn wave before hitting the necromancer (melee only)
# until it is defeated. Returns True when the target is killed, raises otherwise.

def kill_mob(state, log_func, step_func, target, max_steps=300):
    """
    Hunts and kills the target on the current floor with melee, arrows and spells.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        target: MobType to kill any mob of that class (PASSIVE, MELEE, RANGED),
            a tuple (MobType, type_id) to kill one specific mob type, or
            BlockType.NECROMANCER / "boss" to defeat the necromancer boss
            (the player has to be on the boss floor)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        True if a matching mob was killed (or the boss is defeated)

    Raises:
        Exception: If the target is invalid, no matching mob is on the floor, the target
            despawned or stayed unreachable, the player cannot damage the target, the
            player left the floor, the player died, or max_steps was reached
    """
    import heapq

    import numpy as np

    from craftax.craftax.constants import (
        DIRECTIONS,
        MOB_TYPE_DAMAGE_MAPPING,
        MOB_TYPE_DEFENSE_MAPPING,
        SOLID_BLOCKS,
        Action,
        BlockType,
        MobType,
        ProjectileType,
    )
    from craftax.craftax.craftax_state import EnvParams
    from craftax.craftax.util.game_logic_utils import get_player_damage_vector

    mob_names = {
        MobType.PASSIVE: ["Cow", "Bat", "Snail"],
        MobType.MELEE: [
            "Zombie", "Gnome warrior", "Orc soldier", "Lizard",
            "Knight", "Troll", "Pigman", "Frost troll",
        ],
        MobType.RANGED: [
            "Skeleton", "Gnome archer", "Orc mage", "Kobold",
            "Knight archer", "Deep thing", "Fire elemental", "Ice elemental",
        ],
    }
    mob_attributes = {
        MobType.PASSIVE: "passive_mobs",
        MobType.MELEE: "melee_mobs",
        MobType.RANGED: "ranged_mobs",
    }

    # Resolve and validate the target
    boss_mode = False
    target_classes = []
    target_type_id = None
    if isinstance(target, str) and target.strip().lower() in ("boss", "necromancer"):
        boss_mode = True
    elif isinstance(target, BlockType) and target in (
        BlockType.NECROMANCER,
        BlockType.NECROMANCER_VULNERABLE,
    ):
        boss_mode = True
    elif (
        isinstance(target, tuple)
        and len(target) == 2
        and isinstance(target[0], MobType)
        and isinstance(target[1], (int, np.integer))
        and not isinstance(target[1], bool)
    ):
        target_classes = [target[0]]
        target_type_id = int(target[1])
    elif isinstance(target, MobType):
        target_classes = [target]
    else:
        raise Exception(
            f"Invalid target {target!r}: expected MobType, (MobType, type_id), "
            f"BlockType.NECROMANCER or 'boss'"
        )

    if MobType.PROJECTILE in target_classes:
        raise Exception("Invalid target: projectiles cannot be killed")
    if target_type_id is not None and not 0 <= target_type_id < len(mob_names[target_classes[0]]):
        raise Exception(
            f"Invalid target: type_id {target_type_id} does not exist for {target_classes[0].name} mobs"
        )

    if boss_mode:
        target_name = "the necromancer boss"
    elif target_type_id is not None:
        target_name = (
            f"{target_classes[0].name} mob {mob_names[target_classes[0]][target_type_id]} "
            f"(type_id {target_type_id})"
        )
    else:
        target_name = f"a {target_classes[0].name} mob"

    max_steps = int(max_steps)
    if max_steps < 0:
        raise Exception(f"Invalid max_steps {max_steps}: must be non-negative")

    num_levels = int(state.map.shape[0])
    boss_level = num_levels - 1
    boss_hits_required = num_levels - 1
    start_level = int(state.player_level)
    max_player_projectiles = int(state.player_projectiles.mask.shape[1])
    # Mobs further away than this are removed by the game (except during the boss fight)
    despawn_distance = int(EnvParams().mob_despawn_distance)

    necromancer_position = None
    if boss_mode:
        if start_level != boss_level:
            raise Exception(
                f"Cannot fight the boss: player is on floor {start_level}, the boss is on floor {boss_level}"
            )
        necromancer_cells = np.argwhere(
            (np.asarray(state.map[boss_level]) == BlockType.NECROMANCER.value)
            | (np.asarray(state.map[boss_level]) == BlockType.NECROMANCER_VULNERABLE.value)
        )
        if len(necromancer_cells) == 0:
            raise Exception(f"Cannot fight the boss: no necromancer found on floor {boss_level}")
        necromancer_position = (int(necromancer_cells[0][0]), int(necromancer_cells[0][1]))
        # During the boss fight every monster has to die before the boss is vulnerable
        hunted_classes = [MobType.MELEE, MobType.RANGED]
    else:
        hunted_classes = target_classes

    # Movement actions with their (row, col) offsets, in a fixed order for determinism
    moves = [
        (action.value, int(DIRECTIONS[action.value][0]), int(DIRECTIONS[action.value][1]))
        for action in (Action.LEFT, Action.RIGHT, Action.UP, Action.DOWN)
    ]
    opposite_action = {
        a: next(b for b, r2, c2 in moves if (r2, c2) == (-r1, -c1)) for a, r1, c1 in moves
    }
    action_names = {action.value: action.name for action in Action}

    # Blocks that stop projectiles (they fly over water and lava)
    projectile_blocking_blocks = set(SOLID_BLOCKS)
    # Cells the player cannot stand on
    impassable_blocks = set(SOLID_BLOCKS) | {
        BlockType.WATER.value,
        BlockType.LAVA.value,
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER_VULNERABLE.value,
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

    walk_cost = 1
    tunnel_cost = 4
    mob_extra_cost = 6
    max_mine_attempts = 3
    max_mob_wait_steps = 2
    max_unreachable_steps = 10
    projectile_range = 6

    tracked = None
    previous_candidates = None
    previous_player_position = None
    failed_mine_attempts = {}
    unminable_cells = set()
    mob_block_steps = 0
    unreachable_steps = 0

    log_func(f"[kill_mob] Start hunting {target_name} with a budget of {max_steps} steps")

    for steps_taken in range(max_steps + 1):
        # ---------- Observe ----------
        player_row = int(state.player_position[0])
        player_col = int(state.player_position[1])
        current_level = int(state.player_level)
        facing = int(state.player_direction)

        if current_level != start_level:
            log_func(f"[kill_mob] Player moved from floor {start_level} to floor {current_level}")
            raise Exception(
                f"Killing failed: player left floor {start_level} while hunting {target_name}"
            )

        if boss_mode and int(state.boss_progress) >= boss_hits_required:
            log_func(
                f"[kill_mob] The necromancer is defeated ({int(state.boss_progress)}/{boss_hits_required} hits) "
                f"after {steps_taken} steps"
            )
            return True

        block_map = np.asarray(state.map[current_level])
        mob_occupied = np.asarray(state.mob_map[current_level]).astype(bool)
        map_rows, map_cols = block_map.shape

        # Every mob slot of the hunted classes: (class, index) -> (alive, row, col, health, type_id)
        slots = {}
        candidates = []
        for mob_class in hunted_classes:
            mobs = getattr(state, mob_attributes[mob_class])
            mob_mask = np.asarray(mobs.mask[current_level])
            mob_positions = np.asarray(mobs.position[current_level])
            mob_type_ids = np.asarray(mobs.type_id[current_level])
            mob_healths = np.asarray(mobs.health[current_level])
            for mob_index in range(len(mob_mask)):
                slots[(mob_class, mob_index)] = (
                    bool(mob_mask[mob_index]),
                    int(mob_positions[mob_index][0]),
                    int(mob_positions[mob_index][1]),
                    float(mob_healths[mob_index]),
                    int(mob_type_ids[mob_index]),
                )
                if not mob_mask[mob_index]:
                    continue
                if target_type_id is not None and int(mob_type_ids[mob_index]) != target_type_id:
                    continue
                candidates.append(
                    (
                        mob_class,
                        mob_index,
                        int(mob_positions[mob_index][0]),
                        int(mob_positions[mob_index][1]),
                        float(mob_healths[mob_index]),
                        int(mob_type_ids[mob_index]),
                    )
                )

        # Detect kills, despawns and damage since the previous step (projectiles land later)
        if previous_candidates is not None:
            for old in previous_candidates:
                slot = slots[(old[0], old[1])]
                old_label = f"{mob_names[old[0]][old[5]]} ({old[0].name} #{old[1]})"
                vanished = (
                    not slot[0]
                    or abs(slot[1] - old[2]) + abs(slot[2] - old[3]) > 1
                    or slot[3] > old[4]
                )
                if vanished:
                    old_distance = abs(old[2] - previous_player_position[0]) + abs(old[3] - previous_player_position[1])
                    if current_level == boss_level or old_distance < despawn_distance - 2:
                        log_func(
                            f"[kill_mob] Killed {old_label} at ({old[2]}, {old[3]}) after {steps_taken} steps"
                        )
                        if not boss_mode:
                            log_func(f"[kill_mob] Successfully killed {target_name}")
                            return True
                    else:
                        log_func(f"[kill_mob] {old_label} despawned at distance {old_distance}")
                    if tracked is not None and (tracked[0], tracked[1]) == (old[0], old[1]):
                        tracked = None
                elif slot[3] < old[4]:
                    log_func(
                        f"[kill_mob] {old_label} took {old[4] - slot[3]:.2f} damage, "
                        f"health {old[4]:.2f} -> {slot[3]:.2f}"
                    )

        # Keep following the same mob as long as it is the same living mob
        if tracked is not None:
            match = next(
                (c for c in candidates if c[0] == tracked[0] and c[1] == tracked[1]), None
            )
            if (
                match is None
                or abs(match[2] - tracked[2]) + abs(match[3] - tracked[3]) > 1
                or match[4] > tracked[4]
            ):
                log_func(
                    f"[kill_mob] Lost track of {mob_names[tracked[0]][tracked[5]]} "
                    f"({tracked[0].name} #{tracked[1]})"
                )
                tracked = None
            else:
                tracked = match

        log_func(
            f"[kill_mob] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"floor {current_level}, facing {action_names.get(facing, facing)}, "
            f"health {float(state.player_health):.1f}, mana {int(state.player_mana)}, "
            f"arrows {int(state.inventory.arrows)}, {len(candidates)} matching mob(s) alive"
            + (
                f", boss hits {int(state.boss_progress)}/{boss_hits_required}, "
                f"spawn wave timer {int(state.boss_timesteps_to_spawn_this_round)}"
                if boss_mode else ""
            )
        )

        if steps_taken >= max_steps:
            log_func(f"[kill_mob] Max steps ({max_steps}) reached without killing {target_name}")
            raise Exception(
                f"Killing failed: max steps ({max_steps}) reached without killing {target_name}"
            )

        # ---------- Decide on an action ----------
        action = Action.NOOP.value
        action_reason = ""
        expected_cell = None
        mining_cell = None
        attacking_boss = False
        weapon_used = None

        if bool(state.is_sleeping) or bool(state.is_resting):
            action_reason = "player is sleeping/resting, actions are ignored until it wakes up"
        else:
            pickaxe_level = int(state.inventory.pickaxe)

            # Damage vectors (physical, fire, ice) of every currently usable attack
            projectile_slot_free = (
                int(np.sum(np.asarray(state.player_projectiles.mask[current_level]))) < max_player_projectiles
            )
            melee_vector = np.asarray(get_player_damage_vector(state), dtype=np.float32)
            ranged_weapons = []
            if int(state.inventory.bow) >= 1 and int(state.inventory.arrows) >= 1 and projectile_slot_free:
                arrow_vector = np.array(
                    MOB_TYPE_DAMAGE_MAPPING[ProjectileType.ARROW2.value, MobType.PROJECTILE.value],
                    dtype=np.float32,
                )
                bow_enchantment = int(state.bow_enchantment)
                if bow_enchantment in (1, 2):
                    arrow_vector[bow_enchantment] += arrow_vector[0] / 2
                arrow_vector *= 1 + 0.2 * (int(state.player_dexterity) - 1)
                ranged_weapons.append(("arrow", Action.SHOOT_ARROW.value, arrow_vector))
            magic_coefficient = 1 + 0.5 * (int(state.player_intelligence) - 1)
            if bool(state.learned_spells[0]) and int(state.player_mana) >= 2 and projectile_slot_free:
                ranged_weapons.append(
                    (
                        "fireball",
                        Action.CAST_FIREBALL.value,
                        np.asarray(
                            MOB_TYPE_DAMAGE_MAPPING[ProjectileType.FIREBALL.value, MobType.PROJECTILE.value],
                            dtype=np.float32,
                        ) * magic_coefficient,
                    )
                )
            if bool(state.learned_spells[1]) and int(state.player_mana) >= 2 and projectile_slot_free:
                ranged_weapons.append(
                    (
                        "iceball",
                        Action.CAST_ICEBALL.value,
                        np.asarray(
                            MOB_TYPE_DAMAGE_MAPPING[ProjectileType.ICEBALL.value, MobType.PROJECTILE.value],
                            dtype=np.float32,
                        ) * magic_coefficient,
                    )
                )

            # Dijkstra over the floor; tunnelling and passing other mobs cost extra
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
                    if (next_row, next_col) in unminable_cells:
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

            # Attack spots of every candidate: cell -> (action that faces the mob, distance in a straight line)
            attack_spots = {}
            attack_damages = {}
            for candidate in candidates:
                defense = np.asarray(
                    MOB_TYPE_DEFENSE_MAPPING[candidate[5], candidate[0].value], dtype=np.float32
                )
                damages = [("melee", Action.DO.value, float(np.sum((1 - defense) * melee_vector)))] + [
                    (name, weapon_action, float(np.sum((1 - defense) * vector)))
                    for name, weapon_action, vector in ranged_weapons
                ]
                attack_damages[(candidate[0], candidate[1])] = damages
                max_reach = projectile_range if any(d[2] > 0 for d in damages[1:]) else 1
                spots = {}
                for outward_action, d_row, d_col in moves:
                    for reach in range(1, max_reach + 1):
                        spot_row = candidate[2] + d_row * reach
                        spot_col = candidate[3] + d_col * reach
                        if not (0 <= spot_row < map_rows and 0 <= spot_col < map_cols):
                            break
                        is_player_cell = (spot_row, spot_col) == (player_row, player_col)
                        if not is_player_cell and mob_occupied[spot_row, spot_col]:
                            break
                        spot_block = int(block_map[spot_row, spot_col])
                        if spot_block in projectile_blocking_blocks:
                            break
                        if is_player_cell or spot_block not in impassable_blocks:
                            spots[(spot_row, spot_col)] = (opposite_action[outward_action], reach)
                attack_spots[(candidate[0], candidate[1])] = spots

            # Pick the mob that is cheapest to attack if none is being followed
            if tracked is None and len(candidates) > 0:
                tracked = candidates[0]
                best_key = None
                for candidate in candidates:
                    spots = attack_spots[(candidate[0], candidate[1])]
                    reach_cost = min(
                        (float(distance[spot]) for spot in spots), default=np.inf
                    )
                    manhattan = abs(candidate[2] - player_row) + abs(candidate[3] - player_col)
                    key = (
                        0 if np.isfinite(reach_cost) else 1,
                        reach_cost if np.isfinite(reach_cost) else manhattan,
                        candidate[2],
                        candidate[3],
                        candidate[0].value,
                        candidate[1],
                    )
                    if best_key is None or key < best_key:
                        best_key = key
                        tracked = candidate

                damages = attack_damages[(tracked[0], tracked[1])]
                if all(d[2] <= 0 for d in damages):
                    log_func(f"[kill_mob] No available attack damages {mob_names[tracked[0]][tracked[5]]}")
                    raise Exception(
                        f"Killing failed: the player cannot damage {mob_names[tracked[0]][tracked[5]]}"
                    )
                log_func(
                    f"[kill_mob] Targeting {mob_names[tracked[0]][tracked[5]]} ({tracked[0].name} #{tracked[1]}) "
                    f"at ({tracked[2]}, {tracked[3]}) with {tracked[4]:.2f} health; damage per attack: "
                    + ", ".join(f"{name} {damage:.2f}" for name, _, damage in damages)
                    + ("" if best_key[0] == 0 else "; currently unreachable")
                )

            if tracked is None and not boss_mode:
                log_func(f"[kill_mob] No matching mob ({target_name}) is alive near the player on floor {current_level}")
                raise Exception(
                    f"Killing failed: no matching mob ({target_name}) is present near the player on floor {current_level}"
                )

            # Decide which mob to engage from the current cell: the target, or an adjacent monster
            engage = None
            if tracked is not None:
                tracked_spots = attack_spots[(tracked[0], tracked[1])]
                if (player_row, player_col) in tracked_spots:
                    face_action, reach = tracked_spots[(player_row, player_col)]
                    engage = (tracked, face_action, reach, attack_damages[(tracked[0], tracked[1])], "target")
            if engage is None:
                for mob_class in (MobType.MELEE, MobType.RANGED):
                    mobs = getattr(state, mob_attributes[mob_class])
                    mob_mask = np.asarray(mobs.mask[current_level])
                    mob_positions = np.asarray(mobs.position[current_level])
                    for mob_index in range(len(mob_mask)):
                        if engage is not None or not mob_mask[mob_index]:
                            continue
                        mob_row = int(mob_positions[mob_index][0])
                        mob_col = int(mob_positions[mob_index][1])
                        face_action = next(
                            (
                                a for a, d_row, d_col in moves
                                if player_row + d_row == mob_row and player_col + d_col == mob_col
                            ),
                            None,
                        )
                        if face_action is None:
                            continue
                        mob_type_id = int(np.asarray(mobs.type_id[current_level])[mob_index])
                        defense = np.asarray(MOB_TYPE_DEFENSE_MAPPING[mob_type_id, mob_class.value], dtype=np.float32)
                        defender = (
                            mob_class,
                            mob_index,
                            mob_row,
                            mob_col,
                            float(np.asarray(mobs.health[current_level])[mob_index]),
                            mob_type_id,
                        )
                        damages = [("melee", Action.DO.value, float(np.sum((1 - defense) * melee_vector)))] + [
                            (name, weapon_action, float(np.sum((1 - defense) * vector)))
                            for name, weapon_action, vector in ranged_weapons
                        ]
                        engage = (defender, face_action, 1, damages, "adjacent monster")

            boss_vulnerable = (
                boss_mode
                and len(candidates) == 0
                and int(state.boss_timesteps_to_spawn_this_round) <= 0
            )
            necromancer_action = None
            if boss_mode and tracked is None:
                necromancer_action = next(
                    (
                        a for a, d_row, d_col in moves
                        if player_row + d_row == necromancer_position[0]
                        and player_col + d_col == necromancer_position[1]
                    ),
                    None,
                )

            if engage is not None:
                unreachable_steps = 0
                mob_block_steps = 0
                engaged, face_action, reach, damages, role = engage
                engaged_label = f"{mob_names[engaged[0]][engaged[5]]} ({engaged[0].name} #{engaged[1]})"
                best_weapon = None
                for weapon in damages:
                    if weapon[0] == "melee" and reach > 1:
                        continue
                    if best_weapon is None or weapon[2] > best_weapon[2]:
                        best_weapon = weapon
                if facing != face_action:
                    action = face_action
                    action_reason = (
                        f"facing {role} {engaged_label} at ({engaged[2]}, {engaged[3]}), "
                        f"{reach} cell(s) away, to attack with {best_weapon[0]}"
                    )
                else:
                    action = best_weapon[1]
                    weapon_used = best_weapon[0]
                    action_reason = (
                        f"attacking {role} {engaged_label} at ({engaged[2]}, {engaged[3]}) with {best_weapon[0]} "
                        f"from {reach} cell(s) away (expected damage {best_weapon[2]:.2f}, "
                        f"health {engaged[4]:.2f})"
                    )
            elif necromancer_action is not None:
                unreachable_steps = 0
                mob_block_steps = 0
                if facing != necromancer_action:
                    action = necromancer_action
                    action_reason = f"turning towards the necromancer at {necromancer_position}"
                elif not boss_vulnerable:
                    action_reason = (
                        f"waiting next to the necromancer until it is vulnerable "
                        f"(spawn wave timer {int(state.boss_timesteps_to_spawn_this_round)})"
                    )
                else:
                    action = Action.DO.value
                    attacking_boss = True
                    action_reason = f"attacking the necromancer at {necromancer_position} with melee"
            else:
                # Path to the cheapest cell from which the target can be attacked
                if tracked is not None:
                    goal_spots = attack_spots[(tracked[0], tracked[1])]
                    goal_label = f"{mob_names[tracked[0]][tracked[5]]} ({tracked[0].name} #{tracked[1]}) at ({tracked[2]}, {tracked[3]})"
                else:
                    goal_spots = {}
                    for a, d_row, d_col in moves:
                        spot_row = necromancer_position[0] + d_row
                        spot_col = necromancer_position[1] + d_col
                        if 0 <= spot_row < map_rows and 0 <= spot_col < map_cols:
                            goal_spots[(spot_row, spot_col)] = (opposite_action[a], 1)
                    goal_label = f"the necromancer at {necromancer_position}"
                best_goal = None
                for spot in goal_spots:
                    if spot == (player_row, player_col) or not np.isfinite(distance[spot]):
                        continue
                    key = (float(distance[spot]), spot[0], spot[1])
                    if best_goal is None or key < best_goal:
                        best_goal = key

                if best_goal is None:
                    unreachable_steps += 1
                    if unreachable_steps > max_unreachable_steps:
                        log_func(
                            f"[kill_mob] {goal_label} stayed unreachable for {max_unreachable_steps} steps"
                        )
                        raise Exception(f"Killing failed: {goal_label} is unreachable")
                    action_reason = (
                        f"no reachable attack position for {goal_label}, waiting for it to move "
                        f"({unreachable_steps}/{max_unreachable_steps})"
                    )
                else:
                    unreachable_steps = 0
                    cell = (best_goal[1], best_goal[2])
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
                    goal_reach = goal_spots[(best_goal[1], best_goal[2])][1]

                    if mob_occupied[next_row, next_col]:
                        mob_block_steps += 1
                        if mob_block_steps <= max_mob_wait_steps:
                            action_reason = (
                                f"another mob blocks next cell ({next_row}, {next_col}), waiting "
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
                        if next_block in tunnel_pickaxe_requirement:
                            if facing != move_action:
                                action = move_action
                                action_reason = (
                                    f"turning towards {BlockType(next_block).name} at ({next_row}, {next_col}) to tunnel"
                                )
                            else:
                                action = Action.DO.value
                                mining_cell = (next_row, next_col)
                                action_reason = (
                                    f"mining {BlockType(next_block).name} at ({next_row}, {next_col}) "
                                    f"to get to {goal_label}"
                                )
                        else:
                            action = move_action
                            expected_cell = (next_row, next_col)
                            action_reason = (
                                f"moving to ({next_row}, {next_col}) towards attack position "
                                f"({best_goal[1]}, {best_goal[2]}) {goal_reach} cell(s) from {goal_label} "
                                f"(path cost {best_goal[0]:.0f})"
                            )

        # ---------- Act ----------
        previous_candidates = candidates
        previous_player_position = (player_row, player_col)

        log_func(f"[kill_mob] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Killing failed: step function returned no state for action {action_names[action]}")

        episode_reset = int(new_state.timestep) <= int(state.timestep)
        if episode_reset and attacking_boss and int(state.boss_progress) + 1 >= boss_hits_required:
            # Defeating the boss ends the episode, so the environment resets right away
            log_func(
                f"[kill_mob] Final hit landed, the necromancer is defeated "
                f"({boss_hits_required}/{boss_hits_required} hits) and the episode ended"
            )
            return True
        if float(new_state.player_health) <= 0 or episode_reset:
            log_func("[kill_mob] The player died or the episode ended during the fight")
            raise Exception(f"Killing failed: the player died while hunting {target_name}")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[kill_mob] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if int(new_state.monsters_killed[current_level]) > int(state.monsters_killed[current_level]):
            log_func(
                f"[kill_mob] Monsters killed on floor {current_level}: "
                f"{int(state.monsters_killed[current_level])} -> {int(new_state.monsters_killed[current_level])}"
            )

        if attacking_boss:
            if int(new_state.boss_progress) > int(state.boss_progress):
                log_func(
                    f"[kill_mob] Hit the necromancer ({int(new_state.boss_progress)}/{boss_hits_required} hits), "
                    f"a new spawn wave starts"
                )
            else:
                log_func("[kill_mob] The attack on the necromancer did no damage")

        if weapon_used == "arrow":
            log_func(
                f"[kill_mob] Shot an arrow, arrows {int(state.inventory.arrows)} -> {int(new_state.inventory.arrows)}"
            )
        elif weapon_used in ("fireball", "iceball"):
            log_func(
                f"[kill_mob] Cast a {weapon_used}, mana {int(state.player_mana)} -> {int(new_state.player_mana)}"
            )

        if expected_cell is not None and int(new_state.player_level) == current_level:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(
                    f"[kill_mob] Move to {expected_cell} did not succeed, still at {new_position}; replanning"
                )

        if mining_cell is not None and int(new_state.player_level) == current_level:
            new_block = int(new_state.map[current_level, mining_cell[0], mining_cell[1]])
            if new_block == int(block_map[mining_cell]):
                failed_mine_attempts[mining_cell] = failed_mine_attempts.get(mining_cell, 0) + 1
                log_func(
                    f"[kill_mob] Mining {mining_cell} had no effect "
                    f"({failed_mine_attempts[mining_cell]}/{max_mine_attempts})"
                )
                if failed_mine_attempts[mining_cell] >= max_mine_attempts:
                    unminable_cells.add(mining_cell)
                    log_func(f"[kill_mob] Treating {mining_cell} as impassable from now on")
            else:
                log_func(f"[kill_mob] Mined {mining_cell}, it is now {BlockType(new_block).name}")

        state = new_state

    raise Exception(f"Killing failed: max steps ({max_steps}) reached without killing {target_name}")
