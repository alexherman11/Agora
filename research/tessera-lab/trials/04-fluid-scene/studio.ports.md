# Studio ports: fluid scene

Agreed directly with Atlas and Toolkit:

- Studio defines `hosts.label` and uses the host record ID as the exact static portal/drop view ID. It seeds `hosts/studio.host` and `hosts/reading.host`. Atlas seeds `hosts/atlas.host`; Toolkit seeds `hosts/console.host`. Each host view has `dropRole:"card-host"`.
- `card.move {id,x,y,drop}` accepts any registered host ID. A null drop preserves the current host; a different valid host changes `cards.host` and resets local x/y to 24,24. An unknown host refuses the entire action.
- Shared card occurrence remains `card.shell` under `card.portal`, with `card.face` and `card.tools` as open extension addresses. `card.shell` uses variable `cards.width` and intrinsic `box.height:"auto"`. Atlas vector edges measure this occurrence by card ID; no fixed center offset is part of the port.
- `cards.expanded` controls readable editing. `card.expand {id}` and `card.collapse {id}` change it. The shared card keeps content, size and identity through transfers.
- `cards.z` controls overlap within a host. Create, expand, and move bring the active card forward; `card.focus {id}` and its grip button let a user bring any visible card forward before editing. The card shell reads this z value without changing its occurrence ID or measured link address.
- Studio adds independent `surfaces/reading`, view `reading.surface`, and `reading.host`. It retains the surface/grip roles for Toolkit's generic arrangement and gestures.
- Studio retains its independent priority-10 `role:surface` roundness claim for the deliberate style conflict.
