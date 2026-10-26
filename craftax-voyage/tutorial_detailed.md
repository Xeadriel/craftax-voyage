# Craftax: Tutorial

Craftax is a game about mining, crafting, surviving and fighting through 9 floors, ending with the necromancer boss.

Below is a detailed breakdown of everything noteworthy.

## 1. Reading the state

- **Map**: you see 11 columns × 9 rows centred on yourself. Each line is `x, y: block`.
  - `x` is the column offset from -5 to 5; negative is left, positive is right.
  - `y` is the row offset from -4 to 4; negative is up, positive is down.
  - `0, 0` is your own tile. `1, 0` is directly right of you, `0, -1` directly above.
  - A creature or item standing on a block is shown as `Cow on grass`, `ladder_down on path`, `torch on path`.
  - `Darkness` means the tile is unlit (place torches to see it). `darkness` is a solid dungeon filler block with nothing behind it. `out_of_bounds` is beyond the edge of the 48×48 world.
- **Inventory**: counts of each resource, then your tools (e.g. `Wood Pickaxe`, `Stone Sword`), then health, food, drink, energy, mana, XP and attributes.
- **Direction**: the way you face. Actions like mining and placing affect the tile you face.
- The state does not tell you whether it is day or night.

## 2. Basic actions

- **Move** with LEFT, RIGHT, UP, DOWN. Moving into a direction also turns you to face it. You cannot walk into water, lava, or solid blocks (trees, stone, ores, tables, furnaces, plants, walls, chests, fountains, graves).
- **DO** interacts with the faced tile: mine a block, attack a creature, drink water, eat a ripe plant, or open a chest.
- **Near a station** means the crafting table or furnace is in one of the 8 tiles around you (diagonals count). You do not need to face it.
- **Enchantment tables** must be faced directly.
- **NOOP** does nothing.

## 3. Crafting

Crafting needs a `crafting_table` nearby; iron items need a `furnace` nearby as well. Each craft consumes the listed resources.

| Action | Cost | Needs nearby | Result |
|---|---|---|---|
| MAKE_WOOD_PICKAXE | 1 wood | table | pickaxe level 1 |
| MAKE_STONE_PICKAXE | 1 wood, 1 stone | table | pickaxe level 2 |
| MAKE_IRON_PICKAXE | 1 wood, 1 stone, 1 iron, 1 coal | table + furnace | pickaxe level 3 |
| MAKE_DIAMOND_PICKAXE | 1 wood, 3 diamond | table | pickaxe level 4 |
| MAKE_WOOD_SWORD | 1 wood | table | sword level 1 |
| MAKE_STONE_SWORD | 1 wood, 1 stone | table | sword level 2 |
| MAKE_IRON_SWORD | 1 wood, 1 stone, 1 iron, 1 coal | table + furnace | sword level 3 |
| MAKE_DIAMOND_SWORD | 1 wood, 2 diamond | table | sword level 4 |
| MAKE_IRON_ARMOUR | 3 iron, 3 coal | table + furnace | one armour piece of iron |
| MAKE_DIAMOND_ARMOUR | 3 diamond | table | one armour piece of diamond |
| MAKE_ARROW | 1 wood, 1 stone | table | +2 arrows |
| MAKE_TORCH | 1 wood, 1 coal | table | +4 torches |

- You only ever hold one pickaxe and one sword; crafting a better one replaces the old one. A craft fails if you already have that level or higher.
- Tiers can be skipped, e.g. a diamond pickaxe can be crafted without owning an iron one.
- There are 4 armour slots. Each craft fills one slot (diamond can replace iron).
- Inventory counts are capped at 99.

## 4. Placing

Placing puts a block on the tile you face. The tile must not be solid and must not already hold an item (torch, ladder).

