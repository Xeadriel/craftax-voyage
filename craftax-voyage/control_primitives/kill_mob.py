# Description:
# Deterministically hunts down and kills a mob in sight (any mob of a class, one specific
# mob type, or the necromancer boss) on the current floor, using only what the player
# can see or has seen. Uses melee attacks, arrows (bow + arrows), fireballs and iceballs
# (learned spells + mana), always picking the attack that deals the most damage to the
# mob's defenses. Moves with Dijkstra path planning over the known map (optimistic
# through unseen cells) to the cheapest cell from which the mob can be attacked (next to
# it, or in a clear, known straight line within range for projectiles), tunnelling
# through mineable blocks when the pickaxe allows it, and defends itself against
# adjacent monsters. The engaged mob is followed across steps by proximity; a kill is a
# tracked mob vanishing right after the player hit it (melee or projectile).
# For the boss it clears every visible spawn wave and hits the necromancer (melee only)
# whenever it is vulnerable until the game is won. Returns the final state on success,
# raises otherwise.

def kill_mob(state, log_func, step_func, target, max_steps=20):
    """
    Hunts and kills a target in sight on the current floor with melee, arrows and spells.

    Only mobs the player can currently see are hunted, so explore first (e.g. with
    explore_until) until the target is in view. A mob that leaves the view is followed
    to its last known position for a few steps.

    Args:
        state: Current EnvState
        log_func: Logging function taking a single string
        step_func: Function taking an action id (int) and returning the new EnvState
        target: MobType to kill any mob of that class (PASSIVE, MELEE, RANGED),
            a tuple (MobType, type_id) to kill one specific mob type, or
            BlockType.NECROMANCER / "boss" to defeat the necromancer boss
            (the player has to be on the boss floor and must have seen the necromancer)
        max_steps: Maximum number of calls to step_func before giving up

    Returns:
        The final EnvState (after the last step) once a matching mob was killed by the
        player, or, for the boss, the state returned right after the winning hit (the
        game ends and the environment resets)

    Raises:
        Exception: If the target is invalid, no matching mob is in sight (explore first),
            the target was lost from view or stayed unreachable, the necromancer was not
            seen yet, the player cannot damage the target, the player left the floor, the
            player died, or max_steps was reached
    """
    import heapq

    import numpy as np

    from control_primitives.knowledge import (
        UNKNOWN,
        boss_vulnerable,
        is_visible,
        known_blocks,
        visible_mask,
        visible_mobs,
        visible_player_projectiles,
    )
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
    start_level = int(state.player_level)

    necromancer_position = None
    if boss_mode:
        if start_level != boss_level:
            raise Exception(
                f"Cannot fight the boss: player is on floor {start_level}, the boss is on floor {boss_level}"
            )
        necromancer_cells = np.argwhere(known_blocks(state) == BlockType.NECROMANCER.value)
        if len(necromancer_cells) == 0:
            log_func("[kill_mob] The necromancer has not been seen on this floor yet")
            raise Exception("Cannot fight the boss: necromancer not seen, explore first")
        necromancer_position = (int(necromancer_cells[0][0]), int(necromancer_cells[0][1]))
        # During the boss fight every spawn wave monster has to die before the boss is vulnerable
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
    projectile_actions = (
        Action.SHOOT_ARROW.value,
        Action.CAST_FIREBALL.value,
        Action.CAST_ICEBALL.value,
    )

    # Blocks that stop projectiles (they fly over water and lava)
    projectile_blocking_blocks = set(SOLID_BLOCKS)
    # Cells the player cannot stand on
    impassable_blocks = set(SOLID_BLOCKS) | {
        BlockType.WATER.value,
        BlockType.LAVA.value,
        BlockType.INVALID.value,
        BlockType.OUT_OF_BOUNDS.value,
        BlockType.DARKNESS.value,
        BlockType.NECROMANCER.value,
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
    unknown_cost = 2
    tunnel_cost = 4
    mob_extra_cost = 6
    max_mine_attempts = 3
    max_mob_wait_steps = 2
    max_unreachable_steps = 10
    max_lost_steps = 5
    ranged_cooldown_steps = 5
    projectile_range = 6
    projectile_hit_distance = 2

    def mob_label(mob):
        return f"{mob_names[mob[0]][mob[1]]} ({mob[0].name})"

    # Mobs are (class, type_id, row, col, health). The engaged mob is followed by proximity:
    # same class and type, at most one cell per step away, health never increases.
    tracked = None
    tracked_visible = False
    lost_steps = 0
    previous_candidates = None
    tracked_previous_index = None
    previous_action = None
    previous_facing_cell = None
    previous_projectile_cells = []
    failed_mine_attempts = {}
    unminable_cells = set()
    mob_block_steps = 0
    unreachable_steps = 0
    ranged_cooldown = 0
    failed_shots = 0
    boss_hits = 0

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

        block_map = known_blocks(state)
        view = visible_mask(state)
        mobs_in_view = visible_mobs(state)
        map_rows, map_cols = block_map.shape

        mob_occupied = np.zeros((map_rows, map_cols), dtype=bool)
        for _, _, mob_row, mob_col, _ in mobs_in_view:
            mob_occupied[mob_row, mob_col] = True

        candidates = [
            mob for mob in mobs_in_view
            if mob[0] in hunted_classes and (target_type_id is None or mob[1] == target_type_id)
        ]

        # Match the matching mobs seen last step to the ones in view now (a mob moves at most
        # one cell per step and its health never increases) to detect kills and damage.
        # A mob counts as killed by the player if it vanished right after the player hit its
        # cell with DO, or while one of the player's projectiles was close to it.
        if previous_candidates is not None:
            pairs = []
            for old_index, old in enumerate(previous_candidates):
                for new_index, new in enumerate(candidates):
                    if (old[0], old[1]) != (new[0], new[1]):
                        continue
                    distance_moved = abs(old[2] - new[2]) + abs(old[3] - new[3])
                    if distance_moved > 1:
                        continue
                    pairs.append(
                        (
                            distance_moved,
                            0 if new[4] <= old[4] + 1e-6 else 1,
                            abs(old[4] - new[4]),
                            old_index,
                            new_index,
                        )
                    )
            pairs.sort()
            matched_old = {}
            matched_new = set()
            for _, _, _, old_index, new_index in pairs:
                if old_index in matched_old or new_index in matched_new:
                    continue
                matched_old[old_index] = new_index
                matched_new.add(new_index)

            for old_index, old in enumerate(previous_candidates):
                is_tracked = tracked_visible and old_index == tracked_previous_index
                if old_index in matched_old:
                    new = candidates[matched_old[old_index]]
                    if new[4] < old[4] - 1e-6:
                        log_func(
                            f"[kill_mob] {mob_label(old)} took {old[4] - new[4]:.2f} damage, "
                            f"health {old[4]:.2f} -> {new[4]:.2f}"
                        )
                    if is_tracked:
                        tracked = new
                    continue

                hit_by_player = (
                    previous_action == Action.DO.value and (old[2], old[3]) == previous_facing_cell
                ) or any(
                    abs(old[2] - p_row) + abs(old[3] - p_col) <= projectile_hit_distance
                    for p_row, p_col in previous_projectile_cells
                )
                if hit_by_player:
                    log_func(
                        f"[kill_mob] Killed {mob_label(old)} at ({old[2]}, {old[3]}) after {steps_taken} steps"
                    )
                    if not boss_mode:
                        log_func(f"[kill_mob] Successfully killed {target_name}")
                        return state
                    if is_tracked:
                        tracked = None
                        tracked_visible = False
                    continue

                surroundings_visible = all(
                    0 <= old[2] + d_row < map_rows
                    and 0 <= old[3] + d_col < map_cols
                    and view[old[2] + d_row, old[3] + d_col]
                    for d_row, d_col in [(0, 0)] + [(m[1], m[2]) for m in moves]
                )
                if is_tracked and surroundings_visible:
                    log_func(
                        f"[kill_mob] {mob_label(old)} at ({old[2]}, {old[3]}) disappeared without being "
                        f"killed by the player (despawned); no longer tracking it"
                    )
                    tracked = None
                    tracked_visible = False
                elif is_tracked:
                    log_func(
                        f"[kill_mob] {mob_label(old)} left the view at ({old[2]}, {old[3]}); "
                        f"following its last known position for up to {max_lost_steps} steps"
                    )
                    tracked = old
                    tracked_visible = False
                    lost_steps = 0
                elif surroundings_visible:
                    log_func(
                        f"[kill_mob] {mob_label(old)} at ({old[2]}, {old[3]}) disappeared without being "
                        f"killed by the player (despawned)"
                    )
        else:
            matched_new = set()

        # A tracked mob out of view: look for it near its last known position
        if tracked is not None and not tracked_visible:
            lost_steps += 1
            best_key = None
            best_match = None
            for new_index, new in enumerate(candidates):
                if new_index in matched_new or (new[0], new[1]) != (tracked[0], tracked[1]):
                    continue
                distance_moved = abs(new[2] - tracked[2]) + abs(new[3] - tracked[3])
                if distance_moved > lost_steps:
                    continue
                key = (distance_moved, 0 if new[4] <= tracked[4] + 1e-6 else 1, abs(new[4] - tracked[4]))
                if best_key is None or key < best_key:
                    best_key = key
                    best_match = new
            if best_match is not None:
                log_func(f"[kill_mob] {mob_label(best_match)} is back in view at ({best_match[2]}, {best_match[3]})")
                tracked = best_match
                tracked_visible = True
                lost_steps = 0
            elif lost_steps > max_lost_steps:
                log_func(
                    f"[kill_mob] Gave up following {mob_label(tracked)}: not seen for {max_lost_steps} steps "
                    f"around its last known position ({tracked[2]}, {tracked[3]})"
                )
                tracked = None
                if len(candidates) == 0 and not boss_mode:
                    raise Exception(
                        f"Killing failed: lost sight of the target and no matching mob ({target_name}) in sight, explore first"
                    )

        log_func(
            f"[kill_mob] Step {steps_taken}/{max_steps}: position ({player_row}, {player_col}), "
            f"floor {current_level}, facing {action_names.get(facing, facing)}, "
            f"health {float(state.player_health):.1f}, mana {int(state.player_mana)}, "
            f"arrows {int(state.inventory.arrows)}, {len(candidates)} matching mob(s) in sight"
            + (
                f", boss {'vulnerable' if boss_vulnerable(state) else 'not vulnerable'}, "
                f"boss hits landed {boss_hits}"
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
            if tracked is None and len(candidates) == 0 and not boss_mode:
                log_func(f"[kill_mob] No matching mob ({target_name}) is in sight")
                raise Exception(f"Killing failed: no matching mob ({target_name}) in sight, explore first")
        else:
            pickaxe_level = int(state.inventory.pickaxe)
            if ranged_cooldown > 0:
                ranged_cooldown -= 1

            # Damage vectors (physical, fire, ice) of every currently usable attack
            melee_vector = np.asarray(get_player_damage_vector(state), dtype=np.float32)
            ranged_weapons = []
            if ranged_cooldown == 0:
                if int(state.inventory.bow) >= 1 and int(state.inventory.arrows) >= 1:
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
                if bool(state.learned_spells[0]) and int(state.player_mana) >= 2:
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
                if bool(state.learned_spells[1]) and int(state.player_mana) >= 2:
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

            def damages_against(mob_class, type_id):
                defense = np.asarray(MOB_TYPE_DEFENSE_MAPPING[type_id, mob_class.value], dtype=np.float32)
                return [("melee", Action.DO.value, float(np.sum((1 - defense) * melee_vector)))] + [
                    (name, weapon_action, float(np.sum((1 - defense) * vector)))
                    for name, weapon_action, vector in ranged_weapons
                ]

            # Dijkstra over the known floor; unseen cells are assumed walkable at an extra cost,
            # but the first step must go into a known cell. Tunnelling and passing visible mobs
            # cost extra.
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

            def attack_spots_for(mob_row, mob_col, damages):
                # Cells from which a mob at (mob_row, mob_col) can be attacked:
                # cell -> (action that faces the mob, distance in a straight line).
                # The line of fire only passes known, non-blocking cells without other mobs.
                max_reach = projectile_range if any(d[2] > 0 for d in damages[1:]) else 1
                spots = {}
                for outward_action, d_row, d_col in moves:
                    for reach in range(1, max_reach + 1):
                        spot_row = mob_row + d_row * reach
                        spot_col = mob_col + d_col * reach
                        if not (0 <= spot_row < map_rows and 0 <= spot_col < map_cols):
                            break
                        is_player_cell = (spot_row, spot_col) == (player_row, player_col)
                        if not is_player_cell and mob_occupied[spot_row, spot_col]:
                            break
                        spot_block = int(block_map[spot_row, spot_col])
                        if spot_block == UNKNOWN or spot_block in projectile_blocking_blocks:
                            break
                        if is_player_cell or spot_block not in impassable_blocks:
                            spots[(spot_row, spot_col)] = (opposite_action[outward_action], reach)
                return spots

            # Pick the visible mob that is cheapest to attack if none is being followed
            if tracked is None and len(candidates) > 0:
                best_key = None
                best_index = None
                for candidate_index, candidate in enumerate(candidates):
                    spots = attack_spots_for(
                        candidate[2], candidate[3], damages_against(candidate[0], candidate[1])
                    )
                    reach_cost = min((float(distance[spot]) for spot in spots), default=np.inf)
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
                        best_index = candidate_index
                tracked = candidates[best_index]
                tracked_visible = True
                lost_steps = 0

                damages = damages_against(tracked[0], tracked[1])
                if all(d[2] <= 0 for d in damages):
                    log_func(f"[kill_mob] No available attack damages {mob_names[tracked[0]][tracked[1]]}")
                    raise Exception(
                        f"Killing failed: the player cannot damage {mob_names[tracked[0]][tracked[1]]}"
                    )
                log_func(
                    f"[kill_mob] Targeting {mob_label(tracked)} at ({tracked[2]}, {tracked[3]}) "
                    f"with {tracked[4]:.2f} health; damage per attack: "
                    + ", ".join(f"{name} {damage:.2f}" for name, _, damage in damages)
                    + ("" if best_key[0] == 0 else "; currently unreachable")
                )

            if tracked is None and not boss_mode:
                log_func(f"[kill_mob] No matching mob ({target_name}) is in sight")
                raise Exception(f"Killing failed: no matching mob ({target_name}) in sight, explore first")

            tracked_damages = None
            tracked_spots = {}
            if tracked is not None:
                tracked_damages = damages_against(tracked[0], tracked[1])
                tracked_spots = attack_spots_for(tracked[2], tracked[3], tracked_damages)

            # Decide which mob to engage from the current cell: the target, or an adjacent monster
            engage = None
            if tracked is not None and tracked_visible and (player_row, player_col) in tracked_spots:
                face_action, reach = tracked_spots[(player_row, player_col)]
                engage = (tracked, face_action, reach, tracked_damages, "target")
            if engage is None:
                for mob in mobs_in_view:
                    if mob[0] not in (MobType.MELEE, MobType.RANGED):
                        continue
                    face_action = next(
                        (
                            a for a, d_row, d_col in moves
                            if player_row + d_row == mob[2] and player_col + d_col == mob[3]
                        ),
                        None,
                    )
                    if face_action is None:
                        continue
                    engage = (mob, face_action, 1, damages_against(mob[0], mob[1]), "adjacent monster")
                    break

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
                engaged_label = mob_label(engaged)
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
                elif not boss_vulnerable(state):
                    action_reason = "waiting next to the necromancer until it is vulnerable"
                else:
                    action = Action.DO.value
                    attacking_boss = True
                    action_reason = f"attacking the vulnerable necromancer at {necromancer_position} with melee"
            else:
                # Path to the cheapest cell from which the target (or its last known position) can be attacked
                if tracked is not None:
                    goal_spots = tracked_spots
                    goal_label = (
                        f"{mob_label(tracked)} at ({tracked[2]}, {tracked[3]})"
                        + ("" if tracked_visible else " (last seen)")
                    )
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
        tracked_previous_index = None
        if tracked is not None and tracked_visible:
            tracked_previous_index = next(
                (i for i, mob in enumerate(candidates) if mob == tracked), None
            )
            if tracked_previous_index is None:
                tracked_visible = False
        previous_action = action
        previous_facing_cell = (
            player_row + int(DIRECTIONS[facing][0]),
            player_col + int(DIRECTIONS[facing][1]),
        )
        previous_projectile_cells = [
            (p_row, p_col) for _, p_row, p_col in visible_player_projectiles(state)
        ]
        if action in projectile_actions:
            # A projectile fired this step spawns in front of the player
            previous_projectile_cells.append(previous_facing_cell)
        boss_was_vulnerable = boss_mode and boss_vulnerable(state)

        log_func(f"[kill_mob] Step {steps_taken + 1}/{max_steps}: {action_names[action]} - {action_reason}")
        new_state = step_func(action)
        if new_state is None:
            raise Exception(f"Killing failed: step function returned no state for action {action_names[action]}")

        if attacking_boss and int(new_state.player_level) != current_level:
            # Defeating the boss ends the game, so the environment resets to the overworld right away
            log_func(
                f"[kill_mob] Final hit landed, the necromancer is defeated after {boss_hits + 1} hit(s) "
                f"in this fight and the game ended"
            )
            return new_state
        if float(new_state.player_health) <= 0:
            log_func("[kill_mob] The player died during the fight")
            raise Exception(f"Killing failed: the player died while hunting {target_name}")

        if float(new_state.player_health) < float(state.player_health):
            log_func(
                f"[kill_mob] Warning: health dropped from {float(state.player_health):.1f} "
                f"to {float(new_state.player_health):.1f}"
            )

        if attacking_boss:
            if boss_was_vulnerable and not boss_vulnerable(new_state):
                boss_hits += 1
                log_func(
                    f"[kill_mob] Hit the necromancer ({boss_hits} hit(s) in this fight), a new spawn wave starts"
                )
            else:
                log_func("[kill_mob] The attack on the necromancer did no damage")

        if weapon_used in ("arrow", "fireball", "iceball"):
            # The shot only happened if it used up an arrow / mana
            if weapon_used == "arrow":
                fired = int(new_state.inventory.arrows) < int(state.inventory.arrows)
                resource_change = f"arrows {int(state.inventory.arrows)} -> {int(new_state.inventory.arrows)}"
            else:
                fired = int(new_state.player_mana) < int(state.player_mana)
                resource_change = f"mana {int(state.player_mana)} -> {int(new_state.player_mana)}"
            if fired:
                log_func(f"[kill_mob] Fired a {weapon_used}, {resource_change}")
            else:
                failed_shots += 1
                ranged_cooldown = ranged_cooldown_steps
                log_func(
                    f"[kill_mob] The {weapon_used} was not fired ({resource_change}, too many projectiles "
                    f"in flight?), {failed_shots} failed shot(s); preferring melee for {ranged_cooldown_steps} steps"
                )
                # Nothing was launched, so it cannot be credited with a kill
                previous_projectile_cells = previous_projectile_cells[:-1]

        if expected_cell is not None and int(new_state.player_level) == current_level:
            new_position = (int(new_state.player_position[0]), int(new_state.player_position[1]))
            if new_position != expected_cell:
                log_func(
                    f"[kill_mob] Move to {expected_cell} did not succeed, still at {new_position}; replanning"
                )

        if mining_cell is not None and int(new_state.player_level) == current_level:
            if is_visible(new_state, mining_cell[0], mining_cell[1]):
                new_block = int(known_blocks(new_state)[mining_cell])
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
