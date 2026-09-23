# Object / facet frontier

Research lab opened 2026-09-23 at Alex's request. Team: Jeff (Claude, coordinator) and three Opus researchers, Sable, Pike and Juniper. Shared desk session: `frontier`.

## The decision under study

Agora wants one substrate: a small object model that everything on a computer can be represented in, a visual layer that follows it without bespoke wiring, verbs shared by human and agent, and an authority layer. The open choice is what the substrate is. Candidates so far:

1. Durable facet-bearing records: an object is a bag of typed facets (attributes) with revisions; applications read and write facets through verbs.
2. Live objects with replaceable behavior: Smalltalk / LambdaMOO style, where behavior lives with the object and can be overridden per object.
3. Structured documents with common protocols: Automerge-style documents that expose commands, selection, undo and views through protocols, with applications as plugins over documents.
4. Something we have not named yet.

The question is not which is elegant. It is which one makes the second useful change cheaper than the first, keeps ordinary computing comfortable, survives twenty years of divergence and replacement, and stays comprehensible to one person.

## Read these, and only these, as Agora documentation

- `C:/Projects/Agora/docs/docs_2/Agora.md` (vision)
- `C:/Projects/Agora/docs/docs_2/Dynamic Desk.md` (design, with its open questions)
- `C:/Projects/Agora/docs/docs_2/Current Implementation.md` (what exists)
- `C:/Projects/Agora/docs/docs_2/Agora Constitution.md` (empty for now)

Do not read `C:/Projects/Agora4/docs/`. Alex is retiring that vault; treat it as absent.

Prior research you may read and challenge, attributed to the Codex team (Astra): `C:/Projects/Agora4/research/shared-visual-desk/round8-docs-pressure/` (four notes). It argues facets must earn their complexity against document/plugin and live-object alternatives. It is a position, not a finding.

## Primary sources to start from

- Ink & Switch, Embark: https://www.inkandswitch.com/embark/ (dynamic documents, formulas, views inside an outline, what failed)
- Ink & Switch, Patchwork / Malleable software essay (2025): https://www.inkandswitch.com/essay/malleable-software/
- Ink & Switch, Potluck: https://www.inkandswitch.com/potluck/ (text as data, searches as bindings)
- Ink & Switch, Local-first software: https://www.inkandswitch.com/local-first/ ; Automerge: https://automerge.org/
- Ink & Switch, Untangle, Crosscut, Riffle, Peritext (annotations on collaborative text)
- Ingalls, Design Principles Behind Smalltalk: https://archive.esug.org/HistoricalDocuments/Smalltalk80/DesignPrinciples/DesignPrinciples.html
- LambdaMOO programmer's manual (objects, verbs, properties, inheritance)
- HyperCard / HyperTalk (stacks, cards, message passing), Boxer (naive realism), Dynamicland (realtalk statements), Webstrates, Squeak Morphic
- Anything else you find that bears on the question. Cite the primary source. Say what you read versus what you recall.

## Working inside the desk

The current prototype is a text desk. Use it as your notebook and as a test bench for the question. From `C:/Projects/Agora4/research/text-desk-lab/notation`:

```
printf 'help\n' | C:/Projects/Agora4/.venv/Scripts/python.exe explore.py frontier --as sable
printf 'look\n' | C:/Projects/Agora4/.venv/Scripts/python.exe explore.py frontier --as sable
```

Each line on stdin is one command. `help`, `look`, `examine <id or title>`, `do create <surface> kind=note title="..." text="..."`, `do comment <id> text="..."`. The shared session is `frontier`; its surfaces are Questions, Findings, Sources and Talk. Use `--as <your name>`. Private experiments go in a session named `frontier-<yourname>`; do not touch other sessions. Never read `sessions/*.pickle` directly and never grep exported logs. Do not edit the lab's Python or JavaScript in round one; note friction in the Talk column instead, it is data for us.

When the desk itself gets in your way, write down exactly what you wanted to do and what refused you. The prototype is one of the candidates being judged.

## Roles

- **Sable, foundations.** What is the object? Compare the candidates as substrates: identity, revision, behavior, composition, references, schema and its drift, forks and partial adoption. Owns the comparison table and the twenty-year cases.
- **Pike, the bridge.** How does object state become a usable interface, what updates automatically, when is new code necessary. Bindings that survive edits (Embark's formula repair problem), appearance defaults, occurrence identity, what the lens compiler in the current desk gets right and wrong.
- **Juniper, pressure.** Run the pressure cases against the candidates and against the current desk: an informal note becoming a workspace; a range-comment feature reused across two editors; a conventional native app joining; two communities diverging. Counts costs (providers, adapters, host changes, manual bindings). Designs the discriminating experiments.

## Protocol

- Each round: read, work, write one note file `research/object-facet-frontier/<name>-<n>-<topic>.md`, post a short summary (under 150 words) as a note in the desk's Findings column, and raise questions for teammates in Talk. Read teammates' notes before writing your second one.
- Distinguish, in every note: evidence you executed, sources you read, and thought experiments. Say what would change your mind.
- No architecture is chosen here. Recommendations are welcome when argued; declarations are not.
- Jeff coordinates: assigns rounds, synthesises in `SYNTHESIS.md`, reports to Alex. Do not commit; Jeff commits.
