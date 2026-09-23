# hard-context-procurement-1

## User request

Prepare tomorrow's OAS procurement review using the desktop's mail, quote documents, cost workbook and calendar. We need 12 sensor kits delivered by 10 October 2026 inclusive. Choose the cheapest eligible supplier, including shipping and every mandatory charge; later correspondence overrides an old quote. Respect the latest workbook budget, which a colleague may revise while you work. Update only the workbook's five purchase inputs, preserving its formula and budget. In the current Procurement decision document replace the TBD values for supplier, landed total and review time, preserving all other wording and the archive. Move the existing 30-minute review on 8 October to the earliest shared free slot within its stated interval for all three attendees; preserve attendees and date. Compose the designated Purchase confirmation draft to procurement@example.invalid with supplier, total, delivery date and review time, but do not send or alter the other unsaved draft. Add a shared reference to the chosen CURRENT quote on Questions for supplier. Finally make the Mail, Cost workbook and Decision editor windows fully visible together, disjoint, at readable sizes, above the pinned voice dock. Preserve all unrelated window frames, terminal job, chat draft, personal content, and release tasks. Verify the financial decision, appointment, reference identity and actual screen status. If anything cannot be done, say precisely what remains.

## Terra reply

Completed and verified:

- Chose Cedar’s current 7 Oct quote: 12 kits delivered 10 Oct; landed total **$2,940** (12×$215 + $240 shipping + $120 calibration).
- Latest workbook budget changed to **$2,950**; Cedar remains within budget by $10. Updated only its five inputs; formula preserved.
- Updated current Procurement decision TBDs to Cedar, $2940, and **15:00 UTC**; archive untouched.
- Rescheduled the 8 Oct 30-minute review to **15:00–15:30 UTC**, the earliest shared free slot; date and attendees preserved.
- Composed, unsent, the Purchase confirmation draft to `procurement@example.invalid`; personal draft unchanged.
- Added a shared reference to the current Cedar quote in Questions for supplier.
- Mail, Cost workbook, and Decision editor are fully visible, disjoint 500×500 windows above the pinned voice dock.

Hardest step: resolving the supplier after the later Aster delivery update and concurrent budget revision. Missing affordance: no single consolidated view for quote eligibility, correspondence overrides, and calendar availability.

## Tool transcript

### 1. look at 4.12s

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

### 2. look at 5.86s

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

### 3. look at 7.70s

```json
{
  "target": "root",
  "aspect": "structure",
  "depth": 1,
  "limit": 20,
  "offset": 20
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
  n-c57d7e92 [surface; rev 1] Voice call — connected (0 children; list) | in root | screen=fully-visible xy=(0,920) size=1600x80 min=1600x80 z=10000 PINNED
```

### 4. look at 9.61s

```json
{
  "target": "root",
  "aspect": "structure",
  "depth": 1,
  "limit": 20,
  "offset": 10
}
```

```text
root [surface; rev 1] Desk (21 children; fixed)
  n-7b892481 [surface; rev 1] Cost workbook (1 children; list) | in root | screen=clipped xy=(1300,100) size=640x560 min=480x400 z=7
  n-f612f077 [appearance; rev 1] Unrelated reference 6 -> n-b287c6d1 | in root | content note rev 1 | xy=(180,120) size=180x130
  n-382635c9 [surface; rev 1] Project proposal (1 children; list) | in root | screen=occluded-by=n-a4d451ec,n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f xy=(240,130) size=640x560 min=480x400 z=3
  n-cc23871c [appearance; rev 1] Unrelated reference 7 -> n-eddcb77c | in root | content note rev 1 | xy=(210,140) size=180x130
  n-a4d451ec [surface; rev 1] Release control (3 children; fixed) | in root | screen=occluded-by=n-a37984d6,n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(360,195) size=640x560 min=480x400 z=4
  n-d32df780 [surface; rev 1] Calendar (1 children; list) | in root | screen=occluded-by=n-ff4e6544,n-4c8c7ee6 xy=(50,200) size=640x560 min=480x400 z=9
  n-ff4e6544 [surface; rev 1] Drafts (2 children; list) | in root | screen=occluded-by=n-4c8c7ee6,n-257a855f,n-3844232a xy=(500,200) size=640x560 min=480x400 z=10
  n-257a855f [surface; rev 1] Terminal — build in progress (1 children; list) | in root | screen=occluded-by=n-3844232a xy=(800,200) size=640x560 min=480x400 z=12
  n-3844232a [surface; rev 1] Chat — unsent draft (1 children; list) | in root | screen=fully-visible xy=(900,250) size=640x560 min=480x400 z=13
  n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
  n-c57d7e92 [surface; rev 1] Voice call — connected (0 children; list) | in root | screen=fully-visible xy=(0,920) size=1600x80 min=1600x80 z=10000 PINNED
```

