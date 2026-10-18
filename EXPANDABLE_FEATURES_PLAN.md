# The five foundations and their implemented follow-ups

The formerly deferred first and later expansions now have player actions in the Adventures hub.

| Foundation | Added follow-ups | Code |
| --- | --- | --- |
| Story journal | Twenty authored side stories with costs, evidence and recorded resolutions; public trust affects the Season Three Warden | `addon_quests.py`, `season_three.py` |
| Keeper conversations | Named village work/family/gift conversations, friendship ranks, mentor memory, companion dialogue and reunions | `relationship_addons.py` |
| Professions | Specialties, textile patterns, toolkit durability, apprenticeship/batches, mastery trials and signatures | `artisan_addons.py`, `village_jobs.py` |
| Rumours | Paid informants, confidence affected by reputation, two-scout verification, false leads and map notes | `foundation_expansions.py`, `journal_addons.py` |
| Source anomalies | Survey, brace construction and a restoration choice; ordinary fragment stabiliser recipe and village community projects | `foundation_expansions.py`, `community_addons.py` |

These extend the existing six professions and journal rather than replacing them. Hidden clans remain rare, permanent runes stay permanent, stocks and sites have exploration-based limits, and menus never generate free work shifts. Protected broken-core fragments are studied rather than consumed. See IMPLEMENTATION_CHECKLIST.md for the wider 100-addon catalogue.
