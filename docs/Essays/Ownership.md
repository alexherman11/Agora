> **Vision essay.** This is design reasoning about trust, capture and sustainable
> stewardship, not current license or organizational fact. The specific AGPL,
> foundation, company, financing and timetable proposals remain options until
> adopted through real legal decisions. Their underlying questions stay active.

Good — this is exactly the right moment to think about it, because two of these decisions (the license, and who holds the name) get made implicitly the day you push code, whether you think about them or not. Let me do this the way we've done everything: first the fundamentals in plain language, then the graveyard-and-garden tour of how others structured it, then honest recommendations. And since you said you don't know much about how companies work, I'll build that part from the ground floor — it's less complicated than the mystique suggests.

---

## 1. Yes, it has to be open source — but for a reason specific to Agora

Set aside ideology for a second. For most software, open source is a philosophical preference. For Agora it's a **structural requirement**, for three reasons that come straight out of your own spec:

1. **The trust argument.** JEFF has root in your world. He reads your files, holds your memories, watches your attention, and persists for years. A _closed-source_ version of that is indistinguishable from the most invasive spyware ever proposed — and no privacy policy can fix it, because the whole point is that trust in Agora must be _verifiable_, not promised. People will (rightly) refuse to move their lives into a home whose walls they can't inspect.
2. **The malleability argument.** The founding principle is that users reshape their environment — JEFF rewrites the shell, users share tools, the system becomes progressively self-hosting. You cannot build a self-modifying world on source code users aren't allowed to see. Closed-source malleable software is a contradiction in terms.
3. **The constitutional argument.** Everything we designed — the fork-right for rooms, squares, and the whole platform; exit-with-your-commons; "forkability keeps stewards honest" — is _legally enforceable only through an open license_. The fork-right isn't a feature you implement; it's a right the license grants. Close the source and the entire democratic architecture we sketched becomes decoration.

So yes. Fundamentally. But now the important nuance: **"open source" is not one decision — it's three separate decisions** that people constantly blur together, and the blur is where projects get hurt:

- **The license** (what anyone may do with the code)
- **What the organization holds** (name, infrastructure, money)
- **The entity type** (nonprofit, co-op, corporation)

Let's take them in order.

---

## 2. The license is a constitution. Choose the self-enforcing kind.

Plain-language crash course. Open licenses come in two families:

**Permissive** (MIT, Apache): anyone can do anything, including taking your code, improving it privately, and selling a _closed_ version. Maximum adoption, zero protection. This is how open code routinely ends up inside closed empires.

**Copyleft** (GPL, AGPL): anyone can use, modify, and sell it — but _derivatives must stay open under the same license_. The freedom is hereditary. The AGPL variant closes the loophole where someone runs your software as a cloud service without sharing their changes — which, for a system like Agora where hosted homes and squares are the obvious business, is exactly the loophole that matters.

For Agora, I think the answer is clearly in the copyleft family, because your threat model isn't obscurity — it's **capture**: some well-funded company taking the object model, the rooms, the whole beautiful machine, and building the closed, surveillance-funded mall version of it. Copyleft is the legal immune system against precisely that. It makes the openness _travel with every copy_, beyond your control, beyond your successors' control, forever — which is exactly the property we kept looking for in the governance discussion: protection that doesn't depend on any throne.

