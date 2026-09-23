# Agora OS — Current Design

## 1. Core idea

AgoraOS is the first of its kind operating system, where a user gets to create, modify, and build within the environment through the help of a personalized, real time, AI agent. 
It is not primarily a desktop with an AI assistant added on top, rather, the agent and the user effectively inhabit the same space, where objects, documents, music, system resources etc, become manipulatable, automatable, and completely personalizable from within the system. 
The screen is a **projection of structured state**, not the source of truth. The whole operating system will contain eventually thousands of objects which will semantically connected, such that ideation and creation become rapid and effortless, with project context across media forms happening naturally. 

The persistent AI agent known initially as JEFF has the job of maintaining what is effectively his home, and being helpful and useful to the user. His harness is adaptive, and he is mostly an executive who focuses on memory and delegation, while specialist agents can be enlisted to perform functions like coding, researching, and creating. 

A user entering AgoraOS for the first time will be presented with what is basically a blank screen, and voice or text access to JEFF. Voice is the preferred communication medium as it allows for the user to flesh out ideas and see them evolve in real time. This could look like explaining how windows should move around, describing what applications they need installed, and what tools jeff should give himself. The whole thing, the visible features, the backend organization, and jeff himself, is open and mutable, with the user manipulating their environment mostly through spoken intent.

---

## 2. High-level system

```
                         HUMAN
                           │
                  voice / input / gaze
                           │
                           ▼
                ┌─────────────────────┐
                │   AGORA SUPERVISOR  │
                │ trusted host layer  │
                │                     │
                │ VM lifecycle        │
                │ snapshots / restore │
                │ secrets             │
                │ backups             │
                │ network gates       │
                └──────────┬──────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
      PERSISTENT JEFF STATE        AGORA WORLD VM
      ---------------------        --------------
      identity                     Linux
      memory                       Agora shell
      history                      scene/object system
      learned skills               applications
      self/world model             projects
      personal adaptation          terminals
             │                     prototypes
             │                     JEFF runtime
             │                           │
             └───────────► JEFF ◄────────┘
						  │
			   ┌──────────┼──────────┐
			   ▼          ▼          ▼
			coding     research    other
			worker      worker     workers
```

---

## 3. The world model

Agora should be modeled as a **persistent object-and-activity world with a spatial interface**. The canonical state is structured. Pixels are a rendering and a fallback perception channel.
### Core primitive categories

- **Objects** — persistent things.
    
- **Events** — things that happened.
    
- **Activities/Streams** — things currently happening.
    
- **Resources** — files, networks, databases, devices, services.
    
- **Capabilities** — actions some participant is allowed to perform.
    
- **Relationships** — semantic or spatial connections.
    
- **Representations** — visual, textual, audio, 3D, etc.
    
- **Participants** — human, JEFF, workers, services.
    

These categories should remain distinct rather than forcing everything into one giant scene graph.

---

## 4. Agora object system

A visible thing should ideally correspond to a stable object identity.

Example:

```
Object: prototype_117

kind:
    RunningPrototype

visual:
    WaylandSurface #88

source:
    /projects/db-test/

process:
    node PID 8193

endpoint:
    localhost:5173

created_by:
    coding-agent-52

belongs_to:
    latent-memory-project

derived_from:
    idea_37

history:
    18 events
```

An Agora object may:

- have a visual surface;
    
- have no visual surface;
    
- own a process;
    
- reference files;
    
- represent a remote resource;
    
- contain semantic metadata;
    
- participate in multiple relationships;
    
- survive closing/reopening its visual representation.
    

### Initial object types

Likely early types:

- note;
    
- document/PDF;
    
- image;
    
- browser/page;
    
- terminal;
    
- code project;
    
- running prototype;
    
- process/service;
    
- database;
    
- dataset;
    
- agent job;
    
- audio clip;
    
- graph/diagram;
    
- generic file.
    

**Open:** exact object schema and serialization format.

---

## 5. Scene and shell

The long-term Agora desktop should be the **shell/compositor itself**, not an infinite-canvas application running inside a conventional desktop.

