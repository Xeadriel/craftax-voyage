"""
The curriculum's (and the critic's) view of the game: a short report of what the
player knows, built only from what the player can see or has seen.
"""

import numpy as np

from craftax.craftax.constants import (
    MONSTERS_KILLED_TO_CLEAR_LEVEL,
    Achievement,
    BlockType,
    ItemType,
    MobType,
)
from craftax.craftax.util.game_logic_utils import (
    get_max_drink,
    get_max_energy,
    get_max_food,
    get_max_health,
    get_max_mana,
)

from control_primitives.craft import RECIPES
from control_primitives.enchant import ENCHANT_ELEMENTS, ENCHANT_MANA_COST
from control_primitives.kill_mob import MOB_NAMES
from control_primitives.knowledge import known_blocks, known_items, ladder_open, visible_mask, visible_mobs
from control_primitives.mine_block import MINEABLE_BLOCKS

FLOOR_NAMES = [
    "Overworld",
    "Dungeon",
    "Gnomish Mines",
    "Sewers",
    "Vaults",
    "Troll Mines",
    "Fire Realm",
    "Ice Realm",
    "Graveyard",
]

TIER_NAMES = ["none", "wood", "stone", "iron", "diamond"]
ARMOUR_NAMES = ["none", "iron", "diamond"]
ENCHANTMENT_NAMES = ["none", "fire", "ice"]
POTION_NAMES = ["red", "green", "blue", "pink", "cyan", "yellow"]

STATION_BLOCKS = [
    BlockType.CRAFTING_TABLE.value,
    BlockType.FURNACE.value,
    BlockType.ENCHANTMENT_TABLE_FIRE.value,
    BlockType.ENCHANTMENT_TABLE_ICE.value,
]
# Resources are all mineable blocks; stations are reported on their own
RESOURCE_BLOCKS = [value for value in MINEABLE_BLOCKS if value not in STATION_BLOCKS]
SOURCE_BLOCKS = [
    BlockType.WATER.value,
    BlockType.FOUNTAIN.value,
    BlockType.RIPE_PLANT.value,
    BlockType.CHEST.value,
]
KEY_ORES = [
    BlockType.COAL.value,
    BlockType.IRON.value,
    BlockType.DIAMOND.value,
    BlockType.SAPPHIRE.value,
    BlockType.RUBY.value,
]
TRACKED_BLOCKS = RESOURCE_BLOCKS + STATION_BLOCKS + SOURCE_BLOCKS


def block_name(value):
    return BlockType(value).name.lower()


def vitals(state):
    """
    Current value and maximum of every intrinsic. The maxima depend on the
    player's attributes.

    Returns:
        Dict "health", "food", "drink", "energy", "mana" -> (current, max)
    """
    return {
        "health": (round(float(state.player_health), 1), int(get_max_health(state))),
        "food": (int(state.player_food), int(get_max_food(state))),
        "drink": (int(state.player_drink), int(get_max_drink(state))),
        "energy": (int(state.player_energy), int(get_max_energy(state))),
        "mana": (int(state.player_mana), int(get_max_mana(state))),
    }


def craftable(state):
    """
    What could be crafted with the current inventory if the player stood next to
    the required stations (the game's own rules, see control_primitives/craft.py).

    Returns:
        Dict "crafting_table" / "crafting_table+furnace" -> recipe names
    """
    inventory = state.inventory
    armour = np.asarray(inventory.armour)
    result = {"crafting_table": [], "crafting_table+furnace": []}

    for name, (_, cost, stations, kind, attribute, level_or_yield) in RECIPES.items():
        if any(int(getattr(inventory, material)) < amount for material, amount in cost.items()):
            continue
        if kind == "tool" and int(getattr(inventory, attribute)) >= level_or_yield:
            continue
        if kind == "armour" and not (armour < level_or_yield).any():
            continue
        if kind == "stack" and int(getattr(inventory, attribute)) >= 99:
            continue
        result["+".join(stations)].append(name)

    return result


