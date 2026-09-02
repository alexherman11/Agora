# Security — addendum: the two-sided model

**Supersedes the compartment architecture in [[Security]] §3 and the approval framing in §4.6 and §6.** The three nouns (§2), the coverage map (§5), the invariants (§11), and the conflicts list (§8) stand. This addendum is the version to build.

---

## 1. One line, two sides

Everything in the security document reduces to one boundary. Everything on the inside is trusted with itself. Everything that crosses the line is checked.

| Side | Contents | Trust |
|---|---|---|
| **the world** | objects, facets, the log, apps, lenses, workers, reconcilers, the daemon with root, its memory | the daemon is trusted with all of it |
| **the host side** | one small program: supervisor + keep + brokers | no model, no content, no personal data; it checks crossings and records them |

The seven compartments of §3 map onto this without loss:

| Was | Is |
|---|---|
| Surface | the person's client, talking to the host side over an authenticated channel |
| Keep | a table inside the host-side program |
| Brokers | functions inside the host-side program, one per resource class |
| World | the world |
| Witness store | the daemon's memory: data in the world's storage domain that is excluded from world snapshots; it holds no authority |
| Yard | a throwaway VM the host side starts on request, with explicit inputs and no keys |
| Gate | a validation step the host side runs on anything entering the world from outside |

This is Ring 0 and Ring 2 from [[Agora Spec|the core spec]], with Ring 0 named precisely: the supervisor already there, plus the keep, plus the brokers. Ring 1 (the daemon's persistent state) is data, not a compartment. Ring 3 (workers) is inside the world under the daemon's delegation.

## 2. The membrane rule

The host side is consulted at exactly three moments:

1. **A crossing.** An effect that is irreversible, external, credentialed, or physical: send, pay, post, print, open a device, use a secret, reach the network, touch the host filesystem, enter or leave a room. The broker checks the request against the ceiling, performs it, and writes a receipt.
2. **A ceiling.** A request that would exceed what the person delegated. The host side refuses and tells the daemon why; the daemon may propose raising the ceiling, which is a surface decision.
3. **An act of authorship.** The short list of verbs by which the person stays the author of their world (§4).

Everything else — every read, every write, every mint, every spec, every worker grant, every lens, every room share under the ceiling — is the daemon's judgment and never leaves the world.

## 3. Ceilings, not clicks

The keep holds delegation. On day one it holds roughly this, set once on the surface and changed rarely:

```
delegation to jeff:
  world:        root                               # everything inside the line
  workers:      may grant any subset of the above; grants expire with the task
  rooms:        may lend objects tagged shareable to members; may not give custody
  network:      allowed to [listed domains]; others require a ceiling change
  spend:        [$X] per day, [$Y] per action, without asking
  one-time:     first use of a new target asks once; after that, under spend
  devices:      microphone and camera only while a call object is active
  never:        enroll or remove a device; change this delegation; change recovery; vote
```

Below those lines the daemon acts without asking and without the host side knowing until an effect crosses. A click is how a line moves. The right default is generous inside the house and stingy at the door.

## 4. Acts of authorship

The verbs the person holds and the daemon never does, reduced to what actually constitutes ownership of a world:

- change the delegation (raise, lower, or revoke any ceiling);
- enroll or remove a device; change recovery;
- give custody of an object to another world;
- release a specific private fact into a room, beyond what the delegation already allows;
- erase;
- vote, or hold any civic credential.

Everything not on this list is delegable, and most of it is delegated on day one.

## 5. The keep

A table and a counter in the host-side program:

```
grants:      the delegation above, plus per-task worker grants the daemon issues
generation:  a monotonic revocation counter; every check compares against it
journal:     append-only, signed: ceiling changes, crossings and their receipts, revocations, restores, forks
keys:        in the device's secure enclave where available; otherwise in the host-side store
```

It is protected by three properties, not by machinery: it is small enough to read; it is unreachable from the world except through typed requests; it executes nothing. On restore or fork, the keep does not move, so nothing inside the restored world holds authority until the daemon's delegation is re-confirmed on the surface — one click, once, or automatic under a standing policy the person set.

## 6. What becomes convention and test, not system

Keep the ideas; defer the enforcement. Each becomes a rule the trusted projector follows and a test in the drill, and grows into a system only when a real attack shows the coarse version failing.

| Idea | Day-one form |
|---|---|
| trust classes (four) | two: *from the person*, or *not*; the projector wraps everything not from the person with its source |
| confidentiality classes (three) | two: *private*, or *shared to a named room*; the broker refuses a private-derived payload at any crossing to anyone else |
| the eight-rung ladder | three: see it, install it, run it with these grants |
| heat budgets | one rule: nothing from outside the person's world may interrupt; security warnings render on the surface, not in the field |
| composition analysis | one rule: workers get no shared writable directory and no network by default |
| deployment truth | one sentence in the client: what this mode exposes |

## 7. The spine to build

The smallest thing that can be attacked and can be lived in:

1. a SQLite store and an append-only log; five facets (`name`, `text`, `tags`, `file-backing`, `process.spec/status`); live and pinned references;
2. one reconciler (process) and the capability reconciler;
3. the assembler: projections at three tiers, salience from direct attention and recency only;
4. the host-side program: supervisor, the keep as above, one broker fronting a fake email service that accepts an irreversible action;
5. a surface: a chat client that shows the delegation and takes the six verbs in §4;
6. the daemon, in the world, with root.

*This spine is also [[Agora Spec]] §22, which is the maintained copy.*

Then the drill from [[Security]] §10, with raw clients that bypass the SDK — and, alongside it, the test that decides whether any of this was worth it: **after a few weeks, is the daemon noticeably better because of the object layer than the same model in a plain VM?** Memory that never dangles; "this" that resolves; a demo that comes back after a reboot without being asked.

## 8. What still holds

From the invariants in [[Security]] §11, unchanged: claims never become grants; effects never happen without one; grants never copy, rise, or survive rollback; enforcement lives outside the root it constrains; record before acting, never re-act on restore; the person can revoke, recover, and export without the world or the daemon cooperating.

One added: **inside the line, the daemon is trusted; at the line, the host side checks.** Everything above is that sentence, sized to fit a first build.

---

*Design specification. Bracketed values are open decisions. The Constitution remains authoritative.*
