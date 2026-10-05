# Skill: read_book
# Purpose: Reads a book to learn a spell
# Required inputs: max_steps (int)
# Preconditions: Player must have a book in inventory
# Expected effects: Book is consumed, spell is learned
# Failure conditions: No book in inventory
# Explanation: Uses state.inventory for book availability, Action.READ_BOOK for reading interaction

import jax
import jax.numpy as jnp
from craftax.craftax.constants import Action
from craftax.craftax.craftax_state import EnvState

def read_book(state: EnvState, max_steps: int = 100) -> bool:
    """
    Reads a book to learn a spell.
    
    Returns True if spell was learned, False otherwise.
    """
    # Check if we have a book in inventory
    if state.inventory.books <= 0:
        return False
    
    # Read the book by pressing READ_BOOK key
    for step in range(max_steps):
        key = jax.random.PRNGKey(0)
        
        # Read
        action = Action.READ_BOOK.value
        _, new_state, reward, done, info = state.step(key, state, action, state.default_params)
        state = new_state
        
        # Check if spell was learned
        if state.learned_spells[0] or state.learned_spells[1]:
            return True
        
        # Check if we're stuck
        if step > 0 and step > max_steps // 2:
            return False
    
    return False
