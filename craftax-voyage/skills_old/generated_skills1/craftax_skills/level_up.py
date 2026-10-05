# Skill: level_up
# Purpose: Levels up a player attribute using XP
# Required inputs: attribute_type (string: 'dexterity', 'strength', 'intelligence')
# Preconditions:
#   - Player must have XP >= 1
#   - Player must have attribute < max attribute
# Expected effects:
#   - XP is consumed
#   - Attribute is increased by 1
#   - Achievement may be triggered for leveling up
# Failure conditions:
#   - No XP available
#   - Attribute is at maximum level
# Explanation: Uses level_up_attributes from game_logic.py which handles attribute leveling
#           Checks player_xp and attributes from state to determine leveling capability
#           Attributes are stored in state and have max limits from EnvParams

import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState


def level_up(state: EnvState, attribute_type: str) -> EnvState:
    """
    Levels up a player attribute using XP.
    
    Args:
        state: Current environment state
        attribute_type: Type of attribute to level up ('dexterity', 'strength', 'intelligence')
    
    Returns:
        New state with attribute leveled up
    
    Raises:
        ValueError: If leveling up is not possible
    """
    # Map attribute type to action
    attr_to_action = {
        'dexterity': Action.LEVEL_UP_DEXTERITY.value,
        'strength': Action.LEVEL_UP_STRENGTH.value,
        'intelligence': Action.LEVEL_UP_INTELLIGENCE.value
    }
    
    if attribute_type not in attr_to_action:
        raise ValueError(f"Unknown attribute type: {attribute_type}")
    
    action = attr_to_action[attribute_type]
    
    # Check if player has XP
    if state.player_xp < 1:
        raise ValueError("No XP available")
    
    # Check if attribute can be leveled up
    max_attr = 5  # From EnvParams.max_attribute
    current_attr = {
        'dexterity': state.player_dexterity,
        'strength': state.player_strength,
        'intelligence': state.player_intelligence
    }
    
    if current_attr[attribute_type] >= max_attr:
        raise ValueError(f"Attribute {attribute_type} is at maximum level")
    
    # Level up attribute
    new_xp = state.player_xp - 1
    new_attr = current_attr[attribute_type] + 1
    
    return state.replace(
        player_xp=new_xp,
        player_dexterity=new_attr if attribute_type == 'dexterity' else state.player_dexterity,
        player_strength=new_attr if attribute_type == 'strength' else state.player_strength,
        player_intelligence=new_attr if attribute_type == 'intelligence' else state.player_intelligence,
    )
