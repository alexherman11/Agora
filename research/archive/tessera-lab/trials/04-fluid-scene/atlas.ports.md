# Atlas ports for fluid scene

Atlas seeds `hosts/atlas.host` with label `Relationship Atlas`, using Studio's registry keyed by exact static portal destination view ID. `atlas.host` remains a `card-host` drop surface. Studio retains `card.shell`, `card.face`, `card.tools`, and `card.move {id,x,y,drop}`; cards may live in any registered host, including Studio's new `reading.host`.

Atlas owns `connections` with `fromId` and `toId` card references; `atlas.connect {id,fromId,toId}` and `atlas.disconnect {id}` work across windows. Connected cards can be moved, resized and edited. Deletion is refused until their links are removed. Atlas seeds a cross-window link from retained `studio-brief` to `atlas-signal`, agreed with Studio.

The `atlas.edge` line is in viewport space and derives each endpoint from `["measure","card.shell",cardId,"centerX"]` and `centerY`. This paint-only dependency follows the actual card occurrence after portals, intrinsic sizing, docking and preview moves; it is deliberately absent from actions and layout. Atlas retains an independent `role:surface` radius claim at priority 10.
