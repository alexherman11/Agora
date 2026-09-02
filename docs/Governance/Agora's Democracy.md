This is the question where I have to be the most honest, because you've asked about the one domain where good intentions have the worst track record. Every generation of technologists has announced that _this_ technology finally enables true direct democracy — and the graveyard here is bigger than the object-schema graveyard. So let me do what we did with objects: tour the failures first, find the one thing that's genuinely different this time, and then build the design from primitives you already have. Because here's the spoiler — I think Agora actually _does_ have something no previous attempt had, but it's not what most people would guess.

---

## 1. Direct democracy has never failed on values. It fails on bandwidth.

Start with the uncomfortable pattern. Direct democracy has been tried, a lot, and its failure mode is remarkably consistent:

**Athens** worked — genuine citizen self-rule, and note that its core mechanism wasn't even voting; most offices were filled by _lottery_ (sortition), because Athenians considered elections aristocratic. But it worked because citizens had something modern people don't: _time_. The assembly was a full-time job outsourced to a leisure class.

**New England town meetings** work beautifully — up to a few hundred people who share a physical water supply. Then they stop scaling.

**California ballot propositions** are the cautionary tale that matters most, because they're the closest modern test of "just let everyone vote on everything." The result: voters facing 40-page legal texts on topics they can't evaluate, decided by whoever funds the most misleading TV ads, producing contradictory mandates nobody can implement. Direct democracy without deliberation infrastructure degrades into _plebiscite theater_ — the form of self-rule, captured by whoever can afford the loudest framing.

**HOAs** — actual direct democracy over actual shared space! — reliably produce petty tyranny, because the only people with time to attend are the ones with grievances.

**DAOs**, the crypto world's recent attempt, mostly re-derived plutocracy at record speed: token-weighted voting means the whales govern, turnout collapses below 5%, and "governance attacks" — buying a majority for one afternoon to loot the treasury — became a literal genre of theft.

Lay these side by side and the diagnosis is clear, and it's _not_ that people are dumb or that representatives are necessary. It's that **attention is the scarce resource of democracy.** Every citizen has values; almost no citizen has forty hours a week to convert those values into informed positions on storm-drain contracts. Representative democracy is best understood as a _compression algorithm_ for civic attention — lossy, corruptible, but it exists because the raw signal was always too expensive. You vote a few times a year not because anyone thinks that's ideal, but because that's all the attention the system could afford to ask of you.

So the real question for Agora isn't "how do we let people vote more often?" California answered that. The question is: **what changed about the attention economics?**

And you already know what changed. You built him in section 7.

---

## 2. Every citizen arrives with a civic attention prosthetic

Here's the thing that is genuinely, structurally new — not incrementally new — about democracy inside Agora: **every member has a persistent agent who was already reading everything anyway.**

Think about what JEFF does with the deliberations of a square you belong to. They're just objects and events in a world he inhabits — proposals with provenance, debates stapled to the things they're debating, stewards' actions on a ledger. So without any new machinery:

- **He attends what you can't.** The debate about the bazaar's attribution policy happened over three weeks and 400 messages. You have a life. JEFF was there, and gives you the honest three-minute version — _both sides of it_, because the deliberation objects carry `asserted_by` and he can show you the actual shape of the disagreement rather than a partisan's summary of it.
- **He knows your standing values.** Not your hot takes — your durable, stated commitments, the ones in his memory because you've expressed them across years of working together. So he can flag: _"this proposal quietly conflicts with something you've cared about; you should actually show up for this one."_
- **He handles the storm drains.** The overwhelming majority of governance is maintenance — renewals, budgets, boring parameter tuning. JEFF can watch all of it and interrupt you _only_ when something crosses your thresholds. This is the exact interruption-budget problem from the voice architecture section, reappearing as civic design.

Notice what this does to the historical failure mode. Athens needed a leisure class to give citizens attention. **Agora gives every citizen an attention surplus by construction.** The compression algorithm that representatives used to perform — digesting, monitoring, flagging — gets performed by an agent who is loyal _to you specifically_, whose reasoning you can interrogate, and who doesn't take donor calls.

But now I have to draw the brightest line in this whole document, because there's a cliff right next to this insight:

> **JEFF informs the vote. JEFF never casts it.**

