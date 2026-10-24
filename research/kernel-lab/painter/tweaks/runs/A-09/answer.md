Added “Snooze until tomorrow” to card menus on `taskboard-components` (`dk170`). Cards hide until the next UTC day, then return in their existing lane.

No code was necessary—only arrangement changes. The other board remains unchanged.

Verified hide/return conditions using “Fix the bar before the neighbourhood demo” (`dk105`), then cleared the test snooze. All 25 cards are restored. Visual appearance and an actual midnight rollover were not inspected.