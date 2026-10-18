"""Follow-ups for journal choices, reliable rumours and Source restoration."""

from copy import deepcopy
import data
import original_ui as ui
from expansion_state import state, pay, choose


def menu(game):
    p = game.player
    s = state(p)
    f = s["field"]
    while True:
        c = choose(
            "RUMOURS & SOURCE RESTORATION",
            [
                "Buy a travelling informant’s lead (10 souls)",
                "Follow a recorded rumour",
                "Craft a portable stabiliser (2 Source fragments + 100 souls)",
                "Stabilise a regional anomaly: staged restoration",
                "Review optional story consequences",
            ],
        )
        if c is None:
            return
        if c == 0:
            if not pay(p, 10):
                print("Need ten souls.")
                continue
            entries = data.REGION_STRUCTURES.get(p["region"], [])
            if not entries:
                continue
            target = game.random.choice(entries)["name"]
            reputation = (
                ui.village
                and __import__("village_life").state(p, ui.village).get("reputation", 0)
            ) or 0
            reliable = game.random.random() < min(0.95, 0.65 + reputation * 0.03)
            f.setdefault("leads", []).append(
                dict(
                    region=p["region"],
                    target=target,
                    reliable=reliable,
                    accepted=p.get("wander_count", 0),
                    verified=False,
                )
            )
            print(
                "The informant describes "
                + target
                + ". Confidence "
                + str(min(95, 65 + reputation * 3))
                + "%. Scout twice before following the lead; directions can be mistaken."
            )
        elif c == 1:
            leads = f.get("leads", [])
            index = choose(
                "RECORDED LEADS",
                [
                    x["target"]
                    + " · "
                    + ("verified" if x["verified"] else "unverified")
                    for x in leads
                ],
            )
            if index is None:
                continue
            lead = leads[index]
            if lead["verified"]:
                print("This lead is already resolved.")
                continue
            if (
                p["region"] != lead["region"]
                or p.get("wander_count", 0) - lead["accepted"] < 2
            ):
                print("Reach the region and scout twice first.")
                continue
            lead["verified"] = True
            if lead["reliable"]:
                found = p.setdefault("discovered_structures", {}).setdefault(
                    p["region"], []
                )
                if lead["target"] not in found:
                    found.append(lead["target"])
                print("The lead was accurate. The ordinary landmark is now mapped.")
            else:
                print(
                    "The directions were mistaken. Your notebook records the unreliable report."
                )
        elif c == 2:
            source = p.setdefault("source_story", {})
            fragments = source.get("fragments", 0)
            if (
                not source.get("season_one_complete")
                or fragments < 2
                or not pay(p, 100)
            ):
                print(
                    "Need postgame access, two ordinary Source fragments and 100 souls. Protected broken-core finds are not used."
                )
                continue
            source["fragments"] -= 2
            p["inventory"].append(dict(name="Core Stabiliser", value=150))
            print("Portable stabiliser assembled from ordinary Source fragments.")
        elif c == 3:
            if not p.get("source_story", {}).get("season_one_complete"):
                print("Finish the Dreamscape invasion first.")
                continue
            anomaly = f.setdefault("restoration_anomalies", {}).setdefault(
                p["region"], dict(stage=0)
            )
            if anomaly["stage"] == 0:
                anomaly["stage"] = 1
                anomaly["started"] = p.get("wander_count", 0)
                print(
                    "You survey the local anomaly. Scout two more times and bring two Stone."
                )
            elif anomaly["stage"] == 1:
                if p.get("wander_count", 0) - anomaly["started"] < 2 or not pay(
                    p, materials={"Stone": 2}
                ):
                    print("Scout twice and bring two Stone.")
                    continue
                anomaly["stage"] = 2
                print("The braces are ready. Choose a restoration outcome next.")
            elif anomaly["stage"] == 2:
                choice = choose(
                    "RESTORATION",
                    [
                        "Return the current to the region: +3 public trust",
                        "Channel a small fragment safely: +2 ordinary Source fragments",
                    ],
                )
                if choice is None:
                    continue
                if choice == 0:
                    s["relationships"]["public_trust"] = (
                        s["relationships"].get("public_trust", 0) + 3
                    )
                else:
                    p["source_story"]["fragments"] = (
                        p["source_story"].get("fragments", 0) + 2
                    )
                anomaly.update(stage=3, choice=choice)
                print(
                    "Anomaly stabilised. Its choice is recorded for future expeditions."
                )
            else:
                print("This regional anomaly is restored.")
        elif c == 4:
            for key, q in s["quests"].items():
                if q.get("complete"):
                    print(
                        key
                        + ": "
                        + q.get("ending", "")
                        + " · "
                        + str(q.get("choices", []))
                    )
