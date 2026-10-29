# Community-built, civic and geographic knowledge graphs

*Research notes for Agora (first case: Seabright, ~200 neighbours). Gathered 28 Oct 2026 by a Claude research subagent via web search and fetch. Evidence labels follow AGENTS.md: everything below is **read** (from the cited page or search result) unless marked **recall** (my prior knowledge, not re-verified this session) or **imagined** (inference/design). Pages I only saw as search snippets are marked "(snippet)".*

## 1. OpenStreetMap: data model, tag governance, convergence, vandalism

### Takeaway
OSM runs a planet-scale graph on three primitive element types plus a completely free-form `key=value` tag layer; the vocabulary converged not by approval but by usage (Taginfo counts), documentation (the wiki), and above all by **editor presets**, which are controlled by editor maintainers rather than votes. Votes are explicitly non-binding. Quality control is mostly social and after-the-fact (full history, changeset review tools), and the worst vandalism wave came from an external game (Pokémon Go) that gave people an incentive to fake the map.

### Cited Findings
**Data model**
- Three element types, all taggable: **node** (lat/lon point; standalone feature or shape point of a way), **way** (ordered list of 1–2,000 nodes; a closed way can be an area), **relation** (general structure linking nodes/ways/relations; must carry a `type` tag that sets how its other tags are read, e.g. route, turn restriction, multipolygon). — [OSM wiki: Elements](https://wiki.openstreetmap.org/wiki/Elements)
- Relation members are ordered and carry a **role** (e.g. `from`/`to` in turn restrictions); an element may appear more than once. — [OSM wiki: Elements](https://wiki.openstreetmap.org/wiki/Elements)
- Tags: Unicode key/value, max 255 chars each, one value per key per element; semicolon multi-values exist but are not universal. "There's no fixed tag list"; the most common convention is preferred and Taginfo measures usage. — [OSM wiki: Elements](https://wiki.openstreetmap.org/wiki/Elements)
- Every element stores id, last editor (user + uid), timestamp, `visible` flag, `version`, and changeset; the server rejects an update whose version doesn't match (optimistic concurrency); full history of every element is kept. IDs are unique only per type. — [OSM wiki: Elements](https://wiki.openstreetmap.org/wiki/Elements)
- Areas with holes or >2,000 nodes need a multipolygon relation (outer + inner ways). — [OSM wiki: Elements](https://wiki.openstreetmap.org/wiki/Elements)

**Tag governance**
- The proposal process "records that a rough consensus exists"; draft on wiki → discussion on tagging list/talk page → possible vote. — [OSM wiki: Proposal process](https://wiki.openstreetmap.org/wiki/Proposal_process)
- Current rules: ≥2 weeks RFC (all talk-page discussion resolved) before voting; voting ≥2 weeks; approval needs **≥8 approve votes and ≥75% approval**, abstentions not counted. — [OSM wiki: Proposal process](https://wiki.openstreetmap.org/wiki/Proposal_process) (A 2015 revision used "8 unanimous or 15 total with majority" — [snippet of older revision](https://wiki.openstreetmap.org/wiki/Special:Diff/1143140/1150734))
- Approval is **non-binding** on "any mapper, software developer, or data consumer"; it is a documentation change. "OpenStreetMap does not restrict mapping to tagging schemes backed by an approved proposal." A proposal can be marked inactive when a tag reached de facto status without a vote. — [OSM wiki: Proposal process](https://wiki.openstreetmap.org/wiki/Proposal_process)
- An approved tag "will not be automatically rendered or added to presets"; proposers are told to go and request preset updates in iD, JOSM and StreetComplete. — [OSM wiki: Proposal process](https://wiki.openstreetmap.org/wiki/Proposal_process)
- The wiki itself notes that votes are not necessarily representative of all mappers and proposals are usually in English. — [OSM wiki: Proposal (snippet)](https://wiki.openstreetmap.org/wiki/Proposal)
- iD's preset repository (id-tagging-schema) says it is "not authoritative or definitive" and supports tags "based on practicality, usage, and community approval", but sometimes can't support a used or approved tag. StreetComplete's osmfeatures reuses this data. — [id-tagging-schema (npm)](https://npmjs.com/package/@openstreetmap/id-tagging-schema) (snippet)
- OSMF (2020): contentious tagging is "at best an unwelcome distraction; at worst development can be blocked"; iD "aspires to refrain from making decisions on what tags are appropriate" and aims to represent consensus in presets; OSMF asked iD to document its approach. — [OSM blog: Toward resolution of controversies related to iD](https://blog.openstreetmap.org/2020/06/08/toward-resolution-of-controversies-related-to-id/) (snippet)
- Mailing-list critics (2018) argued that whoever controls presets steers how mappers tag, and asked for verifiable preset principles and alternative preset sets; iD's lead developer said preset decisions mostly happen "because someone asked us to in a ticket or pull request". — [tagging list 2018](https://lists.openstreetmap.org/pipermail/tagging/2018-June/037401.html); [talk list 2019](https://lists.openstreetmap.org/pipermail/talk/2019-September/083293.html) (snippets)

**Convergence of the vocabulary**
- As of June 2017 Taginfo counted >89 million distinct tags; wiki documentation is incomplete and has conflicting versions across translations. Mocnik, Zipf & Raifer studied documented vs actual use and changing scope/granularity. — [The OpenStreetMap folksonomy and its evolution (2017)](https://research.utwente.nl/en/publications/the-openstreetmap-folksonomy-and-its-evolution/) (snippet)
- A 40-city Taginfo study found mappers often do not follow the wiki's "useful combinations": Taginfo listed 107 other keys used with `amenity=restaurant` with no clear common subset. — [MDPI IJGI 5(12):232](https://www.mdpi.com/2220-9964/5/12/232) (snippet)
- In collaborative tagging generally (del.icio.us), per-resource tag frequencies converge to power-law distributions. — [ACM TWEB 2009](https://api.crossref.org/works/10.1145%2F1594173.1594176) (snippet; not OSM)

**Vandalism and quality control**
- OSMCha is a rule-based QA tool that automatically flags suspicious changesets on geometry/tag plausibility, edit size, and contributor behaviour; a 2026 ISPRS paper analysed 740,038 OSMCha changesets in Japan (spatiotemporal analysis, not an accuracy evaluation). — [ISPRS Archives L-4-W1-2026](https://isprs-archives.copernicus.org/articles/L-4-W1-2026/275/2026/) (snippet)
- OVID (Tempelmeier & Demidova) is an attention-based changeset classifier beating baselines by 4.7 F1 points on real vandalism; authors note labelled vandalism data is scarce and prior work used synthetic data. — [arXiv 2201.10406](https://arxiv.org/abs/2201.10406) (snippet)
- **Pokémon Go wave (2016–17):** players added fictional parks, footpaths, lakes for in-game advantage (believed to affect "nests"); a SotM 2019 talk analysed the life cycle of this "carto-vandalism". — [SotM 2019 talk](https://pretalx.com/sotm2019-at/talk/VPXQAV/) (snippet). A Florida mapper's anecdotal estimate: ~15% of parks fake; mappers also reported paths/cycleways/residential roads retagged as footways; many players also made good-faith edits and the game increased editor numbers. — [talk-us list, 2017](https://lists.openstreetmap.org/pipermail/talk-us/2017-January/017044.html) (snippet; anecdotal). No "smoking gun" that game spawns derived from OSM was found at the time — [BushmanK diary](https://www.openstreetmap.org/user/BushmanK/diary/40341) (snippet). Niantic adopted OSM as Pokémon Go's base map in 2017 — [OSM 20th birthday timeline](https://birthday20.openstreetmap.org/timeline/2017-niantic-switches-to-openstreetmap-as-the-base-map-for-pokemon-go) (snippet).

### Inferences
- **(imagined)** OSM shows that a free vocabulary can work at scale *only because* three things carry the governance load: (a) usage statistics as the arbiter (Taginfo), (b) shared documentation of meanings, and (c) the editors' preset lists, which are where vocabulary actually meets ordinary contributors. For Agora, the analogue of presets is the lens/kind picker people see when they add a thing; whoever curates that list effectively governs the vocabulary, so it should be a visible, forkable world object with its own history, not code.
- **(imagined)** Non-binding approval + "any tags you like" fits "everyone may always fork": vocabulary choices are documentation, and anyone can extend; convergence comes from tools and usage. The cost is tag sprawl (89M distinct tags) and inconsistent combinations — tolerable at 200 neighbours if usage counts are shown at the point of tagging.
- **(imagined)** Optimistic versioning per element + full history + changeset grouping is a cheap, proven base for community review and revert at small scale; Agora's event log already plays this role.
- **(imagined)** The Pokémon Go lesson: when map data drives a reward (in Agora, possibly "fog of war" unlocks or discovery), people will fabricate map data to earn it. Keep reward signals decoupled from the shared factual layer, or require a second neighbour to confirm features that drive rewards.

### Gaps
- No measured data found on how strongly iD presets drive tag adoption (only opinion and anecdote).
- No precision/recall study of OSMCha.
- Did not reach OSMF Data Working Group policies or the Local Chapters model; small-community OSM governance (e.g., local mapping groups) not examined.

## 2. Wikidata and Wikipedia communities: properties, classes, WikiProjects, notability, disputes

### Takeaway
Wikidata governs its schema (properties) through a public proposal channel with support/oppose discussion, closed by uninvolved higher-rights editors; creating properties is fast, deleting is slow, and most controversial threads end without consensus. Item admission is governed by a deliberately vague three-part notability rule, the most interesting of which is "structural need" — an item may exist because other items need it.

### Cited Findings
- Study of Wikidata discussion channels: ~481,000 threads / 1.26M posts overall; deep sample of 69 threads (Property proposal, Properties for deletion, Requests for comment). 30% of sampled threads controversial (RfC 52%, deletion 30%, property proposal 9%). — [Agreeing and Disagreeing in Collaborative KG Construction (arXiv 2306.11766)](https://arxiv.org/html/2306.11766v3)
- 62% of controversial threads ended without consensus (vs 38% of non-controversial). Property creation is much faster than deletion; "a couple of votes" can settle a creation. Threads are closed by an uninvolved editor with higher rights (including admins); some closed for inactivity; how closers decide is unclear. — [arXiv 2306.11766](https://arxiv.org/html/2306.11766v3)
- Conflict is rare (~7% of codes; ~1% of controversy participants are disruptors). 95% of controversial threads concern knowledge-engineering practice (modelling), only 20% fact accuracy. Debates typically involve 2–4 people; support/oppose votes often lack justification. Authors recommend clearer, findable policies and tools to keep contributors engaged until consensus. — [arXiv 2306.11766](https://arxiv.org/html/2306.11766v3)
- Roszkowski (2024) models adding a property as a socio-epistemic process (initiation, knowledge work, closure) and finds ontology change is institutionalised through community-accepted regulations. — [Journal of Documentation, doi:10.1108/jd-01-2024-0008](https://doi.org/10.1108/jd-01-2024-0008) (snippet)
- A community member reports a property proposal must be open ≥7 days with majority support (secondary, unverified). — [greaterwrong comment](https://www.greaterwrong.com/posts/xZKGEKMuozFuGzCvK/some-dynamics-around-project-organization/comment/WXjLpQ2FnAeHLB2qd) (snippet)
- Notability: an item is acceptable iff (1) it has a sitelink to a Wikimedia page, (2) it refers to a clearly identifiable entity describable by serious public references, or (3) it "fulfills a structural need", e.g. needed to make statements in other items more useful. The guideline is "intentionally left a bit vague"; disputes go to a deletion request, "the final decision is always up to the community." — [Wikidata: Items](https://www.wikidata.org/wiki/Wikidata:Items); [NLL2024 data modelling slides](https://upload.wikimedia.org/wikipedia/commons/8/83/NLL2024_-_Data_modelling_in_Wikidata.pdf) (snippets; live policy page not fetched)

### Inferences
- **(imagined)** "Structural need" is directly useful for Agora's kinds: a thing earns existence if other things refer to it (a street, a group, a recurring event), not only if it is "notable". That is a graph-native admission rule that suits a neighbourhood where nothing is notable to the outside world.
- **(imagined)** Wikidata's asymmetry (cheap to add a property, expensive to remove) is a pattern Agora will reproduce; plan for deprecation/supersession rather than deletion, which matches the desk's "supersede with a banner" doc rule.
- **(imagined)** Most disputes are about modelling, not facts. In a 200-person community with non-technical members, modelling disputes should be absorbed by agents/stewards and kept out of neighbours' view; fact disputes (is this bench still here?) are the ones neighbours can settle.
- **(imagined)** Scale difference: Wikidata's closer-with-elevated-rights pattern needs a pool of uninvolved experienced editors; in Seabright there may be 2–5. A rotating steward role or "two neighbours who weren't in the thread" is the scaled-down version.

### Gaps
- WikiProjects' role in curating class hierarchies and property constraints not researched this session (recall: WikiProjects publish data models and constraint templates, property constraints flag violations — not verified).
- Wikipedia dispute handling (talk pages, RfC, ArbCom) not researched beyond the Wikidata RfC channel.
- Live text of Wikidata:Notability not fetched; reform discussion status unknown.

## 3. Civic and local knowledge graphs: open data, Open Referral/HSDS, civic tech, asset mapping, PGIS

### Takeaway
The durable civic graphs are narrow, shared *vocabularies* for one domain (HSDS for services: organisation → service → location → schedule) with a profile mechanism for local variation, and simple loop-closing tools (FixMyStreet) where a report visibly leads to an outcome. Asset mapping and participatory GIS are rich as processes but have thin outcome evidence and are constrained by staff, time and funding.

### Cited Findings
- HSDS is an exchange format for machine-readable data about health, human and social services — where they are and who provides them — intended to share directory data as open data for any third-party system; the FAQ calls it a common vocabulary letting directories exchange data. — [HSDS overview](https://openreferral.readthedocs.io/en/latest/hsds/overview.html); [HSDS FAQs](https://openreferral.readthedocs.io/en/latest/hsds/hsds_faqs.html) (snippets)
- HSDS 3.0 docs cover schema and API references, publication formats, a logical model, and guidance on identifiers, schedules and taxonomies; **profiles** let local variants be defined as changes to base schema files (JSON Schema 2020-12). — [HSDS 3.0 docs](https://github.com/openreferral/specification/blob/3.0/docs/hsds/overview.md); [profiles](https://openreferral.readthedocs.io/en/latest/_sources/hsds/profiles.md.txt) (snippets)
- HSDA (companion API) covers accessing, updating, exchanging and synchronising directory data; an older version was versioned independently of HSDS. — [HSDA](https://github.com/openreferral/specification/blob/8bb7de5c1c75f7ca20add5506b0da5c79afe318f/docs/hsda/index.md) (snippet; possibly outdated)
- Adoption claim (unverified, self-description by one publisher): Findhelp, United Way 211 and Unite Us use HSDS. — [Feeding America/feedam HSDS page](https://feedam.org/hsds) (snippet)
- FixMyStreet: World Bank-linked analysis of ~400,000 reports found people whose first report was fixed were **54% more likely to report again**. — [mySociety research summary](https://www.mysociety.org/2014/12/08/research-on-the-impact-of-mysocietys-digital-tools/) (snippet)
- In Barnet, 52% of FixMyStreet reporters had never reported an issue to the council before. — [Centre for Public Impact case study](https://www.centreforpublicimpact.org/case-study/public-engagement-in-uk) (snippet)
- mySociety warns FixMyStreet data cannot fairly compare areas and does not endorse ranking areas with it; it issued a statement on misuse of its data (2024). — [mySociety statement, Feb 2024](https://www.mysociety.org/2024/02/06/statement-from-mysociety-regarding-misuse-of-fixmystreet-data/) (snippet)
- Neighbourhood mapping by residents (street-by-street walks) used in evaluating an infant-mortality programme to capture assets and context. — [Aronson et al., Maternal and Child Health Journal 2007](https://www.springermedicine.com/neighborhood-mapping-and-evaluation-a-methodology-for-participat/21690282) (snippet)
- South LA PGIS study mapped assets (streetlights) and challenges (crime hotspots) around park access; authors note participatory mapping is used sparingly in public health. — [MDPI IJERPH 15(4):825](https://mdpi.com/1660-4601/15/4/825) (snippet)
- Community GIS success depends on technology, time, staff expertise and funding; most community organisations lack staff/resources to build their own. — [Evaluation Exchange: geographic data for neighborhood revitalization](https://archive.globalfrp.org/evaluation/the-evaluation-exchange/issue-archive/evaluating-community-based-initiatives/using-geographic-data-for-neighborhood-revitalization) (snippet)
- A Chicago project built participatory asset-mapping infrastructure from VGI concepts, participatory design and free/open tools. — [Chapman health sciences article](https://digitalcommons.chapman.edu/health_sciences_articles/8) (snippet)

### Inferences
- **(imagined)** HSDS's shape (organisation, service, location, schedule, contact, taxonomy term) is a ready-made kind set for Seabright "groups" and "events" that would also let Agora export to/import from 211-style directories. Its *profile* mechanism (local deltas over a base schema) is the same idea Agora needs for per-community kinds over a shared base.
- **(imagined)** FixMyStreet's 54% shows the engine of a civic graph is closing the loop visibly. Agora's community map should show what happened to a report/request, not only collect it.
- **(imagined)** mySociety's ranking warning generalises: aggregate community data invites league tables and misuse; Agora should decide which aggregates exist at all.
- **(imagined)** PGIS/asset mapping fails on staff/time; personal agents could be the "GIS staff" non-technical neighbours lack — but only if the agent proposes and a human confirms.

### Gaps
- Code for America (brigade network wind-down, GetCalFresh) and mySociety's MapIt/TheyWorkForYou were not researched this session.
- No rigorous before/after outcome study of asset mapping or PGIS found.
- HSDS 3.0 changelog and sync details not read.

## 4. Social graphs and local platforms: linking people, places, events; harms and mitigations

### Takeaway
The strongest mitigations in local platforms are structural, not algorithmic: Front Porch Forum's human pre-moderation of every post into a daily digest, Nextdoor's friction in the crime-report form, and opt-in, off-by-default location sharing. Location itself is the most dangerous datum: four coarse spatio-temporal points uniquely identify 95% of people, and aggregate "anonymous" heatmaps leak sensitive places.

### Cited Findings
**Front Porch Forum (Vermont)**
- Every post is reviewed by human staff before publication and sent as community-specific email digests; roughly half of ~30 staff do civility enforcement; only community members using real names may post; personal attacks and hateful content off-limits. — [Boston Globe, 5 Dec 2024](https://www.bostonglobe.com/2024/12/05/business/front-porch-forum-social-media-network-vermont-williamstown) (snippet); [New_ Public: The Vermont miracle](https://newpublic.substack.com/p/the-vermont-miracle-how-one-local) (snippet)
- Criticism: opacity — a declined post cited ToU §2.6 (repeating similar content/dominating discussion); critics complain of one-size-fits-all moderation. — [Rutland Herald commentary](https://www.rutlandherald.com/opinion/commentary/rkiouak-fpf-decides-what-you-hear/article_2d1e39c8-92ee-5d75-b32c-1520e21ac650.html); [Seven Days](https://www.sevendaysvt.com/?p=154502) (snippets)

**Nextdoor**
- 2016 redesign of the crime & safety form to resemble a police/dispatcher questionnaire (height, clothing, age) and prompt for more detail when race is mentioned; company-reported 75% reduction in posts with racial profiling in test markets; rolled out to 110,000 neighbourhoods; also ~50% increase in abandoned posts; inspired by Jennifer Eberhardt's research. — [Nextdoor blog, Aug 2016](https://blog.nextdoor.com/2016/08/24/reducing-racial-profiling-on-nextdoor); [BuzzFeed News](https://www.buzzfeednews.com/article/carolineodonovan/nextdoor-rolls-out-product-fix-it-hopes-will-stem-racial-pro) (snippets)
- BuzzFeed (May 2017) found racial profiling still prevalent and measures incompletely implemented. — [Wikipedia: Nextdoor](https://Www.wikipedia.org/wiki/Nextdoor) (snippet)

**Location sharing (Snap Map / Zenly)**
- Snap Map (2017): safety experts warned of stalking and bullying; location sharing off by default; Ghost Mode hides location but posts to public "Our Story" still appear on the map regardless of setting; ex-friends/ex-partners retain access via friend lists. — [NNEDV Safety Net: Snap Map](https://www.techsafety.org/blog/2017/7/6/whats-the-deal-with-snap-map); [INFORRM blog](https://inforrm.org/2017/07/08/snapchat-snap-map-the-spy-who-snapped-me-sophie-kay/) (snippets)

**Aggregate location leakage**
- Strava's 2018 global heatmap revealed military bases and soldiers' routines (e.g., jogging loops at forward operating bases); individuals could be identified under default settings. Strava restricted street-level detail to registered users and simplified opt-out. — [Wareable](https://www.wareable.com/sport/strava-heat-maps-military-bases-5682); [Yahoo/Engadget](https://sg.finance.yahoo.com/news/exposing-secret-military-bases-strava-194900382.html) (snippets; press, not peer-reviewed)
- Strava's CEO: users "in areas without other activity density" inadvertently exposed locations. — [same](https://sg.finance.yahoo.com/news/exposing-secret-military-bases-strava-194900382.html) (snippet)
- de Montjoye et al. 2013: 15 months of mobility data on ~1.5M people; **four spatio-temporal points uniquely identify 95%** at hourly / cell-tower resolution; uniqueness falls only as roughly the 1/10 power of resolution, so coarsening gives little anonymity. — [Scientific Reports, PMC3607247](https://pmc.ncbi.nlm.nih.gov/articles/PMC3607247)

### Inferences
- **(imagined)** For a 200-person place, Strava's "low density" failure is the default condition: any aggregate layer (heatmap, fog-of-war revealed tiles shared with others) over few people effectively identifies individuals and homes. Fog-of-war exploration should stay private to the explorer by default (consistent with Agora's "visual state not in world" rule); any shared derivative needs k-anonymity-style thresholds that 200 people may never meet.
- **(imagined)** FPF's digest + pre-review is exactly what scales *down*: a few hundred people, slow cadence, one reviewer. Personal agents could draft and a human steward (rotating) could approve. Its weakness — opaque rejection — is fixable with a visible, forkable rule set and a reason on every decline.
- **(imagined)** Nextdoor's lesson: shape the input form, not just moderate the output. Agora's kinds (e.g. a "safety report" kind with required descriptive fields) are the lever; friction is acceptable (50% abandonment was the point).
- **(imagined)** Ghost Mode's leak (public posts still placed on the map) shows that location must be a property of each object, not a global user setting; every geotagged thing needs its own visibility.

### Gaps
- Meetup's event/group graph and Zenly (recall: Snap shut Zenly down in Feb 2023 — not verified this session) not researched.
- No peer-reviewed study of Snap Map harms found; only advocacy/press.
- No study of doxxing on hyperlocal platforms found this session.

## 5. Federated and forkable data: ActivityPub, AT Protocol, Solid; how vocabularies evolve

### Takeaway
AT Protocol has the most explicit answer to "how does a shared vocabulary evolve across independent parties": lexicons are owned by DNS-rooted namespaces, evolution is additive-only (new fields optional, no renames/type changes, unknown fields ignored, open unions), and breaking change means a new name. The fediverse evolves by JSON-LD extension and an informal FEP process with no authority over the core vocabulary, and moderates mostly by server-level blocklists, a heavy and conflict-prone burden. Solid is now stewarded by the ODI but adoption numbers are unknown.

### Cited Findings
**AT Protocol**
- "The authority for a Lexicon is determined by the NSID, and rooted in DNS control of the domain authority"; resolution does not recurse up or down DNS. — [atproto Lexicon spec](https://atproto.com/specs/lexicon)
- Evolution: "Any new fields must be optional"; "Types can not change"; "Fields can not be renamed"; closed unions cannot change; unions are open by default (types may be added, not removed). — [atproto Lexicon spec](https://atproto.com/specs/lexicon)
- "Unexpected fields in data which otherwise conforms to the Lexicon should be ignored" (at worst warnings). — [atproto Lexicon spec](https://atproto.com/specs/lexicon)
- Schemas are published as `com.atproto.lexicon.schema` records in an atproto repo, keyed by NSID; a DNS TXT record `_lexicon` links the domain authority to a DID (`did=`). — [atproto Lexicon spec](https://atproto.com/specs/lexicon)
- Style guide: put shared definitions in a separate `.defs` schema; breaking changes → new name/major version (e.g. `noteV2`). — [Lexicon style guide](https://atproto.com/guides/lexinomicon); [community example](https://tangled.org/desertthunder.dev/malfestio/tree/main/lexicons) (snippets)
- Bluesky "stackable moderation": a base layer from Bluesky plus user-chosen additional labelers; anyone can run a labeler by implementing two endpoints (`subscribeLabels`, `queryLabels`); Ozone, the in-house moderation tool, was open-sourced March 2024. — [Bluesky blog: stackable moderation](https://bsky.social/about/blog/03-12-2024-stackable-moderation); [Bluesky moderation architecture](https://docs.bsky.app/blog/blueskys-moderation-architecture) (snippets)

**ActivityPub / fediverse**
- (recall) ActivityPub is a W3C Recommendation (Jan 2018) on the ActivityStreams 2.0 vocabulary, extended via JSON-LD contexts — [W3C ActivityPub](https://www.w3.org/TR/activitypub/) (not fetched this session).
- FEP process (FEP-a4ed, Final) run by SocialHub, a liaison of the W3C SocialCG; maintainers say FEPs have no control over what is added to ActivityStreams; interim guidance is "use your own namespace"; FEP-2e40 (vocabulary extension process) was withdrawn; FEP-888d (draft) proposes w3id.org/fep namespaces. — [SocialHub: FEP-a4ed](https://socialhub.activitypub.rocks/t/fep-a4ed-the-fediverse-enhancement-proposal-process/1171?page=2); [FEP-2e40](https://socialhub.activitypub.rocks/t/fep-2e40-the-fep-vocabulary-extension-process/2972) (snippets)
- Server blocklisting is the main moderation tool of Mastodon admins (Bono et al., WebSci 2024). — [ISI publication page](https://www.isi.edu/results/publications/15611/an-exploration-of-decentralized-moderation-on-mastodon/) (snippet)
- Interviews with 12 moderators: blocklists vary widely in goals, inclusion criteria and transparency. — [arXiv 2506.05522](https://arxiv.org/abs/2506.05522v1) (snippet)
- Admins on larger instances struggle to find moderation resources (WatchGen, 2023). — [arXiv 2302.05915](https://arxiv.org/pdf/2302.05915.pdf) (snippet)
- 2026: community size strongly predicts rule development; federation interactions play a limited role. — [arXiv 2606.05069](https://arxiv.org/abs/2606.05069v2) (snippet)
- Shared "community boundary" blocklists have incited conflict (interviews with 9 users). — [Northeastern SEALab](https://sealab.sites.northeastern.edu/research/folk-risk-models-and-mutual-aid-on-federated-social-networks) (snippet)
- An admin: relying on per-user blocks "effectively asks our moderators to moderate the entire Fediverse." — [theATL.social post](https://yall.theatl.social/post/52447) (snippet; practitioner opinion)

**Solid**
- The ODI became Solid's steward in October 2024, maintaining open-source foundations, supporting standardisation in the W3C Linked Web Storage group, funding pilots; Inrupt is the commercial company. — [ODI news](https://theodi.org/news-and-events/news/odi-and-solid-come-together-to-give-individuals-greater-control-over-personal-data/) (snippet)
- No reliable 2025–26 pod adoption figures found; an older ~60,000 developer-pods figure dates from the early period. — [ODI blog](https://theodi.org/news-and-events/blog/evolving-the-web-with-solid/) (snippet); a July 2026 EDM Association/ODI webinar Q&A says many providers implement Solid under different hosting models but gives no numbers — [EDM Q&A PDF](https://edmcouncil.org/wp-content/uploads/2026/08/EDMWebinar_Solid-and-ODI_Q-and-A_20260714.pdf) (snippet)

### Inferences
- **(imagined)** AT Protocol's lexicon rules are a near-direct spec for Agora kinds under "everyone may always fork": (1) kinds are owned by a namespace, so a fork names its own; (2) additive-only evolution keeps old and new readers compatible; (3) unknown fields are ignored, so a forked community's extras don't break the original's lenses; (4) breaking change = new kind name, with supersession links. This also matches the AGENTS rule that design content is superseded, never deleted.
- **(imagined)** DNS-rooted authority does not fit a neighbourhood (neighbours won't own domains). Agora would need an equivalent root of authority — the community's own world/charter id — and a way for a person's private kinds to be promoted into the community namespace.
- **(imagined)** Stackable labelers map well onto personal agents: each neighbour's agent could subscribe to community and personal "labelers" (filters) rather than one central moderation; the community still needs a base layer.
- **(imagined)** Fediverse evidence suggests server-level federation decisions are the costliest, most conflict-prone part; if Seabright ever federates with other Agora communities, defaults should be "don't federate" and federation per-group or per-kind, not per-server.

### Gaps
- AT Protocol repo/account migration (PDS portability) not verified this session.
- Mastodon/fediverse geolocation or local-place features not researched.
- Solid's data model (RDF, shape trees, access control spec status) not researched.

## 6. Discovery and serendipity in place-based apps built on community POIs

### Takeaway
Niantic's games built a global POI graph by letting high-level players nominate and other high-level players review points (Ingress OPR → Wayfarer), then reused it across games; the review queue was noisy, and when the games changed hands the shared POI graph began to fork. The game incentive also leaked into OSM as fabricated features.

### Cited Findings
- Ingress players at level 10+ could nominate portals; every nomination went through a review (OPR); level-12+ players reviewed; accepted portals synced to Pokémon Go ~a day later if they met PokéStop rules. One reviewer estimated their review outcomes around "50/50" good vs bad and judged OSM's good-to-bad ratio far better (anecdote). — [OSM user diary comments, Tim Couwelier](https://api.openstreetmap.org/user/Tim%20Couwelier/diary_comments) (snippet)
- Wayfarer (2019) let selected Pokémon Go players review nominations; review was framed partly as protecting delicate landmarks from sudden influxes of players. — [SlashGear](https://www.slashgear.com/pokemon-go-niantic-wayfarer-will-let-selected-players-review-interesting-spots-14595264) (snippet)
- After the Scopely takeover, "Wayfarer is no longer connected to Ingress"; Niantic Spatial (Ingress) had no review facility; players worry Ingress and Wayfarer/PoGo POI databases will diverge. — [Wayfarer community: Wayfarer and Ingress Updates](https://community.wayfarer.nianticlabs.com/t/wayfarer-and-ingress-updates-discussion/83723?page=2) (snippet)
- Imported POIs cause false "duplicate" rejections of real nominations; a remote-submission bug placed submissions at the last submitted location. — [Wayfarer community: duplicate rejected](https://community.wayfarer.nianticlabs.com/t/submission-marked-as-duplicate-and-appeal-rejected/43835) (snippet)
- Players asked for a public "Wayspot map" so they can see what exists. — [Wayfarer community: importance of a Wayspot map](https://community.wayfarer.nianticlabs.com/t/community-feedback-the-importance-of-a-wayspot-map/89743) (snippet)
- Pokémon Go-driven fake OSM features: see Section 1.

### Inferences
- **(imagined)** The POI graph outlived and outgrew its games — a sign that community-submitted points are the durable asset. For Agora, fog-of-war discovery should reveal *neighbours' contributed things* (a story attached to a corner, a group's meeting spot) rather than generic POIs, and the contributions belong to the community graph, not the game.
- **(imagined)** The Ingress/Wayfarer split is a corporate, unplanned fork with no merge path — the opposite of "everyone may always fork" done well. Agora's forks should keep shared ids and provenance so later reconciliation is possible.
- **(imagined)** Reviewer rank-gating (level 10/12) is a reputation gate; at 200 people that gate is "known neighbour", which FPF's real-name membership already provides.
- **(imagined)** Hiding the existing dataset (no Wayspot map) produced duplicates and frustration; the shared layer should be browsable by contributors.

### Gaps
- No peer-reviewed study of serendipity/discovery effects in location-based games found this session (e.g., effects on physical activity or neighbourhood exploration).
- Niantic's 2025 sale of its games to Scopely and the Niantic Spatial spin-out are inferred from the community thread, not verified against a primary announcement.
- Fog-of-war apps specifically (e.g., exploration trackers) not researched.
