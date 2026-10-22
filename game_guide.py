"""Player-facing guide for the original text edition; no secret commands."""

SECTIONS = [
    ("resource-sites", "Quarries and timber yards", [
        "Each quarry trip gives 2 Stone for village building plus 1 regional metal for forging. Each timber-yard trip gives 2 Timber for building plus 1 regional wood for crafting. Ironpeak’s dwarven quarry gives Stone and Titanium; Bromm’s metal shop is separate.",
        "Supplies are finite: each named site can be worked once per 20-wander cycle. Find more sites or return after the next cycle. Building supplies appear under village construction; metals and woods appear in crafting inventory. Village building menus also let you convert spare crafting materials into building supplies."
    ]),
    (
        "first-steps",
        "Start here",
        [
            "Press Play, name your character and choose a class. New characters wake in Old Village with only a Rusty Sword: no runes, potions or spare equipment. Classes change your starting strengths and combat skill.",
            "Speak to Elian with village option 18. He is your mentor, the elderly grandson of Miren, one of the warriors who stabilised the ancient temple. Option 14 talks to the village keeper. Leave with 7, choose Explore, then Wander to begin your journey.",
            "Try this first: talk to Elian, read the keeper’s warning, save a village note, leave, save your character, then wander. Watch your health and hunger before challenging a guardian.",
        ],
    ),
    (
        "controls",
        "Menus, questions and keyboard controls",
        [
            "The main text menu has seven categories. Choose 1 for Explore or 2 for Inventory & Equip. A category opens its own numbered secondary menu; its numbers are local, so always read the current list. Tabs open the same categories.",
            "The highlighted question belongs to the story panel, directly below the journal. Type your response in the answer box and press Enter, or use a numbered button. Some original submenus start counting at 0; follow their displayed numbers rather than assuming 0 always means Back.",
            "Back to category safely leaves most submenus. During a fight you must use the combat Run option; Back cannot escape an enemy. Escape returns toward the category menu when allowed. / focuses the answer box, and up/down arrows browse your command history.",
            "Attacks, village menus and other options follow automatically when you are already near the bottom. Only very long blocks keep your reading position. Scrolling up to read earlier entries pauses automatic following. Latest jumps to the newest text when you choose; Recall last fills the previous command without sending it. Copy journal copies the visible history, and Clear journal clears its display. Compact sidebar reduces the status panel. The sidebar itself never follows updates automatically: use its manual scrollbar to read any part.",
        ],
    ),
    (
        "easy-reading",
        "Difficulty, Easy reading and read-aloud",
        [
            "Choose Normal for the standard combat balance or Easy for beginners. Easy enemies have 25% less health and their direct attacks deal 40% less damage. Starting items, rewards and story are unchanged. Easy has fewer monster outcomes and more gathering; the Wandering dictionary shows both tables. Status effects and hazards still hurt, and death still ends the character. Choose difficulty when creating a character or change it in Settings at a safe category/village menu. The choice travels with your save; older saves use Normal. Easy reading and Tablet mode change the controls independently of difficulty.",
            "The Easy reading switch in the top bar uses large clear text, spacious buttons, stronger contrast and a plain background while keeping your chosen region colours. A− and A+ adjust its separate 18–28 pixel text size. Turning the switch off restores the standard appearance; these settings stay in this browser.",
            "Easy reading and Tablet mode use buttons instead of typing. Choose a preset character name or village note, use quantity buttons when buying, and tap labelled answers for village, shop, combat and activity choices. Save slots use your character’s name automatically. Turn both modes off to use custom typed names, notes or search text in the standard interface. The game waits for your choice; the presentation mode does not change difficulty, costs or rules.",
            "Read latest aloud speaks only on request. Select text first to read that passage, or press it without a selection to hear the latest output and question. Stop reading stops speech; new output also stops the old passage. Narration language, browser voices and reading speed are in Customise. Choose Hindi or press हिंदी में सुनें for Hindi narration. Install a Hindi voice first. Supported browsers translate automatically; otherwise translate the page to Hindi using the browser and select the translated passage. Hindi setup help explains both steps. A Hindi voice alone does not translate English. Device/browser support and installed voices vary.",
            "Explain game words opens a short glossary for health, mana, attack, defence, experience, money, runes, status effects, shifts and saves. Save / Load gives direct access to your save slots while Easy reading is on. Saving is still limited to safe category menus; export a backup to move a character between devices.",
        ],
    ),
    (
        "new-quality-controls",
        "Potions, quick equipment, raids, companions and tablets",
        [
            "Inventory & Equip → Use carried potions drinks a bottle outside combat. Inventory's detailed list also has option 10 for potions. Healing at full health keeps the bottle. Blending two healing potions shows BREW COMPLETE, the new bottle and its healing amount, then waits for Enter before returning to the village.",
            "The equipment sidebar has a weapon selector and Equip button, plus a potion selector and Drink button. They work at category and outer village menus. Battles and purchases use their own controls. The sidebar keeps its manual scrollbar and never automatically follows updates.",
            "Food, scrolls and saleable loot are separate inventory groups. Sell ALL loot only sells trinkets; it preserves food and scrolls. Scroll sales have their own action. Buying takeaway food asks for a positive quantity and charges the full total within the shop's stock.",
            "At local reputation 10, an inn offers one free rest per 20-wander cycle; the quote shows zero cost. Existing reputation food discounts still apply. Village workers now advance one shift per Wander anywhere, and two shifts on paid or reputation-earned inn rest.",
            "Three companions travel and assist in fights. You can recruit more: extras stay in Old Village. Visit Old Village option 26, or Companion care → sanctuary, to send a party member home and bring another out. Home companions do not lose hunger while you wander or earn combat evolution XP remotely.",
            "Settlement raids have 3 attackers at levels 1–8, 4 at 9–16 and 5 from 17 onward. Assign each available worker using the visual role cards, or type the displayed numbers. Cards show level, role effects, current assignments and repair costs. All surviving monsters may act each round. The Season One Woods quest has three waves with 2, 3 and 4 monsters; use Change target to select an opponent.",
            "Tablet mode in the top bar gives touch-friendly buttons, readable selectors and a tablet layout. It enables automatically on detected tablet-size touch devices and can be toggled manually. Colours, saves and text controls still work. An iPad requires an accessible running server; GitHub downloads contain source code.",
            "To play on an iPad or Android tablet with every laptop switched off, open the game’s deployed online address. Tablet mode changes controls; the computer ZIP cannot run Python on an iPad. The owner can deploy the repository through its Render button once, then share the HTTPS game link. The tablet needs Internet. Add that link to the Home Screen for easy opening. Keep the same browser/address for saves and export backups; cloud accounts and automatic cross-device saves are not included.",
            "The version badge in the top corner shows the running release. Press it for older version downloads, checkpoint export and downgrade steps. On a computer, extract the older folder and close the current server before launching it. A hosted game needs the website owner to roll back its server through the hosting dashboard; downloading a ZIP cannot switch a shared website. Newer saves may not work in older versions, so keep untouched exported backups.",
        ],
    ),
    (
        "survival",
        "Health, hunger, mana and death",
        [
            "Health reaching zero ends this character’s run. The active autosave clears and new character creation opens. Separately named save slots are retained. Death does not restore your old character automatically.",
            "Starting a wander at full hunger (100/100) restores up to 3 HP before hunger is spent. Your hunger then falls by 5 each wander, or 1 with the hunger resistance skill. Below 30 you receive a warning; at zero each further wander deals 10 damage. Eat carried food through Inventory & Equip, buy takeaway food, or use a village restaurant.",
            "Food restores the amount printed beside it. A restaurant meal is eaten immediately and also heals; takeaway food goes into your inventory and can be saved for a companion. Inns exchange souls for local-quality healing. Check prices and stock before paying.",
            "Mana pays for elemental arts. Souls, also called gold in some older menus, buy goods, upgrades and services. Carrying an item does not automatically equip or consume it.",
        ],
    ),
    (
        "exploration",
        "Wandering, travelling and discovery",
        [
            "Wander advances time, weather, hunger, companion hunger and local resource cycles. Regular encounters can be monsters, merchants, companions or peaceful paths. Themed loot respects its home regions: Sea Pearls, for example, drop only at Sunken Coast, while common trinkets can be found anywhere. Night makes monsters tougher and affects some encounters; ordinary enemies have four evolution stages at player levels 1, 5, 10 and 15. Their HP, ATK and DEF also grow between stages and after level 15. From level 10, occasional regional mini-bosses join the pool. Their direct hits use their scaled attack instead of a flat damage roll. Enemy cards show stage, level, ATK and DEF; Dictionary → Evolutions lists every chain. Equipment does not set enemy strength. Easy keeps its existing health/damage reductions.",
            "One weighted main roll chooses the wander result. Normal: 51% monster, 20% gathering, 10% structure, 10% event, 5% merchant, 1% companion, 3% peaceful. Easy: 36%, 30%, 12%, 12%, 6%, 1%, 3% respectively. Gathering gives one ingredient or one building supply, then rolls 70% ordinary monster / 30% new ordinary structure. You keep the item; this follow-up cannot roll more gathering or peaceful. Hidden-clan and bounty ranges are included within structures and monsters, not separate rolls. Already known ordinary structure tickets become monsters. With ordinary discoveries left, gathering follow-ups raise combat totals to 65% Normal / 57% Easy and structure totals to 16% / 21%, before special-event fights. Weather, survival, shifts and scheduled story scenes still update.",
            "Travel lists unlocked regions. Defeating the current main-region guardian unlocks the next region. Structures lists discovered local places. A watch post can reveal an ordinary village route without revealing hidden elemental villages.",
            "The Village Directory lists discovered villages across regions and allows repeat visits. The world map shows unlocked progression. The optional Creator’s Realm has its own access conditions and is not necessary for the original ending.",
        ],
    ),
    (
        "combat",
        "Combat and preparation",
        [
            "Read the large combat question in the story panel. The original fight choices include Attack, Scroll, Staff, Run, your class skill, Companion, Potion, Rune and Elemental art when available. Each choice has its own follow-up question.",
            "Equip a weapon and armour before fighting. Scrolls, loose runes, potions and staff charges are limited supplies. Skills have cooldowns; elemental arts cost mana. An invalid or cancelled choice may return to the current fight question, so read the text before acting again.",
            "Ordinary fights allow Run unless an effect blocks fleeing. Guardians must be defeated. Effects can damage over time, prevent actions, change damage or defence, heal, shield or provide other abilities. The sidebar shows active effects and remaining duration; Dictionary → Effects explains their mechanics.",
            "Battle companions need at least 30 hunger. Juveniles offer a weak strike; stage 1 unlocks elemental support and special moves. Their support follows attacks; their special move can be used once per fight. A final evolution improves passive support. Peaceful companion species stay peaceful.",
        ],
    ),
    (
        "inventory",
        "Inventory, equipment and safe duplicate selling",
        [
            "Inventory displays equipment, food and loot, runes, potions, ingredients and materials. Sort by name, attack/power, defence, element or sell value, with an optional second sort. Search and favourites help you find and protect useful items.",
            "Equip Weapon and Equip Armour change what your character wears. Owning better gear is not enough: equip it. Weapon-bound runes stay attached permanently.",
            "Auto-sell duplicates starts off. Enabling it sells identical spare weapons, armour and staffs at category menus, retaining an exact variant and protecting equipped, favourite, bound and imbued equipment. Consumables and crafting supplies are kept. Manual bulk sales are separate choices: read them before confirming.",
            "Protected ancient finds have their own collection and cannot be sold, salvaged or used for crafting. They are reserved for later story content.",
        ],
    ),
    (
        "runes",
        "Runes, effects and all two-rune fusions",
        [
            "A loose rune is used once when cast. Binding it to a weapon consumes the loose rune and creates a permanent attachment that attacks cannot spend, remove or replace. Staff uses and charges remain finite.",
            "Fuse exactly two normal runes. All 8,778 unordered pairs of the 132 normal types are supported, including two of the same type when you own two copies. A fusion cannot be used as an ingredient for another fusion in this edition.",
            "A fusion keeps its component effects and gains a pair synergy. Dictionary → Fusions lets you choose two types and preview their abilities before spending them. Named recipes may add additional compatible effects. Pair synergies use shared mechanical families rather than 8,778 separately hand-written combat systems.",
            "Rage and Berserk, for example, increase attack and reduce defence for their listed turns. Effects expire; they do not permanently add their temporary bonuses to your base statistics.",
        ],
    ),
    (
        "clan-defence-and-forges",
        "Clan visits, Woods defence and elemental forging",
        [
            "Discovered elemental clans remain in Explore → Structures. Their automatic background matches fire, ice, storm or nature; fixed and custom colours remain your choice. History, shops and services return to the clan menu. Choose 4 to leave. Option 3 opens the traveller shop in Season One and the larger halls in Season Two; prices, stock and item stats are shown together.",
            "Elian's fourth conversation choice, Story journal 9 or clan option 8 opens Protect Whispering Woods. Prepare 2 Timber and 1 Stone in Whispering Woods, repel three attacks, then report to Elian in Old Village. Discovered clans may send volunteers to defend, gather, treat or repair; finding rare clans is optional. Clan option 7 opens settlement raid defence and worker assignments. Clan cores and keepers stay home.",
            "Ironpeak Mountains Quarry is home to Bromm's dwarven bulk-metal shop. Buy a positive quantity within its finite stock. Eight metal types are available initially, fourteen at level 10 and twenty at level 20 or in Season Two. Stocks refresh every 20 wanders.",
            "Village option 25 opens regional specialist traders: herbs and woods in Whispering Woods, cloth in Tundra, runes in Crystal Spire, food on Sunken Coast, hides in Infernal Depths and weapon cores in Riftlands. These are different people; only the Ironpeak quarry traders are dwarves. Riftlands shipments have eight of every ordinary core and a 25% chance of one rare charged core. Opening a menu or loading a save never rerolls it.",
            "Crafting hub C, specialist shop C or Crimson Forge option 5 sacrifices one loose normal rune or one matching-energy fusion into one ordinary weapon core. A fusion is accepted only when BOTH original normal components belong to that core’s listed energy family. A fire/water fusion cannot charge a Phoenix Core; two fire-family components can. The fusion is consumed once and its component abilities and synergy remain in the forged weapon. The charging menu lists compatibility limits and only offers compatible carried runes. Hot cores reject water/tide and ice families; Glacier and Ocean reject hot runes; dark cores reject light families and Celestial rejects dark families. Nature rejects death, necrotic and inferno; Blight rejects life and harmony. Phoenix cannot accept Water. Other normal elements remain allowed; normal rune fusion recipes keep their existing rules.",
            "Enter Crimson Forge through Travel → F or discovered Structures in Crimson Depths. Win its three infestation fights, with time to rest between them. Only its reclaimed hearth can spend a charged core plus one metal and one wood on a named elemental weapon. Each hit activates its permanent native core ability and the sacrificed rune ability. Ordinary village core forging stays physical; protected clan cores and broken-core relics cannot be spent. Charged cores appear in Inventory and forge weapons are protected from automatic duplicate sales and salvage.",
        ],
    ),
    (
        "crafting",
        "Crafting benches and professions",
        [
            "Enter a discovered village before using its crafting hub. Villages have different available benches, starting levels and quality. Their numbered menus show only facilities that exist there; for example, farm harvesting and blacksmith choices are absent where those services do not exist. Familiar action numbers stay the same, so gaps are normal. Missing benches cannot be used until you construct them: village option 17 opens Build / upgrade village facilities. The sidebar lists each local service and its current benefit.",
            "Build a missing ordinary facility for 5 Timber, 4 Stone, 2 Iron fittings and 100 souls. It starts at Level 1 and becomes usable immediately, including its workers and community projects. Buildings are local and persist when you leave or import a save. Upgrade any existing facility, including farms, to Level 5. Higher farm quality yields more regional ingredients per harvest; upgrading never resets the once-per-20-wander harvest limit. Shop capacity increases at the next restock.",
            "A forge makes weapons, a loom makes armour, an enchantment tower makes staffs, an alchemy lab brews potions, and a disenchantry salvages eligible gear. Blacksmith upgrades improve carried equipment for a quoted price. Rune binding and fusion are under Upgrades & Runes.",
            "Workshop quality changes results: weapon attack, armour defence, staff power, ingredient preservation, salvage recovery and trading discounts. Successful crafting develops professions; browsing menus grants no crafting experience. Story & Lore includes your profession progress.",
            "Only elemental villages offer an Imbuing Temple. The separate Source Temple stands in the Riftlands. Ordinary villages do not gain a temple through automatic development or community projects.",
        ],
    ),
    (
        "alchemy",
        "Ingredients, brewing and potion supplies",
        [
            "Gather regional ingredients while wandering or harvest a ready village farm. Use an alchemy lab to mix two ingredients; using the same ingredient requires two copies. Known combinations produce potions, while an unknown mixture can fail and hurt you.",
            "A successful brew can be used immediately or bottled. Skilled laboratories and profession ranks can preserve an ingredient on success. Shops stock a limited selection of ready-made potions; stock is not infinite.",
            "The original text edition uses its existing ingredient combinations. The earlier /edition browser version has separate brewing rules and saves. Do not assume its recipes transfer to this edition.",
        ],
    ),
    (
        "villages",
        "Different villages, local stocks and saved notes",
        [
            "The world has 32 additional ordinary villages, two per region including the optional Creator’s Realm, as well as the original villages and four hidden elemental settlements. Farming, forge, market, mountain and sanctuary profiles offer different services and strengths.",
            "Restaurant options show prices and remaining quantities. Village option 19 sells local metals, woods and construction supplies where a trading service exists. Takeaway food and material stock refresh every 20 wanders; leaving, revisiting or loading does not refill them.",
            "Use option 11 or the sidebar Edit note button to save a village with a note such as cheap food, farming village or great loom. Option 12 or Tags adds comma-separated labels. Save village bookmarks it without needing a note.",
            "Explore → Village Directory searches village name, region, service, tag and note. Toggle saved-only, edit bookmarks or revisit a known village. Notes and supplies belong to the current character’s save.",
        ],
    ),
    (
        "development",
        "Village growth, construction and 100 community projects",
        [
            "Each actual arrival counts as one visit. Every village independently chooses a development interval of 10–15 visits, then residents improve a random existing service by one building level. Browsing its menus does not count. At maximum level, development grants reputation instead.",
            "Option 17 upgrades existing buildings using Timber, Stone, Iron fittings and souls. The listed cost is paid only after confirmation. Buildings stop at level 5. You can convert carried wood and metal into construction materials; quarries and timber yards offer finite gathering trips every 20-wander cycle.",
            "Option 20 offers locally compatible choices from 100 named community construction projects. Their selections differ by settlement. Each project costs materials and souls, can be built once per village and grants +1 local reputation. Every third completed project for one service adds +1 effective service quality, up to +3.",
            "These are 100 projects sharing construction rules, not 100 unrelated gameplay systems. Ordinary building levels and project bonuses are separate. Improved shop capacity takes effect at the next restock. Option 21 displays the local development history.",
        ],
    ),
    (
        "companions",
        "Companion food, hunger and evolution",
        [
            "You may recruit up to three travelling companions, with additional companions housed in Old Village met while wandering. Open Character → Companions to see their home region, hunger, evolution progress and acceptable foods. Choose Feed, select a companion, then choose a suitable carried food.",
            "Each companion eats the food types stocked in its home region, even when you travel elsewhere. For example, an Ember Fox eats Ashen Wastes food, such as Ember Bread. Buy takeaway food and carry it; restaurant meals eaten by you cannot be fed later.",
            "Companion hunger starts at 100 and falls by 5 each wander. Feeding consumes one item and restores that food’s listed hunger. Wrong food, cancellation and feeding a full companion keep your item. Below 30 they rest instead of helping in battle and do not earn battle XP. They remain with you and do not die from hunger.",
            "Feeding does not grant evolution XP. Actual help in a won battle earns combat bond XP: at 20 they become an Awakened form (stage 1); at 60 they gain a named final form (stage 2), such as Sunfire Ember Fox. Juvenile battle companions can help with a weak strike; peaceful companions can earn bond by healing you. Final forms have stronger passive battle support. Evolution progress and battle-level XP are separate; peaceful species evolve but remain peaceful.",
            "Old saves receive full companion hunger and their catalogued home region when loaded. Hunger, meals, stage and form persist with the character.",
        ],
    ),
    (
        "ruins",
        "Ruins, tomes and protected fragments",
        [
            "Ancient civilisation ruins exist in every region. Search a site once per 20-wander cycle: 35% fragment, 25% tome, 40% no recoverable find. Each kind can be recovered only once at a particular site, so an already-owned result does not create another item.",
            "Fragments come from the eleven destroyed cores. Tomes preserve the fallen civilisations’ history. They have little practical use yet and cannot be sold, salvaged or used for imbuing. Keep them for Season Three. The four surviving clan cores remain intact.",
        ],
    ),
    (
        "temple",
        "Core blessings and the Riftlands Source Temple",
        [
            "Visit a hidden elemental village to ask for its clan blessing or test yourself against its guardian. Receiving an attunement never takes the clan’s protected core away.",
            "The Riftlands Source Temple sells a portable Core Stabiliser for 300 souls. Its infusion menu combines core energy and a stabiliser with a weapon or staff. The stabiliser is consumed. A physical core from an old save is consumed if used; a clan attunement channels energy remotely and remains available.",
            "A weapon’s permanent rune remains bound after infusion. Broken-core fragments are never valid imbuing ingredients. Equipment that is already infused cannot be infused again.",
        ],
    ),
    (
        "story",
        "Chapter One, the interlude and Season Two",
        [
            "Long ago the Riftlands separated the Dreamscape from the main world. Its king corrupted Source energy at the Sacred Temple, merged the realms and became the monsters’ king. Eleven destroyed cores left their civilisations powerless. Warriors of the four surviving clans sacrificed themselves to stabilise the temple and banish him.",
            "The rift has reopened. Elian and the village keepers explain the invasion from the start. Unlock all fifteen main regions and defeat The Dreaming God, the Dreamscape King, to finish Chapter One. Defeating the Creator is optional.",
            "After the victory, Elian warns that someone must have reopened the rift. Complete 20 additional side quests during the rebuilding interlude, then start Season Two from the journal or mentor. In lore five months pass; you do not wait five real months.",
            "Season Two follows deliberate stabiliser sabotage. Gather testimony from the four elemental keepers, investigate at the Riftlands temple, confront Vael and repair the stabiliser with the clans’ harmonic knowledge. The journal tracks the requirements. After repairing the stabiliser, the Season Three expedition opens through Adventures. The overarching villain’s creation-artifact goal is revealed only there; its underlying motive remains deliberately undisclosed.",
        ],
    ),
    (
        "quests",
        "Side quests, libraries and challenge records",
        [
            "Village option 16 or a watch post opens the local quest board. Up to three ordinary quests can be active. Exploration and battles update their matching goals; read the printed objectives and rewards.",
            "Local village errands trade requested ingredients for souls and reputation once per restock cycle. Elemental villages have their own keeper requests, themed shops and exclusive libraries after the postgame gate. Their tomes and teachers can teach elemental arts.",
            "Character includes statistics, skill trees, achievements and a bestiary. Quests & Challenges includes daily/weekly goals, boss-rush options and records, and the story journal. Daily and weekly goals now advance from actual kills, XP, crafting and collection. Guardian-region goals count distinct regions; rewards are delivered once as usable supplies. Read each entry’s requirements before starting.",
            "The optional menus now provide playable local systems: commissions, daily rewards, cosmetics, guild supplies, festivals, run rules, arena opponents, town facilities, factions, treasure maps, mounts and New Game+. Shared trades and arena ghosts are shared only by players on the same hosted instance; separate offline computers have separate markets. Use Adventures, projects & research for the 100-addon catalogue.",
        ],
    ),
    (
        "saves",
        "Six saves, autosave and portable backups",
        [
            "Return to a main or category menu to save. Six slots hold independent named characters or checkpoints. Loading a slot replaces the active session while keeping other slots. Autosave updates at those safe menus, not halfway through a battle, shop purchase or village conversation.",
            "Export downloads a JSON backup of your latest safe checkpoint. Import restores that save. Keep exported backups before clearing browser data or changing devices. The earlier browser edition has its own incompatible save format.",
            "Closing the game without returning to a safe menu can lose progress since the previous checkpoint. Leave a village with its Leave option, return to the category menu and save before closing.",
        ],
    ),
    (
        "appearance",
        "Dictionary, colours, accessibility and devices",
        [
            "The title menu contains Dictionary, Tutorial, Customise and Saves. Play / Continue opens your adventure. Dictionary → All searches the full content reference: every catalogue item, materials, cores and charging limits, equipment stats, regional loot probabilities, creatures, structures, village services, companions, recipes, quests, construction projects and game systems. Filter by category or search any name, region, ability or material. Show next 60 loads more results. The specialist rune, fusion-preview, effect and potion tabs remain available. Wandering, Weather, World events and Loot tabs show encounter probabilities and the things that can happen; wandering estimates reflect your current discoveries.",
            "Automatic scenery changes colour by region and structure. Customise can fix a theme or set your own background and accent colours. A− and A+ change text size; Compact sidebar changes the status layout. The visible story question also describes the answer box for screen readers.",
            "On Windows extract the download and open Play Soules.bat with Python installed. Keep its server window open while playing in your browser. An iPad needs an accessible hosted server; the GitHub repository itself is source code, not a public play server.",
        ],
    ),
]

