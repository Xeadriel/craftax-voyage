# Description:
# Kills a mob of a specified type if found nearby.
# Uses appropriate weapon based on mob type and player equipment.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
    MobType,
)
from craftax.craftax.util.game_logic_utils import (
    is_in_mob,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def kill_mob(env_step_fn, state, mob_type: MobType, max_steps: int = 100):
    """
    Kills a mob of a specified type if found nearby.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        mob_type: Type of mob to kill (PASSIVE, MELEE, RANGED)
        max_steps: Maximum number of steps to kill
    
    Returns:
        True if mob was killed
    
    Raises:
        ValueError: If mob not found, no weapon available, or killing failed
    """
    import jax.numpy as jnp
    
    # Find a mob of the specified type
    mob_pos = find_mob(env_step_fn, state, mob_type, max_steps)
    
    if mob_pos is None:
        raise ValueError(f"No {mob_type.name} mob found in visible area")
    
    # Check if we have appropriate weapon
    weapon = get_weapon_for_mob(mob_type)
    
    if weapon is None:
        raise ValueError(f"No weapon available to kill {mob_type.name} mobs")
    
    # Move to mob
    move_to_mob(env_step_fn, state, mob_pos, max_steps)
    
    # Kill the mob
    success = kill_at_position(env_step_fn, state, mob_pos, weapon, max_steps)
    
    return success


def find_mob(env_step_fn, state, mob_type: MobType, max_steps: int = 50):
    """
    Finds a mob of the specified type in the visible area.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        mob_type: Type of mob to find
        max_steps: Maximum number of steps to search
    
    Returns:
        Position of mob or None
    """
    import jax.numpy as jnp
    
    # Check all visible positions for the mob type
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            candidate_pos = state.player_position + jnp.array([dx, dy])
            if in_bounds(state, candidate_pos):
                # Check mob map for this position
                if state.mob_map[state.player_level][candidate_pos[0], candidate_pos[1]]:
                    # Check mob type
                    for mob_class in [state.melee_mobs, state.passive_mobs, state.ranged_mobs]:
                        if mob_class.mask[state.player_level].sum() > 0:
                            for mob_idx in range(mob_class.mask.shape[1]):
                                if mob_class.mask[state.player_level, mob_idx]:
                                    mob_type_id = mob_class.type_id[state.player_level, mob_idx]
                                    mob_mob_type = get_mob_type_from_id(mob_type_id)
                                    if mob_mob_type == mob_type:
                                        return candidate_pos
    
    return None


def get_weapon_for_mob(mob_type: MobType) -> Action:
    """
    Returns the appropriate weapon action for a mob type.
    
    Args:
        mob_type: Type of mob
    
    Returns:
        Weapon action (SWORD, PICKAXE, BOW, etc.)
    """
    weapon_actions = {
        MobType.PASSIVE.value: Action.DO.value,  # Can eat passive mobs
        MobType.MELEE.value: Action.DO.value,   # Can melee attack
        MobType.RANGED.value: Action.SHOOT_ARROW.value,  # Should use bow
    }
    
    return weapon_actions.get(mob_type.value, Action.DO.value)


def move_to_mob(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Moves the player to the mob position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Target position [x, y]
        max_steps: Maximum number of steps to move
    
    Raises:
        ValueError: If target position is invalid or unreachable
    """
    import jax.numpy as jnp
    
    # Calculate direction to target
    current_pos = state.player_position
    direction = target_pos - current_pos
    
    # Check if target is in bounds
    if not in_bounds(state, target_pos):
        raise ValueError(f"Target position {target_pos} is out of bounds")
    
    # Check if target is in a solid block
    if is_in_solid_block(state, target_pos):
        raise ValueError(f"Target position {target_pos} is a solid block")
    
    # Check if target is in a mob
    if is_in_mob(state, target_pos):
        raise ValueError(f"Target position {target_pos} is occupied by a mob")
    
    # Move towards target
    for step in range(max_steps):
        # Find closest valid direction
        best_dir = None
        best_distance = float('inf')
        
        for action in [Action.UP.value, Action.DOWN.value, Action.LEFT.value, Action.RIGHT.value]:
            proposed_pos = current_pos + DIRECTIONS[action]
            
            if in_bounds(state, proposed_pos) and not is_in_solid_block(state, proposed_pos) and not is_in_mob(state, proposed_pos):
                distance = jnp.sum(jnp.abs(proposed_pos - target_pos))
                if distance < best_distance:
                    best_distance = distance
                    best_dir = action
        
        if best_dir is None:
            raise ValueError("Cannot move towards target - no valid path")
        
        # Execute move
        env_step_fn(state, best_dir)
        state = state.replace(
            player_position=current_pos + DIRECTIONS[best_dir],
            player_direction=best_dir
        )
        current_pos = state.player_position
    
    # Verify we reached the target
    if not in_bounds(state, target_pos):
        raise ValueError("Failed to reach target position")
    
    return True


def kill_at_position(env_step_fn, state, target_pos, weapon: Action, max_steps: int = 50):
    """
    Kills a mob at the specified position.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        target_pos: Position of mob [x, y]
        weapon: Weapon action to use
        max_steps: Maximum number of steps to kill
    
    Returns:
        True if mob was killed
    
    Raises:
        ValueError: If killing failed
    """
    import jax.numpy as jnp
    
    # Check if position is valid
    if not in_bounds(state, target_pos):
        raise ValueError(f"Position {target_pos} is out of bounds")
    
    # Check if position is in a solid block
    if is_in_solid_block(state, target_pos):
        raise ValueError(f"Position {target_pos} is a solid block")
    
    # Check if position is in a mob
    if not is_in_mob(state, target_pos):
        raise ValueError(f"Position {target_pos} is not occupied by a mob")
    
    # Execute killing action
    for step in range(max_steps):
        # Check if we're at the target position
        if state.player_position != target_pos:
            # Move to target
            move_to_mob(env_step_fn, state, target_pos, max_steps - step)
            break
        
        # Try to attack using DO action
        env_step_fn(state, Action.DO.value)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if mob was killed
        if not is_in_mob(state, target_pos):
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Killing action failed after multiple attempts")
    
    raise ValueError("Killing action failed")


def get_mob_type_from_id(mob_type_id: int) -> MobType:
    """
    Returns the mob type from the mob type ID.
    
    Args:
        mob_type_id: Mob type ID
    
    Returns:
        Mob type
    """
    # Map mob type IDs to mob types
    mob_id_to_type = {
        0: MobType.PASSIVE.value,  # Zombie, Cow, Bat, Snail
        1: MobType.MELEE.value,    # Gnome Warrior, Orc Soldier, Lizard, Knight, Troll, Pigman, Frost Troll
        2: MobType.RANGED.value,   # Skeleton, Gnome Archer, Orc Mage, Kobold, Archer, Deep Thing, Fire Elemental, Ice Elemental
    }
    
    return MobType(mob_id_to_type.get(mob_type_id, MobType.PASSIVE.value))
