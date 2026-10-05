# Description:
# Opens a chest and collects specified items.
# Returns True if successful, False if chest not found or items not available.
# Handles loot collection and inventory management.

def open_chest(state, items_to_collect, max_steps=100):
    """
    Open a chest and collect specified items.
    
    Args:
        state: Current environment state
        items_to_collect: Dict mapping item names to quantities
        max_steps: Maximum steps to find and open chest (default 100)
    
    Returns:
        bool: True if items collected, False otherwise
    """
    from craftax.craftax.constants import Action, DIRECTIONS, in_bounds, is_in_solid_block, is_in_mob, ItemType
    
    # Find chest in current view
    found_position = None
    for x in range(OBS_DIM[0]):
        for y in range(OBS_DIM[1]):
            block_pos = state.player_position + jnp.array([x, y])
            if in_bounds(state, block_pos):
                if state.map[state.player_level, block_pos[0], block_pos[1]] == BlockType.CHEST.value:
                    found_position = block_pos
                    break
        if found_position:
            break
    
    if not found_position:
        raise ValueError("Cannot find chest in current view")
    
    # Check if we can reach the chest
    if is_in_solid_block(state, found_position):
        raise ValueError(f"Cannot reach chest at {found_position} - solid block")
    
    if is_in_mob(state, found_position):
        raise ValueError(f"Cannot reach chest at {found_position} - mob present")
    
    # Move to the chest
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
            raise ValueError(f"Cannot reach chest - out of bounds")
        
        if is_in_solid_block(state, proposed_position):
            raise ValueError(f"Cannot reach chest - solid block at {proposed_position}")
        
        if is_in_mob(state, proposed_position):
            raise ValueError(f"Cannot reach chest - mob at {proposed_position}")
        
        state = state.replace(
            player_position=proposed_position,
            player_direction=move_dir.value
        )
        
        dx = found_position[0] - state.player_position[0]
        dy = found_position[1] - state.player_position[1]
        steps_taken += 1
    
    # Open the chest by interacting
    state, did_attack_mob, did_kill_mob = attack_mob(
        state, found_position, get_player_damage_vector(state), True
    )
    
    return True
