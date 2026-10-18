"""One claim per local calendar date, using the creator's Malaysian timezone."""

from datetime import datetime, date, timedelta, timezone
import data
from expansion_state import state


def today():
    return datetime.now(timezone(timedelta(hours=8))).date()


def claim(player, current=None):
    current = current or today()
    record = state(player).setdefault("daily", {})
    last = (
        date.fromisoformat(record["last_claim"]) if record.get("last_claim") else None
    )
    if last and current <= last:
        return (
            False,
            "Already claimed for this date. Your next reward is available on a later calendar day.",
        )
    streak = record.get("streak", 0) + 1 if last == current - timedelta(days=1) else 1
    # Original milestone rewards plus a small reward on every other day.
    reward = data.LOGIN_BONUSES.get("day_" + str(streak), {"gold": 30})
    player["gold"] += reward.get("gold", 0)
    supplies = record.setdefault("materials", {})
    for name, amount in reward.get("materials", {}).items():
        supplies[name] = supplies.get(name, 0) + amount
    cosmetics = player.setdefault("cosmetics", {})
    cosmetics["currency"] = cosmetics.get("currency", 0) + reward.get(
        "cosmetic_currency", 0
    )
    if reward.get("legendary_core"):
        player.setdefault("cores", []).extend(
            ["Dragon Core"] * reward["legendary_core"]
        )
    record.update(
        last_claim=current.isoformat(),
        streak=streak,
        total_claims=record.get("total_claims", 0) + 1,
    )
    player["login_streak"] = streak
    return (
        True,
        f"Day {streak} claimed: {reward}. A missed calendar day resets the consecutive streak. Saved characters track their own claims.",
    )


def menu(game):
    record = state(game.player).get("daily", {})
    print(
        f"\n--- DAILY LOGIN · {today()} · MALAYSIAN TIME ---\nStreak: {record.get('streak', 0)} · Last claim: {record.get('last_claim', 'never')}"
    )
    for day, reward in data.LOGIN_BONUSES.items():
        print(day.replace("_", " ") + ": " + str(reward))
    print(
        "One claim per character per calendar day. This single-player reward uses your computer’s clock; it is not a competitive server reward."
    )
    if input("Claim today’s reward? (y/n) > ").strip().lower() == "y":
        print(claim(game.player)[1])
