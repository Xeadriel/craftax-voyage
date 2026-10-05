# Description:
# Provides reusable enchanting skills for enchanting items at enchantment tables.
# Each skill checks for prerequisites and fails if not met.

from craftax.craftax.constants import *
from craftax.craftax.craftax_state import EnvState
from craftax.craftax.game_logic import craftax_step

def enchant_item(state: EnvState, action_func, item_type: BlockType, step_count: int = 10, max_steps: int = 50) -> bool:
    """
    Enchants an item of the specified type at an enchantment table.
    Returns True if enchanting was successful, False otherwise.
    """
    for _ in range(step_count):
        if action_func != Action.DO.value:
            return False
        
        # Check if at enchantment table
        if not is_near_block(state, BlockType.ENCHANTMENT_TABLE_FIRE.value) and not is_near_block(state, BlockType.ENCHANTMENT_TABLE_ICE.value):
            return False
        
        # Check if has mana
        if state.player_mana < 9:
            return False
        
        # Check if has gemstone
        if item_type == BlockType.FIREBALL.value:
            if state.inventory.ruby < 1:
                return False
        elif item_type == BlockType.ICEBALL.value:
            if state.inventory.sapphire < 1:
                return False
        
        # Check if has item to enchant
        if item_type == BlockType.SWORD.value:
            if state.inventory.sword < 1:
                return False
        elif item_type == BlockType.BOW.value:
            if state.inventory.bow < 1:
                return False
        elif item_type == BlockType.ARMOUR.value:
            if state.inventory.armour.sum() < 1:
                return False
        
        state = craftax_step(state
