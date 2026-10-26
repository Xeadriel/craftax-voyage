"""
What the critic is shown about one skill execution: what changed, what the
control primitives report happened, and why a run ended in death. The skill's
own log lines are never part of it.
"""

import re
from functools import lru_cache

import numpy as np

from control_primitives import control_primitive_names
from control_primitives.knowledge import visible_mobs
from utils.situation_report import (
    ARMOUR_NAMES,
    ENCHANTMENT_NAMES,
    FLOOR_NAMES,
    POTION_NAMES,
    TIER_NAMES,
    _mob_name,
    _tiles,
    blocks_in_view,
    vitals,
)

PRIMITIVE_LINE = re.compile(r"^\[(\w+)\] ")
STEP_LINE = re.compile(r"^\[\w+\] Step \d+/\d+")

INVENTORY_FIELDS = [
    ("wood", "wood"), ("stone", "stone"), ("coal", "coal"), ("iron", "iron"),
    ("diamond", "diamond"), ("sapphire", "sapphire"), ("ruby", "ruby"),
    ("sapling", "sapling"), ("torches", "torch"), ("arrows", "arrow"), ("books", "book"),
]


@lru_cache(maxsize=1)
def _primitive_names():
    return frozenset(control_primitive_names())


def primitive_events(lines):
    """
    The control primitives' own report lines ("[mine_block] Mined COAL 1/3 ..."),
    without their per-step lines and without anything the skill logged itself.
    """
    events = []
    for line in lines:
        match = PRIMITIVE_LINE.match(line)
        if match and match.group(1) in _primitive_names() and not STEP_LINE.match(line):
            events.append(line)
    return events


def _vitals_text(values):
    return ", ".join(f"{name} {value:g}/{maximum}" for name, (value, maximum) in values.items())


def _equipment(state):
    inventory = state.inventory
    return {
        "pickaxe": TIER_NAMES[int(inventory.pickaxe)],
        "sword": TIER_NAMES[int(inventory.sword)],
        "bow": "yes" if int(inventory.bow) > 0 else "no",
        "armour slots": "[" + ", ".join(ARMOUR_NAMES[int(a)] for a in np.asarray(inventory.armour)) + "]",
        "sword enchantment": ENCHANTMENT_NAMES[int(state.sword_enchantment)],
        "bow enchantment": ENCHANTMENT_NAMES[int(state.bow_enchantment)],
        "armour enchantments": "["
        + ", ".join(ENCHANTMENT_NAMES[int(e)] for e in np.asarray(state.armour_enchantments))
        + "]",
        "learned spells": ", ".join(
            name for name, learned in zip(["fireball", "iceball"], np.asarray(state.learned_spells)) if learned
        ) or "none",
    }


def _counts(state):
    inventory = state.inventory
    counts = {label: int(getattr(inventory, field)) for field, label in INVENTORY_FIELDS}
    for colour, count in zip(POTION_NAMES, np.asarray(inventory.potions)):
        counts[f"{colour} potion"] = int(count)
    for name in ["xp", "dexterity", "strength", "intelligence"]:
        counts[name] = int(getattr(state, f"player_{name}"))
    return counts


def state_diff(before, after, new_achievements):
    """
    What changed between the state before and the state after a skill execution.
    """
    vitals_before, vitals_after = vitals(before), vitals(after)
    lines = [
        "Vitals: "
        + ", ".join(
            f"{name} {vitals_before[name][0]:g}/{vitals_before[name][1]} -> "
            f"{vitals_after[name][0]:g}/{vitals_after[name][1]}"
            for name in vitals_before
        )
    ]

    changes = []
    counts_before, counts_after = _counts(before), _counts(after)
    for name, old in counts_before.items():
        new = counts_after[name]
        if new != old:
            changes.append(f"{name} {old} -> {new} ({new - old:+d})")

    equipment_before, equipment_after = _equipment(before), _equipment(after)
    for name, old in equipment_before.items():
        if equipment_after[name] != old:
            changes.append(f"{name} {old} -> {equipment_after[name]}")

    level_before, level_after = int(before.player_level), int(after.player_level)
    if level_after != level_before:
        name = FLOOR_NAMES[level_after] if 0 <= level_after < len(FLOOR_NAMES) else f"floor {level_after}"
        changes.append(f"floor {level_before} -> {level_after} ({name})")
    else:
        # Moving changes these counts as well; placing or mining shows up here too
        view_before, view_after = blocks_in_view(before), blocks_in_view(after)
        for name in sorted(set(view_before) | set(view_after)):
            old, new = view_before.get(name, 0), view_after.get(name, 0)
            if new != old:
                changes.append(f"{name} in view {old} -> {new}")

    lines.append("Changes: " + ("; ".join(changes) if changes else "no changes"))
    lines.append("New achievements: " + (", ".join(new_achievements) if new_achievements else "none"))
    return "\n".join(lines)


def death_critique(death_state, events):
    """
    The critique for an execution that ended with the player's death, written
    without the critic.
    """
    player = np.asarray(death_state.player_position)
    threats = [
        f"{_mob_name(mob_class, type_id)} {_tiles(abs(row - int(player[0])) + abs(col - int(player[1])))} away"
        for mob_class, type_id, row, col, _ in visible_mobs(death_state)
        if mob_class.name != "PASSIVE"
    ]
    lines = [
        "The player died.",
        "Vitals at the last step before death: " + _vitals_text(vitals(death_state)),
        "Threats in view then: " + (", ".join(threats) if threats else "none"),
        "Primitive events of this attempt:",
    ]
    lines += events if events else ["none"]
    return "\n".join(lines)