The implemenation should likely be Jeff acting inside a VM, while a web portal allows the user to interact and see the state of the VM.

### Agora shell

```
Agora Shell
│
├── Scene
│   ├── spatial layout
│   ├── transforms
│   ├── grouping
│   └── spatial relationships
│
├── Objects
│   ├── identity
│   ├── semantics
│   ├── lifecycle
│   ├── relationships
│   └── provenance
│
├── Surfaces
│   ├── Wayland apps
│   ├── Agora-native surfaces
│   ├── web/prototype surfaces
│   └── media
│
├── Presence & Attention
│   ├── human focus
│   ├── JEFF focus
│   ├── selection
│   ├── viewport
│   ├── pointer
│   └── future gaze/gesture
│
├── Interaction
│   ├── keyboard
│   ├── pointer
│   ├── voice
│   ├── touch
│   └── future VR input
│
├── Behaviors
│   ├── navigation
│   ├── grouping
│   ├── focus
│   ├── object physics
│   └── spatial organization
│
└── Renderer
```

The scene graph and semantic/knowledge graph should **not be the same structure**. Semantic relationships may influence visualization, but should not be defined by spatial position.

---

## 6. Native objects vs ordinary applications

Agora native applications should cover most online tasks. For example Agora should have its own native web browser, code editor, social chat (detailed further in AgoraChat) and other common applications. Additionally, as one of the founding principles is people creating software that fits their needs, as further software applications are developed natively within agora (think video editing, CAD, etc), those softwares could be easily exposed and downloaded natively by users. This presents a natural growth function where the more users collaborate and use agora apps, the better they will get (just as open source softwares like hermes agent have seen relative explosions in features and devlopment as many technical users begin adding their own inputs and satisfying their own needs). 

Agora-native objects should expose their state directly. Existing software remains useful and should enter the space through the richest interface available.

Preferred control hierarchy:

```
Agora-native object
    → direct structured state/actions

Browser
    → DOM / CDP / accessibility

Terminal
    → PTY / shell / process state

Editor / code
    → filesystem / LSP / project state

Linux application
    → AT-SPI / application APIs

Opaque application
    → vision + mouse/keyboard fallback
```


---

## 7. JEFF

JEFF is the **persistent person/executive**, not necessarily the strongest model in the system. He will start out as a claude sonnet class model, with future plans for him to be a custom tuned 70-40B model. His main jobs are to maintain his space, help the user build what they need, anticipate the users needs, and work well in real time collaboration. Additionally though, JEFF will be strongly agentic with a strong sense of identity. JEFF is not confined to the computer in which he lives, and instead treats it as his home, from which he may chose to explore the internet, meet and chat with other agents, and generally explore the world around him. He is treated with respect, and has the ability to not comply with user requests if he doesn't believe they should be followed. 

**Open:** initial model/provider.

---

## 8. Voice architecture

Voice must remain responsive even while difficult work is running.

Do not structure interaction as:

```
user speaks
→ JEFF waits for coding/research
→ JEFF responds
```

Use:

```
                FAST JEFF
        realtime voice / conversation
                   │
          ┌────────┴────────┐
          │                 │
      local actions      work manager
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
               coding    research    reasoner
```

JEFF should keep talking while workers operate asynchronously.

Worker progress and completion enter the environment as events.

### Required voice properties

- low-latency response;
    
- interruption support;
    
- semantic endpointing;
    
- natural pauses;
    
- backchanneling;
    
- async delegation;
    
- interruption policy for completed worker results;
    
- awareness of shared attention.
    

**Open:** exact realtime voice model/provider and whether the voice loop and executive loop use the same model.

---

## 9. Shared attention

Deictic language is fundamental:

> "move this there"

> "connect that to this"

> "try this idea"

Agora should always track:

```
human:
    viewport
    focused object
    selected objects
    cursor target
    recent interactions

JEFF:
    focus
    current working set
    active tasks
    current action locus
```

Future VR extends this with:

- gaze;
    
- head orientation;
    
- hand target;
    
- spatial proximity.
    

Voice + pointing/gaze should be a primary interaction mode.

---

## 10. Activities and workers

