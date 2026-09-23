# Trial 2: expedition dispatch, a step change in difficulty

Build a different complete application, not an extension of the notes UI. Three
concurrent GPT-5.6 agents author independent programs against these public ports.
No reading peers' declarations before initial freeze. Coordinator owns no feature
code. Generic language additions were specified before authoring.

## Shared vocabulary (builders declare their own fields)

Planning builder: `missions` fields title:string, projectId:string,
status:string (draft/dispatched/cancelled); `lines` fields missionId:string,
sku:string, qty:number. Commands:
* mission.create {id,title,projectId}
* line.add {id,missionId,sku,qty}, line.remove {id}
* mission.dispatch {id,eventId}, only from draft, packing list nonempty
* mission.cancel {id,eventId}, only from dispatched
Planner seeds ONLY missions/ridge (Ridge survey, projectId alpine, draft),
missions/coast (Coastal survey, projectId ocean, draft), lines/ridge-radio
(ridge, radio, 2), lines/ridge-tent (ridge, tent, 1), lines/coast-radio
(coast, radio, 2). Can supply more AFTER initial verification.
Planner must prevent modifying lines once dispatched or cancelled.
Planning provides views `missions.list` (missions rows), `missions.card` panel
role mission-card, and `missions.tools` row beneath the card, under root workspace.
All builders may add children to these addresses. Nested list queries use parent.

Logistics builder: `stock` fields name:string, available:number counter,
unitCost:number register. Seeds ONLY stock/radio (Field radio, available 3,
unitCost 120) and stock/tent (Storm tent, available 2, unitCost 300).
Adds reactions on mission.dispatch to subtract each packing line quantity from
stock.available, mission.cancel to restore it. Complete batch must forbid negative
inventory. Validate references, quantities >0 and integer, foreign keys. Supply
restock {id,qty}, show inventory, shortages and per-mission packing availability.
Preconditions/constraints must prevent line editing after dispatch. The planner
also checks this; neither may weaken the other. React to all matching lines with
foreach, not fixed per-SKU special cases. No handlers assume line order.

Finance builder: `projects` fields name:string, available:number counter;
`missions.charged`:number default 0 register. Seeds ONLY projects/alpine
(Alpine research, available 1000), projects/ocean (Coastal research, available 400).
On dispatch: compute total using line.qty * matching stock.unitCost; set
mission.charged and subtract total from its project's available funds. On cancel:
refund recorded mission.charged, without recomputing potentially changed prices.
Add constraints project funds >=0, valid project references. Add top-up action,
budget/quote UI, and `ledger` records keyed eventId on dispatch/cancel storing
missionId, kind, amount. Never overwrite old ledger rows. No duplicate refunds:
same mission can cancel only once. Codes supply local.newId as eventId from buttons.

## Required workflows and adversarial checks

Ridge dispatch consumes 2 radios +1 tent and 540 alpine funds in ONE transaction;
coast then refuses due stock; neither ocean funds nor ledger may change on refusal.
Cancel ridge refunds 540 and restores stock; cancel again refuses. Then coast can
dispatch. A new mission with excessive price must refuse despite enough stock.
Two dispatch requests from the same stock snapshot cannot oversell or overspend.
The UI supports creating missions, adding/removing packing lines, dispatch/cancel,
restock/top-up, and inspecting the composed state. Builder cases must include at
least one success and one refusal, using exact shared seed IDs. Each writes only
planning/logistics/finance.tessera.json and corresponding cases in this directory.

One intentional protocol assumption: stock price is fixed in this version; nobody
adds a price edit action. Future trial will test evolving a dispatched program.