| Action | Cost | Where | Result |
|---|---|---|---|
| PLACE_TABLE | 2 wood | any free tile | crafting_table |
| PLACE_FURNACE | 1 stone | any free tile (no table needed, but iron crafting needs both next to you) | furnace |
| PLACE_STONE | 1 stone | any free tile, including water and lava | stone |
| PLACE_TORCH | 1 torch | grass, sand, path, fire_grass, ice_grass | torch (lights tiles within ~4.7 tiles) |
| PLACE_PLANT | 1 sapling | grass only | plant (ripens after 600 steps) |

- Place the furnace so that one tile is next to both the furnace and the table, then stand there to craft iron items.
- Mining a placed table or furnace destroys it and gives nothing back. Enemy projectiles that hit a table or furnace also destroy it.
- Placing stone on water or lava and then mining it turns the tile into walkable path. This is how you bridge water and lava.

## 5. Mining

Use DO on the faced block.

| Block | Needs | Gives | Afterwards |
|---|---|---|---|
| tree, fire_tree, ice_shrub | nothing | 1 wood | the tree is gone (becomes grass) |
| stone | pickaxe level ≥ 1 | 1 stone | path |
| coal | pickaxe level ≥ 1 | 1 coal | path |
| stalagmite | pickaxe level ≥ 1 | 1 stone | path |
| iron | pickaxe level ≥ 2 (stone) | 1 iron | path |
| diamond | pickaxe level ≥ 3 (iron) | 1 diamond | path |
| sapphire | pickaxe level 4 (diamond) | 1 sapphire | path |
| ruby | pickaxe level 4 (diamond) | 1 ruby | path |
| grass | nothing | 10% chance of 1 sapling | stays grass |
| water, fountain | nothing | +1 drink | unchanged |
| ripe_plant | nothing | +4 food | plant (grows again) |
| chest | nothing | random loot (section 10) | path |

- Each tree gives exactly 1 wood and then disappears, so look for groups of trees.
- Walls, enchantment tables, graves, sand, lava and darkness cannot be mined.

## 6. Survival

You start with 9 health, 9 food, 9 drink, 9 energy and 9 mana (these are also the maximums at attribute level 1).

| Stat | Goes down | How to restore |
|---|---|---|
| Food | −1 every 26 steps | kill an animal with melee: +6 food (Cow, Snail, Bat). Eat a ripe_plant: +4 food |
| Drink | −1 every 21 steps | DO on water or a fountain: +1 drink per DO |
| Energy | −1 every 31 steps | SLEEP: +1 energy every 11 steps while asleep |
| Health | see below | keep food, drink and energy above 0; sleep or REST |
| Mana | used by spells and enchanting | regenerates +1 every ~31 steps (faster when asleep and with intelligence) |

- **Health** regenerates +1 every 26 steps (13 when asleep) while food, drink and energy are all above 0. If any of them is 0, you lose 1 health every 16 steps instead. At 0 health you die and the game is over.
- **Drinking**: drink several times in a row (e.g. 5 DOs) to fill up. Do it before drink falls below about 4.
- **Eating**: only melee kills of animals give food; arrows and spells do not. Each animal kill is +6 food.
- **Sleeping**: SLEEP only works if energy is below maximum. You stay asleep until energy is full. While asleep, food and drink fall at half speed, but monsters deal 3.5× melee damage and a hit wakes you. Before sleeping, block yourself in by placing stone on all 4 sides.
- **Resting**: REST works if health is below maximum. You do nothing until health is full, food or drink reaches 0, or you are attacked.
- **Day and night**: a day lasts 300 steps. At night more Zombies spawn on the overworld. Night has no other effect.

## 7. Combat

**Your melee damage** (DO on a creature):

| Sword | none | wood | stone | iron | diamond |
|---|---|---|---|---|---|
| Damage | 1 | 2 | 3 | 5 | 8 |

- Strength adds +25% melee damage per level above 1.
- An enchanted sword adds 50% of its base damage as fire or ice damage.

