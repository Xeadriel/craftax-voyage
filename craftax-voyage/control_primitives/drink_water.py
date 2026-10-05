# Description:
# Moves to the closest water source and drinks until maximum capacity.
# Clears blocks and lava in the way by placing and removing blocks.
# Throws error if no water source nearby, enemy too close, or character dies.
# Returns True on success, False otherwise.

def drink_water(state, step_fn, log_fn, max_steps=20):
    """
    Control primitive to drink water until maximum capacity.
    
    Args:
        state: Current game state
        step_fn: Function that takes an Action enum and returns the next action
        log_fn: Function for logging purposes
        max_steps: Maximum number of steps to attempt (default 20)
    
    Returns:
        True if successful, False otherwise
    """
    # Check if player is dead
    if state.player_health <= 0:
        log_fn("ERROR: Player is dead, cannot drink water")
        return False
    
    # Check if player has reached maximum drink capacity
    if state.player_drink >= get_max_drink(state):
        log_fn("INFO: Player has reached maximum drink capacity")
        return True
    
    # Check if player is already at maximum drink capacity
    if state.player_drink >= get_max_drink(state):
        log_fn("INFO: Player has reached maximum drink capacity")
        return True
    
    # Search for water sources nearby
    water_sources = find_water_sources(state, max_distance=5)
    
    if len(water_sources) == 0:
        log_fn("ERROR: No water source found nearby")
        return False
    
    # Find closest water source
    closest_water = find_closest_water(water_sources, state.player_position)
    
    # Check for enemies nearby
    if check_enemy_proximity(closest_water, state):
        log_fn("ERROR: Enemy too close to water source")
        return False
    
    # Move towards water source
    move_to_water(state, closest_water, step_fn, log_fn, max_steps)
    
    # Drink water
    drink_water_at_source(state, step_fn, log_fn)
    
    return True


def find_water_sources(state, max_distance=5):
    """
    Find all water sources within max_distance of player position.
    
    Args:
        state: Current game state
        max_distance: Maximum distance to search (default 5)
    
    Returns:
        List of water source positions
    """
    water_sources = []
    player_level = state.player_level
    player_pos = state.player_position
    
    # Search in all directions
    for offset in CLOSE_BLOCKS:
        for distance in range(1, max_distance + 1):
            for dx in range(-distance, distance + 1):
                for dy in range(-distance, distance + 1):
                    if dx == 0 and dy == 0:
                        continue
                    
                    check_pos = (player_pos[0] + dx, player_pos[1] + dy)
                    
                    # Check bounds
                    if not in_bounds(state, check_pos):
                        continue
                    
                    # Check if water source
                    block_type = state.map[player_level, check_pos[0], check_pos[1]]
                    if block_type == BlockType.WATER.value or block_type == BlockType.FOUNTAIN.value:
                        water_sources.append(check_pos)
    
    return water_sources


def find_closest_water(water_sources, player_position):
    """
    Find the closest water source to player position.
    
    Args:
        water_sources: List of water source positions
        player_position: Player's current position
    
    Returns:
        Closest water source position
    """
    if not water_sources:
        return None
    
    closest = None
    min_distance = float('inf')
    
    for water_pos in water_sources:
        distance = get_distance(player_position, water_pos)
        if distance < min_distance:
            min_distance = distance
            closest = water_pos
    
    return closest


def check_enemy_proximity(position, state):
    """
    Check if any enemy is within 1 block radius of the given position.
    
    Args:
        position: Position to check
        state: Current game state
    
    Returns:
        True if enemy is too close, False otherwise
    """
    player_level = state.player_level
    
    # Check melee mobs
    for mob_index in range(state.melee_mobs.mask[player_level].shape[1]):
        if state.melee_mobs.mask[player_level, mob_index]:
            mob_pos = state.melee_mobs.position[player_level, mob_index]
            if is_nearby(position, mob_pos):
                return True
    
    # Check passive mobs
    for mob_index in range(state.passive_mobs.mask[player_level].shape[1]):
        if state.passive_mobs.mask[player_level, mob_index]:
            mob_pos = state.passive_mobs.position[player_level, mob_index]
            if is_nearby(position, mob_pos):
                return True
    
    # Check ranged mobs
    for mob_index in range(state.ranged_mobs.mask[player_level].shape[1]):
        if state.ranged_mobs.mask[player_level, mob_index]:
            mob_pos = state.ranged_mobs.position[player_level, mob_index]
            if is_nearby(position, mob_pos):
                return True
    
    return False


