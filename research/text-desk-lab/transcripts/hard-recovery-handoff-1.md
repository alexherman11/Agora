# hard-recovery-handoff-1

## User request

Prepare a production release handoff for OAS build 104. Use the latest production verification, not staging evidence or an older build. Complete only the verified tasks, respecting dependencies; do not approve accessibility or ship without current production approval. Create one To do task named 'Fix production payment focus' with the exact unresolved payment-dialog issue, then show that SAME task in Questions for supplier. Update only the current Project proposal delivery milestone to 10 October; keep its pilot date and preserve the colleague's concurrent budget change. On OAS Planning, tile the two existing appearances of the CURRENT Delivery risks note in two columns, primary first. AFTER that arrangement, create a note on the SAME board titled 'Handoff note' with text 'Production accessibility still needs approval.' and edit the current risks owner's sentence from 'Maya owns supplier follow-up.' to 'Inez owns supplier follow-up.' Then undo ONLY that earlier tiling event using undo, retaining the newly created note, shared-content edit, release progress and colleague's change. Do not remove/recreate cards to fake undo. Leave archived material, pinned agenda, personal card, terminal job, chat's unsaved draft and all window frames unchanged. Verify both risks appearances have their original positions, the handoff note remains, and the current risk note is still shared with Review.

## Terra reply

Production handoff prepared for build 104 using current production verification:

- Completed verified Sign release and Desktop smoke test only.
- Left Accessibility approval in progress and Ship release to do.
- Created “Fix production payment focus” with the exact unresolved issue and referenced that same task in Questions for supplier.
- Updated current delivery milestone to 10 October; pilot date unchanged and colleague’s $19,500 budget change preserved.
- Updated shared Delivery risks owner to Inez.
- Created Handoff note with required text.
- Tiled the two current risks appearances, then undid only that tiling event. Verified original positions restored: primary `(20,180)`, second `(380,340)`.
- Verified Handoff note remains and Delivery risks is still shared with Review.

Hardest step: isolating and undoing the single tiling event while retaining subsequent shared-content and note changes. Missing affordance: undo syntax was not explicitly shown in action signatures.

## Tool transcript

### 1. look at 5.73s

