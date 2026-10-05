# Description:
# Kills a mob of a specific type that is visible in the current view.
# Returns True if mob killed, False if mob not found or unreachable.
# Handles melee and ranged attacks based on available weapons.

def kill_mob(state, mob_type, max_steps=100):
    """
    Kill a mob of the specified type.
    
    Args:
        state: Current environment state
        mob_type: MobType enum value (0=passive, 1=melee, 2=ranged)
        max_steps: Maximum steps to search and kill (default 100)
    
    Returns:
        bool: True if mob killed, False otherwise
    """
    from craftax.craftax.constants import Action, DIRECTIONS, in_bounds, is_in_solid_block, is_in_mob
    from craftax.craftax.game_logic import get_player_damage_vector
    
    # Search for the mob in the current view
    found_position = None
    found_mob_index = -1
    
    if mob_type == 0:  # Passive
        for i in range(state.passive_mobs.mask.shape[1]):
            if state.passive_mobs.mask[state.player_level, i]:
                mob_pos = state.passive_mobs.position[state.player_level, i]
                if in_bounds(state, mob_pos):
                    found_position = mob_pos
                    found_mob_index = i
                    break
    elif mob_type == 1:  # Melee
        for i in range(state.melee_mobs.mask.shape[1]):
            if state.melee_mobs.mask[state.player_level, i]:
                mob_pos = state.melee_mobs.position[state.player_level, i]
                if in_bounds(state, mob_pos):
                    found_position = mob_pos
                    found_mob_index = i
                    break
    elif mob_type == 2:  # Ranged
        for i in range(state.ranged_mobs.mask.shape[1]):
            if state.ranged_mobs.mask[state.player_level, i]:
                mob_pos = state.ranged_mobs.position[state.player_level, i]
                if in_bounds(state, mob_pos):
                    found_position = mob_pos
                    found_mob_index = i
                    break
    
    if not found_position:
        raise ValueError(f"Cannot find {MobType(mob_type).name} in current view")
    
    # Check if we can reach the mob
    if is_in_solid_block(state, found_position):
        raise ValueError(f"Cannot kill {MobType(mob_type).name} at {found_position} - solid block")
    
    if is_in_mob(state, found_position):
        raise ValueError(f"Cannot kill {MobType(mob_type).name} at {found_position} - mob present")
    
    # Move to the mob
    dx = found_position[0] - state.player_position[0]
    dy = found_position[1] - state.player_position[1]
    
    steps_taken = 0
    while steps_taken < max_steps:
        if abs(dx) <= 1 and abs(dy) <= 1:
            if dx == 1:
                move_dir = Action.RIGHT
            elif dx == -1:
                move_dir = Action.LEFT
            elif dy == 1:
                move_dir = Action.DOWN
            elif dy == -1:
                move_dir = Action.UP
            
            state = state.replace(
                player_position=state.player_position + DIRECTIONS[move_dir.value],
                player_direction=move_dir.value
            )
            break
        
        if abs(dx) >= abs(dy):
            if dx > 0:
                move_dir = Action.RIGHT
            else:
                move_dir = Action.LEFT
        else:
            if dy > 0:
                move_dir = Action.DOWN
            else:
                move_dir = Action.UP
        
        proposed_position = state.player_position + DIRECTIONS[move_dir.value]
        
        if not in_bounds(state, proposed_position):
            raise ValueError(f"Cannot reach {found_position} - out of bounds")
        
        if is_in_solid_block(state, proposed_position):
            raise ValueError(f"Cannot reach {found_position} - solid block at {proposed_position}")
        
        if is_in_mob(state, proposed_position):
            raise ValueError(f"Cannot reach {found_position} - mob at {proposed_position}")
        
        state = state.replace(
            player_position=proposed_position,
            player_direction=move_dir.value
        )
        
        dx = found_position[0] - state.player_position[0]
        dy = found_position[1] - state.player_position[1]
        steps_taken += 1
    
    # Attack the mob
    state, did_attack_mob, did_kill_mob = attack_mob(
        state, found_position, get_player_damage_vector(state), True
    )
    
    return True