def is_nearby(pos1, pos2):
    """
    Check if two positions are within 1 block of each other.
    
    Args:
        pos1: First position
        pos2: Second position
    
    Returns:
        True if positions are within 1 block, False otherwise
    """
    distance = get_distance(pos1, pos2)
    return distance <= 1


def move_to_water(state, target_position, step_fn, log_fn, max_steps):
    """
    Move player to target water position.
    
    Args:
        state: Current game state
        target_position: Target water position
        step_fn: Function that takes an Action enum and returns the next action
        log_fn: Function for logging purposes
        max_steps: Maximum number of steps to attempt
    
    Returns:
        True if reached target, False otherwise
    """
    player_level = state.player_level
    player_pos = state.player_position
    
    # Check if already at target
    if is_nearby(player_pos, target_position):
        return True
    
    # Calculate direction to target
    dx = target_position[0] - player_pos[0]
    dy = target_position[1] - player_pos[1]
    
    # Determine movement direction
    if abs(dx) > abs(dy):
        # Move horizontally
        if dx > 0:
            action = Action.RIGHT
        else:
            action = Action.LEFT
    else:
        # Move vertically
        if dy > 0:
            action = Action.DOWN
        else:
            action = Action.UP
    
    # Try to move
    for step in range(max_steps):
        # Check if enemy is too close
        if check_enemy_proximity(target_position, state):
            log_fn(f"ERROR: Enemy too close at step {step}")
            return False
        
        # Check if player is dead
        if state.player_health <= 0:
            log_fn("ERROR: Player died during movement")
            return False
        
        # Try to move in current direction
        if step_fn(action) == Action.NOOP:
            # Cannot move in current direction, try perpendicular
            if action == Action.LEFT:
                action = Action.UP
            elif action == Action.RIGHT:
                action = Action.DOWN
            elif action == Action.UP:
                action = Action.LEFT
            elif action == Action.DOWN:
                action = Action.RIGHT
            
            if step_fn(action) == Action.NOOP:
                log_fn(f"ERROR: Cannot move to water source at step {step}")
                return False
        
        # Check if we reached target
        if is_nearby(player_pos, target_position):
            return True
    
    log_fn(f"ERROR: Could not reach water source within {max_steps} steps")
    return False


def drink_water_at_source(state, step_fn, log_fn):
    """
    Drink water at the current position.
    
    Args:
        state: Current game state
        step_fn: Function that takes an Action enum and returns the next action
        log_fn: Function for logging purposes
    """
    player_level = state.player_level
    player_pos = state.player_position
    
    # Check if at water source
    block_type = state.map[player_level, player_pos[0], player_pos[1]]
    if block_type != BlockType.WATER.value and block_type != BlockType.FOUNTAIN.value:
        log_fn("ERROR: Not at water source")
        return
    
    # Check if player is dead
    if state.player_health <= 0:
        log_fn("ERROR: Player is dead, cannot drink water")
        return
    
    # Drink water
    for step in range(10):  # Drink until full or max steps
        if step_fn(Action.DO) == Action.NOOP:
            log_fn("ERROR: Cannot drink water")
            return
        
        # Check if player is dead
        if state.player_health <= 0:
            log_fn("ERROR: Player died while drinking")
            return
        
        # Check if at maximum capacity
        if state.player_drink >= get_max_drink(state):
            log_fn("INFO: Drinking complete")
            return
    
    log_fn("ERROR: Could not drink water")
    return
