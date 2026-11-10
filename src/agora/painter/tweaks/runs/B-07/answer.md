Updated `taskboard-js` (`dk176`) with a small, one-second check-mark animation when a card transitions into Done.

Code was necessary; I edited the inline widget code and explicitly reviewed/reactivated it as Alex (`r228`). The other board and shared task/lane facts were untouched.

Stored code verified. Visual playback remains unverified because the widget is unmounted. Filtered or collapsed cards won’t show the animation.