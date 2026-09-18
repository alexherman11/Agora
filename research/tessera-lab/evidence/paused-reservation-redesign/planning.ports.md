# Planning ports for Trial 3

Agreed directly with the logistics and finance builders:

- `mission.dispatch {id,eventId}` moves a draft mission to dispatched and issues its packing lines. Dispatch reservation IDs are `eventId + "/" + line.id`.
- `mission.amend {id,eventId,sku,qty}` issues additional units to a dispatched mission. Its reservation ID is `eventId`. Planning supplies the guarded command; logistics and finance supply reactions on that same action.
- `reservation.return {id,eventId,qty}` is owned by logistics. `id` is the reservation ID. Finance reacts with the refund and ledger entry.
- `mission.close {id}` moves a dispatched mission to closed only when its reservations have zero outstanding units. There is no cancellation command in this redesign.
- Logistics owns `reservations.missionId`, `sku`, `issued`, and `returned`. Finance co-creates `reservations.unitPrice` at the same ID and owns the ledger. `missions.charged` remains lifetime issued charges.
- `missions.list` (mission rows), `missions.card` (role `mission-card`), and `missions.tools` remain stable extension addresses. `missions.reservations` is a nested list of reservations scoped to each mission.

All actions join their own and matching reaction effects against the same pre-action state. The planner never calls a logistics or finance action as a hidden step.
