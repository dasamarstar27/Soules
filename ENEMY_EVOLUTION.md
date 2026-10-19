# Enemy evolution in V25.9

Thirty ordinary species each have four forms, starting at levels 1, 5, 10 and 15. Stage IV continues growing after level 15. Forms are selected from player level and region, never the contents or strength of the player's equipment. The catalogue is copied for encounters; saved weapons and player stats are not rewritten.

Example: Thorn Wolf family on Normal, before night/world-event modifiers:

| Player level | Form | HP | ATK | DEF | XP | Souls |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Thorn Wolf | 30 | 10 | 2 | 20 | 20 |
| 5 | Empowered Thorn Wolf | 72 | 20 | 5 | 30 | 28 |
| 10 | Corrupted Thorn Wolf | 135 | 32 | 9 | 45 | 40 |
| 15 | Apex Corrupted Thorn Wolf | 210 | 45 | 14 | 65 | 55 |
| 20 | Apex Corrupted Thorn Wolf | 294 | 50 | 16 | 75 | 60 |

Each family uses its own regional base stats. Level-1 attacks retain the old 5–15 range; evolved encounters above level 1 use 65–100% of scaled ATK before defence, dodge, status/stat modifiers and critical hits. The stored attack stat now affects actual damage. This patch scales stats and rewards; it does not add new status-proc rules to enemy effect tags.

Night adds its existing 15% stats and can create elites. World events apply their existing modifiers. Easy applies 25% less enemy HP and 40% less incoming direct strike damage once. Rewards continue through the existing world-event/skill/elite logic.

From level 10 the ordinary regional pool gives each species three slots and each existing mini-boss one slot: with the usual two/two roster, 75% ordinary species and 25% mini-bosses. Mini-bosses also grow with level. Creator's Realm retains its mini-boss-only fallback from level 10. Paid tracking of an ordinary species uses the same current-level form, so tracking cannot force a weaker level-1 copy.

These are ordinary wander and tracked-species changes. Regional guardians, scripted story bosses and custom quest encounters keep their separate balancing. The one-roll Normal/Easy encounter percentages and permanent rune rules are unchanged. No character-save migration is required; the next applicable encounter uses the new form.

Validation includes every stage boundary, growth through level 30 for all species, 120 dictionary forms, copied catalogues, mini-boss proportions, real scaled attack damage, reward delivery, Easy/night maximum-health consistency and independence from carried weapon power. Browser checks exercise all four milestones in both difficulties and the Evolutions tab.
