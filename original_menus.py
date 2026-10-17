"""Every original numeric action, grouped without dropping any choices."""

GROUPS = [
    {
        "id": "explore",
        "name": "Explore",
        "options": [
            (1, "Wander"),
            (2, "Travel"),
            (9, "Boss fight"),
            (13, "World map"),
            (17, "Structures"),
        ],
    },
    {
        "id": "inventory",
        "name": "Inventory & Equip",
        "options": [
            (4, "Equip weapon"),
            (5, "Equip armour"),
            (10, "Inventory"),
            (11, "Sell loot"),
            (18, "Eat food"),
        ],
    },
    {
        "id": "crafting",
        "name": "Crafting",
        "options": [
            (3, "Upgrades & runes"),
            (12, "Cast spell"),
            (14, "Crimson forge"),
            (15, "Infuse equipment"),
            (16, "Source temple"),
            (23, "Village crafting hub"),
            (34, "Enchant equipment"),
            (37, "Ritual ceremonies"),
            (39, "Recipe discovery"),
        ],
    },
    {
        "id": "character",
        "name": "Character",
        "options": [
            (6, "Stats & details"),
            (19, "Skill tree"),
            (20, "Achievements"),
            (21, "Bestiary"),
            (22, "Companions"),
            (28, "Advanced skill trees"),
            (29, "Cosmetics"),
            (35, "New Game+"),
            (36, "Battle pass"),
            (42, "Login streak"),
            (46, "Active status effects"),
        ],
    },
    {
        "id": "challenges",
        "name": "Quests & Challenges",
        "options": [
            (24, "Daily challenges"),
            (25, "Weekly challenges"),
            (26, "Boss rush"),
            (27, "Boss rush statistics"),
            (31, "Seasonal events"),
            (32, "Challenge modes"),
            (33, "Story & lore"),
        ],
    },
    {
        "id": "world",
        "name": "World & Social",
        "options": [
            (30, "Guild"),
            (38, "Arena"),
            (40, "Trading post"),
            (41, "Town building"),
            (43, "Factions"),
            (44, "Treasure hunting"),
            (45, "Mounts"),
        ],
    },
    {"id": "system", "name": "System", "options": [(7, "Save game"), (8, "Exit to title")]},
]
BY_ID = {g["id"]: g for g in GROUPS}
assert sorted(n for g in GROUPS for n, _ in g["options"]) == list(range(1, 47))
