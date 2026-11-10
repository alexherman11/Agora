# What the graph could make Agora

> Thinking by Claude, 28 Oct 2026, for Alex. He said: "i'm still not sure you understand the potential of the graph. do some research into knowledge graphs, and think about how they could empower agora." The research is in `reports/Knowledge graphs for Agora.md` and its notes in `research_notes/Knowledge graphs for Agora/`. Labels: **read** (from those notes, which cite their sources), **ran**, **imagined**. Everything about Agora's future here is imagined unless it says otherwise.

## What I had wrong

I treated the graph as a *reading*: `around`, a query you run when you want context. Then I spent two rounds on its guard rails. The research says the potential is somewhere else. In the systems that worked, the graph is not something you look things up in. It is the shape of the whole system, and the thing people and programs exchange.

- **Google:** "things, not strings" (read). Search changed once it knew the things behind the words.
- **Palantir:** one ontology of objects and actions, and every application built on it (read). The apps are cheap because the graph is shared.
- **Bush:** the Memex's core act was tying two items together, and the trail was what you handed to a friend (read).

So the question is not "how do agents query the graph". It is: **what does Agora become if the graph is the computer?** Five answers, then the idea history lost, then what to try first.

## 1. The graph is the application platform

**Palantir's ontology** has two halves: a data model (object types, properties, link types) and a change model (action types bound to object types or to shared shapes, with rules, side effects and writeback) (read). Every app reuses the same actions, and AI agents get those same actions as their tools, each set to run on its own or to ask first (read).

**Agora already has both halves.** Things, kinds and aspects are the data model; the dictionary of words is the change model; lenses are the apps.

**What a whole graph adds:**
- An app built in Agora works on every other app's things the moment it exists. A calendar lens shows the meeting group's events, the task board's deadlines and the map's openings, because they are events.
- Each new lens or word enriches the graph every other app uses. That's Dynamic Desk's "each new capability costs less than the one before", made mechanical.
- **Tana's supertags** show the kind side works for ordinary people (read):
  - a supertag carries fields and commands;
  - the commands appear as buttons on every tagged thing;
  - a supertag can extend another (add fields, never remove inherited ones);
  - a thing can carry several.

  That is Alex's nested kinds with verbs attached, shipped and used.
- **Windows' shell verbs** (read) show how the dictionary should pick which verbs apply:
  - conditions on properties, not just on the type;
  - canonical names kept apart from display labels;
  - rules for how many selected things a verb takes.

**So "words reach things that fit" is the platform itself.** Every thing knows what can be done to it, and every word knows what it can be done to.

## 2. The graph is memory, for people and agents alike

**Bush's memex** (read):
- tied two items so either recalls the other;
- grouped those ties into named trails with comments and side trails;
- let you share a trail by copying it whole into a friend's memex.

Later tools kept the link and dropped the trail. Roam and Obsidian users say backlinks and a thing's local graph help them; the whole-vault graph is decoration (read, anecdotal).

**For agents** (read):
- HippoRAG spreads outward from what's in front of you (personalised PageRank). It gains up to 20% on multi-step questions, at 10–30× lower cost than iterative retrieval.
- Graphiti keeps each fact with when it was true and when it was learned, and retires contradicted facts instead of piling them up. It beat full context on LongMemEval while using about 1.6k tokens instead of 115k.
- Simple baselines stay strong: an agent keeping history in files scores 74% on LoCoMo.

Agora's advantage over all of these is that **its links are made on purpose by acts**, not guessed by a model. That removes most of the cost and noise in the published systems (read).

**What it becomes:**
- `around` turns into spreading activation from the current focus: HippoRAG's method on Agora's real bonds.
- Facts about people (Alex prefers X) become world things that are retired when contradicted, not lines added to a soul file forever.
- After a reset, any agent rebuilds "where was I" from its card's consequences.
- And for Alex, not just agents: a local graph on every thing, the part users actually value.

## 3. The graph is the conscience: provenance and information flow

The kernel's log is already a provenance graph. W3C PROV's core maps onto it almost exactly (read):
- a record is an Activity;
- the actor `wasAssociatedWith` it, `actedOnBehalfOf` a person;
- `saw` is `used`;
- a cause is `wasInformedBy`;
- each fact is a new version that `wasRevisionOf` the one its "hash before" names.

Agora built a provenance graph without meaning to.

**The 2025–26 research on keeping AI agents safe** (CaMeL, FIDES and others) converges on one mechanism (read):
- label every value by its source and by who may read it;
- combine labels as data mixes;
- hand untrusted content around by reference, not inside the agent's context;
- check labels at consequential acts, and ask the person when a check fails.

CaMeL kept 77% task success with provable security, against 84% with no defence (read).

**What it becomes:** Agora could be the computer where agents are constrained by *where their information came from*, by construction:
- **A mail can't make JEFF send money.** The send's ancestry runs through an unchecked outside arrival, so it waits for Alex.
- **A neighbour's agent can't leak a private note into a public post.** The post's ancestry includes a thing its audience can't see.
- **"Why did this happen?"** is a walk back to a human request, taken from the log, not from the agent's own account.

That is Agora.md's "JEFF should not treat external information as rules", made into something the kernel checks.

**Dependency explosion is the known failure** (read): one widely read note makes everything look connected. Hence a narrow "cited" set beside the broad "saw" set.

## 4. The graph is the commons: places bridge groups

**What the research found** (read):
- **OpenStreetMap:** a free-form vocabulary converged through usage counts and editor presets. Votes are non-binding. Whoever curates the presets governs the vocabulary.
- **Wikidata:** a fact keeps its sources and rank, and conflicting facts coexist. Its notability rule includes "structural need": a thing may exist because others need to point at it.
- **AT Protocol lexicons:** rules for vocabularies that many independent communities share. Additive changes only; unknown fields ignored; a breaking change gets a new name.

