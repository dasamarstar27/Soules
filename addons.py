"""One entry point for every implemented addon and the deferred-system menus."""

from addon_catalog import ADDONS
from expansion_state import choose


def run(game, feature):
    if not 1 <= feature <= 100:
        raise ValueError("Unknown addon feature.")
    from expansion_state import count

    count(game.player, "addon_" + str(feature) + "_uses")
    if feature <= 20:
        from addon_quests import menu

        return menu(game, feature)
    modules = (
        "community_addons",
        "artisan_addons",
        "expedition",
        "expansion_combat",
        "magic_addons",
        "food_addons",
        "relationship_addons",
        "journal_addons",
    )
    module = modules[(feature - 21) // 10]
    return __import__(module).activity(game, feature)


def hub(game):
    groups = [
        "Quests & ancient history (1–20)",
        "Village systems (21–30)",
        "Artisans & professions (31–40)",
        "Exploration (41–50)",
        "Tactical combat (51–60)",
        "Rune research & elemental practice (61–70)",
        "Cooking & alchemy (71–80)",
        "Companions & relationships (81–90)",
        "Journal & interface tools (91–100)",
        "Season Three expedition",
        "Rumours & Source restoration",
        "Original workshops & collections",
    ]
    ranges = [
        (1, 20),
        (21, 30),
        (31, 40),
        (41, 50),
        (51, 60),
        (61, 70),
        (71, 80),
        (81, 90),
        (91, 100),
    ]
    while True:
        print(
            "Choose the NUMBER AT THE LEFT to open a category. The 1–20 and 21–30 labels describe adventure IDs, not the number you should type. Nothing is purchased just by opening a category."
        )
        index = choose("ADVENTURES, PROJECTS & RESEARCH", groups)
        if index is None:
            return
        if index == 11:
            from legacy_workshops import collections

            collections(game)
            continue
        if index == 10:
            from foundation_expansions import menu

            menu(game)
            continue
        if index == 9:
            from season_three import menu

            menu(game)
            continue
        start, end = ranges[index]
        ids = list(range(start, end + 1))
        from community_addons import INSTRUCTIONS

        print(
            "Choose a numbered activity below. Read its cost first: some choices immediately spend the listed supplies; 0 returns without selecting one."
        )
        feature = choose(
            groups[index],
            [
                f'{ADDONS[i]["name"]} — {INSTRUCTIONS.get(i, ADDONS[i]["description"])}'
                for i in ids
            ],
        )
        if feature is not None:
            run(game, ids[feature])
