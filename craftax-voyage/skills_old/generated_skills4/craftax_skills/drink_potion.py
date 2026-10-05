# Description:
# Drinks a potion of a specified type.
# Returns True if successful, False if potion not available or invalid type.
# Handles potion effects and inventory management.

def drink_potion(state, potion_type, max_steps=100):
    """
    Drink a potion of the specified type.
    
    Args:
        state: Current environment state
        potion_type: Potion type (red, green, blue, pink, cyan, yellow)
        max_steps: Maximum steps to attempt (default 100)
    
    Returns:
        bool: True if potion drunk, False otherwise
    """
    from craftax.craftax.constants import Action
    
    # Map potion names to indices
    potion_to_index = {
        "red": 0,
        "green": 1,
        "blue": 2,
        "pink": 3,
        "cyan": 4,
        "yellow": 5,
    }
    
    if potion_type not in potion_to_index:
        raise ValueError(f"Unknown potion type: {potion_type}")
    
    potion_index = potion_to_index[potion_type]
    
    # Check if we have the potion
    if state.inventory.potions[potion_index] < 1:
        raise ValueError(f"Cannot drink {potion_type} potion - not in inventory")
    
    # Drink the potion
    state = drink_potion(state, action)
    
    return True
