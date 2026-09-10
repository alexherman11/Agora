# Rooms

**Vision essay, not an implemented multiplayer contract.**

A room could be a persistent place where people read, work, talk and make things
together. Think of writing with a friend while sources, a conversation and a shared
playlist remain nearby. Each person can have their own view and assistant without
turning the entire experience into someone else's screen share.

Stable subjects and explicit actions are useful foundations, but they do not
automatically supply replication, offline editing, permissions, presence, leases
or collaboration semantics. Different applications may need different approaches.
The project has not chosen one custody topology, one room log or one CRDT for all
shared work.

Useful questions include what is shared, what stays personal, how someone leaves,
what remains after a session, and how conflicting edits are explained. A room
could share a document while keeping attention history and drafts private. A
participant might retain a permitted copy without taking anyone else's authority.

Try a concrete two-person workflow before designing a federation: comment on the
same memo, work offline, reconnect, resolve a conflict, then leave with a useful
artifact. Let the experience determine what should become common infrastructure.
See [[Agora Spec]], [[Objects and Facets]] and [[Security]].
