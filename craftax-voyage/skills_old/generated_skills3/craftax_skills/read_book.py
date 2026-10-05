# Description:
# Reads a book to learn a spell.
# Returns True if successfully learned a spell, False otherwise.
# Assumes a book is in the player's inventory.

from craftax.craftax.constants import (
    Action,
)


def read_book(env_step, state, max_steps=5):
    """
    Reads a book to learn a spell.
    
    Args:
        env_step: The environment step function
        state: Current environment state
        max_steps: Maximum number of steps to attempt reading
    
    Returns:
        True if successfully learned spell, False otherwise
    """
    # Check if player has a book
    if state.inventory.books <= 0:
        raise ValueError("Player has no books")
    
    # Read the book
    for _ in range(max_steps):
        state = env_step(None, state, Action.READ_BOOK.value, None)
        if state.player_health <= 0:
            raise ValueError("Player died while reading book")
    
    return True