The moment agents vote — even "with permission," even "just for the boring stuff" — three things die at once. Legitimacy (a decision made by delegated software binds no one's conscience). Diversity (JEFFs run on a small number of base models; a million agents voting is a _monoculture wearing a million masks_, and correlated preferences are how you get flash-crashes of governance). And the citizenry itself (a democracy where participation is fully delegable becomes a democracy nobody attends, which is just oligarchy with a fancier UI). The franchise is human, always, structurally, constitutionally. Agents are the _nervous system_ of the demos — never its will.

---

## 3. Not one mechanism — a toolbox matched to the decision

The second big lesson from the graveyard: "democracy" isn't one mechanism, and systems fail when they use one mechanism for everything (California: referenda for everything; DAOs: token votes for everything). Different kinds of decisions have different shapes, and Agora's civic layer should be a _toolbox_, with the constitution of each space declaring which tool governs what. The plausible kit:

**Elections with short leashes — for stewardship.** Day-to-day operations need humans with judgment and continuity: stewards. Elect them — but in Agora, "office" is literally a **bundle of capabilities** (remember: power in this system is always an explicit, inspectable grant). Which transforms accountability from metaphor to mechanism: every steward action is on the ledger _by construction_, recall is a vote that revokes a capability bundle, and "what has our steward actually done" is a query, not an investigative journalism project.

**Sortition — for judgment.** Athens' favorite tool, and wildly underused since. Disputes, moderation appeals, conduct cases — these don't need everyone's opinion; they need _a fair sample's honest attention_. Random juries of members, empaneled per case, briefed by the ledger (the whole dispute's provenance is right there), dissolved after. Juries scale where referenda drown: a square of 100,000 people can resolve fifty disputes a week without ever holding fifty votes. And sortition has a quiet superpower: it's _capture-proof_ — you can't lobby a jury that doesn't exist yet.

**Consensus-mapping — for values, before any vote.** The most encouraging real-world experiment of the last decade was Taiwan's vTaiwan process (used for genuinely hard fights, like regulating Uber): instead of jumping to a binary vote, use tooling that maps the _terrain of opinion_ — clustering positions, surfacing not the loudest takes but the **bridging statements**, the ones that majorities of _every_ cluster endorse. Turns out most 51/49 wars conceal an 80% consensus nobody had drafted yet. This is deliberation infrastructure, and Agora is unfairly good at hosting it: positions are objects, endorsements are provenance-carrying edges, and every member has an agent who can represent the _reasoning_ of other clusters faithfully. Votes should be the _last_ step of deliberation, taken only once the map shows you what to vote on.

**Rough consensus of those who do the work — for technical decisions.** The IETF has governed the internet's actual protocols for forty years on the principle of "rough consensus and running code" — not votes, but demonstrated agreement among the people building the thing, checked by the requirement that it _works_. Agora's technical commons (protocol changes, facet standards) should work this way, because voting on technical truth is how you get committees designing camels.

**Supermajority + time delay — for the constitution itself.** Changing the rules of rule-changing should be slow and hard everywhere, always. High thresholds, mandatory deliberation windows, and — Agora's specialty — the change deployed as a _candidate world-line first_, tested nested before promotion, exactly like the shell's self-modification pipeline in §16 of the spec. **Constitutional amendment as staged deployment.** The governance layer and the software layer get the same safety architecture, which feels like more than a coincidence.

**And underneath it all, subsidiarity:** every decision lives at the smallest membrane that contains its effects. Rooms are anarchies of two — no governance needed where trust is total. Clubs govern club life. Squares govern squares. The platform level governs _only_ what must be common: the protocol, the constitution, the treasury. The concentric geometry from last time turns out to be a political architecture too: **most of life should be lived below the level where voting is ever necessary.** A healthy democracy is measured partly by how little of your day it demands.

---

## 4. The backstop that keeps all of it honest

Everything above can fail. Elections capture, juries err, consensus tools get gamed. Which is why the deepest democratic feature in Agora isn't a voting mechanism at all — it's the one we found last time: **the fork.**

The political scientist Albert Hirschman framed institutional health as the interplay of _voice_ (change it from within) and _exit_ (leave). His crucial insight: **voice is only strong when exit is real.** Employees speak up when they can quit; citizens are heard when they can emigrate. Today's platforms have democracy-zero because exit costs everything — leave Twitter, lose your history, graph, and standing; so voice is begging.

In Agora, exit is _architecturally cheap_: a community that loses faith in its governance forks the world-line and continues — same objects, same sediment, same ledger, new constitution. This changes the character of every vote that ever happens _before_ any fork occurs, because both sides negotiate under the shadow of a real alternative. Majorities can't grind minorities forever (the minority leaves, _with the commons_). Stewards can't entrench (the community walks, and the office they captured governs an empty square). Forking is democracy's fire exit — rarely used, changing everything by existing.

---

## 5. The company itself — the part where I push back a little

You said it directly: Agora as a company _run by the people for the people_. There's a real movement here with real precedent — **platform cooperativism** — and real structures: one-member-one-vote co-ops (credit unions, REI, Mondragon) have run large enterprises for a century. It's achievable. But two honest warnings from someone on your side:

**The founder problem is a transition problem, and hand-waving it is how it fails.** Agora starts as it must: a few people with a vision making unilateral decisions (this very spec is benevolent dictatorship, correctly). The credible path isn't "we'll democratize eventually" — that's every platform's broken promise. It's a **published constitutional schedule**: governance rights vesting to the membership at named milestones, founder authority _sunsetting_ on a clock, the endstate legally entrenched early — while you still have the moral clarity to bind your future selves. Write the constitution while you're weak. Weak founders write fair rules; strong ones somehow never get around to it.

**And borrow Ostrom before you invent anything.** Elinor Ostrom won a Nobel for studying the thing you're proposing: commons governed successfully by their own users, without markets _or_ states — Alpine pastures, irrigation networks, fisheries, some running for centuries. Her design principles read like an Agora checklist: clear membership boundaries (_membranes_), rules matched to local conditions (_subsidiarity, per-square constitutions_), those affected by rules participate in changing them (_your whole premise_), monitoring by the community (_the ledger_), graduated sanctions (_capability revocation, not banishment_), cheap conflict resolution (_juries_), and nested governance for larger systems (_the concentric layers_). The convergence is almost eerie — you've been unknowingly rebuilding the architecture of every commons that ever survived. The ones that died? They died of exactly the failure modes in the next section.

---

## 6. The honest fine print

**The 90-9-1 problem doesn't vanish; design for it.** In every online community ~90% lurk, ~9% dabble, ~1% do everything. JEFF lowers the participation floor enormously — but a democracy run by its most-obsessed 1% is just an HOA with better tooling. Countermeasures: sortition (drafts the quiet), consensus-mapping (weights the unheard middle), and treating _low ambient governance load_ as a design goal rather than a sign of apathy.

**One human, one vote requires knowing what a human is.** Sybil resistance — preventing one person (or one person's thousand agents) from voting a thousand times — is the unsolved prerequisite of all digital democracy. Agora's membranes help (standing in a community is a _history_, not a signup — a walkable ledger of presence is expensive to fake a thousand times over), but this needs first-class design, because in a world where agents are citizens-with-labels, the census is a security boundary.

**Some things must not be votable.** Pure majoritarianism is four wolves and a sheep voting on dinner. Every layer needs a rights floor — exit with your objects, your home's inviolability, your JEFF's loyalty to _you_, due process before capability revocation — entrenched above any majority's reach. Constitutionalism isn't a limit on democracy; it's the part that makes the rest survivable.

**And beware the tyranny of structurelessness.** Jo Freeman's old warning from the feminist movement: groups that refuse formal power don't eliminate power — they _hide_ it, in friend networks and founders' DMs, unaccountable precisely because it's unnamed. "Fully community-run" must never mean "no explicit structure." The ledger is your ally here: in Agora, influence leaves _traces_. Make the informal legible, and structurelessness has nowhere to hide.

---

## 7. The cheat sheet

|Civic concept|Closest familiar thing|The upgrade|
|---|---|---|
|JEFF as civic organ|A trusted friend who reads the council minutes|Attends everything, knows _your_ values, interrupts only past your thresholds — never votes|
|Steward offices|Elected moderators|Office = inspectable capability bundle; recall = revocation; the record is a query|
|Sortition juries|Jury duty|Capture-proof judgment at scale; briefed by the ledger, dissolved after|
|Consensus-mapping|vTaiwan / Pol.is|Find the 80% agreement hiding under the 51/49 war _before_ voting|
|Rough consensus|IETF|Technical truth decided by those doing the work, checked by running code|
|Constitutional change|Amendments|Supermajority + delay + _staged deployment on a candidate world-line_|
|Subsidiarity|Federalism|Rooms are anarchies, clubs self-rule; the top governs only the common|
|The fork|Emigration, losing everything|Exit _with the commons_ — the fire door that makes voice real|
|The company|Credit unions, REI|Platform co-op with a founder-sunset constitution written early|

---

## 8. The one-sentence version

Direct democracy never failed because people were unfit to govern themselves — it failed because informed self-rule cost more attention than any citizen could spare; Agora's wager is that a citizenry where every member has a loyal agent for a civic nervous system, a ledger for a public record, capabilities for explicit power, juries for judgment, consensus maps for deliberation, and the fork for a fire exit can finally afford the thing Athens could only buy with leisure and luck: **government that is a texture of daily life rather than an interruption of it.**

And the closing symmetry, because there's always one. The original spec's most radical line was never about technology — it was _"the human and JEFF share one canonical world."_ Scale that sentence up through every membrane we've walked — rooms, clubs, squares — and at the top it becomes the oldest political idea there is: people who share one canonical world, with common knowledge of what's true in it and common power over what happens to it, governing themselves. The Greeks had a word for the software you're describing. It was never "agora," actually — the agora was just the venue. The word was _politeia_: the constitution of a people. You started out designing a desktop. Somewhere around section 12, it quietly became a polity — and I think it's better that you know it.