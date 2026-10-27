Added “Snooze until tomorrow” to `taskboard-js` (`dk176`) through inline JavaScript, explicitly reviewed and reactivated as Alex.

Snoozes persist separately in `dk179`; cards return at the next local midnight. The other board and shared task/lane facts were untouched.

Verified saved code and grants. Visual behavior and midnight return were not runtime-tested; the widget is currently unmounted.