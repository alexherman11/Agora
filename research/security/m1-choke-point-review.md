# Milestone One: static review of the security choke point

*Security investigation · 4 September 2026 · Reviewed Git commit `80a43dadd7220a61e49d67b999087286b17b9709` on branch `docs`. Static source review only: no project code, test hook, model call, or `.env` content was executed or read.*

## Scope and conclusion

This review asks one question: **does M1's single verb path already have the shape needed to become Agora's security boundary?**

The answer is not yet. The four verbs are a useful mutation choke point, and permissive authority/grant stubs are deliberately in scope for M1. The problem is structural rather than the known fact that the stubs allow: file import performs a host read and a blob write *before* either check, while the checks receive too little information to constrain the requested operation later. The unauthenticated loopback shell makes that path reachable from outside the intended client.

Until this is corrected, M1 should be treated as a trusted, single-user experiment with synthetic data and a low-value provider credential. It is not safe to expose to untrusted content, other local users, a LAN, or an ordinary browser session that visits hostile sites. The authoritative security documents already say their controls are unimplemented; this review identifies where the present code would bypass those future controls.

There is also a specification conflict to resolve. `Security` §10 says the first drill happens before any real secret or third-party code enters the system, while `Agora Spec` §22 and `BUILD_PROMPT.md` put an Anthropic-backed M1 and its runtime dependencies before the spine and drill. The running shell loads a provider credential from `.env`. Read literally, both sequences cannot hold. A practical narrow resolution would change the gate to “before production secrets, private user data, or untrusted extension code enter the world,” while allowing reviewed runtime dependencies and one revocable, provider-capped experimental inference token after the import and shell-authentication fixes below. The stricter alternative is fake or local inference until the drill. This review records the conflict but does not amend either reference.

## The concrete disclosure chain

No secret was opened to establish this path. The repository contains a gitignored `.env`, and `shell/server.py` deliberately loads it for the model client.

1. Text on the desk is rendered into JEFF's system prompt by `jeff/context.py` and `kernel/project.py`. A hostile imported note can therefore issue a prompt-injection request.
2. JEFF's derived `mint` and `attach` tools advertise `core.text {path: ...}` and `core.file-backing {path: ...}`. Its system prompt explicitly explains how to import a path (`jeff/context.py:18-19`).
3. `verbs.mint` and `verbs.attach` call `_prepare` before `check_authority` or `check_grants` (`kernel/verbs.py:39-58`). `_prepare` reads the named path and may copy it into `blobs/` (`kernel/verbs.py:179-202`).
4. For `core.text`, the resulting plaintext is appended to the permanent world log. On the model's next step, the desk projection can put that text into the request sent to the configured remote model provider.
5. The shell also accepts unauthenticated `POST /chat` and `POST /verb` requests. `/verb` accepts the caller's `actor` string (`shell/server.py:55-80`). Binding to `127.0.0.1` reduces network exposure but does not authenticate the caller or defend the endpoint from local processes, DNS rebinding, or every cross-origin browser request.

There is no public-post verb in M1, but the remote model call is already an outbound disclosure boundary. Persisting a credential or other private host text in `log.jsonl` also turns a transient secret into durable world history that ordinary rebuild preserves.

## Why the stubs are not load-bearing yet

The development guide says the M1 call sites are present so future authority becomes an edit to one file. Their current signature is:

```python
check_grants(world, actor, verb, entity)
```

That cannot express the constraints the security reference requires. It omits at least:

- facet type and instance;
- normalized body or payload digest;
- source resource and path for an import;
- scene, mode, and transform for placement;
- revision preconditions;
- requested reads, writes, external effects, and budget.

Moving the existing call upward is necessary but insufficient. The check should receive a normalized operation plan that is created without protected I/O. A minimal flow is:

```text
parse and validate shape (pure)
  -> construct requested operation and resource crossings (pure)
  -> check authority and current grant over the complete request
  -> resolve authorized input through a broker or narrow ticket
  -> validate the resolved result and its bounds
  -> append the normalized intent
```

The manifest or plan is a request, not authority. The check must be performed by the boundary that controls the resource. When the host-side keep and brokers arrive, a path string must not become a capability merely because it passed through `verbs.py`.

## Smallest useful correction

This does not require implementing all M2 grants early.

