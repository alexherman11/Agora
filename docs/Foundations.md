# Foundations

Status: design commitments. Implementation evidence is maintained separately.

## Computing that can change during use

Agora is an environment a person can use and reshape in conversation. Reading,
writing, browsing, organizing, creating software and working with other people
belong to the same environment. Ordinary use remains useful without customization,
and essential direct controls remain usable when a model is unavailable.

JEFF is a persistent conversational partner serving the person. A request can
become a view, a tool, a data structure, a skill or an ongoing service. The
environment must permit capabilities its platform authors did not anticipate.

This is an experimental design. Its quality is judged by useful work, continuity,
recoverability and the cost of introducing new behavior.

## Principles

1. **The person owns the environment.** Data, source and installed behavior must
   be inspectable and exportable. Forking must preserve useful material, not
   depend on the goodwill of a particular provider.
2. **Objects have enduring identity.** A note remains the same subject when
   moved, renamed, rendered differently or used by another tool. Identity is not
   a location or a credential.
3. **Representations can change freely.** The screen is a rendering of the world.
   Appearance and interaction belong to views, while meaningful durable state
   has an explicit owner.
4. **Native actions share a vocabulary.** Human controls, JEFF and installed
   programs use the same capability registry and world gateway. Attention may
   differ; there must not be a secret second application model for the agent.
5. **Native history is accountable.** Durable native-world changes are recorded
   through authenticated verbs. Tables and indexes derive from that history.
   Replay restores recorded facts without rerunning code or external effects.
6. **A computer contains more than native objects.** Linux files, processes,
   devices and remote systems have independent reality. Their observed status
   must not be confused with a desired state or an authoritative world fact.
7. **Behavior can be authored.** Interfaces, tools, skills and application data
   definitions are editable world content. General runtimes and host capabilities
   provide mechanisms; packages provide application behavior.
8. **Conversation never blocks on work.** JEFF should remain available while
   development and other jobs proceed. Asynchronous development workers are a
   horizon; responsive interaction is the enduring requirement.
9. **Freedom needs recovery.** Broad development authority is useful. Stop,
   backup, restoration and control over external authority must survive a broken
   authored interface or guest.
10. **Sharing does not imply surrender.** A room, remote service or imported
    package receives explicit authority. It does not inherit the local
    development owner's powers merely by becoming visible.

## Foundations that need precise scope

The event log is authoritative for native world state, not for every byte of a
Linux machine or the state of the internet. A snapshot is not semantic history.
A code rollback is not an undo of data migration or a previously sent message.

Guest-root authority and host-root authority are distinct. The person can allow
JEFF to control a guest computer while preserving a protected world service and
recovery outside that guest. This boundary must be implemented and tested.

A skill is a procedure, not a permission grant. A status is an observation with
provenance and freshness, not certainty created by naming a field “status.”

## Experience that should survive growth

A new note appears in the appropriate live views without manually editing their
source. A tool remains installed when its UI closes. Moving the chat panel does
not lose the conversation. A failed candidate does not replace the working
application. A working capability can be installed on a fresh compatible machine.

Social spaces, multiple devices, accessibility, offline use and legacy software
are part of the horizon. Their mechanisms should earn their complexity through
use rather than be assumed solved by the object model.