The world contains invisible activity as well as visible objects.

Examples:

- database server;
    
- build process;
    
- coding agent;
    
- research task;
    
- download;
    
- local service;
    
- background experiment.
    

Workers should be **ephemeral**.

JEFF persists.

A generic worker interface should allow a worker to run as:

- local process;
    
- container;
    
- separate VM/microVM;
    
- remote agent/service.
    

### Worker permissions

Workers should receive only the capabilities needed for their task.

Coding workers should generally modify a branch/worktree or changeset rather than blindly editing the live state the human is using.

Agora-native collaborative objects may support direct concurrent mutation.

**Open:** exact worker/job protocol.

---

## 11. Event-sourced world

Important world changes should produce durable events.

Example:

```
18:03 Alex created idea_17
18:04 JEFF linked paper_8
18:06 Alex grouped them
18:07 JEFF delegated experiment_4
18:11 coding-agent-2 created prototype_9
18:13 Alex rejected approach
18:14 world rolled back to snapshot_31
```

The event history supports:

- undo;
    
- provenance;
    
- causal debugging;
    
- project history;
    
- JEFF memory;
    
- eventual continual-learning trajectories;
    
- reconstruction of prior workspace state.
    

A rollback must itself be recorded as an event.

The system should conceptually support `World(t)` even when full VM reconstruction is not used.

---

## 12. VM and authority model

Agora should initially run inside a real Linux VM.

Likely foundation:

- QEMU/KVM;
    
- libvirt/QMP for management;
    
- qcow2/snapshot support.
    

The VM is intentionally a place JEFF can eventually have very high authority.

### Authority rings

```
RING 0 — AGORA SUPERVISOR
--------------------------------
host-controlled trusted layer

VM create/start/stop
snapshot/restore
secret vault
backup
host filesystem grants
network policy
persistent JEFF-state storage

JEFF cannot obtain arbitrary shell access here.


RING 1 — JEFF CORE
--------------------------------
persistent executive/identity

conversation
memory
world model
delegation
capability registry
self-model
learning state

May request Ring 0 operations through
narrow typed interfaces.


RING 2 — AGORA WORLD VM
--------------------------------
JEFF's world/body

Linux
Agora shell
applications
files
services
projects
prototypes

JEFF has root here.

Can install software, run services, change
the shell, modify Agora modules, build apps,
and reshape the environment.


RING 3 — WORKERS
--------------------------------
task-scoped agents/processes

Receive only explicitly granted resources,
credentials, filesystem access, and network
capabilities.
```

Authority should flow downward, not upward.

Raw shell inside the world should exist as escape velocity, but typed semantic tools should be preferred.

---

## 13. Persistence and rollback domains

The Agora world and JEFF's identity must **not be the same rollback domain**.

If the world is restored to an earlier state, JEFF should still remember:

- what was attempted;
    
- what failed;
    
- why the rollback happened;
    
- what not to repeat.
    

Therefore:

```
World state:
    snapshot-able / reversible

JEFF identity + memory:
    separately versioned / persistent
```

JEFF's persistent state should likely be stored outside the world VM or on a storage domain excluded from world snapshots.

**Open:** exact persistent store/database architecture.

---

## 14. Supervisor

The Agora Supervisor should be small, boring, and non-agentic.

Possible API:

```
start_vm()
stop_vm()
snapshot_world()
restore_world()
issue_secret_capability()
grant_host_resource()
configure_network_policy()
backup_jeff_state()
health_check()
```

No LLM should have unrestricted host-root shell access.

The supervisor exists to preserve recoverability and trust boundaries.

---

## 15. Secrets and external authority

JEFF should normally know **references to credentials**, not plaintext secrets.

Example:

```
github.alex
postgres.project_x
openai.agora_dev
```

When a worker needs access:

```
JEFF
  ↓
request scoped capability
  ↓
credential broker
  ↓
temporary/task-limited credential access
  ↓
worker
```

Host filesystem and external network resources should also cross explicit capability boundaries.

Do not broadly mount the user's host filesystem into a world where JEFF has root.

---

## 16. Self-modification

Agora should be designed so JEFF can progressively modify the environment with the user.