SECTIONS.extend(
    [
        (
            "workers",
            "Village workers and defence assignments",
            [
                "Enter a village and choose Workers & commissions (22), or use its sidebar button. The smith, weaver, enchanter, alchemist and gathering crew exist only where the village has their service. Weapon commissions always need one metal, one ordinary core and one wood; supply them yourself or pay the displayed extra price for finite village stock. Their level controls completion time; their quality controls equipment strength or potion yield. The displayed fee and your carried materials are spent when you place the order.",
                "Collect ready orders in the same village. Productive local actions pass one shift; paid inn rest passes two. Each Wander advances all pending village orders by one shift, even while you are away. Opening menus and ordinary travel do not advance work. Paid work shifts are also available. Gatherers make at most two trips per village per 20-wander cycle. Apprentices enable fully paid batch commissions.",
                "Community activities (23) opens Adventures. Type the number to the LEFT of Village systems (normally 2), then choose the local activity number 1–10. The labels 21–30 are catalogue IDs, not answers. Each row explains its costs and outcome before selection; 0 goes back. Some activity selections immediately spend their listed resources. During Village Watch defence you can assign available local specialists to defend, gather, repair or treat wounds. Service level affects their contribution; repair teams require Timber. Ordinary benches, notes, tags, village development and the 100 earlier construction projects remain available.",
            ],
        ),
        (
            "adventures",
            "The 100 addons and Season Three",
            [
                "World & Social → Adventures, projects & research contains nine groups covering 100 named addons. The first group has 20 authored side stories: accept one in its origin region, scout twice, fulfil its practical objective and choose a resolution. Completed stories count toward the rebuilding interlude. Quest Route Planner groups objectives by region.",
                "Exploration activities include finite fishing and mining, tracking a specific monster, ordinary map surveys, camps, caravan escorts, damaged crossings and peaceful wildlife. Village systems include storehouses, greenhouses, roads, visiting specialists, festivals, votes, wells and restored refuges. Professions add specialties, tools, apprentices, masterwork trials, constrained reforging, patterns and signatures.",
                "Tactical encounters support selecting one of several targets, terrain hazards, battle preparations, charged attacks every third turn, interrupts and trained counterspells. Sufficient bestiary study reveals intentions. Mercy requires an intelligent enemy below a quarter of its health. Practice restores health, mana and effects and gives no battle rewards; any consumables you choose to use remain spent. Special companion moves are limited to one per encounter.",
                "Cooking consumes carried food and a regional ingredient. Cooking ranks improve meals and unlock a Feast. Potions add toxicity; at 64 or above repeated use strains health. Wandering and inn rest reduce it. Drying racks and gardens use local work shifts. Apothecary orders, taste notes, researched substitutions and a four-clan banquet add alchemy activities. Village option 24 blends two healing potions or fortifies one with a local ingredient; read the costs and capped strength first.",
                "Companions have home-protection quests, camp dialogue, temperaments, accessories and a resting sanctuary. Village friendships reward sustained local help. Elian has optional memories; rescued people can return. Protected keepsakes remain in story progress. Feeding keeps companions ready; actual assistance in victories drives their evolution.",
                "Season Three opens only after the Season Two repair. Prepare supplies, meet Sera beyond the bridge, tune protected fragments without consuming them, explore the archive, form an alliance, craft paired-element equipment and confront the cause of the repeated interference. Original workshops & collections also exposes advanced skill purchases, material mastery, equipment collection bonuses, the legendary forge commission, prestige supplies, artifacts and fresh prestige ascension. Boss Rush now runs live tactical encounters with saved records. The earlier chapters still end at their established bosses. The optional Vault follows the expedition ending.",
            ],
        ),
        (
            "optional",
            "Daily rewards and optional progression",
            [
                "Character → Login streak asks you to claim once per Malaysian calendar date. Consecutive dates advance the streak; a missed day resets it. Milestones occur on days 1, 3, 7, 14 and 30, with 30 souls on other days. Each saved character has its own record; offline play relies on your computer clock.",
                "Cosmetics use earned cosmetic currency. Adventure-pass XP comes from wandering and live victories; claim each eligible tier once. Festivals rotate in 30-day calendar blocks and grant one champion reward per block. Town facilities offer income, commission discounts, exploration pass XP and shrine mana. Faction contracts unlock finite vendor stocks. Ritual effects last for combat encounters.",
                "Guild creation and joining, equipment trading and arena ghosts share a small database on the same game server. A solo offline server still offers NPC arena opponents and your own guild progression. Posting a trade escrows the item; buyers claim it once, sellers collect proceeds once, and unsold offers can be cancelled. Only spare unbound equipment can be posted.",
                "Budget mode blocks supported purchases; Solo disables companion combat support. Ironman follows the normal death-ending rule. Speedrun records time to level 10. Ending a mode forfeits its record. After the first campaign, New Game+ starts fresh with harder monsters and retains a written chronicle rather than old supplies.",
            ],
        ),
        (
            "records",
            "Save history and accessible controls",
            [
                "Each explicit save also keeps a checkpoint in the five-entry Save timeline. Saves shows fallen and retired run chronicles and can export a readable character sheet. Timeline entries, slots, controls and chronicles are stored in this browser. Export JSON saves for backups that travel between devices.",
                "Customise can remap Focus answer box, Latest output and Back; numbered answers stay the same. Optional screen-reader combat mode announces your health, enemy health and the current question. Rune sound volume is separate and starts muted. Dictionary rune seals are distinct for every normal rune.",
                "Combat Replay stores the most recent ten fights, up to 80 recorded turns each. Personal markers annotate discovered ordinary locations. The Build Planner compares carried equipment without equipping or consuming it. Optional Journey Statistics can be shown or hidden.",
            ],
        ),
    ]
)

