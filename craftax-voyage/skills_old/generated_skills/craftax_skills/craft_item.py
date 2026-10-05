# Description:
# Crafts an item at a crafting table if the player has the required materials.
# Checks for crafting table location and required inventory.
# Returns True on success, raises ValueError on failure.

from craftax.craftax.constants import (
    Action,
    BlockType,
)
from craftax.craftax.util.game_logic_utils import (
    is_near_block,
    is_in_solid_block,
    is_position_in_bounds_not_in_mob_not_colliding,
    in_bounds,
)


def craft_item(env_step_fn, state, item_name: str, count: int = 1, max_steps: int = 100):
    """
    Crafts an item at a crafting table if the player has the required materials.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        item_name: Name of item to craft (e.g., "wood_pickaxe", "stone_sword")
        count: Number of items to craft
        max_steps: Maximum number of steps to craft
    
    Returns:
        True if crafting was successful
    
    Raises:
        ValueError: If item not found, no crafting table, or crafting failed
    """
    import jax.numpy as jnp
    
    # Check if item name is valid
    if not item_name:
        raise ValueError("Item name cannot be empty")
    
    # Check if we have the required materials
    required_materials = get_required_materials(item_name)
    
    if not required_materials:
        raise ValueError(f"Cannot determine required materials for {item_name}")
    
    # Check inventory for materials
    current_inventory = state.inventory
    
    for material, amount in required_materials.items():
        if current_inventory[material] < amount:
            raise ValueError(
                f"Need {amount} {material.name} to craft {item_name}, "
                f"have {current_inventory[material]}"
            )
    
    # Find crafting table
    crafting_table_pos = find_crafting_table(env_step_fn, state, max_steps)
    
    if crafting_table_pos is None:
        raise ValueError("No crafting table found in visible area")
    
    # Move to crafting table
    move_to_crafting_table(env_step_fn, state, crafting_table_pos, max_steps)
    
    # Craft the item
    success = craft_at_table(env_step_fn, state, crafting_table_pos, item_name, count, max_steps)
    
    return success


def get_required_materials(item_name: str) -> dict:
    """
    Returns the required materials for crafting an item.
    
    Args:
        item_name: Name of item to craft
    
    Returns:
        Dictionary of material -> amount needed
    """
    # Define crafting recipes
    recipes = {
        "wood_pickaxe": {"wood": 1},
        "stone_pickaxe": {"wood": 1, "stone": 1},
        "iron_pickaxe": {"wood": 1, "stone": 1, "iron": 1, "coal": 1},
        "diamond_pickaxe": {"wood": 1, "diamond": 3},
        "wood_sword": {"wood": 1},
        "stone_sword": {"wood": 1, "stone": 1},
        "iron_sword": {"wood": 1, "iron": 1, "stone": 1, "coal": 1},
        "diamond_sword": {"wood": 1, "diamond": 2},
        "iron_armour": {"iron": 3, "coal": 3},
        "diamond_armour": {"diamond": 3},
        "arrow": {"wood": 1, "stone": 1},
        "torch": {"wood": 1, "coal": 1},
    }
    
    return recipes.get(item_name, {})


def find_crafting_table(env_step_fn, state, max_steps: int = 50):
    """
    Finds a crafting table in the visible area.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        max_steps: Maximum number of steps to search
    
    Returns:
        Position of crafting table or None
    """
    import jax.numpy as jnp
    
    # Check if crafting table is nearby
    if is_near_block(state, BlockType.CRAFTING_TABLE.value):
        # Find exact position
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                candidate_pos = state.player_position + jnp.array([dx, dy])
                if in_bounds(state, candidate_pos):
                    block_at_pos = state.map[state.player_level][candidate_pos[0], candidate_pos[1]]
                    if block_at_pos == BlockType.CRAFTING_TABLE.value:
                        return candidate_pos
    
    # Search for crafting table
    for step in range(max_steps):
        # Check all visible positions
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                candidate_pos = state.player_position + jnp.array([dx, dy])
                if in_bounds(state, candidate_pos):
                    block_at_pos = state.map[state.player_level][candidate_pos[0], candidate_pos[1]]
                    if block_at_pos == BlockType.CRAFTING_TABLE.value:
                        return candidate_pos
    
    return None


def move_to_crafting_table(env_step_fn, state, target_pos, max_steps: int = 50):
    """
    Moves the player to the crafting table position.
    
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


def craft_at_table(env_step_fn, state, table_pos, item_name: str, count: int = 1, max_steps: int = 100):
    """
    Crafts an item at the crafting table.
    
    Args:
        env_step_fn: Function to call for environment step
        state: Current environment state
        table_pos: Position of crafting table
        item_name: Name of item to craft
        count: Number of items to craft
        max_steps: Maximum number of steps to craft
    
    Returns:
        True if crafting was successful
    
    Raises:
        ValueError: If crafting failed
    """
    import jax.numpy as jnp
    
    # Check if we're at the crafting table
    if state.player_position != table_pos:
        # Move to crafting table
        move_to_crafting_table(env_step_fn, state, table_pos, max_steps)
        return True
    
    # Craft the item
    for step in range(max_steps):
        # Get crafting action
        action = get_crafting_action(item_name)
        
        if action == Action.NOOP.value:
            raise ValueError(f"No crafting action for {item_name}")
        
        env_step_fn(state, action)
        state = state.replace(timestep=state.timestep + 1)
        
        # Check if item was crafted
        current_inventory = state.inventory
        
        # Check if we have the item
        if current_inventory[item_name] > 0:
            return True
        
        # Check if we're stuck
        if step >= max_steps - 5:
            raise ValueError("Crafting action failed after multiple attempts")
    
    raise ValueError("Crafting action failed")


def get_crafting_action(item_name: str) -> Action:
    """
    Returns the crafting action for an item.
    
    Args:
        item_name: Name of item to craft
    
    Returns:
        Crafting action
    """
    crafting_actions = {
        "wood_pickaxe": Action.MAKE_WOOD_PICKAXE.value,
        "stone_pickaxe": Action.MAKE_STONE_PICKAXE.value,
        "iron_pickaxe": Action.MAKE_IRON_PICKAXE.value,
        "diamond_pickaxe": Action.MAKE_DIAMOND_PICKAXE.value,
        "wood_sword": Action.MAKE_WOOD_SWORD.value,
        "stone_sword": Action.MAKE_STONE_SWORD.value,
        "iron_sword": Action.MAKE_IRON_SWORD.value,
        "diamond_sword": Action.MAKE_DIAMOND_SWORD.value,
        "iron_armour": Action.MAKE_IRON_ARMOUR.value,
        "diamond_armour": Action.MAKE_DIAMOND_ARMOUR.value,
        "arrow": Action.MAKE_ARROW.value,
        "torch": Action.MAKE_TORCH.value,
    }
    
    return crafting_actions.get(item_name, Action.NOOP.value)