def enchantable(state):
    """
    What could be enchanted at a fire / ice enchantment table right now
    (the requirements of control_primitives/enchant.py).

    Returns:
        Dict "fire" / "ice" -> subset of ["sword", "bow", "armour"]
    """
    inventory = state.inventory
    armour = np.asarray(inventory.armour)
    armour_enchantments = np.asarray(state.armour_enchantments)
    result = {}

    for element, (value, _, gem) in ENCHANT_ELEMENTS.items():
        result[element] = []
        if int(state.player_mana) < ENCHANT_MANA_COST or int(getattr(inventory, gem)) < 1:
            continue
        if int(inventory.sword) > 0 and int(state.sword_enchantment) != value:
            result[element].append("sword")
        if int(inventory.bow) > 0 and int(state.bow_enchantment) != value:
            result[element].append("bow")
        if (armour > 0).any() and not (armour_enchantments == value).all():
            result[element].append("armour")

    return result


def _distances(state, cells):
    player = np.asarray(state.player_position)
    return np.abs(cells - player).sum(axis=1)


def _nearest(state, mask):
    """Manhattan distance to the nearest True cell of mask, None if there is none."""
    cells = np.argwhere(mask)
    if len(cells) == 0:
        return None
    return int(_distances(state, cells).min())


def blocks_in_view(state):
    """
    Number of visible cells of every tracked block (resources, stations,
    water, fountains, ripe plants, chests).

    Returns:
        Dict lowercase block name -> count, only blocks that are in view
    """
    level = int(state.player_level)
    in_view = np.asarray(state.map[level])[visible_mask(state)]
    counts = {}
    for value in TRACKED_BLOCKS:
        count = int((in_view == value).sum())
        if count:
            counts[block_name(value)] = count
    return counts


def _tiles(distance):
    return f"{distance} tile" if distance == 1 else f"{distance} tiles"


def _mob_name(mob_class, type_id):
    names = MOB_NAMES[mob_class]
    return names[type_id] if 0 <= type_id < len(names) else f"{mob_class.name.lower()} {type_id}"


