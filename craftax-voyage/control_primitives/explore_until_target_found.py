# Description:
# Explores the environment until a specified target (block or entity) is found,
# or until a maximum number of steps is reached. Clears obstacles in the way
# by mining blocks or placing/removing water/lava. Handles ladders and checks
# player health, hunger, thirst, energy, and enemy proximity. Returns true if
# successful (target found) or false if max steps reached or error occurred.

def explore_until_target_found(state, log, step_func, target_block_type=None, target_mob_type=None, max_steps=100):
    """
    Explores the environment until a specified target is found or max_steps reached.
    
    Args:
        state: Current game state
        log: Logging function for tracking progress
        step_func: Step function that takes Action enum and returns action
        target_block_type: Optional BlockType to search for (e.g., BlockType.CHEST)
        target_mob_type: Optional MobType to search for (e.g., MobType.MELEE)
        max_steps: Maximum steps to search (default 100)
    
    Returns:
        True if target found or search completed successfully
        False if max steps reached or error occurred
    """
    # Check if we have required items before proceeding
    if state.player_health <= 5:
        log("Error: Player health is too low ({}). Cannot explore.".format(state.player_health))
        return False
    
    if state.player_hunger <= 3:
        log("Error: Player hunger is too low ({}). Cannot explore.".format(state.player_hunger))
        return False
    
    if state.player_thirst <= 3:
        log("Error: Player thirst is too low ({}). Cannot explore.".format(state.player_thirst))
        return False
    
    if state.player_energy <= 3:
        log("Error: Player energy is too low ({}). Cannot explore.".format(state.player_energy))
        return False
    
    # Check for nearby enemies (3 blocks radius)
    enemy_distance = check_enemy_proximity(state)
    if enemy_distance is not None and enemy_distance < 3:
        log("Error: Enemy is too close ({} blocks). Cannot explore.".format(enemy_distance))
        return False
    
    # Check if we've reached max steps
    if max_steps <= 0:
        log("Error: Max steps (0) reached immediately.")
        return False
    
    # Get current position and direction
    current_position = state.player_position
    current_direction = state.player_direction
    
    # Calculate target position if specified
    target_position = None
    if target_block_type is not None:
        # Search for target block in all directions
        target_position = find_target_block(state, target_block_type, current_position)
    
    # Search for target entity if specified
    if target_mob_type is not None:
        target_position = find_target_mob(state, target_mob_type, current_position)
    
    # If no target specified, just explore randomly
    if target_position is None:
        target_position = None
    
    # Track steps and success
    steps_taken = 0
    found_target = False
    
    while steps_taken < max_steps:
        # Check for death
        if state.player_health <= 0:
            log("Error: Player died during exploration.")
            return False
        
        # Check for low health
        if state.player_health <= 5:
            log("Error: Player health too low ({}). Cannot explore.".format(state.player_health))
            return False
        
        # Check for low hunger/thirst/energy
        if state.player_hunger <= 3:
            log("Error: Player hunger too low ({}). Cannot explore.".format(state.player_hunger))
            return False
        
        if state.player_thirst <= 3:
            log("Error: Player thirst too low ({}). Cannot explore.".format(state.player_thirst))
            return False
        
        if state.player_energy <= 3:
            log("Error: Player energy too low ({}). Cannot explore.".format(state.player_energy))
            return False
        
        # Check for nearby enemies
        enemy_distance = check_enemy_proximity(state)
        if enemy_distance is not None and enemy_distance < 3:
            log("Error: Enemy too close ({} blocks). Cannot explore.".format(enemy_distance))
            return False
        
        # Check if target found
        if target_position is not None:
            if is_position_reached(state, target_position):
                log("Target found at position {}".format(target_position))
                found_target = True
                break
        
        # Determine action
        action = determine_action(state, target_position, current_direction, steps_taken)
        
        # Execute action
        action_result = step_func(action)
        
        if action_result is None:
            log("Error: Step function returned None for action {}".format(action))
            return False
        
        # Update state based on action result
        if action_result == Action.NOOP.value:
            # No change, continue
            pass
        elif action_result == Action.SLEEP.value or action_result == Action.REST.value:
            # Sleeping/resting, continue
            pass
        elif action_result == Action.DESCEND.value or action_result == Action.ASCEND.value:
            # Moving on ladder
            pass
        else:
            # Movement action
            pass
        
        # Check if target found after action
        if target_position is not None:
            if is_position_reached(state, target_position):
                log("Target found at position {}".format(target_position))
                found_target = True
                break
        
        # Check if max steps reached
        steps_taken += 1
        
        # Check for death
        if state.player_health <= 0:
            log("Error: Player died during exploration.")
            return False
        
        # Check for low health
        if state.player_health <= 5:
            log("Error: Player health too low ({}). Cannot explore.".format(state.player_health))
            return False
        
        # Check for low hunger/thirst/energy
        if state.player_hunger <= 3:
            log("Error: Player hunger too low ({}). Cannot explore.".format(state.player_hunger))
            return False
        
        if state.player_thirst <= 3:
            log("Error: Player thirst too low ({}). Cannot explore.".format(state.player_thirst))
            return False
        
        if state.player_energy <= 3:
            log("Error: Player energy too low ({}). Cannot explore.".format(state.player_energy))
            return False
        
        # Check for nearby enemies
        enemy_distance = check_enemy_proximity(state)
        if enemy_distance is not None and enemy_distance < 3:
            log("Error: Enemy too close ({} blocks). Cannot explore.".format(enemy_distance))
            return False
        
        # Check if max steps reached
        if steps_taken >= max_steps:
            log("Error: Max steps ({} {}) reached before finding target.".format(max_steps, "steps" if max_steps > 1 else "step"))
            return False
    
    # Return success if target found
    if found_target:
        log("Successfully found target after {} steps.".format(steps_taken))
        return True
    
    # Return failure if max steps reached
    log("Failed to find target after {} steps.".format(steps_taken))
    return False


