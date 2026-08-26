# Description:
# Levels up a player attribute (dexterity, strength, or intelligence).
# Returns True if successful, False if not enough XP or attribute already maxed.
# Handles XP management and attribute progression.


def level_up_attribute(state, attribute, max_steps=100):
    """
    Level up a player attribute.

    Args:
        state: Current environment state
        attribute: Attribute to level up (dexterity, strength, or intelligence)
        max_steps: Maximum steps to attempt (default 100)

    Returns:
        bool: True if attribute leveled up, False otherwise
    """
    from craftax.craftax.constants import Action

    # Check if attribute is already maxed
    if state.player_dexterity >= 5 and attribute == "dexterity":
        raise ValueError("Dexterity is already at maximum level")
    if state.player_strength >= 5 and attribute == "strength":
        raise ValueError("Strength is already at maximum level")
    if state.player_intelligence >= 5 and attribute == "intelligence":
        raise ValueError("Intelligence is already at maximum level")

    # Check if we have enough XP
    if state.player_xp < 1:
        raise ValueError("Not enough XP to level up attribute")

    # Map attribute to action
    attribute_to_action = {
        "dexterity": Action.LEVEL_UP_DEXTERITY,
        "strength": Action.LEVEL_UP_STRENGTH,
        "intelligence": Action.LEVEL_UP_INTELLIGENCE,
    }

    action = attribute_to_action[attribute]

    # Level up the attribute
    state = state.replace(
        player_dexterity=state.player_dexterity + 1
        if attribute == "dexterity"
        else state.player_dexterity,
        player_strength=state.player_strength + 1
        if attribute == "strength"
        else state.player_strength,
        player_intelligence=state.player_intelligence + 1
        if attribute == "intelligence"
        else state.player_intelligence,
        player_xp=state.player_xp - 1,
    )

    return True
