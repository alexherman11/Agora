Updated taskboard-components (dk170) with an 850 ms check-mark animation for observed moves into Done.

Code was necessary: added and explicitly reviewed board-specific component dk179 as Alex. Other board and shared task/lane facts are unchanged.

Structure verified with `look-view`; animation pixels could not be inspected. Initial loads don’t animate; reduced motion uses a brief static check.