def check_enemy_proximity(state):
    """
    Check if any enemy is within 3 blocks of the player.
    
    Args:
        state: Current game state
    
    Returns:
        Distance to nearest enemy (int), or None if no enemies
    """
    player_position = state.player_position
    
    # Check melee mobs
    for mob_index in range(len(state.melee_mobs.mask)):
        if state.melee_mobs.mask[state.player_level, mob_index]:
            mob_position = state.melee_mobs.position[state.player_level, mob_index]
            distance = calculate_distance(player_position, mob_position)
            if distance < 3:
                return distance
    
    # Check passive mobs
    for mob_index in range(len(state.passive_mobs.mask)):
        if state.passive_mobs.mask[state.player_level, mob_index]:
            mob_position = state.passive_mobs.position[state.player_level, mob_index]
            distance = calculate_distance(player_position, mob_position)
            if distance < 3:
                return distance
    
    # Check ranged mobs
    for mob_index in range(len(state.ranged_mobs.mask)):
        if state.ranged_mobs.mask[state.player_level, mob_index]:
            mob_position = state.ranged_mobs.position[state.player_level, mob_index]
            distance = calculate_distance(player_position, mob_position)
            if distance < 3:
                return distance
    
    return None


def calculate_distance(pos1, pos2):
    """
    Calculate Manhattan distance between two positions.
    
    Args:
        pos1: First position (tuple or array)
        pos2: Second position (tuple or array)
    
    Returns:
        Manhattan distance (int)
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def find_target_block(state, target_block_type, current_position):
    """
    Find a target block type in the vicinity of current position.
    
    Args:
        state: Current game state
        target_block_type: BlockType to search for
        current_position: Current player position
    
    Returns:
        Position of target block (tuple), or None if not found
    """
    # Search in all directions
    directions = CLOSE_BLOCKS
    
    for direction in directions:
        target_position = current_position + direction
        if is_in_bounds(state, target_position):
            block_type = state.map[state.player_level, target_position[0], target_position[1]]
            if block_type == target_block_type.value:
                return target_position
    
    return None


def find_target_mob(state, target_mob_type, current_position):
    """
    Find a target mob type in the vicinity of current position.
    
    Args:
        state: Current game state
        target_mob_type: MobType to search for
        current_position: Current player position
    
    Returns:
        Position of target mob (tuple), or None if not found
    """
    # Search in all directions
    directions = CLOSE_BLOCKS
    
    for direction in directions:
        target_position = current_position + direction
        if is_in_bounds(state, target_position):
            if is_in_mob(state, target_position):
                # Check mob type
                if is_mob_at_position(state, target_position, target_mob_type):
                    return target_position
    
    return None


def is_in_bounds(state, position):
    """
    Check if position is within map bounds.
    
    Args:
        state: Current game state
        position: Position to check
    
    Returns:
        True if in bounds, False otherwise
    """
    map_size = state.map[state.player_level].shape
    return 0 <= position[0] < map_size[0] and 0 <= position[1] < map_size[1]


def is_in_mob(state, position):
    """
    Check if position contains a mob.
    
    Args:
        state: Current game state
        position: Position to check
    
    Returns:
        True if mob present, False otherwise
    """
    return state.mob_map[state.player_level, position[0], position[1]]


def is_mob_at_position(state, position, mob_type):
    """
    Check if mob of specific type is at position.
    
    Args:
        state: Current game state
        position: Position to check
        mob_type: MobType to check for
    
    Returns:
        True if mob of type present, False otherwise
    """
    # Check all mob types
    for mob_class in [state.melee_mobs, state.passive_mobs, state.ranged_mobs]:
        for mob_index in range(len(mob_class.mask)):
            if mob_class.mask[state.player_level, mob_index]:
                if mob_class.position[state.player_level, mob_index] == position:
                    if mob_class.type_id[state.player_level, mob_index] == mob_type.value:
                        return True
    
    return False


def is_position_reached(state, target_position):
    """
    Check if player has reached target position.
    
    Args:
        state: Current game state
        target_position: Target position to check
    
    Returns:
        True if player at target, False otherwise
    """
    return state.player_position == target_position


def determine_action(state, target_position, current_direction, steps_taken):
    """
    Determine the next action based on state and target.
    
    Args:
        state: Current game state
        target_position: Target position (or None)
        current_direction: Current player direction
        steps_taken: Number of steps taken
    
    Returns:
        Action enum value
    """
    # If target found, return NOOP
    if target_position is not None and is_position_reached(state, target_position):
        return Action.NOOP.value
    
    # If target position specified, move towards it
    if target_position is not None:
        # Calculate direction to target
        direction_to_target = get_direction_to_position(state.player_position, target_position)
        
        # Check if we can move in that direction
        if direction_to_target is not None:
            # Check if target is in front of us
            if direction_to_target == current_direction:
                return Action.DO.value  # Interact/mine
            else:
                # Move towards target
                return move_towards_target(state, direction_to_target)
    
    # No target, move randomly
    return move_randomly(state)


def get_direction_to_position(current_position, target_position):
    """
    Get direction to move towards target position.
    
    Args:
        current_position: Current position
        target_position: Target position
    
    Returns:
        Direction to move (int), or None if not possible
    """
    if current_position == target_position:
        return None
    
    # Calculate direction
    dx = target_position[0] - current_position[0]
    dy = target_position[1] - current_position[1]
    
    # Determine direction
    if abs(dx) > abs(dy):
        if dx > 0:
            return Action.RIGHT.value
        else:
            return Action.LEFT.value
    else:
        if dy > 0:
            return Action.UP.value
        else:
            return Action.DOWN.value


def move_towards_target(state, direction):
    """
    Move towards target position.
    
    Args:
        state: Current game state
        direction: Direction to move
    
    Returns:
        Action enum value
    """
    # Check if we can move in this direction
    proposed_position = state.player_position + DIRECTIONS[direction]
    
    if is_position_in_bounds_not_in_mob_not_colliding(state, proposed_position, COLLISION_LAND_CREATURE):
        return direction
    else:
        # Try to clear path
        return try_clear_path(state, proposed_position, direction)


def try_clear_path(state, proposed_position, direction):
    """
    Try to clear path to target position.
    
    Args:
        state: Current game state
        proposed_position: Position to move to
        direction: Direction to move
    
    Returns:
        Action enum value
    """
    # Check if we need to place/remove water/lava
    block_type = state.map[state.player_level, proposed_position[0], proposed_position[1]]
    
    if block_type == BlockType.WATER.value or block_type == BlockType.LAVA.value:
        # Place stone to cover water/lava
        return Action.PLACE_STONE.value
    elif block_type == BlockType.TREE.value or block_type == BlockType.STONE.value:
        # Mine the block
        return Action.DO.value
    else:
        # Move in direction
        return direction


def move_randomly(state):
    """
    Move in a random direction.
    
    Args:
        state: Current game state
    
    Returns:
        Action enum value
    """
    import random
    
    # Get available directions
    directions = [Action.LEFT.value, Action.RIGHT.value, Action.UP.value, Action.DOWN.value]
    
    # Filter out directions that would move off map
    valid_directions = []
    for direction in directions:
        proposed_position = state.player_position + DIRECTIONS[direction]
        if is_in_bounds(state, proposed_position):
            valid_directions.append(direction)
    
    # If no valid directions, return NOOP
    if not valid_directions:
        return Action.NOOP.value
    
    # Choose random direction
    return random.choice(valid_directions)
