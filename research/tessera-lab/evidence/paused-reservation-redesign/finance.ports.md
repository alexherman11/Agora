# Finance ports and received agreements

- Preserve trial 2 project fixtures: `projects/alpine` has 1000; `projects/ocean` has 400. `projects.available` is a counter.
- Finance owns `reservations.unitPrice`, a register number captured when a reservation is created. Logistics owns `reservations.missionId`, `sku`, `issued`, and `returned` on the same reservation ID.
- Dispatch reservation IDs are `eventId + '/' + line.id`; amendment reservation ID is `eventId`. Planning and logistics confirmed these IDs.
- Finance reacts to `mission.dispatch {id,eventId}` and `mission.amend {id,eventId,sku,qty}`. It co-creates the finance price field at those reservation IDs, debits the mission's project, and creates an immutable ledger record keyed `eventId`.
- Finance reacts to logistics' `reservation.return {id,eventId,qty}`; refund is `qty * reservations[id].unitPrice` from the original issue. Return ledger ID is `eventId`. No action calls another action.
- Planning confirmed `mission.close {id}` after all reservation quantities are returned. Finance keeps `missions.charged` as lifetime issue charges; it does not change on returns.
- Ledger fields are `missionId`, `projectId`, `kind`, `amount`, and `reservationId`; one ledger row per dispatch/amend/return event. Dispatch amount sums all line prices; return amount is a positive refund.
- Finance owns `finance.topUp {id,amount}` and views for project funds, reservation financial details, and ledger.
- Transition constraints will preserve existing reservation prices and ledger facts, prevent deletion, and tie each new ledger entry to matching budget movement. These apply regardless of command name.