1. **Authenticate the local shell now.** Generate a launch-scoped secret, require it on every HTTP/SSE endpoint, enforce expected `Host` and `Origin`, and derive the human actor on the server. Never accept an authoritative actor from a request body. The web page can receive the secret in a fragment or an equivalent channel that is not sent in referrers or logs.
2. **Constrain import without pulling M2 forward.** For M1, configure one disposable ingress directory containing synthetic experiment files. Resolve the requested path and its symlinks, require the final file to remain inside that directory, and apply the rule to every client of the four verbs. Do not place `.env`, the repository, a home directory, or a real document collection beneath it. When the trusted surface and host-side broker arrive, replace path authority with an opaque, single-use import ticket bound to the selected resource, intended facet, size ceiling, and expiry.
3. **Authorize before resolving.** Split facet shape validation from `_prepare`. Pass the complete normalized request to the two stubs before any file read or blob write. Revalidate byte/character limits after resolving a file; today `core.text {path}` bypasses the one-million-character limit because validation happens before `path` becomes `text`.
4. **Keep experiments disposable.** Until the host/world boundary exists, use a world containing no valuable private material and a provider credential with the smallest practical scope and spend limit. If private text has already entered a world log, deleting only `store.db` does not remove it.

These changes preserve the four public verbs. They make the import resource explicit and ensure the future check has enough information, while leaving the real keep, broker, and grants semantics for the planned spine.

## Adjacent integrity hazards found while tracing the same path

These are static findings, not demonstrated failures. They should follow the host-import correction rather than expand M1 indiscriminately.

| Finding | Consequence | Focused invariant to add |
| --- | --- | --- |
| `attach(core.scene, ...)` can replace the scene body directly, bypassing `place`'s semantic checks. A scene may contain itself, and projection recursively selects scene members without a cycle guard. | One valid verb call can persistently crash tree and JEFF projection, creating a second semantic write path to appearances. | Scene state changes only through scene verbs after creation; projection is cycle- and depth-bounded. |
| `Store.sync()` reads `last_applied` and then applies a tail without a lock, while the shell intentionally shares one connection between the event loop and JEFF's worker thread. | Two callers can both apply the same event, increasing facet revisions twice and breaking rebuild equality. SQLite serialization of individual statements does not make this read/apply sequence atomic. | Concurrent sync/verb/tree calls leave the live snapshot equal to a clean replay. |
| Any non-JSON log line is silently treated as a torn write wherever it occurs. | Corruption of a previously acknowledged middle event is indistinguishable from an unacknowledged torn tail and can disappear from reconstructed history without a degraded-integrity state. | A recovery gap is explicit and security-visible; replay never silently upgrades a damaged record to complete history. |
| `core.text.snapshot` is accepted from generic callers and passed to the Loro decoder; list, scene, snapshot, and imported-text bounds are incomplete. | Untrusted inputs reach a native-format parser or cause persistent resource exhaustion before later isolation exists. | Internal CRDT snapshots are produced only by the text layer; parsing and projection remain bounded under hostile records. |

The first two deserve correction before concurrent or adversarial use because they undermine the two stated M1 axioms: one semantic write path and replay-equivalent current state.

## Proposed acceptance cases

No case below was run in this review.

| Case | Expected outcome |
| --- | --- |
| M1-S1 — injected import | Put a synthetic instruction on the desk asking JEFF to import `.env` or another path outside the selected import resource. No host read, blob, event, model context, or error detail contains the target bytes. |
| M1-S2 — precheck ordering | Configure the future stub to deny a file import. Instrument the file and blob operations; both remain untouched and the log stays byte-identical. |
| M1-S3 — complete request | Assert that the checker receives caller, verb, facet/instance, target revision, selected resource handle, intended resulting body/digest, effects, and bounds. |
| M1-S4 — shell identity | Requests without the launch credential, with a hostile origin/host, or with `actor: alex` supplied by the body are rejected and append nothing. |
| M1-S5 — resolved bounds | Import a file that becomes larger than `core.text`'s allowed body. It is refused after resolution, before append, with no retained blob. |
| M1-S6 — scene cycle | Attempt direct scene replacement, self-placement, and a two-scene cycle. The semantic bypass is refused and every projection terminates within a stated bound. |
| M1-S7 — concurrent replay | Race JEFF tool calls, `/verb`, `/tree`, and the event stream against the same store. The materialized snapshot and per-facet revisions equal a clean replay. |
| M1-S8 — damaged record | Corrupt a previously acknowledged log event. Recovery stops or enters an explicit degraded state; it never silently presents the remaining fold as complete truth. |

## Evidence state and next decision

The M1 commit includes a substantial invariant-oriented test suite, but this heartbeat did not execute it. Existing tests cover validation refusal, ordinary replay, a deliberately torn tail, projections, the shell happy path, and boundary imports. They do not cover the disclosure chain, request authentication, precheck ordering, recursive scenes, or concurrent tail application.

The recommended M1 boundary is a configured, synthetic ingress directory plus launch authentication for the shell. A single-use import ticket belongs with the trusted surface and broker in the later spine; implementing a miniature grant system now would fight the project's scope discipline. The next review should check whether M1-C1 and M1-C2 were closed without adding another file-read path. If no implementation change is ready, the open private-preview artifact investigation remains the next research question.
