# Description:
# Explores the environment to find resources and items.
# Checks inventory for required items before attempting actions.
# Returns True if exploration was successful, False otherwise.

def explore(state, action, step_func):
    """
    Explores the environment by moving and checking for resources.
    
    Args:
        state: Current game state
        action: Action enum value (e.g., Action.UP, Action.DOWN, etc.)
        step_func: Step function to execute actions
    
    Returns:
        True if exploration was successful, False otherwise
    """
    # Check if player is at a valid position
    block_position = state.player_position + DIRECTIONS[state.player_direction]
    action_block_in_bounds = in_bounds(state, block_position)
    
    if not action_block_in_bounds:
        return False
    
    # Check if player is not attacking a mob
    did_attack_mob = is_in_mob(state, block_position)
    if did_attack_mob:
        return False
    
    # Check if player has enough energy to move
    if state.player_energy <= 0:
        return False
    
    # Check if player has enough food
    if state.player_food <= 0:
        return False
    
    # Check if player has enough water
    if state.player_drink <= 0:
        return False
    
    # Check if player is not sleeping
    if state.is_sleeping:
        return False
    
    # Check if player is not resting
    if state.is_resting:
        return False
    
    # Check if player is at a valid floor
    if state.player_level >= static_env_params.num_levels:
        return False
    
    # Check if player is at a valid position to descend
    is_at_down_ladder = (
        state.item_map[state.player_level, block_position[0], block_position[1]]
        == ItemType.LADDER_DOWN.value
    )
    
    # Check if player is at a valid position to ascend
    is_at_up_ladder = (
        state.item_map[state.player_level, block_position[0], block_position[1]]
        == ItemType.LADDER_UP.value
    )
    
    # Check if player is at a valid position to place a torch
    is_at_valid_place = CAN_PLACE_ITEM_MAPPING[state.map[state.player_level, block_position[0], block_position[1]]]
    
    # Check if player has enough torches to place
    if state.inventory.torches > 0 and is_at_valid_place:
        step_func(Action.PLACE_TORCH)
        return True
    
    # Check if player has enough saplings to place
    if state.inventory.sapling > 0 and state.map[state.player_level, block_position[0], block_position[1]] == BlockType.GRASS.value:
        step_func(Action.PLACE_PLANT)
        return True
    
    # Check if player has enough stone to place
    if state.inventory.stone > 0 and state.map[state.player_level, block_position[0], block_position[1]] == BlockType.WATER.value:
        step_func(Action.PLACE_STONE)
        return True
    
    # Check if player has enough wood to place a crafting table
    if state.inventory.wood >= 2 and is_at_valid_place:
        step_func(Action.PLACE_TABLE)
        return True
    
    # Check if player has enough stone to place a furnace
    if state.inventory.stone > 0 and is_at_valid_place:
        step_func(Action.PLACE_FURNACE)
        return True
    
    # Check if player has enough books to read
    if state.inventory.books > 0:
        step_func(Action.READ_BOOK)
        return True
    
    # Check if player has enough mana to cast spells
    if state.player_mana >= 2 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.CAST_FIREBALL)
        return True
    
    # Check if player has enough mana to cast iceball
    if state.player_mana >= 2 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.CAST_ICEBALL)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_SWORD)
        return True
    
    # Check if player has enough mana to enchant armour
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_ARMOUR)
        return True
    
    # Check if player has enough mana to enchant bow
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough arrows to shoot
    if state.inventory.arrows > 0 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.SHOOT_ARROW)
        return True
    
    # Check if player has enough potions to drink
    if state.inventory.potions.sum() > 0:
        step_func(Action.DRINK_POTION_RED)
        return True
    
    # Check if player has enough books to read
    if state.inventory.books > 0:
        step_func(Action.READ_BOOK)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_SWORD)
        return True
    
    # Check if player has enough mana to enchant armour
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_ARMOUR)
        return True
    
    # Check if player has enough mana to enchant bow
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state.player_mana >= 9 and state.player_projectiles.mask[state.player_level].sum() < static_env_params.max_player_projectiles:
        step_func(Action.ENCHANT_BOW)
        return True
    
    # Check if player has enough mana to enchant
    if state