# Keys are original action identifiers; the browser derives local menu numbers.
ACTION_HELP = {
    1: "Advance a wander: encounters, discoveries, resources, weather and hunger.",
    2: "Move to an unlocked region; the Crimson Forge shortcut enters its monster-held elemental hearth.",
    3: "Choose blacksmith, scroll, rune binding, two-rune fusion, spell or weapon fusion.",
    4: "Select a carried weapon to equip.",
    5: "Select carried armour to equip.",
    6: "Inspect the original character statistics and progress fields.",
    7: "Save progress; also use browser save slots at a category menu for separate characters.",
    8: "End the running text session; save at a safe menu first.",
    9: "Challenge this region’s guardian. Victory advances main-region access.",
    10: "Browse bags, search, sort, manage favourites and configure duplicate sales.",
    11: "Sell selected inventory categories; read bulk-sale choices carefully.",
    12: "Choose an available spell and follow its requirements.",
    13: "View regional progression and unlocked locations.",
    14: "Clear three Crimson Forge chambers, charge a compatible core with a loose rune, then craft elemental weapons.",
    15: "Infuse eligible equipment at the Riftlands Source Temple.",
    16: "Visit the Source Temple while in Riftlands: stabilisers, infusion and story.",
    17: "Visit a discovered structure in the current region.",
    18: "Consume one carried food to restore your hunger.",
    19: "View and spend available points in the original skill tree.",
    20: "Review achievement progress and recorded unlocks.",
    21: "Inspect encountered monsters and kill records.",
    22: "Feed companions, see regional diets, hunger, named forms and evolution progress.",
    23: "Use the current village’s available benches; enter a village first.",
    24: "Review daily challenge objectives and recorded progress.",
    25: "Review weekly challenge objectives and recorded progress.",
    26: "Start a boss-rush challenge after checking its requirements.",
    27: "Read boss-rush run counts and best scores.",
    28: "Choose an advanced skill tree and spend its displayed point cost once; levels and already learned skills are checked.",
    29: "Buy and equip character appearances, weapon skins and titles with cosmetic currency.",
    30: "Create or join a shared-instance guild, improve its supply level and collect finite supplies.",
    31: "Fight the current 30-day festival encounters and claim its unique materials and cosmetic reward once.",
    32: "Start or end Speedrun, Ironman, Budget or Solo run rules; ending a mode forfeits its record.",
    33: "Open story objectives, lore, profession progress and season progression.",
    34: "Enchant eligible equipment with the displayed success chance and costs.",
    35: "After Chapter One, start a fresh New Game+ with harder enemies and a retained written chronicle.",
    36: "Earn adventure-pass XP through exploration and victories, then claim each eligible tier once.",
    37: "Spend supplies and souls on temporary encounter-based rituals.",
    38: "Fight nonlethal NPC arena opponents or opt in to shared-instance ghost challenges.",
    39: "Review tested brews and exchange daily/pass reward supplies into usable fittings or herbs; Dictionary → Potions lists all ingredient recipes.",
    40: "Post eligible spare equipment into escrow, buy shared-instance offers and collect sale proceeds.",
    41: "Build town facilities and collect finite income; village-specific construction also remains available.",
    42: "Claim a once-per-character calendar-day reward in Malaysian time; missed days reset the streak.",
    43: "Choose one faction and receive its combat and activity bonuses.",
    44: "Buy a map, travel and scout its target region, then recover a finite treasure reward.",
    45: "Buy and equip a mount for travel nourishment and escort benefits.",
    46: "Review active status effects and curing information.",
    48: "Open all 100 addons, villager activities, tactical combat, professions, research and the Season Three expedition.",
    49: "Drink a carried potion outside combat; healing at full health keeps the bottle. The sidebar also offers quick potion and weapon controls.",
    47: "Search discovered villages, save notes and tags, filter bookmarks and revisit.",
}

GUIDE = dict(
    sections=[
        dict(id=key, title=title, paragraphs=paragraphs)
        for key, title, paragraphs in SECTIONS
    ],
    actions=ACTION_HELP,
)
