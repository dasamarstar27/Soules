"""Inventory display sorting and opt-in sales of identical spare equipment."""

import json

SORTS = {"1": "name", "2": "atk", "3": "def", "4": "element", "5": "value"}


def sale_value(item, kind):
    if kind == "weapons":
        return max(0, int(item.get("atk", 0) * 5))
    if kind == "armours":
        return max(0, int(item.get("def", 0) * 5))
    if kind == "staffs":
        return max(0, int(item.get("power", 0) * 5))
    if kind == "runes":
        return 50
    return max(0, int(item.get("value", 0)))


def item_element(item):
    if item.get("element"):
        return item["element"]
    return {
        "fire_weapon": "fire",
        "ice_weapon": "ice",
        "shock_weapon": "storm",
        "poison_weapon": "poison",
        "void_weapon": "void",
    }.get(item.get("effect"), "none")


def item_stat(item, key):
    value = item.get(key, item.get("power", 0) if key == "atk" else 0)
    effects = {
        "atk": (
            "atk_up",
            "massive_atk_up",
            "fire_weapon",
            "ice_weapon",
            "shock_weapon",
            "poison_weapon",
            "void_weapon",
        ),
        "def": ("def_up", "massive_def_up"),
    }
    if "turns" in item and item.get("effect") in effects.get(key, ()):
        value = item.get("value", 0)
    return float(value or 0)


def sort_items(items, primary="name", secondary=None, kind="inventory"):
    def stat(item, key):
        if key == "element":
            return str(item_element(item)).lower()
        if key == "name":
            return str(item.get("name", "")).lower()
        if key == "value":
            return -sale_value(item, kind)
        return -item_stat(item, key)

    keys = [primary] + ([secondary] if secondary and secondary != primary else []) + ["name"]
    return sorted(items, key=lambda item: tuple(stat(item, key) for key in keys))


def sell_duplicates(player, quiet=False):
    sold = 0
    gold = 0
    for key, equipped_key in [("weapons", "weapon"), ("armours", "armour"), ("staffs", None)]:
        bag = player.get(key, [])
        equipped = player.get(equipped_key) if equipped_key else None
        seen = set()
        kept_indices = set()
        ordered = sorted(enumerate(bag), key=lambda pair: (pair[1] is not equipped, pair[0]))
        for index, item in ordered:
            signature = json.dumps(item, sort_keys=True, ensure_ascii=True)
            protected = (
                item is equipped
                or item.get("name") in player.get("inventory_favourites", [])
                or bool(item.get("rune") or item.get("stored_runes") or item.get("elemental_core"))
            )
            if signature in seen and not protected:
                gold += sale_value(item, key)
                sold += 1
            else:
                kept_indices.add(index)
                seen.add(signature)
        player[key] = [item for index, item in enumerate(bag) if index in kept_indices]
    player["gold"] += gold
    if sold:
        print(f"Auto-sold {sold} identical spare equipment items for {gold} souls.")
    elif not quiet:
        print("No identical spare equipment to sell.")
    return sold, gold


def inventory_menu(game):
    p = game.player
    while True:
        primary = p.get("inventory_sort", "name")
        secondary = p.get("inventory_sort_secondary")
        print(
            f"\n===== INVENTORY · sorted by {primary}"
            + (f" then {secondary}" if secondary else "")
            + " ====="
        )
        sections = [
            ("Loot & food", "inventory", [x for x in p["inventory"] if "turns" not in x]),
            ("Scrolls", "inventory", [x for x in p["inventory"] if "turns" in x]),
            ("Weapons", "weapons", p["weapons"]),
            ("Armour", "armours", p["armours"]),
            ("Staffs", "staffs", p["staffs"]),
            ("Runes", "runes", p["runes"]),
            ("Ancient finds — protected for Season Three", "protected_relics",p.get("protected_relics",[])),
        ]
        for title, kind, items in sections:
            query = p.get("inventory_search", "").lower()
            items = [
                item
                for item in items
                if query in (json.dumps(item).lower() + " " + str(item_element(item)).lower())
            ]
            print(f"\n--- {title} ({len(items)}) ---")
            if not items:
                print("Empty")
            grouped = {}
            for item in sort_items(items, primary, secondary, kind):
                signature = json.dumps(item, sort_keys=True)
                if signature not in grouped:
                    grouped[signature] = [item, 0]
                grouped[signature][1] += 1
                if item is p.get("weapon") or item is p.get("armour"):
                    grouped[signature][0] = item
            for item, quantity in grouped.values():
                equipped = item is p.get("weapon") or item is p.get("armour")
                attack = item_stat(item, "atk")
                defense = item_stat(item, "def")
                print(
                    f"- {item['name']} ×{quantity}"
                    + (" ★" if item["name"] in p.get("inventory_favourites", []) else "")
                    + (f" | Element: {item_element(item)} | Protected · cannot sell / salvage" if kind=="protected_relics" else f" | ATK {attack} | DEF {defense} | Element: {item_element(item)} | Sell: {sale_value(item, kind)} souls")
                    + (" [EQUIPPED]" if equipped else "")
                )
        print("\nSort: 1 Name · 2 Attack/power · 3 Defence · 4 Element · 5 Sell value")
        print(
            f"6. Auto-sell identical spare equipment: {'ON' if p.get('auto_sell_duplicates') else 'OFF'}"
        )
        print(
            "7. Sell duplicate equipment now\n8. Favourite / unfavourite item\n9. Search inventory (blank clears)\n0. Back"
        )
        if p.get("inventory_search"):
            print("Search: " + p["inventory_search"])
        print(
            "Keeps one of each exact equipment variant and all equipped or bound/imbued gear. Runes, scrolls, food, potions and materials are kept."
        )
        choice = input("Inventory option > ").strip()
        if choice == "0":
            return
        if choice in SORTS:
            p["inventory_sort"] = SORTS[choice]
            print(
                "Optional second sort: 0 None · 1 Name · 2 Attack · 3 Defence · 4 Element · 5 Sell value"
            )
            p["inventory_sort_secondary"] = SORTS.get(input("Then sort by > ").strip())
        elif choice == "6":
            p["auto_sell_duplicates"] = not p.get("auto_sell_duplicates", False)
            if p["auto_sell_duplicates"]:
                sell_duplicates(p)
        elif choice == "7":
            sell_duplicates(p)
        elif choice == "9":
            p["inventory_search"] = input(
                "Find name, element or effect (blank shows all) > "
            ).strip()[:60]
        elif choice == "8":
            name = input("Exact item name to favourite / unfavourite > ").strip()
            matches = [
                item["name"]
                for _, _, bag in sections
                for item in bag
                if item["name"].lower() == name.lower()
            ]
            if not matches:
                print("No owned item matches that name.")
                continue
            name = matches[0]
            favourites = p.setdefault("inventory_favourites", [])
            if name in favourites:
                favourites.remove(name)
                print("Favourite removed.")
            else:
                favourites.append(name)
                print("Favourite saved. Auto-sell will keep this item type.")
