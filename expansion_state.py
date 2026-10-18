"""Versioned, JSON-only progress shared by the Soules expansion systems."""

from copy import deepcopy
import math
import uuid


def state(player):
    current = player.setdefault("expansion", {})
    current.setdefault("version", 1)
    current.setdefault("character_id", uuid.uuid4().hex)
    for key in (
        "quests",
        "projects",
        "professions",
        "field",
        "magic",
        "relationships",
        "season_three",
        "statistics",
        "activities",
        "features",
        "notes",
    ):
        current.setdefault(key, {})
    return current


def count(player, key, amount=1):
    stats = state(player)["statistics"]
    stats[key] = stats.get(key, 0) + amount
    return stats[key]


def mark(player, feature, detail=True):
    state(player)["features"][str(feature)] = detail


def number(prompt, length):
    try:
        selected = int(input(prompt)) - 1
    except ValueError:
        return None
    return selected if 0 <= selected < length else None


def choose(title, rows):
    print("\n--- " + title + " ---")
    for index, row in enumerate(rows, 1):
        print(f"{index}. {row}")
    print("0. Back")
    return number("Choice > ", len(rows))


def pay(player, gold=0, materials=None, ingredients=None):
    from collections import Counter

    materials = materials or {}
    ingredients = Counter(ingredients or [])
    if (
        state(player).get("systems", {}).get("mode", {}).get("id") == "budget_run"
        and gold > 0
    ):
        return False
    if (
        player["gold"] < gold
        or any(
            player.get("building_materials", {}).get(k, 0) < n
            for k, n in materials.items()
        )
        or any(
            player.get("ingredients", []).count(k) < n for k, n in ingredients.items()
        )
    ):
        return False
    player["gold"] -= gold
    for name, amount in materials.items():
        player["building_materials"][name] -= amount
    for name, amount in ingredients.items():
        for _ in range(amount):
            player["ingredients"].remove(name)
    count(player, "souls_spent", gold)
    count(player, "building_materials_spent", sum(materials.values()))
    count(player, "ingredients_spent", sum(ingredients.values()))
    return True


def validate(value, system_record=True):
    nodes = 0

    def walk(item, depth=0):
        nonlocal nodes
        nodes += 1
        if nodes > 75000 or depth > 14:
            raise ValueError("Expansion save exceeds its limits.")
        if item is None or type(item) is bool:
            return
        if type(item) in (int, float):
            if not math.isfinite(item) or abs(item) > 10**12:
                raise ValueError("Invalid expansion statistic.")
        elif isinstance(item, str):
            if len(item) > 10000:
                raise ValueError("Expansion text too long.")
        elif isinstance(item, list):
            if len(item) > 5000:
                raise ValueError("Expansion collection too large.")
            for child in item:
                walk(child, depth + 1)
        elif isinstance(item, dict):
            if len(item) > 3000 or any(
                not isinstance(k, str) or len(k) > 200 for k in item
            ):
                raise ValueError("Invalid expansion record.")
            for child in item.values():
                walk(child, depth + 1)
        else:
            raise ValueError("Invalid expansion save value.")

    if not isinstance(value, dict):
        raise ValueError("Invalid expansion progress.")
    walk(value)
    if not system_record:
        return
    for key in (
        "quests",
        "projects",
        "professions",
        "field",
        "magic",
        "relationships",
        "season_three",
        "statistics",
        "activities",
        "features",
        "notes",
        "systems",
        "food",
        "daily",
    ):
        if key in value and not isinstance(value[key], dict):
            raise ValueError("Invalid expansion system record: " + key)
    if "daily" in value:
        from datetime import date

        daily = value["daily"]
        if daily.get("last_claim"):
            try:
                date.fromisoformat(daily["last_claim"])
            except (TypeError, ValueError):
                raise ValueError("Invalid daily claim date.")
        for key in ("streak", "total_claims"):
            if key in daily and (type(daily[key]) is not int or daily[key] < 0):
                raise ValueError("Invalid daily claim counter.")

    for key, quest in value.get("quests", {}).items():
        if key not in {str(i) for i in range(1, 21)} or not isinstance(quest, dict):
            raise ValueError("Invalid addon quest record.")
        if (
            type(quest.get("stage")) is not int
            or not 0 <= quest["stage"] <= 3
            or type(quest.get("complete")) is not bool
        ):
            raise ValueError("Invalid addon quest stage.")
        if (
            not isinstance(quest.get("visited", []), list)
            or len(quest.get("visited", [])) > 3
        ):
            raise ValueError("Invalid caravan route.")
    campaign = value.get("season_three", {})
    if "stage" in campaign and (
        type(campaign["stage"]) is not int or not 0 <= campaign["stage"] <= 8
    ):
        raise ValueError("Invalid Season Three stage.")
    blends = value.get("food", {}).get("blends", {})
    if not isinstance(blends, dict):
        raise ValueError("Invalid potion blend collection.")
    for key, blend in blends.items():
        if (
            not isinstance(blend, dict)
            or type(blend.get("heal")) is not int
            or not 1 <= blend["heal"] <= 120
        ):
            raise ValueError("Invalid potion blend.")
