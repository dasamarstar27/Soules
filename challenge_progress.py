"""Calendar challenges driven by real kills, crafting, collection and XP."""

from datetime import timedelta
import data
from daily_rewards import today


def initialise(player):
    current = today()
    week = current - timedelta(days=current.weekday())
    for period, stamp, entries in [
        ("daily", current.isoformat(), data.DAILY_CHALLENGES),
        ("weekly", week.isoformat(), data.WEEKLY_CHALLENGES),
    ]:
        field = "last_" + period + "_reset"
        if not player.get(field) or player[field] < stamp:
            player[field] = stamp
            player[period + "_challenges"] = {
                q["id"]: dict(progress=0, completed=False) for q in entries
            }
        else:
            for q in entries:
                player.setdefault(period + "_challenges", {}).setdefault(
                    q["id"], dict(progress=0, completed=False)
                )


def reward(player, challenge):
    player["gold"] += challenge.get("reward_gold", 0)
    for material, amount in challenge.get("reward_materials", {}).items():
        if material in ("metal_scraps", "crafting_shard"):
            bag = player.setdefault("building_materials", {})
            bag["Iron fittings"] = bag.get("Iron fittings", 0) + amount
        elif material in ("cloth_scraps", "premium_cloth"):
            player.setdefault("cloths", []).extend(
                [list(data.CLOTHS)[0 if material == "cloth_scraps" else -1]] * amount
            )
        elif material == "essence_dust":
            player.setdefault("ingredients", []).extend(["Dew Blossom"] * amount)
        elif material in ("rare_core", "legendary_core"):
            player.setdefault("cores", []).extend(["Dragon Core"] * amount)
        else:
            cosmetics = player.setdefault("cosmetics", {})
            cosmetics["currency"] = cosmetics.get("currency", 0) + 10 * amount
    print(
        "Challenge complete: "
        + challenge["name"]
        + " · "
        + str(challenge.get("reward_gold", 0))
        + " souls; reward supplies delivered as usable materials, herbs or cosmetic currency."
    )


def update(player, kind, amount=1):
    initialise(player)
    for period, entries in [
        ("daily", data.DAILY_CHALLENGES),
        ("weekly", data.WEEKLY_CHALLENGES),
    ]:
        for quest in entries:
            if quest["type"] != kind:
                continue
            entry = player[period + "_challenges"][quest["id"]]
            if entry["completed"]:
                continue
            if kind == "region_boss_clear":
                regions = entry.setdefault("regions", [])
                if amount not in regions:
                    regions.append(amount)
                entry["progress"] = len(regions)
            elif kind == "level_reach":
                entry["progress"] = max(entry["progress"], amount)
            else:
                entry["progress"] += amount
            if entry["progress"] >= quest["target"]:
                entry["completed"] = True
                reward(player, quest)


def observe_inventory(player):
    from expansion_state import state

    activities = state(player)["activities"]
    count = len(player.get("inventory", []))
    previous = activities.get("observed_inventory")
    activities["observed_inventory"] = count
    if previous is not None and count > previous:
        update(player, "item_collect", count - previous)


def validate(player):
    from datetime import date

    for period in ("daily", "weekly"):
        field = "last_" + period + "_reset"
        if field in player:
            try:
                date.fromisoformat(player[field])
            except (TypeError, ValueError):
                raise ValueError("Invalid challenge calendar.")
        entries = player.get(period + "_challenges", {})
        if not isinstance(entries, dict) or len(entries) > 20:
            raise ValueError("Invalid challenge records.")
        for entry in entries.values():
            if (
                not isinstance(entry, dict)
                or type(entry.get("progress")) not in (int, float)
                or not 0 <= entry["progress"] <= 10**9
                or type(entry.get("completed")) is not bool
            ):
                raise ValueError("Invalid challenge progress.")