def situation_report(state):
    """
    The player-visible state as a short text report.
    """
    level = int(state.player_level)
    inventory = state.inventory
    lines = []

    # Vitals and attributes
    current = vitals(state)
    parts = []
    for name in ["health", "food", "drink", "energy", "mana"]:
        value, maximum = current[name]
        part = f"{name.capitalize()} {value:g}/{maximum}"
        if name in ("food", "drink", "energy"):
            part += f" (can gain up to {max(maximum - value, 0)})"
        parts.append(part)
    lines.append("Vitals: " + " | ".join(parts))
    lines.append(
        f"Sleeping: {'yes' if bool(state.is_sleeping) else 'no'} | "
        f"Resting: {'yes' if bool(state.is_resting) else 'no'}"
    )
    lines.append(
        f"Attributes: XP {int(state.player_xp)} | dexterity {int(state.player_dexterity)} | "
        f"strength {int(state.player_strength)} | intelligence {int(state.player_intelligence)}"
    )

    # Mobs in view
    mobs = sorted(
        (int(_distances(state, np.array([[row, col]]))[0]), mob_class, type_id)
        for mob_class, type_id, row, col, _ in visible_mobs(state)
    )
    threats = [
        f"{_mob_name(mob_class, type_id)} {_tiles(distance)} away"
        for distance, mob_class, type_id in mobs
        if mob_class != MobType.PASSIVE
    ]
    lines.append("Threats in view: " + (", ".join(threats) if threats else "none"))

    # Equipment and inventory
    armour = [ARMOUR_NAMES[int(a)] for a in np.asarray(inventory.armour)]
    armour_enchantments = [ENCHANTMENT_NAMES[int(e)] for e in np.asarray(state.armour_enchantments)]
    spells = [name for name, learned in zip(["fireball", "iceball"], np.asarray(state.learned_spells)) if learned]
    lines.append(
        f"Equipment: pickaxe {TIER_NAMES[int(inventory.pickaxe)]} | "
        f"sword {TIER_NAMES[int(inventory.sword)]} (enchantment {ENCHANTMENT_NAMES[int(state.sword_enchantment)]}) | "
        f"bow {'yes' if int(inventory.bow) > 0 else 'no'} (enchantment {ENCHANTMENT_NAMES[int(state.bow_enchantment)]}) | "
        f"armour slots [{', '.join(armour)}] (enchantments [{', '.join(armour_enchantments)}]) | "
        f"spells: {', '.join(spells) if spells else 'none'}"
    )
    potions = ", ".join(
        f"{colour} potion {int(count)}" for colour, count in zip(POTION_NAMES, np.asarray(inventory.potions))
    )
    lines.append(
        f"Inventory: wood {int(inventory.wood)}, stone {int(inventory.stone)}, coal {int(inventory.coal)}, "
        f"iron {int(inventory.iron)}, diamond {int(inventory.diamond)}, sapphire {int(inventory.sapphire)}, "
        f"ruby {int(inventory.ruby)}, sapling {int(inventory.sapling)}, torch {int(inventory.torches)}, "
        f"arrow {int(inventory.arrows)}, book {int(inventory.books)}, {potions}"
    )

    # What is in view right now
    level_map = np.asarray(state.map[level])
    in_view_mask = visible_mask(state)
    view_parts = []
    for value in RESOURCE_BLOCKS + SOURCE_BLOCKS:
        distance = _nearest(state, in_view_mask & (level_map == value))
        if distance is not None:
            count = int((in_view_mask & (level_map == value)).sum())
            view_parts.append(f"{block_name(value)} {count} (nearest {_tiles(distance)})")
    passive = {}
    for distance, mob_class, type_id in mobs:
        if mob_class == MobType.PASSIVE:
            passive.setdefault(_mob_name(mob_class, type_id), distance)
    view_parts += [f"{name} (nearest {_tiles(distance)})" for name, distance in passive.items()]
    lines.append("In view now: " + (", ".join(view_parts) if view_parts else "nothing notable"))

    # What the player remembers of this floor
    memory = known_blocks(state)
    items = known_items(state)
    seen_parts = []
    for value in RESOURCE_BLOCKS + SOURCE_BLOCKS:
        distance = _nearest(state, memory == value)
        if distance is not None:
            seen_parts.append(f"{block_name(value)} (nearest {_tiles(distance)})")
        elif value in KEY_ORES or value == BlockType.CHEST.value:
            seen_parts.append(f"{block_name(value)} not seen")
    ladder_distance = _nearest(
        state, (items == ItemType.LADDER_DOWN.value) | (items == ItemType.LADDER_DOWN_BLOCKED.value)
    )
    kills_needed = max(MONSTERS_KILLED_TO_CLEAR_LEVEL - int(state.monsters_killed[level]), 0)
    ladder_status = "open" if ladder_open(state) else f"blocked, {kills_needed} more kills needed"
    if ladder_distance is None:
        seen_parts.append(f"ladder down not seen ({ladder_status})")
    else:
        seen_parts.append(f"ladder down {_tiles(ladder_distance)} away ({ladder_status})")
    lines.append("Seen on this floor: " + ", ".join(seen_parts))

    # Stations
    station_parts = []
    for value in STATION_BLOCKS:
        in_view = _nearest(state, in_view_mask & (level_map == value))
        seen = _nearest(state, memory == value)
        if in_view is not None:
            status = f"in view ({_tiles(in_view)})"
        elif seen is not None:
            status = f"seen ({_tiles(seen)})"
        else:
            status = "none seen"
        station_parts.append(f"{block_name(value)} {status}")
    lines.append("Stations: " + ", ".join(station_parts))

    # Hypothetical crafting and enchanting
    craft_lists = craftable(state)
    lines.append(
        "Craftable with a crafting table: " + (", ".join(craft_lists["crafting_table"]) or "nothing")
    )
    lines.append(
        "Craftable with a crafting table + furnace: "
        + (", ".join(craft_lists["crafting_table+furnace"]) or "nothing")
    )
    enchant_lists = enchantable(state)
    lines.append("Enchantable at a fire enchantment table: " + (", ".join(enchant_lists["fire"]) or "nothing"))
    lines.append("Enchantable at an ice enchantment table: " + (", ".join(enchant_lists["ice"]) or "nothing"))

    # Floor and achievements
    floor_name = FLOOR_NAMES[level] if 0 <= level < len(FLOOR_NAMES) else f"floor {level}"
    lines.append(f"Floor: {level} ({floor_name})")
    achievements = np.asarray(state.achievements)
    missing = [
        achievement.name.lower().replace("_", " ")
        for achievement in Achievement
        if not achievements[achievement.value]
    ]
    lines.append("Missing achievements: " + (", ".join(missing) if missing else "none"))

    return "\n".join(lines)
