# Iteration log

## Initial outline trials

Meeting: 10/10 state checks; 29 calls, 44.11 seconds. Terra explicitly reported
the lack of a single child-layout view, and separately read each card's geometry.
Both initial runs tried depth=4 / limit=100, then recovered from the bounded-read
refusal. The explicit tool schema advertised depth<=3 / limit<=20.

Proposal: 9/10 checks, 19 calls, 48.94 seconds. The original prompt ambiguously
said "new paragraph reference" after mentioning both an inserted paragraph and
a delivery-paragraph reference. Terra added an extra reference and reported that
choice. This is a task-design ambiguity, not clean evidence of interface failure.
Preserve `outline-proposal-1`; clarify the task, keep the original checker, and
run a new outline baseline before comparing projection changes.

## First interface hypothesis, recorded before implementation

Keep operations unchanged. A context projection should combine immediate-child
placement and content-reference identity, and expose the selected node's action
signatures without a separate discovery call. It should show each entry's parent
so a page does not begin with an orphaned indented node. Oversized read requests
can be bounded with an explicit clamp notice, rather than wasting a refusal call.
These are candidate improvements, not assumed wins; measure output size as well
as calls and elapsed time. No new layout or editing capabilities in this variation.