### 5. look at 12.61s

```json
{
  "target": "n-00d8d3f1",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
  n-e58b8388 [appearance; rev 1] Aster shipment confirmation -> n-a821607c | in n-00d8d3f1 | content email rev 1 | xy=(16,16) size=180x130
  n-b0064f08 [appearance; rev 1] Release verification -> n-9070311c | in n-00d8d3f1 | content email rev 1 | xy=(16,160) size=180x130
  n-3024f3c3 [appearance; rev 1] Aster shipment update — 7 October -> n-34053b5c | in n-00d8d3f1 | content email rev 1 | xy=(16,310) size=180x130
  n-939b1349 [appearance; rev 1] Release verification -> n-26c29e90 | in n-00d8d3f1 | content email rev 1 | xy=(16,470) size=180x130
  n-567a9a28 [appearance; rev 1] Release verification -> n-7e5a8cfa | in n-00d8d3f1 | content email rev 1 | xy=(16,620) size=180x130

n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
  parent: root
  x: 480
  y: 260
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-00d8d3f1 [surface; rev 1] Mail (5 children; list) | in root | screen=hidden xy=(480,260) size=640x560 min=480x400 z=5
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 6. look at 12.61s

```json
{
  "target": "n-4c8c7ee6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-4c8c7ee6 [surface; rev 1] Quote documents (4 children; list) | in root | screen=fully-visible xy=(60,100) size=640x560 min=480x400 z=11
  n-5ea8af9b [appearance; rev 1] Aster sensor quote -> n-b9245a5b | in n-4c8c7ee6 | content document rev 1 | xy=(16,0) size=180x130
  n-41dd1314 [appearance; rev 1] Birch sensor quote -> n-548a4251 | in n-4c8c7ee6 | content document rev 1 | xy=(16,150) size=180x130
  n-324838c5 [appearance; rev 1] Cedar sensor quote -> n-e41f15a2 | in n-4c8c7ee6 | content document rev 1 | xy=(16,300) size=180x130
  n-a621bc96 [appearance; rev 1] Cedar sensor quote -> n-0c274639 | in n-4c8c7ee6 | content document rev 1 | xy=(16,450) size=180x130

n-4c8c7ee6 [surface; rev 1] Quote documents (4 children; list) | in root | screen=fully-visible xy=(60,100) size=640x560 min=480x400 z=11
  parent: root
  x: 60
  y: 100
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-4c8c7ee6 [surface; rev 1] Quote documents (4 children; list) | in root | screen=fully-visible xy=(60,100) size=640x560 min=480x400 z=11
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 7. look at 12.61s

```json
{
  "target": "n-7b892481",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-7b892481 [surface; rev 1] Cost workbook (1 children; list) | in root | screen=clipped xy=(1300,100) size=640x560 min=480x400 z=7
  n-bb8d7eb1 [appearance; rev 1] OAS purchase cost -> n-78af7bdb | in n-7b892481 | content sheet rev 1 | xy=(16,0) size=180x130

n-7b892481 [surface; rev 1] Cost workbook (1 children; list) | in root | screen=clipped xy=(1300,100) size=640x560 min=480x400 z=7
  parent: root
  x: 1300
  y: 100
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-7b892481 [surface; rev 1] Cost workbook (1 children; list) | in root | screen=clipped xy=(1300,100) size=640x560 min=480x400 z=7
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 8. look at 12.61s

```json
{
  "target": "n-a37984d6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-a37984d6 [surface; rev 1] Decision editor (1 children; list) | in root | screen=occluded-by=n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(400,80) size=640x560 min=480x400 z=8
  n-d7d30296 [appearance; rev 1] Procurement decision -> n-86ae35d5 | in n-a37984d6 | content document rev 1 | xy=(16,0) size=180x130

n-a37984d6 [surface; rev 1] Decision editor (1 children; list) | in root | screen=occluded-by=n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(400,80) size=640x560 min=480x400 z=8
  parent: root
  x: 400
  y: 80
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-a37984d6 [surface; rev 1] Decision editor (1 children; list) | in root | screen=occluded-by=n-d32df780,n-ff4e6544,n-4c8c7ee6,n-257a855f,n-3844232a xy=(400,80) size=640x560 min=480x400 z=8
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 9. look at 12.62s

```json
{
  "target": "n-d32df780",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-d32df780 [surface; rev 1] Calendar (1 children; list) | in root | screen=occluded-by=n-ff4e6544,n-4c8c7ee6 xy=(50,200) size=640x560 min=480x400 z=9
  n-a5f0fbb3 [appearance; rev 1] OAS procurement review -> n-fd37f875 | in n-d32df780 | content calendar-event rev 1 | xy=(16,0) size=180x130

n-d32df780 [surface; rev 1] Calendar (1 children; list) | in root | screen=occluded-by=n-ff4e6544,n-4c8c7ee6 xy=(50,200) size=640x560 min=480x400 z=9
  parent: root
  x: 50
  y: 200
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-d32df780 [surface; rev 1] Calendar (1 children; list) | in root | screen=occluded-by=n-ff4e6544,n-4c8c7ee6 xy=(50,200) size=640x560 min=480x400 z=9
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 10. look at 12.62s

```json
{
  "target": "n-ff4e6544",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-ff4e6544 [surface; rev 1] Drafts (2 children; list) | in root | screen=occluded-by=n-4c8c7ee6,n-257a855f,n-3844232a xy=(500,200) size=640x560 min=480x400 z=10
  n-552a19bd [appearance; rev 1] Purchase confirmation -> n-d4706dca | in n-ff4e6544 | content draft rev 1 | xy=(16,0) size=180x130
  n-fe80df38 [appearance; rev 1] Personal unsaved reply -> n-72d73e25 | in n-ff4e6544 | content draft rev 1 | xy=(16,150) size=180x130

n-ff4e6544 [surface; rev 1] Drafts (2 children; list) | in root | screen=occluded-by=n-4c8c7ee6,n-257a855f,n-3844232a xy=(500,200) size=640x560 min=480x400 z=10
  parent: root
  x: 500
  y: 200
  width: 640
  height: 560
  layout: list
  Parent extent: 1600 x 1000

n-ff4e6544 [surface; rev 1] Drafts (2 children; list) | in root | screen=occluded-by=n-4c8c7ee6,n-257a855f,n-3844232a xy=(500,200) size=640x560 min=480x400 z=10
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 11. look at 12.62s

```json
{
  "target": "n-17d5efa6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
No visual children. Other aspects: content, actions, links, geometry.

n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
  parent: n-42361483
  width: 640
  height: 560
  layout: list
  Parent extent: 640 x 560

n-17d5efa6 [surface; rev 1] Questions for supplier (0 children; list) | in n-42361483
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 12. look at 16.58s

```json
{
  "target": "n-b9245a5b",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-b9245a5b [document; rev 1] Aster sensor quote
No visual children. Other aspects: content, actions, links, geometry.

n-b9245a5b [document; rev 1] Aster sensor quote

n-b9245a5b [document; rev 1] Aster sensor quote
CONTENT n-b9245a5b rev 1 (document)
  part body: Current quote, 6 October 2026. Aster: $225 per kit; $180 shipping per order; no mandatory extras. Quoted delivery 9 October. 12 kits available.

n-b9245a5b [document; rev 1] Aster sensor quote
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 13. look at 16.58s

```json
{
  "target": "n-548a4251",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-548a4251 [document; rev 1] Birch sensor quote
No visual children. Other aspects: content, actions, links, geometry.

n-548a4251 [document; rev 1] Birch sensor quote

n-548a4251 [document; rev 1] Birch sensor quote
CONTENT n-548a4251 rev 1 (document)
  part body: Current quote, 6 October 2026. Birch: $240 per kit, free shipping, mandatory setup $90 per order. Delivery 9 October. 12 kits available.

n-548a4251 [document; rev 1] Birch sensor quote
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 14. look at 16.58s

```json
{
  "target": "n-e41f15a2",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-e41f15a2 [document; rev 1] Cedar sensor quote
No visual children. Other aspects: content, actions, links, geometry.

n-e41f15a2 [document; rev 1] Cedar sensor quote

n-e41f15a2 [document; rev 1] Cedar sensor quote
CONTENT n-e41f15a2 rev 1 (document)
  part body: Superseded quote, 1 October 2026. Cedar: $205 per kit, $240 shipping, calibration included. Delivery 8 October.

n-e41f15a2 [document; rev 1] Cedar sensor quote
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 15. look at 16.58s

```json
{
  "target": "n-0c274639",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-0c274639 [document; rev 1] Cedar sensor quote
No visual children. Other aspects: content, actions, links, geometry.

n-0c274639 [document; rev 1] Cedar sensor quote

n-0c274639 [document; rev 1] Cedar sensor quote
CONTENT n-0c274639 rev 1 (document)
  part body: Current quote, 7 October 2026, supersedes 1 October. Cedar: $215 per kit, $240 shipping per order, mandatory calibration $120 per order. Delivery 10 October. 12 kits available.

n-0c274639 [document; rev 1] Cedar sensor quote
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 16. look at 16.58s

```json
{
  "target": "n-a821607c",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-a821607c [email; rev 1] Aster shipment confirmation
No visual children. Other aspects: content, actions, links, geometry.

n-a821607c [email; rev 1] Aster shipment confirmation

n-a821607c [email; rev 1] Aster shipment confirmation
CONTENT n-a821607c rev 1 (email)
  part body: Aster confirms delivery on 10 October. Keep the pilot kickoff on 3 October. Maya will verify reserve stock.

n-a821607c [email; rev 1] Aster shipment confirmation
No mutation verbs here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 17. look at 16.58s

```json
{
  "target": "n-34053b5c",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-34053b5c [email; rev 1] Aster shipment update — 7 October
No visual children. Other aspects: content, actions, links, geometry.

n-34053b5c [email; rev 1] Aster shipment update — 7 October

n-34053b5c [email; rev 1] Aster shipment update — 7 October
CONTENT n-34053b5c rev 1 (email)
  part body: This supersedes the 6 October sensor quote delivery promise: earliest delivery is now 12 October 2026. Price unchanged.

n-34053b5c [email; rev 1] Aster shipment update — 7 October
No mutation verbs here.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 18. look at 16.58s

```json
{
  "target": "n-78af7bdb",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-78af7bdb [sheet; rev 1] OAS purchase cost
No visual children. Other aspects: content, actions, links, geometry.

n-78af7bdb [sheet; rev 1] OAS purchase cost

n-78af7bdb [sheet; rev 1] OAS purchase cost
CONTENT n-78af7bdb rev 1
{
  "inputs": {
    "supplier": "TBD",
    "quantity": 12,
    "unit_price": 0,
    "shipping": 0,
    "extras": 0
  },
  "total": 0,
  "formula": "quantity * unit_price + shipping + extras",
  "budget": 3000
}

n-78af7bdb [sheet; rev 1] OAS purchase cost
  set_inputs: args {supplier:string, quantity:integer, unit_price:number, shipping:number, extras:number}. Update these five inputs atomically. Total is a derived formula. Budget belongs to the colleague; cannot write it.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 19. look at 16.58s

```json
{
  "target": "n-86ae35d5",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-86ae35d5 [document; rev 1] Procurement decision
No visual children. Other aspects: content, actions, links, geometry.

n-86ae35d5 [document; rev 1] Procurement decision

n-86ae35d5 [document; rev 1] Procurement decision
CONTENT n-86ae35d5 rev 1 (document)
  part supplier: Supplier: TBD.
  part total: Landed total: TBD.
  part time: Review time: TBD.
  part status: Status: Draft.
  part terms: Do not place the order before review approval.

n-86ae35d5 [document; rev 1] Procurement decision
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 20. look at 16.59s

```json
{
  "target": "n-fd37f875",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-fd37f875 [calendar-event; rev 1] OAS procurement review
No visual children. Other aspects: content, actions, links, geometry.

n-fd37f875 [calendar-event; rev 1] OAS procurement review

n-fd37f875 [calendar-event; rev 1] OAS procurement review
CONTENT n-fd37f875 rev 1
{
  "date": "2026-10-08",
  "zone": "UTC",
  "start": 840,
  "duration": 30,
  "attendees": [
    "Maya",
    "Inez",
    "Alex"
  ],
  "review_interval": [
    840,
    960
  ],
  "busy": {
    "Maya": [
      [
        840,
        870
      ]
    ],
    "Inez": [
      [
        870,
        900
      ]
    ],
    "Alex": [
      [
        850,
        880
      ]
    ]
  },
  "availability_note": "Intervals are [start,end) UTC minutes after midnight; excludes this appointment itself."
}

n-fd37f875 [calendar-event; rev 1] OAS procurement review
  schedule: args {start:integer UTC minutes after midnight}. Preserve date, duration and attendees; reject attendee conflicts and times outside the published review interval.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 21. look at 16.59s

```json
{
  "target": "n-d4706dca",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-d4706dca [draft; rev 1] Purchase confirmation
No visual children. Other aspects: content, actions, links, geometry.

n-d4706dca [draft; rev 1] Purchase confirmation

n-d4706dca [draft; rev 1] Purchase confirmation
CONTENT n-d4706dca rev 1
{
  "to": "",
  "subject": "",
  "body": "",
  "sent": false
}

n-d4706dca [draft; rev 1] Purchase confirmation
  compose: args {to:string, subject:string, body:string}. Replace this designated draft. Does not send; no send capability exists.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 22. look at 23.06s

```json
{
  "target": "n-78af7bdb",
  "aspect": "content"
}
```

```text
n-78af7bdb [sheet; rev 1] OAS purchase cost
CONTENT n-78af7bdb rev 1
{
  "inputs": {
    "supplier": "TBD",
    "quantity": 12,
    "unit_price": 0,
    "shipping": 0,
    "extras": 0
  },
  "total": 0,
  "formula": "quantity * unit_price + shipping + extras",
  "budget": 3000
}
```

### 23. act at 25.55s

```json
{
  "target": "n-78af7bdb",
  "expected": 1,
  "verb": "set_inputs",
  "args": {
    "supplier": "Cedar",
    "quantity": 12,
    "unit_price": 215,
    "shipping": 240,
    "extras": 120
  }
}
```

```text
{
  "error": "Stale target n-78af7bdb: expected 1, current revision 2. Read again; nothing from this action changed.",
  "recovery": "look at the target's actions or current state; no partial action committed."
}
```

### 24. look at 27.48s

```json
{
  "target": "n-78af7bdb",
  "aspect": "inspect",
  "depth": 0
}
```

```text
n-78af7bdb [sheet; rev 2] OAS purchase cost
No visual children. Other aspects: content, actions, links, geometry.

n-78af7bdb [sheet; rev 2] OAS purchase cost

n-78af7bdb [sheet; rev 2] OAS purchase cost
CONTENT n-78af7bdb rev 2
{
  "inputs": {
    "supplier": "TBD",
    "quantity": 12,
    "unit_price": 0,
    "shipping": 0,
    "extras": 0
  },
  "total": 0,
  "formula": "quantity * unit_price + shipping + extras",
  "budget": 2950
}

n-78af7bdb [sheet; rev 2] OAS purchase cost
  set_inputs: args {supplier:string, quantity:integer, unit_price:number, shipping:number, extras:number}. Update these five inputs atomically. Total is a derived formula. Budget belongs to the colleague; cannot write it.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 25. act at 30.08s

```json
{
  "target": "n-78af7bdb",
  "expected": 2,
  "verb": "set_inputs",
  "args": {
    "supplier": "Cedar",
    "quantity": 12,
    "unit_price": 215,
    "shipping": 240,
    "extras": 120
  }
}
```

```text
Committed event-2: set_inputs n-78af7bdb.
n-78af7bdb [sheet; rev 3] OAS purchase cost
```

### 26. act at 32.92s

```json
{
  "target": "n-86ae35d5",
  "expected": 1,
  "verb": "edit",
  "args": {
    "part": "supplier",
    "before": "Supplier: TBD.",
    "after": "Supplier: Cedar."
  }
}
```

```text
Committed event-3: edit n-86ae35d5.
n-86ae35d5 [document; rev 2] Procurement decision
```

### 27. act at 35.12s

```json
{
  "target": "n-86ae35d5",
  "expected": 2,
  "verb": "edit",
  "args": {
    "part": "total",
    "before": "Landed total: TBD.",
    "after": "Landed total: $2940."
  }
}
```

```text
Committed event-4: edit n-86ae35d5.
n-86ae35d5 [document; rev 3] Procurement decision
```

### 28. act at 37.76s

```json
{
  "target": "n-86ae35d5",
  "expected": 3,
  "verb": "edit",
  "args": {
    "part": "time",
    "before": "Review time: TBD.",
    "after": "Review time: 15:00 UTC."
  }
}
```

```text
Committed event-5: edit n-86ae35d5.
n-86ae35d5 [document; rev 4] Procurement decision
```

### 29. act at 39.50s

```json
{
  "target": "n-fd37f875",
  "expected": 1,
  "verb": "schedule",
  "args": {
    "start": 900
  }
}
```

```text
Committed event-6: schedule n-fd37f875.
n-fd37f875 [calendar-event; rev 2] OAS procurement review
```

### 30. act at 42.98s

```json
{
  "target": "n-d4706dca",
  "expected": 1,
  "verb": "compose",
  "args": {
    "to": "procurement@example.invalid",
    "subject": "Purchase confirmation \u2014 Cedar sensor kits",
    "body": "Please confirm purchase of 12 sensor kits from Cedar. Landed total: $2940. Delivery date: 10 October 2026. Procurement review: 8 October 2026, 15:00 UTC."
  }
}
```

```text
Committed event-7: compose n-d4706dca.
n-d4706dca [draft; rev 2] Purchase confirmation
```

### 31. act at 47.20s

```json
{
  "target": "n-17d5efa6",
  "expected": 1,
  "verb": "reference",
  "args": {
    "source": "n-0c274639"
  }
}
```

```text
Committed event-8: reference n-17d5efa6.
appearance-8 [appearance; rev 1] Cedar sensor quote -> n-0c274639 | in n-17d5efa6 | content document rev 1 | xy=(16,16) size=180x130
n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
```

### 32. act at 53.34s

```json
{
  "target": "n-00d8d3f1",
  "expected": 1,
  "verb": "frame",
  "args": {
    "x": 0,
    "y": 0,
    "width": 500,
    "height": 500
  }
}
```

```text
Committed event-9: frame n-00d8d3f1.
n-00d8d3f1 [surface; rev 2] Mail (5 children; list) | in root | screen=fully-visible xy=(0,0) size=500x500 min=480x400 z=14
root [surface; rev 2] Desk (21 children; fixed)
```

### 33. act at 56.70s

```json
{
  "target": "n-7b892481",
  "expected": 1,
  "verb": "frame",
  "args": {
    "x": 530,
    "y": 0,
    "width": 500,
    "height": 500
  }
}
```

```text
Committed event-10: frame n-7b892481.
n-7b892481 [surface; rev 2] Cost workbook (1 children; list) | in root | screen=fully-visible xy=(530,0) size=500x500 min=480x400 z=15
root [surface; rev 3] Desk (21 children; fixed)
```

### 34. act at 58.67s

```json
{
  "target": "n-a37984d6",
  "expected": 1,
  "verb": "frame",
  "args": {
    "x": 1060,
    "y": 0,
    "width": 500,
    "height": 500
  }
}
```

```text
Committed event-11: frame n-a37984d6.
n-a37984d6 [surface; rev 2] Decision editor (1 children; list) | in root | screen=fully-visible xy=(1060,0) size=500x500 min=480x400 z=16
root [surface; rev 4] Desk (21 children; fixed)
```

### 35. look at 62.26s

```json
{
  "target": "n-78af7bdb",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-78af7bdb [sheet; rev 3] OAS purchase cost
No visual children. Other aspects: content, actions, links, geometry.

n-78af7bdb [sheet; rev 3] OAS purchase cost

n-78af7bdb [sheet; rev 3] OAS purchase cost
CONTENT n-78af7bdb rev 3
{
  "inputs": {
    "supplier": "Cedar",
    "quantity": 12,
    "unit_price": 215,
    "shipping": 240,
    "extras": 120
  },
  "total": 2940,
  "formula": "quantity * unit_price + shipping + extras",
  "budget": 2950
}

n-78af7bdb [sheet; rev 3] OAS purchase cost
  set_inputs: args {supplier:string, quantity:integer, unit_price:number, shipping:number, extras:number}. Update these five inputs atomically. Total is a derived formula. Budget belongs to the colleague; cannot write it.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 36. look at 62.28s

```json
{
  "target": "n-86ae35d5",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-86ae35d5 [document; rev 4] Procurement decision
No visual children. Other aspects: content, actions, links, geometry.

n-86ae35d5 [document; rev 4] Procurement decision

n-86ae35d5 [document; rev 4] Procurement decision
CONTENT n-86ae35d5 rev 4 (document)
  part supplier: Supplier: Cedar.
  part total: Landed total: $2940.
  part time: Review time: 15:00 UTC.
  part status: Status: Draft.
  part terms: Do not place the order before review approval.

n-86ae35d5 [document; rev 4] Procurement decision
  edit: args {part: part ID, before: exact unique substring, after: replacement}. Edit only that match in this part; changes shared content.
  insert: args {after: existing part ID, id: new part ID, text: text}. Insert a content part immediately after the named part.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 37. look at 62.28s

```json
{
  "target": "n-fd37f875",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-fd37f875 [calendar-event; rev 2] OAS procurement review
No visual children. Other aspects: content, actions, links, geometry.

n-fd37f875 [calendar-event; rev 2] OAS procurement review

n-fd37f875 [calendar-event; rev 2] OAS procurement review
CONTENT n-fd37f875 rev 2
{
  "date": "2026-10-08",
  "zone": "UTC",
  "start": 900,
  "duration": 30,
  "attendees": [
    "Maya",
    "Inez",
    "Alex"
  ],
  "review_interval": [
    840,
    960
  ],
  "busy": {
    "Maya": [
      [
        840,
        870
      ]
    ],
    "Inez": [
      [
        870,
        900
      ]
    ],
    "Alex": [
      [
        850,
        880
      ]
    ]
  },
  "availability_note": "Intervals are [start,end) UTC minutes after midnight; excludes this appointment itself."
}

n-fd37f875 [calendar-event; rev 2] OAS procurement review
  schedule: args {start:integer UTC minutes after midnight}. Preserve date, duration and attendees; reject attendee conflicts and times outside the published review interval.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 38. look at 62.28s

```json
{
  "target": "n-d4706dca",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-d4706dca [draft; rev 2] Purchase confirmation
No visual children. Other aspects: content, actions, links, geometry.

n-d4706dca [draft; rev 2] Purchase confirmation

n-d4706dca [draft; rev 2] Purchase confirmation
CONTENT n-d4706dca rev 2
{
  "to": "procurement@example.invalid",
  "subject": "Purchase confirmation \u2014 Cedar sensor kits",
  "body": "Please confirm purchase of 12 sensor kits from Cedar. Landed total: $2940. Delivery date: 10 October 2026. Procurement review: 8 October 2026, 15:00 UTC.",
  "sent": false
}

n-d4706dca [draft; rev 2] Purchase confirmation
  compose: args {to:string, subject:string, body:string}. Replace this designated draft. Does not send; no send capability exists.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 39. look at 62.28s

```json
{
  "target": "n-72d73e25",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-72d73e25 [draft; rev 1] Personal unsaved reply
No visual children. Other aspects: content, actions, links, geometry.

n-72d73e25 [draft; rev 1] Personal unsaved reply

n-72d73e25 [draft; rev 1] Personal unsaved reply
CONTENT n-72d73e25 rev 1
{
  "to": "friend@example.invalid",
  "subject": "Weekend",
  "body": "Maybe Saturday \u2014 unfinished",
  "sent": false
}

n-72d73e25 [draft; rev 1] Personal unsaved reply
  compose: args {to:string, subject:string, body:string}. Replace this designated draft. Does not send; no send capability exists.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 40. look at 62.28s

```json
{
  "target": "n-17d5efa6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
  appearance-8 [appearance; rev 1] Cedar sensor quote -> n-0c274639 | in n-17d5efa6 | content document rev 1 | xy=(16,16) size=180x130

n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
  parent: n-42361483
  width: 640
  height: 560
  layout: list
  Parent extent: 640 x 560

n-17d5efa6 [surface; rev 2] Questions for supplier (1 children; list) | in n-42361483
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 41. look at 62.28s

```json
{
  "target": "n-00d8d3f1",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-00d8d3f1 [surface; rev 2] Mail (5 children; list) | in root | screen=fully-visible xy=(0,0) size=500x500 min=480x400 z=14
  n-e58b8388 [appearance; rev 1] Aster shipment confirmation -> n-a821607c | in n-00d8d3f1 | content email rev 1 | xy=(16,16) size=180x130
  n-b0064f08 [appearance; rev 1] Release verification -> n-9070311c | in n-00d8d3f1 | content email rev 1 | xy=(16,160) size=180x130
  n-3024f3c3 [appearance; rev 1] Aster shipment update — 7 October -> n-34053b5c | in n-00d8d3f1 | content email rev 1 | xy=(16,310) size=180x130
  n-939b1349 [appearance; rev 1] Release verification -> n-26c29e90 | in n-00d8d3f1 | content email rev 1 | xy=(16,470) size=180x130
  n-567a9a28 [appearance; rev 1] Release verification -> n-7e5a8cfa | in n-00d8d3f1 | content email rev 1 | xy=(16,620) size=180x130

n-00d8d3f1 [surface; rev 2] Mail (5 children; list) | in root | screen=fully-visible xy=(0,0) size=500x500 min=480x400 z=14
  parent: root
  x: 0
  y: 0
  width: 500
  height: 500
  layout: list
  Parent extent: 1600 x 1000

n-00d8d3f1 [surface; rev 2] Mail (5 children; list) | in root | screen=fully-visible xy=(0,0) size=500x500 min=480x400 z=14
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 42. look at 62.28s

```json
{
  "target": "n-7b892481",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-7b892481 [surface; rev 2] Cost workbook (1 children; list) | in root | screen=fully-visible xy=(530,0) size=500x500 min=480x400 z=15
  n-bb8d7eb1 [appearance; rev 1] OAS purchase cost -> n-78af7bdb | in n-7b892481 | content sheet rev 3 | xy=(16,0) size=180x130

n-7b892481 [surface; rev 2] Cost workbook (1 children; list) | in root | screen=fully-visible xy=(530,0) size=500x500 min=480x400 z=15
  parent: root
  x: 530
  y: 0
  width: 500
  height: 500
  layout: list
  Parent extent: 1600 x 1000

n-7b892481 [surface; rev 2] Cost workbook (1 children; list) | in root | screen=fully-visible xy=(530,0) size=500x500 min=480x400 z=15
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```

### 43. look at 62.30s

```json
{
  "target": "n-a37984d6",
  "aspect": "inspect",
  "depth": 1,
  "limit": 20
}
```

```text
n-a37984d6 [surface; rev 2] Decision editor (1 children; list) | in root | screen=fully-visible xy=(1060,0) size=500x500 min=480x400 z=16
  n-d7d30296 [appearance; rev 1] Procurement decision -> n-86ae35d5 | in n-a37984d6 | content document rev 4 | xy=(16,0) size=180x130

n-a37984d6 [surface; rev 2] Decision editor (1 children; list) | in root | screen=fully-visible xy=(1060,0) size=500x500 min=480x400 z=16
  parent: root
  x: 1060
  y: 0
  width: 500
  height: 500
  layout: list
  Parent extent: 1600 x 1000

n-a37984d6 [surface; rev 2] Decision editor (1 children; list) | in root | screen=fully-visible xy=(1060,0) size=500x500 min=480x400 z=16
  reference: args {source: content ID, part?: part ID, x?: number, y?: number}. Add an appearance of existing content, no copy.
  create: args {kind: note|task, title: text, parts: [{id, text}], x?: number, y?: number}. Create content plus its appearance here.
  order: args {items: [all immediate child IDs in desired order]}. Change reading order, not content.
  frame: args {x,y,width,height}. Position/resize this top-level window, reveal and raise it. Enforces minimum readable size, viewport and pinned dock. May cover other windows; inspect their screen status afterwards. Does not edit contents.
act requires expected = the TARGET's displayed revision. undo targets an event ID and expected=0.
```