**Ranged attacks**:
- **Bow**: SHOOT_ARROW uses 1 arrow and deals 5 physical damage (+20% per dexterity level above 1). The bow comes from the first chest opened on floor 1. Arrows are crafted (1 wood + 1 stone = 2 arrows).
- **Spells**: CAST_FIREBALL / CAST_ICEBALL cost 2 mana and deal 3 fire / 3 ice damage (+50% per intelligence level above 1). Learn them with READ_BOOK (books are found in chests on floors 3 and 4; each book teaches a random spell you don't know yet).
- Projectiles fly in the direction you face and stop at the first creature or solid block. You can have at most 3 in flight.

**Armour**:
- Each iron piece reduces physical damage by 10%, and each diamond piece by 20% (all 4 diamond pieces: −80%).
- Each fire-enchanted piece reduces fire damage by 20%; each ice-enchanted piece reduces ice damage by 20%.

**Damage types and resistances**: damage is physical, fire or ice. Some creatures resist some types (see the floor tables). A creature that is 90% resistant to physical damage takes only a tenth of your sword damage, so use the element it is not immune to.

**Monsters**:
- Melee monsters chase you when they are within 10 tiles and attack when adjacent, once every 5 steps.
- Ranged monsters keep 4–5 tiles away and shoot along a straight row or column, once every 4 steps. Step out of their row and column to dodge.
- There are at most 3 melee monsters, 2 ranged monsters and 3 animals on a floor at a time. Monsters spawn more than 9 tiles away from you and despawn when 14 or more tiles away.

## 8. Progression between floors

- Each floor has a `ladder_down` to the next floor and a `ladder_up` back (the overworld has no up ladder, the graveyard has neither).
- Stand on the ladder and use DESCEND or ASCEND. You arrive on the other floor's matching ladder.
- **Opening the ladder down**: you must kill 8 monsters (melee or ranged, not animals) on a floor before its ladder down works. The overworld ladder is open from the start.
- Monsters spawn 3× more often on a floor until its 8 kills are done.
- You can always go back up, e.g. to drink, eat or collect wood on an earlier floor.

**Experience and attributes**:
- You gain 1 XP the first time you enter each of floors 1 to 8 (8 XP in total).
- Spend XP with LEVEL_UP_DEXTERITY, LEVEL_UP_STRENGTH or LEVEL_UP_INTELLIGENCE (1 XP each, maximum level 5 per attribute).

| Attribute | Each level above 1 gives |
|---|---|
| Dexterity | +2 max food, drink and energy; they decay 12.5% slower; +20% bow damage |
| Strength | +1 max health; +25% melee damage |
| Intelligence | +3 max mana; faster mana regeneration; +50% spell damage; +5% enchantment damage |

## 9. Floors

### Floor 0: Overworld

| | |
|---|---|
| Terrain | grass with groups of trees, lakes of water with sand shores, stone mountains with path tunnels and caves |
| Wood | yes, trees on grass |
| Water | lakes |
| Food | Cow (3 health), ripe plants from saplings |
| Ores (share of stone tiles) | coal 3%, iron 2%, diamond 0.1% (very rare; usually 0–2 on the whole map) |
| Light | daylight, always visible in the state |
| Monsters | Zombie (melee, 5 health, 2 damage), Skeleton (ranged, 3 health, arrows 2 damage) |
| Ladder down | open from the start; always on a path tile inside the stone mountains |

- You start in the middle of the map on grass, with no water or mountains in the first few tiles.
- Mountains contain stone, coal and iron, and also lava in their deepest parts. You cannot walk into lava.
- Wood exists only on floors 0, 6 and 7. Collect plenty before going down (at least 10 extra), because floors 1 to 5 have no trees.
- Plants only grow on the overworld. Planting saplings near your base gives you food when you come back.
- You do not need to kill 8 mobs to progress to the next floor in Floor 0

### Floor 1: Dungeon

| | |
|---|---|
| Terrain | 8 rectangular rooms connected by corridors, surrounded by walls and darkness |
| Wood | none |
| Water | fountains (in about half of the rooms) |
| Food | Snail (6 health) |
| Ores | none in the walls; chests can contain ore |
| Light | fully lit; each room has torches in its corners |
| Monsters | Orc Soldier (melee, 9 health, 3 damage), Orc Mage (ranged, 6 health, fireballs 3 fire damage) |
| Chests | one per room (8). The first chest you open always contains a bow |

### Floor 2: Gnomish Mines

| | |
|---|---|
| Terrain | dark caves of path with stone walls and stalagmites, pools of water |
| Wood | none (stalagmites give stone, not wood) |
| Water | pools |
| Food | Bat (4 health) |
| Ores (share of stone tiles) | coal 4%, iron 2%, diamond 0.5%, sapphire 0.25%, ruby 0.25%; richer near the outer edges |
| Light | dark; only the area around the arrival ladder is lit. Place torches (craft them from 1 wood + 1 coal) |
| Monsters | Gnome Warrior (melee, 7 health, 4 damage), Gnome Archer (ranged, 5 health, arrows 2 damage) |

- Bring torches and wood. Diamonds become findable here; 3 diamonds make a diamond pickaxe, which is needed for sapphire and ruby.

### Floor 3: Sewers

| | |
|---|---|
| Terrain | rooms and corridors like the dungeon, with patches of water on the floor |
| Wood | none |
| Water | water patches and pools in rooms |
| Food | Snail (6 health) |
| Light | fully lit |
| Monsters | Lizard (melee, 11 health, 5 damage, can swim through water), Kobold (ranged, 8 health, daggers 4 damage) |
| Chests | one per room (8). The first chest you open contains a book |
| Special | the ice enchantment table (enchantment_table_ice) |

- Water patches block your path; fill them with stone and mine it to cross.

### Floor 4: Vaults

| | |
|---|---|
| Terrain | rooms and corridors |
| Wood | none |
| Water | fountains |
| Food | Snail (6 health) |
| Light | fully lit |
| Monsters | Knight (melee, 12 health, 6 damage, takes half physical damage), Archer (ranged, 12 health, arrows 5 damage, takes half physical damage) |
| Chests | one per room (8). The first chest you open contains a book |
| Special | the fire enchantment table (enchantment_table_fire) |

### Floor 5: Troll Mines

| | |
|---|---|
| Terrain | dark caves like the gnomish mines, with water pools |
| Wood | none |
| Water | pools |
| Food | Bat (4 health) |
| Ores (share of stone tiles) | coal 4%, iron 3%, diamond 1%, sapphire 1%, ruby 1% (the richest floor) |
| Light | dark; place torches |
| Monsters | Troll (melee, 20 health, 6 physical + 1 fire + 1 ice damage, takes 20% less physical damage), Deep Thing (ranged, 4 health, lives only in water, slimeballs 4 physical + 3 fire + 3 ice damage) |

- Craft full diamond armour here (4 pieces × 3 diamond). Deep Things die quickly but hit very hard; stay out of their row and column.

### Floor 6: Fire Realm

| | |
|---|---|
| Terrain | islands of fire_grass in a sea of lava |
| Wood | yes, fire_tree (gives wood like a normal tree) |
| Water | **none**. Go back up to floor 5 to drink |
| Food | Bat (4 health) |
| Ores (share of stone tiles) | coal 5%, ruby 2.5% |
| Light | fully visible |
| Monsters | Pigman (melee, 20 health, 3 physical + 5 fire damage), Fire Elemental (ranged, 14 health, fireballs 3 physical + 5 fire damage). Both are immune to fire and take only 10% of physical damage |

- Use ice damage: an ice-enchanted sword, the iceball spell, or an ice-enchanted bow. Fire-enchanted armour reduces their fire damage.
- Bridge the lava by placing stone on it and mining the stone.

### Floor 7: Ice Realm

| | |
|---|---|
| Terrain | islands of ice_grass in water, with stone mountains |
| Wood | yes, ice_shrub (very common; you can walk through it) |
| Water | yes |
| Food | **none** (no animals spawn). Go back up to floor 6 to eat |
| Ores (share of stone tiles) | diamond 0.5%, sapphire 2% |
| Light | dark; place torches |
| Monsters | Frost Troll (melee, 24 health, 4 physical + 5 ice damage), Ice Elemental (ranged, 16 health, iceballs 4 physical + 5 ice damage). Both are immune to ice and take only 10% of physical damage |

- Use fire damage: a fire-enchanted sword, the fireball spell, or a fire-enchanted bow. Ice-enchanted armour reduces their ice damage.

### Floor 8: Graveyard (boss)

| | |
|---|---|
| Terrain | an open area of path with graves, surrounded by walls; the necromancer is in the centre |
| Wood, water, food | none, but food, drink and energy do not decrease on this floor |
| Ladders | none; you cannot leave |
| Damage taken | ×1.5 on this floor |

- Monsters spawn in waves from graves near you. Wave 1 is overworld monsters (Zombie, Skeleton), wave 2 dungeon monsters, and so on up to wave 8 with Frost Trolls and Ice Elementals.
- When no monsters are left alive, the necromancer becomes vulnerable. Hit it once with DO while standing next to it; that starts the next wave.
- 8 hits defeat the necromancer and win the game.

## 10. Chests and potions

Chests are found only on floors 1, 3 and 4 (one per room, 8 per floor). Opening one (DO) removes it. Each chest independently has a:

| Chance | Contents |
|---|---|
| 60% | 4–7 torches |
| 60% | ore: coal 1–3, iron 1–2, or a single diamond, sapphire or ruby |
| 50% | 1–2 potions of a random colour |
| 25% | 1–4 arrows |
| 20% | a pickaxe or sword of a random level (only kept if better than yours) |

**Potions**: DRINK_POTION_RED, _GREEN, _BLUE, _PINK, _CYAN, _YELLOW. Each colour has one of these effects: +8 health, −3 health, +8 mana, −3 mana, +8 energy, −3 energy. Which colour does what changes every game, so test them when it is safe (not at low health).

**Enchanting** (stand facing the enchantment table):

| Action | Needs | Effect |
|---|---|---|
| ENCHANT_SWORD | a sword, 9 mana, 1 gem | sword deals +50% extra damage of that element |
| ENCHANT_ARMOUR | armour, 9 mana, 1 gem | one armour piece gets −20% damage of that element |
| ENCHANT_BOW | a bow, 9 mana, 1 gem | arrows deal extra damage of that element |

- The ice table (floor 3) uses 1 sapphire and gives ice enchantments. The fire table (floor 4) uses 1 ruby and gives fire enchantments.
- Sapphires and rubies need a diamond pickaxe to mine, or come from chests.

## 11. Recommended early game progression

1. Mine some wood (trees on the overworld).
2. Place a crafting table (costs 2 wood).
3. Craft a wood pickaxe and a wood sword (they cost 1 wood each).
4. Mine some stone from the mountains.
5. Craft a stone pickaxe and a stone sword (they cost 1 wood + 1 stone each).

Try not to get stuck in the Overworld forever as iron, coal and diamonds (if there even spawn any) in Floor 0 will likely not suffice to get a full iron set or diamond set. When in doubt, prepare enough wood and stone and proceed to the next floors.
6. Mine coal and iron (iron needs the stone pickaxe).
7. Craft an iron pickaxe and an iron sword (they cost 1 wood, 1 stone, 1 iron, 1 coal each, next to table and furnace).
8. Craft iron armour with the remaining iron: each piece costs 3 iron + 3 coal (next to table and furnace) and reduces physical damage by 10%, up to 4 pieces (12 iron + 12 coal for −40%).
   - The iron tools come first (2 iron in total), then every further 3 iron + 3 coal is one armour piece.
   - Iron is only about 2% of stone tiles on the overworld, so mine every iron you can see.
   - Iron is more common in the Gnomish Mines (2%) and the Troll Mines (3%), and chests often contain 1–2 iron, so you can complete the set later. Make sure you have enough wood and stone to place a new table and furnace there if needed.
   - Diamond armour (3 diamond per piece, −20% each) replaces iron pieces later; craft it once you have spare diamonds after the diamond pickaxe (costs 3 diamonds) and sword (costs 2 diamonds).
9. Craft torches (1 wood + 1 coal = 4 torches) and arrows (1 wood + 1 stone = 2 arrows).
10. Collect a lot of extra wood and some stone, then find the ladder down inside the mountains and descend.
11. On each new floor: kill 8 monsters to open the ladder, open chests, drink and eat when possible, spend XP.

Throughout the game:
- CRITICAL: Monitor your drink and drink when low. This takes priority over whatever resource collecting or crafting comes next.
- CRITICAL: Monitor your food and eat when low. This takes priority over whatever resource collecting or crafting comes next.
- CRITICAL: Monitor your energy and sleep when low. This takes priority over whatever resource collecting or crafting comes next. If you're low on food or drink, you should eat or drink first because you can't do so while sleeping and only wake up when your energy has fully refilled.
- Plan ahead. Try not go let any of the intrinsics go below 3 because if you die you loose everything.
- Carry a few stone blocks for bridging water and lava and for walling yourself in.
- If health is low, block yourself in with stone and REST or SLEEP (sleep is always better if possible).
- Crafting tables and furnaces cannot be carried. Carry wood and stone so you can place new ones on any floor.
- Use the State's "Ladder Open" information in order to find out if you can descend.
- Always descend to the next Floor if your resources allow it and the ladder is open.
- Always craft the best possible equipment if you have the resources
- Always balance enchantments
- IMPORTANT: Your end goal is to descend as many floors as you can without dying!

## 12. Achievements

Each achievement is unlocked once, the first time you do it. Try to do all of them.

- **Overworld basics**: COLLECT_WOOD, PLACE_TABLE, MAKE_WOOD_PICKAXE, MAKE_WOOD_SWORD, COLLECT_STONE, PLACE_STONE, MAKE_STONE_PICKAXE, MAKE_STONE_SWORD, PLACE_FURNACE, COLLECT_COAL, COLLECT_IRON, MAKE_IRON_PICKAXE, MAKE_IRON_SWORD, MAKE_ARROW, MAKE_TORCH, PLACE_TORCH, COLLECT_DIAMOND, MAKE_DIAMOND_PICKAXE, MAKE_DIAMOND_SWORD, MAKE_IRON_ARMOUR, MAKE_DIAMOND_ARMOUR, COLLECT_SAPPHIRE, COLLECT_RUBY
- **Survival**: COLLECT_DRINK, EAT_COW, EAT_SNAIL, EAT_BAT, COLLECT_SAPLING, PLACE_PLANT, EAT_PLANT, WAKE_UP
- **Exploration**: ENTER_DUNGEON, ENTER_GNOMISH_MINES, ENTER_SEWERS, ENTER_VAULT, ENTER_TROLL_MINES, ENTER_FIRE_REALM, ENTER_ICE_REALM, ENTER_GRAVEYARD
- **Items and magic**: OPEN_CHEST, FIND_BOW, FIRE_BOW, DRINK_POTION, LEARN_FIREBALL, CAST_FIREBALL, LEARN_ICEBALL, CAST_ICEBALL, ENCHANT_SWORD, ENCHANT_ARMOUR
- **Combat**: DEFEAT_ZOMBIE, DEFEAT_SKELETON, DEFEAT_ORC_SOLIDER, DEFEAT_ORC_MAGE, DEFEAT_GNOME_WARRIOR, DEFEAT_GNOME_ARCHER, DEFEAT_LIZARD, DEFEAT_KOBOLD, DEFEAT_KNIGHT, DEFEAT_ARCHER, DEFEAT_TROLL, DEFEAT_DEEP_THING, DEFEAT_PIGMAN, DEFEAT_FIRE_ELEMENTAL, DEFEAT_FROST_TROLL, DEFEAT_ICE_ELEMENTAL, DAMAGE_NECROMANCER, DEFEAT_NECROMANCER
