# Season Three: Beyond the Broken Bridge

Implemented in `season_three.py`, using the shared tactical combat and expansion state. Entry requires the Season Two stabiliser repair, 50 souls, two Timber and two carried foods. This is a text campaign with named expedition areas within the optional Creator’s Realm, rather than additional main-region unlock gates.

1. Travel by a controlled expedition to the Written Shore and meet Sera, an exiled archivist.
2. Tune two protected broken-core fragments to the ward. The fragments remain in your collection.
3. Defeat the Margin Warden. Public trust earned through earlier choices can reduce its attack.
4. Enter the Archive of Beginnings. The same hidden antagonist is connected to the reopened Dreamscape rift and the instructions behind the Season Two sabotage. **Only here** is its objective revealed: destroy the male Creator and seize his Book and Pen of Creation. Its underlying motive and personal identity remain concealed. The Creator is capable of both kindness and cruelty.
5. Choose the village council, archivists or clan wardens as your alliance. All four keeper testimonies are required; the cores remain in their villages.
6. Prepare one of two paired-element recipes: Flame + Ice → Dawn-and-Dusk Blade, or Nature + Light → Living Radiance Staff. Each costs two normal runes and 75 souls. Both component abilities work and the inscription is permanent.
7. Stop the Hidden Hand in the Hall of Creation.
8. Choose custody: the Creator under witnessed limits, a village council, or a seal maintained by the clans. Sera preserves the records and completes her quest. The optional two-enemy Unwritten Vault opens afterward, with one reward per exploration cycle.

Chapter One still ends at the Dreamscape King after all main regions are unlocked. Season Two still ends at the repaired stabiliser after the five-month rebuilding interlude. Neither requires defeating the Creator. No villain motive has been invented as settled canon.

Validation: the complete progression, gates, protected fragments/cores, two crafting inputs, battle transitions and ending are exercised in `tests/test_expansion_systems.py`; paired staff permanence has a separate real-effect regression check.