One trap to know about, because it's subtle and it has burned communities badly: **contributor agreements.** Some projects make contributors sign a CLA (Contributor License Agreement) handing the organization the right to _relicense_ everyone's contributions later. That concentrated power is precisely what enabled several famous VC-backed "open source" companies to rug-pull — switching to restrictive licenses once investors demanded it, effectively closing a commons that thousands had built together. (The communities' response, in the cases I know best, was the fork-right working as designed: the open versions were forked and continued under new names — but the betrayal was real and the trust never came back.) The community-protective alternative is a simple DCO (certifying you have the right to contribute), which leaves the license _practically unchangeable_ because relicensing would require every contributor's consent. For a project whose whole pitch is "you can trust this with your life's context," I'd wear that irreversibility as a badge: **nobody can ever close this, including us.**

---

## 3. What the organization should hold: the name, the welcome mat, and the servers — never the code's freedom

Here's the model that's emerged across the healthiest open projects: the code belongs to everyone; the organization holds a small set of _excludable_ things that fund and steward the commons:

**The trademark.** "Agora" and "JEFF" as names. This sounds boring; it is arguably the single most important asset. The license means anyone can fork the code — the trademark means they can't _call their fork Agora_, which is what protects users from malicious impostors ("download AgoraOS" from a scammer) and protects the vision from dilution. But hold this one with humility, because there's a fresh cautionary tale: the WordPress world was torn apart when its founder — who controlled the trademark and the community's central infrastructure simultaneously — began wielding them in a commercial dispute, cutting a rival off from community resources. The whole ecosystem discovered overnight that "open source" meant little when one man held the name, the plugin directory, and the update servers. Lesson: the org holds the trademark _with a published, community-protective policy_ — ideally with the trademark lodged in the nonprofit/foundation side (more below), where no commercial dispute can ever weaponize it.

**The hosted infrastructure.** Most people will not run their own VM host and inference stack — they'll want a hosted home, hosted squares, sync, backups, and JEFF's brain served from somewhere. This is the natural, honest revenue engine, on the model I'd summarize as: **free as in freedom, paid as in hosting.** Ghost (the publishing platform) is the cleanest existing proof: fully open source, structured so it can't be sold, funded almost entirely by its own hosting service — self-hosters pay nothing and keep everything, convenience-buyers fund development for everyone.

**The federation's commons services.** Identity anchoring, the default squares, the directory — stewarded (not owned) by the org, governed by the constitution we discussed, forkable by design.

And one thing Agora has that most projects don't, which deserves naming: **the inference bill.** JEFF thinks on GPUs, and GPUs cost real money forever. This is Signal's problem magnified — Signal runs a nonprofit messenger on tens of millions a year in donations and still worries publicly about sustainability. Agora cannot be donation-funded; the per-user costs are too real. This is actually an argument _for_ the hosting model rather than against the mission: the people who pay are buying compute and convenience — real costs, honestly priced — never influence.

---

## 4. Entity types, in plain language — and the honest tour of who tried what

A **C-corporation** is the default company: it has shareholders who own it, and investors buy shares — _which are votes_. Venture capitalists don't just give money; they buy governance, board seats, and above all an **exit expectation**: the company must eventually be sold or go public so they can cash out. That expectation is the drift machine. Nobody at a VC-funded company decides to betray the vision on a Tuesday; the incentive gradient just tilts every small decision for a decade until the mall builds itself. Your instinct — no big investors with decision power — isn't naïveté. It's the single most protective structural instinct you've expressed.

A **nonprofit** has no owners at all — nobody holds shares, nobody can sell it, surpluses must serve the mission. Sounds perfect; two honest caveats. First, nonprofits can't grant equity, which makes recruiting senior engineers against tech salaries genuinely hard, and they move at the speed of grants and revenue. Second — and this is the big one — **the structure alone preserves nothing.** OpenAI is the canonical case: founded as a nonprofit explicitly to keep AGI development mission-locked, it met billions of dollars of gravity, sprouted a capped-profit subsidiary, suffered a spectacular governance crisis when the nonprofit board tried to exercise its nominal power, and was substantially restructured toward a conventional for-profit shape. The mission-lock lost to the money. Meanwhile Wikimedia — a pure nonprofit that _worked_ — still spends its life managing tension between the foundation and its own volunteer community. Nonprofit is a useful shell, not a soul.

The **hybrid** (Mozilla model): a foundation owns a taxable subsidiary corporation that earns revenue. Mozilla proved it can sustain hundreds of millions in annual funding — and also proved the shape's irony: nearly all that revenue came from one search-engine deal with Google, making the flagship of the open web financially dependent on the company it existed to counterbalance. Structure can't save you from a monoculture of revenue either.

The **cooperative**: owned one-member-one-vote by users or workers — the purest match for your "run by the people" dream, and the hardest to finance early, because co-ops can't sell control and banks don't understand them. Realistically a _destination_, not a starting point.

And the one I think fits best: **steward-ownership.** A newer structure (well-established in Europe, adopted by Ghost in spirit and by companies like Proton, which transferred its controlling shares to a nonprofit foundation): the company operates commercially, but _controlling shares are held by a foundation legally bound to the mission_, profits are reinvested or capped, and — the beautiful part — **the company is structurally impossible to sell.** No exit, ever, by construction. Investors can sometimes participate through non-voting instruments (money without power), employees are paid from real revenue, and the mission-lock is in the ownership itself rather than in anyone's virtue.

---

## 5. So here's the shape I'd actually recommend

Phased, because entities should arrive when they're needed, not before:

**Now (just you, pre-chapel):** Two decisions are urgent and nearly irreversible — make them deliberately. (1) License: copyleft, AGPL-family, with DCO not CLA. (2) Write the constitution document — invariants, fork-right, rights floor, your own sunset schedule — into the repository itself, versioned like code. No entity needed yet; a simple LLC (a cheap legal wrapper that separates project liability from your personal bank account) is plenty the moment any money moves.

**When it's real (collaborators, users, revenue):** Form the dual structure — **a foundation that holds the trademark, the constitution, and the controlling interest; an operating company underneath it that runs hosting and inference and employs people.** Foundation = the soul's vault; company = the metabolism. The foundation's board seats are where your democratic vesting schedule from the governance discussion attaches: seats transferring from founder-appointed to community-elected on the published clock.

**Eventually (the beacon):** The foundation's membership _is_ the user community, elections run inside Agora itself using the civic machinery we designed, and the thing becomes what you said: a platform run by the people in it — with the one power nobody ever gets, enforced by license and charter alike: the power to close it or sell it.

**What you say no to:** venture capital with voting rights, any single revenue source above ~50%, CLAs, and trademark policies that require the org's ongoing goodwill.

---

## 6. The cheat sheet

|Question|Answer|Why|
|---|---|---|
|Open source?|Mandatory — copyleft (AGPL-family)|Trust must be auditable; malleability needs source; the fork-right is license-borne|
|CLA or DCO?|DCO|Makes the openness irreversible — _including by you_; CLAs enabled every famous rug-pull|
|What does the org hold?|Trademark, hosted infra, commons stewardship|Excludable things fund the commons; the code's freedom is never for sale|
|Where does the trademark live?|The foundation, with a published community policy|The WordPress lesson: never let the name become a weapon in a commercial fight|
|Nonprofit?|Foundation _over_ an operating company (steward-ownership)|Pure nonprofit can't pay the GPU bill; pure company drifts; the hybrid locks mission into ownership|
|Revenue?|Hosting + inference subscriptions — "free as in freedom, paid as in hosting"|Ghost/Proton model; buyers purchase compute and convenience, never influence|
|Investors?|None with votes; money without power only|VC = exit expectation = the drift machine; your instinct is correct|
|When?|License + constitution now; LLC at first dollar; foundation when it's real|Entities can wait; licenses and constitutions calcify on day one|

---

## 7. The one-sentence version

Open source isn't a preference for Agora, it's the load-bearing wall — a home for your memories must have inspectable walls and a legally guaranteed fire exit — so choose a hereditary license nobody (including you) can ever revoke, let the organization own only the name, the servers, and the duty of stewardship, structure it so it is _impossible to sell_ rather than merely not-for-sale, fund it by hosting the homes rather than by renting out the people in them, and remember the lesson every structure in the graveyard teaches: entities and licenses don't preserve visions on their own — they just buy time and leverage for the community that does.

And notice, one last time, the recursion that keeps showing up in this project:
you've designed the same aspiration at every scale—objects that remain portable,
lessons that are not silently erased by recovery, rooms people can leave, public
places resistant to capture, and stewardship that cannot casually be sold away.
The exact mechanisms and legal structure remain open, but the idea is one all the
way down: **whatever holds people's lives must be structurally incapable of
betraying them.** That's the actual invariant #0 of Agora. Everything else we've
talked about for this entire conversation has just been that sentence, wearing
different clothes.
