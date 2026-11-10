"""World-authored window-kind defaults. No application names or sizes here.

wm-settings sizes is an ordered JSON object. Later matching kinds override
earlier kinds. This is intent; HWNDs and observed geometry never enter it.
"""
from fnmatch import fnmatchcase
import json
import math


FIELDS = {'exe', 'app', 'agora', 'browser_class', 'window_class'}
FRACTIONS = {'width', 'height', 'min_width', 'min_height'}


def validate(value):
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict) or len(value) > 128:
        raise ValueError('sizes must be an object with at most 128 named kinds')
    for name, rule in value.items():
        if not isinstance(name, str) or not name or not isinstance(rule, dict):
            raise ValueError('each size kind needs a name and rule')
        if set(rule) - (FRACTIONS | {'match', 'compact'}):
            raise ValueError('unknown size rule field')
        match = rule.get('match', {})
        if not isinstance(match, dict) or set(match) - FIELDS:
            raise ValueError('match fields: exe, app, agora, browser_class, window_class')
        for pattern in match.values():
            if not isinstance(pattern, (str, bool, list)) or isinstance(pattern, list) and (
                    not pattern or any(not isinstance(p, str) for p in pattern)):
                raise ValueError('match values must be globs, lists of globs, or booleans')
        for key in FRACTIONS & rule.keys():
            n = rule[key]
            if isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) or not 0 < n <= 1:
                raise ValueError('size fractions must be greater than zero and at most one')
        if 'compact' in rule and not isinstance(rule['compact'], bool):
            raise ValueError('compact must be boolean')
    return value


def resolve(row, rules):
    result = {}
    for name, rule in rules.items():
        def matches(field, pattern):
            value = row.get(field)
            if isinstance(pattern, bool):
                return bool(value) == pattern
            value = str(value or '').replace('\\', '/')
            if field == 'exe':
                value = value.rsplit('/', 1)[-1]
            return any(fnmatchcase(value.casefold(), p.casefold()) for p in
                       (pattern if isinstance(pattern, list) else [pattern]))
        if all(matches(field, pattern) for field, pattern in rule.get('match', {}).items()):
            result.update(rule)
            result['kind'] = name
    return result


def dimensions(row, work, rules, observed, gaps=(0, 0)):
    """Fractions of usable space; half-width includes its share of the gutter."""
    rule = resolve(row, rules)
    outer, inner = gaps
    usable = (max(1, work.w - 2 * outer - inner), max(1, work.h - 2 * outer))
    minimum = tuple(max(1, math.floor(usable[i] * rule.get(key, 0)))
                    for i, key in enumerate(('min_width', 'min_height')))
    preferred = tuple(max(minimum[i], min(usable[i], round(usable[i] * rule[key])
                        if key in rule else observed[i]))
                      for i, key in enumerate(('width', 'height')))
    return preferred, minimum