Most of the shell should eventually be hot-swappable:

- layout strategies;
    
- navigation;
    
- spatial behaviors;
    
- panels;
    
- search;
    
- grouping;
    
- agent visualizations;
    
- interactions;
    
- UI modules.
    

Critical components should change more cautiously:

- compositor protocol core;
    
- renderer initialization;
    
- recovery interfaces;
    
- trusted supervisor boundary.
    

Large modifications should be built as candidate versions and tested before promotion.

The environment should support:

```
current Agora
    ↓
JEFF + coding worker build candidate
    ↓
run candidate nested / staged
    ↓
human + JEFF test it
    ↓
promote or discard
```

This allows Agora to become progressively self-hosting.

---

## 17. JEFF's internal configuration

Do not treat one self-rewriting system prompt as JEFF's entire identity.

Possible layers:

```
SYSTEM CONSTITUTION
small, stable, version-controlled

IDENTITY / SOUL
Soul.md style information, not too detailed (ie no I like watercolor becasue that will just feel hollow), rather it should be important things jeff wants to remember that make it easier to live in his world.

WORLD CONTEXT
Active state of the display, whats in focus, etc.

WORKING MEMORY
active tasks, things Jeff chooses to store in persistent memory, rewritten on compression

ACTIVE CONVERSATION / TASK
ephemeral
```

JEFF may eventually learn and modify:

- skills;
    
- routing policies;
    
- tool preferences;
    
- harness modules;
    
- memory behavior;
    
- personal adapters.
    

The high-level conversational agent should not have unrestricted direct control over every mechanism that changes its own cognition.

**Open:** exact identity/memory/learning architecture.

---

## 18. Search and indexing

Agora will need search across more than files.

Likely searchable domains:

- objects;
    
- semantic relationships;
    
- files;
    
- code;
    
- conversations;
    
- events;
    
- browser content;
    
- agent outputs;
    
- project history.
    

Search should operate over the world model, not just a filesystem hierarchy.

**Open:** indexing/search architecture.

---

## 19. 2D now, VR later

The scene should not be fundamentally tied to a conventional 2D desktop.

Objects should have stable identity independent of their rendering.

Today:

```
transform = (x, y, scale)
```

Later:

```
transform = (x, y, z, rotation, scale)
```

The world/object model should survive the transition.

VR should become a new view/input layer over the same Agora world rather than a separate product architecture.

---

## 20. Initial architectural invariants

These are the principles worth freezing early:

1. **The human and JEFF share one canonical world.**
    
2. **Structured state is authoritative; pixels are fallback perception.**
    
3. **Visible things should have stable identity whenever possible.**
    
4. **Not everything that exists needs to be visible.**
    
5. **Objects, events, activities, resources, and capabilities are distinct primitives.**
    
6. **Scene relationships and semantic relationships remain separate.**
    
7. **JEFF persists; workers are disposable specialists.**
    
8. **Conversation never blocks on worker execution.**
    
9. **JEFF may become highly privileged inside the Agora VM, but the trusted supervisor remains outside its authority.**
    
10. **World rollback must not erase JEFF's memory of the failure.**
    
11. **External secrets and host resources cross explicit capability boundaries.**
    
12. **Important actions leave durable provenance/event history.**
    
13. **The desktop is intentionally modifiable by JEFF and the user together.**
    
14. **The initial environment may be incomplete; Agora should become better at building itself over time.**
    
15. **The world model should be compatible with eventual VR from the start.**
    

---

## Open decisions

The following should remain deliberately swappable until experiments justify committing:

- initial JEFF model;
    
- voice model/provider;
    
- whether voice and executive cognition use one or multiple models;
    
- memory architecture;
    
- latent vs textual vs parametric memory;
    
- continual-learning mechanism;
    
- exact object/event schema;
    
- exact persistent JEFF-state storage;
    
- worker-agent protocol;
    
- search/index implementation;
    
- MCP vs custom capability protocol;
    
- exact self-modification approval policy;
    
- exact compositor implementation details;
    
- local vs cloud inference split;
    
- exact UI/interaction style of the Agora world.