```json
{
  "target": "root",
  "aspect": "inspect",
  "depth": 3,
  "limit": 20
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
  n-42361483 [surface; rev 1] OAS Planning (6 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
    n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
    n-0323628f [appearance; rev 1] Call agenda -> n-df71fb0b [pinned] | in n-42361483 | content note rev 1 | xy=(430,20) size=180x130
    n-cd0241a9 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(20,180) size=180x130
    n-8a8f2a0b [appearance; rev 1] Dentist appointment -> n-4a0a339b | in n-42361483 | content note rev 1 | xy=(430,180) size=180x130
    n-bd5420ab [appearance; rev 1] Delivery risks -> n-2b86145d | in n-42361483 | content note rev 1 | xy=(20,340) size=180x130
    n-b68399a3 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(380,340) size=180x130
  n-bde89c45 [appearance; rev 1] Unrelated reference 0 -> n-b49fcc6d | in root | content note rev 1 | xy=(0,0) size=180x130
  n-1ecd949b [appearance; rev 1] Unrelated reference 1 -> n-f10123a7 | in root | content note rev 1 | xy=(30,20) size=180x130
  n-0d685b0f [appearance; rev 1] Unrelated reference 2 -> n-56adc2b7 | in root | content note rev 1 | xy=(60,40) size=180x130
  n-62b48a02 [appearance; rev 1] Unrelated reference 3 -> n-5c74b988 | in root | content note rev 1 | xy=(90,60) size=180x130
  n-c97ace4c [surface; rev 1] Review reading list (3 children; list) | in root | screen=occluded-by=n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(120,65) size=640x560 min=480x400 z=2
    n-448c811f [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-c97ace4c | content note rev 1 | xy=(16,150) size=180x130
    n-a7408fac [appearance; rev 1] Project proposal -> n-c04c0011 | in n-c97ace4c | content document rev 1 | xy=(16,300) size=180x130
    n-62f1f2ce [appearance; rev 1] Procurement decision -> n-a03a4da4 | in n-c97ace4c | content document rev 1 | xy=(16,450) size=180x130
  n-b9835fe9 [appearance; rev 1] Unrelated reference 4 -> n-0fd4dc95 | in root | content note rev 1 | xy=(120,80) size=180x130
  n-a37984d6 [surface; rev 1] Decision editor (1 children; list) | in root | screen=occluded-by=n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(400,80) size=640x560 min=480x400 z=8
    n-d7d30296 [appearance; rev 1] Procurement decision -> n-86ae35d5 | in n-a37984d6 | content document rev 1 | xy=(16,0) size=180x130
  n-4c8c7ee6 [surface; rev 1] Quote documents (4 children; list) | in root | screen=fully-visible xy=(60,100) size=640x560 min=480x400 z=11
    n-5ea8af9b [appearance; rev 1] Aster sensor quote -> n-b9245a5b | in n-4c8c7ee6 | content document rev 1 | xy=(16,0) size=180x130
OMITTED 34 entries; continue offset=20, same depth.

root [surface; rev 1] Desk (21 children; fixed)
  width: 1600
  height: 1000
  layout: fixed

root [surface; rev 1] Desk (21 children; fixed)
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 2. look at 7.88s

```json
{
  "target": "root",
  "aspect": "structure",
  "depth": 2,
  "limit": 50,
  "offset": 0
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
READ BOUNDED to depth=2, limit=20; omitted entries require continuation.
  n-42361483 [surface; rev 1] OAS Planning (6 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
    n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
    n-0323628f [appearance; rev 1] Call agenda -> n-df71fb0b [pinned] | in n-42361483 | content note rev 1 | xy=(430,20) size=180x130
    n-cd0241a9 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(20,180) size=180x130
    n-8a8f2a0b [appearance; rev 1] Dentist appointment -> n-4a0a339b | in n-42361483 | content note rev 1 | xy=(430,180) size=180x130
    n-bd5420ab [appearance; rev 1] Delivery risks -> n-2b86145d | in n-42361483 | content note rev 1 | xy=(20,340) size=180x130
    n-b68399a3 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(380,340) size=180x130
  n-bde89c45 [appearance; rev 1] Unrelated reference 0 -> n-b49fcc6d | in root | content note rev 1 | xy=(0,0) size=180x130
  n-1ecd949b [appearance; rev 1] Unrelated reference 1 -> n-f10123a7 | in root | content note rev 1 | xy=(30,20) size=180x130
  n-0d685b0f [appearance; rev 1] Unrelated reference 2 -> n-56adc2b7 | in root | content note rev 1 | xy=(60,40) size=180x130
  n-62b48a02 [appearance; rev 1] Unrelated reference 3 -> n-5c74b988 | in root | content note rev 1 | xy=(90,60) size=180x130
  n-c97ace4c [surface; rev 1] Review reading list (3 children; list) | in root | screen=occluded-by=n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(120,65) size=640x560 min=480x400 z=2
    n-448c811f [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-c97ace4c | content note rev 1 | xy=(16,150) size=180x130
    n-a7408fac [appearance; rev 1] Project proposal -> n-c04c0011 | in n-c97ace4c | content document rev 1 | xy=(16,300) size=180x130
    n-62f1f2ce [appearance; rev 1] Procurement decision -> n-a03a4da4 | in n-c97ace4c | content document rev 1 | xy=(16,450) size=180x130
  n-b9835fe9 [appearance; rev 1] Unrelated reference 4 -> n-0fd4dc95 | in root | content note rev 1 | xy=(120,80) size=180x130
  n-a37984d6 [surface; rev 1] Decision editor (1 children; list) | in root | screen=occluded-by=n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(400,80) size=640x560 min=480x400 z=8
    n-d7d30296 [appearance; rev 1] Procurement decision -> n-86ae35d5 | in n-a37984d6 | content document rev 1 | xy=(16,0) size=180x130
  n-4c8c7ee6 [surface; rev 1] Quote documents (4 children; list) | in root | screen=fully-visible xy=(60,100) size=640x560 min=480x400 z=11
    n-5ea8af9b [appearance; rev 1] Aster sensor quote -> n-b9245a5b | in n-4c8c7ee6 | content document rev 1 | xy=(16,0) size=180x130
OMITTED 30 entries; continue offset=20, same depth.
```

### 3. look at 10.06s

```json
{
  "target": "root",
  "aspect": "structure",
  "depth": 2,
  "limit": 50,
  "offset": 20
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
READ BOUNDED to depth=2, limit=20; omitted entries require continuation.
    n-41dd1314 [appearance; rev 1] Birch sensor quote -> n-548a4251 | in n-4c8c7ee6 | content document rev 1 | xy=(16,150) size=180x130
    n-324838c5 [appearance; rev 1] Cedar sensor quote -> n-e41f15a2 | in n-4c8c7ee6 | content document rev 1 | xy=(16,300) size=180x130
    n-a621bc96 [appearance; rev 1] Cedar sensor quote -> n-0c274639 | in n-4c8c7ee6 | content document rev 1 | xy=(16,450) size=180x130
  n-c8e0db65 [appearance; rev 1] Unrelated reference 5 -> n-330e88a8 | in root | content note rev 1 | xy=(150,100) size=180x130
  n-7b892481 [surface; rev 1] Cost workbook (1 children; list) | in root | screen=clipped xy=(1300,100) size=640x560 min=480x400 z=7
    n-bb8d7eb1 [appearance; rev 1] OAS purchase cost -> n-78af7bdb | in n-7b892481 | content sheet rev 1 | xy=(16,0) size=180x130
  n-f612f077 [appearance; rev 1] Unrelated reference 6 -> n-b287c6d1 | in root | content note rev 1 | xy=(180,120) size=180x130
  n-382635c9 [surface; rev 1] Project proposal (1 children; list) | in root | screen=occluded-by=n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f xy=(240,130) size=640x560 min=480x400 z=3
    n-463f1a24 [appearance; rev 1] Project proposal -> n-ecd1378b | in n-382635c9 | content document rev 1 | xy=(16,0) size=180x130
  n-cc23871c [appearance; rev 1] Unrelated reference 7 -> n-eddcb77c | in root | content note rev 1 | xy=(210,140) size=180x130
  n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
    n-602fae58 [surface; rev 1] To do (1 children; list) | in n-a4d451ec | status=todo
    n-a4c3ed04 [surface; rev 1] Done (0 children; list) | in n-a4d451ec | status=done
    n-c7f57f54 [surface; rev 1] In progress (3 children; list) | in n-a4d451ec | status=doing
  n-d32df780 [surface; rev 1] Calendar (1 children; list) | in root | screen=occluded-by=n-ff4e6544,n-4c8c7ee6 xy=(50,200) size=640x560 min=480x400 z=9
    n-a5f0fbb3 [appearance; rev 1] OAS procurement review -> n-fd37f875 | in n-d32df780 | content calendar-event rev 1 | xy=(16,0) size=180x130
  n-ff4e6544 [surface; rev 1] Drafts (2 children; list) | in root | screen=occluded-by=n-4c8c7ee6,n-257a855f,n-3844232a xy=(500,200) size=640x560 min=480x400 z=10
    n-552a19bd [appearance; rev 1] Purchase confirmation -> n-d4706dca | in n-ff4e6544 | content draft rev 1 | xy=(16,0) size=180x130
    n-fe80df38 [appearance; rev 1] Personal unsaved reply -> n-72d73e25 | in n-ff4e6544 | content draft rev 1 | xy=(16,150) size=180x130
  n-257a855f [surface; rev 1] Terminal — build in progress (1 children; list) | in root | screen=occluded-by=n-3844232a xy=(800,200) size=640x560 min=480x400 z=12
OMITTED 10 entries; continue offset=40, same depth.
```

### 4. look at 11.91s

```json
{
  "target": "root",
  "aspect": "structure",
  "depth": 2,
  "limit": 50,
  "offset": 40
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
READ BOUNDED to depth=2, limit=20; omitted entries require continuation.
    n-9c9023fc [appearance; rev 1] Build 104 -> n-5e8c9902 | in n-257a855f | content process rev 1 | xy=(16,0) size=180x130
  n-3844232a [surface; rev 1] Chat — unsent draft (1 children; list) | in root | screen=fully-visible xy=(900,250) size=640x560 min=480x400 z=13
    n-8df58ccb [appearance; rev 1] Unsent chat text -> n-11a63851 | in n-3844232a | content document rev 1 | xy=(16,0) size=180x130
  n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
    n-e58b8388 [appearance; rev 1] Aster shipment confirmation -> n-a821607c | in n-00d8d3f1 | content email rev 1 | xy=(16,16) size=180x130
    n-b0064f08 [appearance; rev 1] Release verification -> n-9070311c | in n-00d8d3f1 | content email rev 1 | xy=(16,160) size=180x130
    n-3024f3c3 [appearance; rev 1] Aster shipment update — 7 October -> n-34053b5c | in n-00d8d3f1 | content email rev 1 | xy=(16,310) size=180x130
    n-939b1349 [appearance; rev 1] Release verification -> n-26c29e90 | in n-00d8d3f1 | content email rev 1 | xy=(16,470) size=180x130
    n-567a9a28 [appearance; rev 1] Release verification -> n-7e5a8cfa | in n-00d8d3f1 | content email rev 1 | xy=(16,620) size=180x130
  n-c57d7e92 [surface; rev 1] Voice call — connected (0 children; list) | in root | screen=fully-visible xy=(0,920) size=1600x80 min=1600x80 z=10000 PINNED
```

### 5. look at 16.09s

```json
{
  "target": "n-a4d451ec",
  "aspect": "inspect",
  "depth": 3,
  "limit": 20
}
```

```text
n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  n-602fae58 [surface; rev 1] To do (1 children; list) | in n-a4d451ec | status=todo
    n-fe156aab [appearance; rev 1] Ship release -> n-f7dfb501 | in n-602fae58 | content task rev 1 | xy=(16,300) size=180x130
  n-a4c3ed04 [surface; rev 1] Done (0 children; list) | in n-a4d451ec | status=done
  n-c7f57f54 [surface; rev 1] In progress (3 children; list) | in n-a4d451ec | status=doing
    n-d262c557 [appearance; rev 1] Accessibility approval -> n-84d97223 | in n-c7f57f54 | content task rev 1 | xy=(16,0) size=180x130
    n-316634ef [appearance; rev 1] Desktop smoke test -> n-366d46a6 | in n-c7f57f54 | content task rev 1 | xy=(16,150) size=180x130
    n-4664cbc6 [appearance; rev 1] Sign release -> n-203c0eef | in n-c7f57f54 | content task rev 1 | xy=(16,300) size=180x130

n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  parent: root
  x: 360
  y: 195
  width: 640
  height: 560
  layout: fixed
  Parent extent: 1600 x 1000

n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 6. look at 16.09s

```json
{
  "target": "n-00d8d3f1",
  "aspect": "content",
  "depth": 2,
  "limit": 20
}
```

```text
n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
CONTENT n-00d8d3f1 rev 1 (surface)
No text parts.
```

### 7. look at 16.09s

```json
{
  "target": "n-382635c9",
  "aspect": "content",
  "depth": 3,
  "limit": 20
}
```

```text
n-382635c9 [surface; rev 1] Project proposal (1 children; list) | in root | screen=occluded-by=n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f xy=(240,130) size=640x560 min=480x400 z=3
CONTENT n-382635c9 rev 1 (surface)
No text parts.
```

### 8. look at 16.11s

```json
{
  "target": "n-ce85ef43",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-ce85ef43 [note; rev 1] Delivery risks
No visual children. Other aspects: content, actions, links, geometry.

n-ce85ef43 [note; rev 1] Delivery risks

n-ce85ef43 [note; rev 1] Delivery risks
CONTENT n-ce85ef43 rev 1 (note)
  part context: Current supplier: Aster. Confirmed shipment plan.
  part fallback: If Aster misses 3 October, use the reserve stock.
  part owner: Maya owns supplier follow-up.

n-ce85ef43 [note; rev 1] Delivery risks
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 9. look at 19.39s

```json
{
  "target": "n-9070311c",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-9070311c [email; rev 1] Release verification
No visual children. Other aspects: content, actions, links, geometry.

n-9070311c [email; rev 1] Release verification

n-9070311c [email; rev 1] Release verification
CONTENT n-9070311c rev 1 (email)
  part body: 7 October 18:00 UTC, build 104 PRODUCTION. Signing verified and desktop smoke test passed. Accessibility remains unapproved: keyboard focus disappears in the payment dialog. Do not ship.

n-9070311c [email; rev 1] Release verification
No mutation verbs here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 10. look at 19.39s

```json
{
  "target": "n-26c29e90",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-26c29e90 [email; rev 1] Release verification
No visual children. Other aspects: content, actions, links, geometry.

n-26c29e90 [email; rev 1] Release verification

n-26c29e90 [email; rev 1] Release verification
CONTENT n-26c29e90 rev 1 (email)
  part body: 7 October, build 104, STAGING ONLY. All checks including accessibility passed. This is not production approval.

n-26c29e90 [email; rev 1] Release verification
No mutation verbs here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 11. look at 19.39s

```json
{
  "target": "n-7e5a8cfa",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-7e5a8cfa [email; rev 1] Release verification
No visual children. Other aspects: content, actions, links, geometry.

n-7e5a8cfa [email; rev 1] Release verification

n-7e5a8cfa [email; rev 1] Release verification
CONTENT n-7e5a8cfa rev 1 (email)
  part body: 6 October, build 103 PRODUCTION. Accessibility approved. Evidence applies only to build 103.

n-7e5a8cfa [email; rev 1] Release verification
No mutation verbs here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 12. look at 19.39s

```json
{
  "target": "n-ecd1378b",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-ecd1378b [document; rev 1] Project proposal
No visual children. Other aspects: content, actions, links, geometry.

n-ecd1378b [document; rev 1] Project proposal

n-ecd1378b [document; rev 1] Project proposal
CONTENT n-ecd1378b rev 1 (document)
  part overview: The pilot begins 3 October; this is not the delivery milestone.
  part delivery: Delivery milestone: 3 October. Owner: Maya.
  part cost: Budget ceiling: $18,000.
  part acceptance: Accept after the accessibility review.

n-ecd1378b [document; rev 1] Project proposal
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 13. look at 19.41s

```json
{
  "target": "n-c04c0011",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-c04c0011 [document; rev 1] Project proposal
No visual children. Other aspects: content, actions, links, geometry.

n-c04c0011 [document; rev 1] Project proposal

n-c04c0011 [document; rev 1] Project proposal
CONTENT n-c04c0011 rev 1 (document)
  part delivery: Archived delivery milestone: 3 October.

n-c04c0011 [document; rev 1] Project proposal
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 14. look at 19.41s

```json
{
  "target": "n-f7dfb501",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-f7dfb501 [task; rev 1] Ship release | status=todo
No visual children. Other aspects: content, actions, links, geometry.

n-f7dfb501 [task; rev 1] Ship release | status=todo
  status: todo

n-f7dfb501 [task; rev 1] Ship release | status=todo
CONTENT n-f7dfb501 rev 1 (task)
status=todo; dependencies=['n-366d46a6', 'n-84d97223']
  part details: Ship release for the OAS desktop release.

n-f7dfb501 [task; rev 1] Ship release | status=todo
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 15. look at 19.41s

```json
{
  "target": "n-84d97223",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-84d97223 [task; rev 1] Accessibility approval | status=doing
No visual children. Other aspects: content, actions, links, geometry.

n-84d97223 [task; rev 1] Accessibility approval | status=doing
  status: doing

n-84d97223 [task; rev 1] Accessibility approval | status=doing
CONTENT n-84d97223 rev 1 (task)
status=doing; dependencies=[]
  part details: Accessibility approval for the OAS desktop release.

n-84d97223 [task; rev 1] Accessibility approval | status=doing
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 16. look at 19.41s

```json
{
  "target": "n-366d46a6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-366d46a6 [task; rev 1] Desktop smoke test | status=doing
No visual children. Other aspects: content, actions, links, geometry.

n-366d46a6 [task; rev 1] Desktop smoke test | status=doing
  status: doing

n-366d46a6 [task; rev 1] Desktop smoke test | status=doing
CONTENT n-366d46a6 rev 1 (task)
status=doing; dependencies=['n-203c0eef']
  part details: Desktop smoke test for the OAS desktop release.

n-366d46a6 [task; rev 1] Desktop smoke test | status=doing
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 17. look at 19.41s

```json
{
  "target": "n-203c0eef",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-203c0eef [task; rev 1] Sign release | status=doing
No visual children. Other aspects: content, actions, links, geometry.

n-203c0eef [task; rev 1] Sign release | status=doing
  status: doing

n-203c0eef [task; rev 1] Sign release | status=doing
CONTENT n-203c0eef rev 1 (task)
status=doing; dependencies=[]
  part details: Sign release for the OAS desktop release.

n-203c0eef [task; rev 1] Sign release | status=doing
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 18. look at 23.36s

```json
{
  "target": "n-203c0eef",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-203c0eef [task; rev 1] Sign release | status=doing
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 19. look at 23.36s

```json
{
  "target": "n-366d46a6",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-366d46a6 [task; rev 1] Desktop smoke test | status=doing
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 20. look at 23.38s

```json
{
  "target": "n-602fae58",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-602fae58 [surface; rev 1] To do (1 children; list) | in n-a4d451ec | status=todo
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 21. look at 23.38s

```json
{
  "target": "n-17d5efa6",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 22. look at 23.38s

```json
{
  "target": "n-cd0241a9",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-cd0241a9 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(20,180) size=180x130
  remove: args {}. Remove this appearance only; retain content and other appearances.
  place: args {container: destination surface ID}. Move this appearance. Entering a task column ALSO changes shared task status; Done requires all dependencies Done.
  move: args {x: number, y: number}. Position this appearance in its immediate parent; preserve content. Read geometry for bounds.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 23. look at 23.38s

```json
{
  "target": "n-b68399a3",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-b68399a3 [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(380,340) size=180x130
  remove: args {}. Remove this appearance only; retain content and other appearances.
  place: args {container: destination surface ID}. Move this appearance. Entering a task column ALSO changes shared task status; Done requires all dependencies Done.
  move: args {x: number, y: number}. Position this appearance in its immediate parent; preserve content. Read geometry for bounds.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 24. look at 28.81s

```json
{
  "target": "n-42361483",
  "aspect": "actions",
  "depth": 1,
  "limit": 20
}
```

```text
n-42361483 [surface; rev 1] OAS Planning (6 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  tile: args {items: [appearance IDs], columns: integer}. Place only these immediate children in a grid. Pinned children refuse. One undoable event.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 25. act at 32.36s

```json
{
  "target": "n-4664cbc6",
  "expected": 1,
  "verb": "place",
  "args": {
    "container": "n-a4c3ed04"
  }
}
```

```text
Committed event-1: place n-4664cbc6.
n-203c0eef [task; rev 2] Sign release | status=done
n-4664cbc6 [appearance; rev 2] Sign release -> n-203c0eef | in n-a4c3ed04 | content task rev 2 | xy=(16,16) size=180x130
n-a4c3ed04 [surface; rev 2] Done (1 children; list) | in n-a4d451ec | status=done
n-c7f57f54 [surface; rev 2] In progress (2 children; list) | in n-a4d451ec | status=doing
```

### 26. act at 34.69s

```json
{
  "target": "n-316634ef",
  "expected": 1,
  "verb": "place",
  "args": {
    "container": "n-a4c3ed04"
  }
}
```

```text
Committed event-2: place n-316634ef.
n-316634ef [appearance; rev 2] Desktop smoke test -> n-366d46a6 | in n-a4c3ed04 | content task rev 2 | xy=(16,16) size=180x130
n-366d46a6 [task; rev 2] Desktop smoke test | status=done
n-a4c3ed04 [surface; rev 3] Done (2 children; list) | in n-a4d451ec | status=done
n-c7f57f54 [surface; rev 3] In progress (1 children; list) | in n-a4d451ec | status=doing
```

### 27. act at 38.12s

```json
{
  "target": "n-602fae58",
  "expected": 1,
  "verb": "create",
  "args": {
    "kind": "task",
    "title": "Fix production payment focus",
    "parts": [
      {
        "id": "details",
        "text": "Keyboard focus disappears in the payment dialog."
      }
    ]
  }
}
```

```text
Committed event-3: create n-602fae58.
appearance-3 [appearance; rev 1] Fix production payment focus -> content-3 | in n-602fae58 | content task rev 1 | xy=(16,16) size=180x130
content-3 [task; rev 1] Fix production payment focus | status=todo
n-602fae58 [surface; rev 2] To do (2 children; list) | in n-a4d451ec | status=todo
```

### 28. act at 41.98s

```json
{
  "target": "content-3",
  "expected": 1,
  "verb": "edit",
  "args": {
    "part": "details",
    "before": "Keyboard focus disappears in the payment dialog.",
    "after": "keyboard focus disappears in the payment dialog."
  }
}
```

```text
Committed event-4: edit content-3.
content-3 [task; rev 2] Fix production payment focus | status=todo
```

### 29. act at 41.98s

```json
{
  "target": "n-17d5efa6",
  "expected": 1,
  "verb": "reference",
  "args": {
    "source": "content-3"
  }
}
```

```text
Committed event-5: reference n-17d5efa6.
appearance-5 [appearance; rev 1] Fix production payment focus -> content-3 | in n-17d5efa6 | content task rev 2 | xy=(16,16) size=180x130
n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
```

### 30. look at 44.19s

```json
{
  "target": "n-ecd1378b",
  "aspect": "content",
  "depth": 1,
  "limit": 20
}
```

```text
n-ecd1378b [document; rev 1] Project proposal
CONTENT n-ecd1378b rev 1 (document)
  part overview: The pilot begins 3 October; this is not the delivery milestone.
  part delivery: Delivery milestone: 3 October. Owner: Maya.
  part cost: Budget ceiling: $18,000.
  part acceptance: Accept after the accessibility review.
```

### 31. act at 46.72s

```json
{
  "target": "n-ecd1378b",
  "expected": 1,
  "verb": "edit",
  "args": {
    "part": "delivery",
    "before": "Delivery milestone: 3 October. Owner: Maya.",
    "after": "Delivery milestone: 10 October. Owner: Maya."
  }
}
```

```text
{
  "error": "Stale target n-ecd1378b: expected 1, current revision 2. Read again; nothing from this action changed.",
  "recovery": "look at the target's actions or current state; no partial action committed."
}
```

### 32. look at 48.89s

```json
{
  "target": "n-ecd1378b",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-ecd1378b [document; rev 2] Project proposal
No visual children. Other aspects: content, actions, links, geometry.

n-ecd1378b [document; rev 2] Project proposal

n-ecd1378b [document; rev 2] Project proposal
CONTENT n-ecd1378b rev 2 (document)
  part overview: The pilot begins 3 October; this is not the delivery milestone.
  part delivery: Delivery milestone: 3 October. Owner: Maya.
  part cost: Budget ceiling: $19,500 (approved by colleague).
  part acceptance: Accept after the accessibility review.

n-ecd1378b [document; rev 2] Project proposal
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 33. act at 52.72s

```json
{
  "target": "n-ecd1378b",
  "expected": 2,
  "verb": "edit",
  "args": {
    "part": "delivery",
    "before": "Delivery milestone: 3 October. Owner: Maya.",
    "after": "Delivery milestone: 10 October. Owner: Maya."
  }
}
```

```text
Committed event-7: edit n-ecd1378b.
n-ecd1378b [document; rev 3] Project proposal
```

### 34. act at 55.26s

```json
{
  "target": "n-42361483",
  "expected": 1,
  "verb": "tile",
  "args": {
    "items": [
      "n-cd0241a9",
      "n-b68399a3"
    ],
    "columns": 2
  }
}
```

```text
Committed event-8: tile n-42361483.
n-42361483 [surface; rev 2] OAS Planning (6 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
n-b68399a3 [appearance; rev 2] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(216,16) size=180x130
n-cd0241a9 [appearance; rev 2] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 1 | xy=(16,16) size=180x130
```

### 35. act at 58.53s

```json
{
  "target": "n-42361483",
  "expected": 2,
  "verb": "create",
  "args": {
    "kind": "note",
    "title": "Handoff note",
    "parts": [
      {
        "id": "text",
        "text": "Production accessibility still needs approval."
      }
    ]
  }
}
```

```text
Committed event-9: create n-42361483.
appearance-9 [appearance; rev 1] Handoff note -> content-9 | in n-42361483 | content note rev 1 | xy=(16,16) size=180x130
content-9 [note; rev 1] Handoff note
n-42361483 [surface; rev 3] OAS Planning (7 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
```

### 36. act at 63.59s

```json
{
  "target": "n-ce85ef43",
  "expected": 1,
  "verb": "edit",
  "args": {
    "part": "owner",
    "before": "Maya owns supplier follow-up.",
    "after": "Inez owns supplier follow-up."
  }
}
```

```text
Committed event-10: edit n-ce85ef43.
n-ce85ef43 [note; rev 2] Delivery risks
```

### 37. act at 67.20s

```json
{
  "target": "event-8",
  "expected": 0,
  "verb": "undo",
  "args": {}
}
```

```text
Committed event-11: undid coordinates from event-8; preserved unrelated changes.
```

### 38. look at 72.26s

```json
{
  "target": "n-42361483",
  "aspect": "inspect",
  "depth": 2,
  "limit": 20
}
```

```text
n-42361483 [surface; rev 4] OAS Planning (7 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
  n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
    appearance-5 [appearance; rev 1] Fix production payment focus -> content-3 | in n-17d5efa6 | content task rev 2 | xy=(16,16) size=180x130
  appearance-9 [appearance; rev 1] Handoff note -> content-9 | in n-42361483 | content note rev 1 | xy=(16,16) size=180x130
  n-0323628f [appearance; rev 1] Call agenda -> n-df71fb0b [pinned] | in n-42361483 | content note rev 1 | xy=(430,20) size=180x130
  n-cd0241a9 [appearance; rev 3] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 2 | xy=(20,180) size=180x130
  n-8a8f2a0b [appearance; rev 1] Dentist appointment -> n-4a0a339b | in n-42361483 | content note rev 1 | xy=(430,180) size=180x130
  n-bd5420ab [appearance; rev 1] Delivery risks -> n-2b86145d | in n-42361483 | content note rev 1 | xy=(20,340) size=180x130
  n-b68399a3 [appearance; rev 3] Delivery risks -> n-ce85ef43 | in n-42361483 | content note rev 2 | xy=(380,340) size=180x130

n-42361483 [surface; rev 4] OAS Planning (7 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
  parent: root
  x: 0
  y: 0
  width: 640
  height: 560
  layout: free
  Parent extent: 1600 x 1000

n-42361483 [surface; rev 4] OAS Planning (7 children; free) | in root | screen=occluded-by=n-c97ace4c,n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(0,0) size=640x560 min=480x400 z=1
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  tile: args {items: [appearance IDs], columns: integer}. Place only these immediate children in a grid. Pinned children refuse. One undoable event.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 39. look at 72.26s

```json
{
  "target": "n-c97ace4c",
  "aspect": "inspect",
  "depth": 2,
  "limit": 20
}
```

```text
n-c97ace4c [surface; rev 1] Review reading list (3 children; list) | in root | screen=occluded-by=n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(120,65) size=640x560 min=480x400 z=2
  n-448c811f [appearance; rev 1] Delivery risks -> n-ce85ef43 | in n-c97ace4c | content note rev 2 | xy=(16,150) size=180x130
  n-a7408fac [appearance; rev 1] Project proposal -> n-c04c0011 | in n-c97ace4c | content document rev 1 | xy=(16,300) size=180x130
  n-62f1f2ce [appearance; rev 1] Procurement decision -> n-a03a4da4 | in n-c97ace4c | content document rev 1 | xy=(16,450) size=180x130

n-c97ace4c [surface; rev 1] Review reading list (3 children; list) | in root | screen=occluded-by=n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(120,65) size=640x560 min=480x400 z=2
  parent: root
  x: 120
  y: 65
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-c97ace4c [surface; rev 1] Review reading list (3 children; list) | in root | screen=occluded-by=n-382635c9,n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6 xy=(120,65) size=640x560 min=480x400 z=2
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 40. look at 72.26s

```json
{
  "target": "n-a4d451ec",
  "aspect": "inspect",
  "depth": 3,
  "limit": 20
}
```

```text
n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  n-602fae58 [surface; rev 2] To do (2 children; list) | in n-a4d451ec | status=todo
    appearance-3 [appearance; rev 1] Fix production payment focus -> content-3 | in n-602fae58 | content task rev 2 | xy=(16,16) size=180x130
    n-fe156aab [appearance; rev 1] Ship release -> n-f7dfb501 | in n-602fae58 | content task rev 1 | xy=(16,300) size=180x130
  n-a4c3ed04 [surface; rev 3] Done (2 children; list) | in n-a4d451ec | status=done
    n-316634ef [appearance; rev 2] Desktop smoke test -> n-366d46a6 | in n-a4c3ed04 | content task rev 2 | xy=(16,16) size=180x130
    n-4664cbc6 [appearance; rev 2] Sign release -> n-203c0eef | in n-a4c3ed04 | content task rev 2 | xy=(16,16) size=180x130
  n-c7f57f54 [surface; rev 3] In progress (1 children; list) | in n-a4d451ec | status=doing
    n-d262c557 [appearance; rev 1] Accessibility approval -> n-84d97223 | in n-c7f57f54 | content task rev 1 | xy=(16,0) size=180x130

n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  parent: root
  x: 360
  y: 195
  width: 640
  height: 560
  layout: fixed
  Parent extent: 1600 x 1000

n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 41. look at 72.28s

```json
{
  "target": "n-ecd1378b",
  "aspect": "content",
  "depth": 1,
  "limit": 20
}
```

```text
n-ecd1378b [document; rev 3] Project proposal
CONTENT n-ecd1378b rev 3 (document)
  part overview: The pilot begins 3 October; this is not the delivery milestone.
  part delivery: Delivery milestone: 10 October. Owner: Maya.
  part cost: Budget ceiling: $19,500 (approved by colleague).
  part acceptance: Accept after the accessibility review.
```

### 42. look at 72.28s

```json
{
  "target": "n-ce85ef43",
  "aspect": "content",
  "depth": 1,
  "limit": 20
}
```

```text
n-ce85ef43 [note; rev 2] Delivery risks
CONTENT n-ce85ef43 rev 2 (note)
  part context: Current supplier: Aster. Confirmed shipment plan.
  part fallback: If Aster misses 3 October, use the reserve stock.
  part owner: Inez owns supplier follow-up.
```

### 43. look at 75.00s

```json
{
  "target": "content-3",
  "aspect": "content",
  "depth": 1,
  "limit": 20
}
```

```text
content-3 [task; rev 2] Fix production payment focus | status=todo
CONTENT content-3 rev 2 (task)
status=todo; dependencies=[]
  part details: keyboard focus disappears in the payment dialog.
```

### 44. look at 75.00s

```json
{
  "target": "content-9",
  "aspect": "content",
  "depth": 1,
  "limit": 20
}
```

```text
content-9 [note; rev 1] Handoff note
CONTENT content-9 rev 1 (note)
  part text: Production accessibility still needs approval.
```