**What it becomes:**
- **Agora.md's "bridge by place".** Two groups' events at the same park bond through the park, so one calendar can show both and each group keeps its own facets. A newcomer opens the park and walks to everything happening, decided or broken there.
- **A decision bonded** to the discussion that led to it and the acts that carried it out: accountable local governance you can walk.
- **FixMyStreet's finding** (read): people whose first report got fixed were 54% more likely to report again. The graph makes "your report → the fix" visible, which is the participation loop.
- **The kind picker is governance**, so it should be a visible, forkable world thing, as OSM's presets should have been.
- **Kinds evolve the lexicon way**, so forks stay readable to each other.

**What the research says to protect:**
- Four location points identify 95% of people. Strava's heatmap exposed places where few people were active. So fog of war stays private to the explorer.
- Rewards get kept off the factual map. Pokémon Go players added fake parks to OSM.

## 5. The graph is the map of the system itself: malleability without fear

Agora's graph holds its own machinery: words, kinds, lenses, grants, modules, rules. Data lineage tools separate what a job declares it reads from what a run actually did. Impact analysis is a walk downstream, and it is precise only at field level (read). Agora has both halves: lenses and rules declare their reads, and the log records the runs.

**What it becomes:**
- "What breaks if I change this word, kind or lens?" gets a real answer before the change, for Alex and for every agent.
- Agora.md names Emacs as a warning: it survived for decades but became undecipherable after "bankruptcy". Malleable systems decay when nobody can see what depends on what. **The graph is how a system everyone edits stays legible.** Of everything here, this may matter most for the decades-long goal.
- An agent learns the system the way it learns the world: by walking from a word to what it touched, and from a lens to what it shows.

## The idea history lost: trails

**A trail is a thing:**
- an ordered list of other things, each with a comment;
- side trails branching off;
- shared by posting it, and placed in the receiver's world, where it links into their own things.

Bush named a profession for it: "trail blazers" (read). In Agora (imagined):
- **Agents hand over trails, not summaries.** "How I diagnosed Rocket League": the task, the window error, the Steam sign-in note, the commit, the test. A summary paraphrases; a trail points at the real things, so the next agent or person can check every step. It's the hand-off note, built from the world.
- **People teach with trails.** "How to make a map layer" is a trail through a real layer, its lens, its word and a working example. That's a guide that can't go stale silently, because its steps are things.
- **The map's lore is trails.** A walking tour, a history of a building, a hidden quest: trails through places, gated by being there. Agora.md's hidden layers, easter eggs and Ready Player One quests are trails with conditions.
- **Investigations and decisions are trails.** What the council considered, in order, each with a note. Civic memory.
- **Trails are graded links.** Choosing what follows what is a link someone made on purpose, and the strongest kind of bond there is. Every trail strengthens the graph without anyone "adding a because edge".

## How machines and people improve the graph together

**Every system that scaled used the same pattern** (read):
- Freebase's move to Wikidata queued machine-proposed facts for people to review.
- Merging duplicates uses two thresholds: the uncertain middle band goes to a person, and active learning picks which pairs to show.
- Explanations reliably raise acceptance of recommendations.

**For Agora (imagined):** agents propose and people accept. Proposals are one-click things with a reason that the log can reverse:
- links ("these two look like the same Rocket League");
- kinds ("these 30 things share start, title and place: an event?");
- merges;
- trails.

That answers Alex's "not making people add a because edge": machines do the noticing, people do the deciding.

## What graphs can do here that folders and tables can't (read, with scale)

| Capability | What the research found | Agora's use |
|---|---|---|
| Faceted browsing | Flamenco: 90% preferred it; 97% said it helped them learn the collection | browse the whole world by kind and aspect, for free |
| One-thing-centred views | people give up on node-link diagrams beyond about 50–100 nodes | a local graph on every thing; never a whole-world hairball |
| Random-walk recommendation | Pixie: up to 50% more engagement, 60 ms per request; the path is the explanation | "you might want X, because…" |
| Link prediction | simple heuristics (Adamic–Adar) remain competitive | suggested links as proposals |
| Emergent groups | Leiden guarantees connected communities where Louvain doesn't | candidate kinds and topics |
| Paths | "how are A and B connected" | agents testing hunches; people tracing why |
| Time | Datomic's as-of, since and history | every view scrubbable through time; "what did JEFF see then" |

## What to try first: five small proofs of the big claims

Each one tests one of the five pictures above, on real things, in a hidden sandbox:
1. **Trails** (memory, sharing): a trail kind and a trail lens. JEFF makes one for a real investigation and Alex walks it.
2. **Facets** (platform, discovery): one lens that browses the whole world by kind and aspect, with counts.
3. **Spreading activation** (memory): `around` as personalised PageRank, replayed against JEFF's past wakes and against a recency baseline.
4. **Ancestry labels** (conscience): a mail asking JEFF to delete something is held for Alex, with the walk that explains why.
5. **Place bridge** (commons): two groups' events at one park, one calendar, each group's extra facet kept.

The kinds rework (properties, marks, words that fit, checked on every run) is the floor under all five, and the privacy fixes come first.

## What would change my mind
- **If Alex and JEFF don't come back to trails after a week,** the trail is Bush's idea, not ours.
- **If spreading activation doesn't beat recency** on the replay, memory stays with simple history and the graph serves the other four pictures.
- **If ancestry labels hold too many acts for confirmation** (the research saw up to 24.5% task loss with policies on), labels need narrowing to "cited" rather than "saw" before they're usable.
- **If the place bridge needs more than renames between groups,** translation between vocabularies has to come before the commons.
