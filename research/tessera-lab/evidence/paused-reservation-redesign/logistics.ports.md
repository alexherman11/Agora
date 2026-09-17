# Logistics ports agreed for Trial 3

The shared collection is `reservations`. Each dispatch creates one reservation per matching packing line at ID `eventId + '/' + line.id`; each amendment creates one reservation at ID `eventId`. The source line and issue quantity are snapshots. Logistics contributes `reservations.missionId`, `sku`, `issued`, and `returned` (counter, default 0). Finance contributes `reservations.unitPrice` to the same created records. These fields are disjoint create effects. The plan remains editable only before dispatch; later issues use amendments.

Planning owns `mission.dispatch {id,eventId}`, `mission.amend {id,eventId,sku,qty}`, and `mission.close {id}`. Logistics owns `reservation.return {id,eventId,qty}`, where `id` is the reservation ID. Planning requires all reservations fully returned before close. Finance reacts to dispatch, amend, and return using the snapshot price. The logistics inventory conservation and reservation transition constraints apply to every action, including future editor actions.

These ports were agreed directly with the planning and finance builders before reading their Trial 3 implementations.
