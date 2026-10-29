"""Short village categories; action IDs remain internal to the existing handlers."""

GROUPS = (
    ("Food & rest", (1, 13, 3, 4, 10)),
    ("Shops & crafting", (2, 19, 25, 8, 9, 6, 24)),
    ("Build & manage", (17, 20, 22, 21)),
    ("People & quests", (14, 15, 18, 16, 5, 26)),
    ("Notes & bookmarks", (11, 12)),
    ("Activities", (23,)),
)


def groups(village):
    from village_life import village_options

    available = dict(village_options(village))
    return [
        (name, [(key, available[key]) for key in keys if key in available])
        for name, keys in GROUPS
        if any(key in available for key in keys)
    ]


def choose(village, selected=None):
    from village_life import village_options

    available = dict(village_options(village))
    menus = groups(village)
    while True:
        if selected is None:
            print("\n--- VILLAGE OPTIONS ---")
            for number, (name, _) in enumerate(menus, 1):
                print(f"{number}. {name}")
            print("7. Leave village")
            value = input("Village > ").strip().lower()
        else:
            name, rows = menus[selected]
            print("\n--- " + name.upper() + " ---")
            for number, (_, label) in enumerate(rows, 1):
                print(f"{number}. {label}")
            print("0. Back to village categories")
            value = input("Village [" + name + "] > ").strip().lower()
        # Existing sidebar and old clients can address an action directly.
        if value.startswith("v:"):
            action = value[2:]
            if (
                action in ("save", "note", "tags")
                or action.isdigit()
                and int(action) in available
            ):
                return action, selected
            print("That service is not available in this village.")
            continue
        if value in ("save", "note", "tags"):
            return value, selected
        if not value.isdigit():
            print("Choose a listed number.")
            continue
        number = int(value)
        if number >= 8 and number in available:
            return value, selected
        if selected is None:
            if number in (0, 7):
                return "7", None
            if 1 <= number <= len(menus):
                selected = number - 1
        elif number == 0:
            selected = None
        elif 1 <= number <= len(menus[selected][1]):
            return str(menus[selected][1][number - 1][0]), selected
        else:
            print("Choose a listed number, or 0 to return.")
