"""expr: arithmetic, comparisons and `if` for lenses, in the shape of a spreadsheet formula inside the declarative tree.

Alex, 5 Oct 2026: "I want if and arithmetic." Built from what the residents' sketches agreed on (Pike a1397, Juniper
a1399, the arithmetic-with-reach note a1448), keeping only what earned its place:

  * values have kinds (number, text, date, time, duration, bool, none) and are never coerced: a stored string is a
    number only when the whole of it is one ('7' is; '2,550 USD' is not, and says so);
  * a missing value is none, printed as none, never 0 or ""; arithmetic on none is none with the reason;
  * aggregates over a selection (count, sum, min, max) carry their reach: '41 of 43; 2 have none', and anything
    built from a partial aggregate stays marked partial;
  * `if` is a guarded definition: several `let name = value when <test>` lines and one `otherwise`; the first that
    holds is taken, and an overlap is said, never silently resolved by position;
  * every expression prints its inputs and its result, so the text printer can say what a value came from;
  * text joins only text: "Total: " + 3 is none with the reason; write it in text as "Total: $(...)".

Grammar (precedence low to high):
    or  ::= and ('or' and)*            x or y: y when x is none (the author's fallback), else x when x is not false
    and ::= not ('and' not)*
    not ::= 'not' not | cmp
    cmp ::= sum (('=' | '!=' | '<' | '>' | '<=' | '>=' | 'has' | '!has') sum)?
    sum ::= term (('+' | '-') term)*
    term ::= unary (('*' | '/') unary)*
    unary ::= '-' unary | atom
    atom ::= number | duration (3d 2h 30m 1w) | date (2026-10-05[ 14:30]) | "text" | $name | $frame.field
           | name (a let named above) | none | true | false | '(' expr ')'
           | count(<selection>) | sum($field of <selection>) | min(...) | max(...)
           | function '(' expr (',' expr)* ')'       weekday($due + 1d), day-n($start, 17), days-from(a, b)

The functions (FUNCS; 9 Oct, step 5 of the grammar unification) are what `derive` used to name from its own closed
list, now ordinary calls whose arguments are expressions: `derive wd = weekday $d` reads as `let wd = weekday($d)`.
A function over a date takes a date, a date-time or a freshness value (`e412 prop · 2026-09-25 21:40`); a wrong
argument is none with the reason, as any expression is. `days-from(a, b)` is a value of kind rows (a table a repeat
can go `over`); the row source `days:<a>..<b>` is the newer way to say the same under `of`.

The evaluator reads names through an environment the caller supplies (see `evaluate`), so the lens's own frames,
props, lets and host facts answer, and every read is reported back for the fence and the print."""
import datetime
import re

KINDS = ("number", "text", "date", "time", "duration", "bool", "none", "rows")
AGGREGATES = ("count", "sum", "min", "max", "join")      # join (13 Oct): the texts, one a line, in order
KEYWORDS = ("and", "or", "not", "has", "none", "true", "false", "of") + AGGREGATES


class Value:
    __slots__ = ("kind", "v", "reach", "partial", "why")

    def __init__(self, kind, v=None, reach=None, partial=False, why=None):
        self.kind, self.v, self.reach, self.partial, self.why = kind, v, reach, partial, why

    def is_none(self):
        return self.kind == "none"

    def __repr__(self):
        return f"Value({self.kind}, {self.v!r})"


def none(why):
    return Value("none", None, why=why)


class ExprError(Exception):
    """The expression cannot be read (a parse error): said with the text, when a lens is saved."""


# ---------------------------------------------------------------------------------------------------------------------
# typing a stored string: the whole of it, or it stays text
# ---------------------------------------------------------------------------------------------------------------------
_NUM = re.compile(r"-?\d+(?:\.\d+)?")
_DUR = re.compile(r"(\d+(?:\.\d+)?)\s*([wdhm])")
_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?")
_UNIT = {"w": 7 * 24 * 60, "d": 24 * 60, "h": 60, "m": 1}


def typed(raw, name="value"):
    """A stored string (or Python value) as a Value. '' and None are none; a whole number, date, time or duration is
    that kind; anything else is text."""
    if isinstance(raw, Value):
        return raw
    if raw is None:
        return none(f"no {name}")
    if isinstance(raw, bool):
        return Value("bool", raw)
    if isinstance(raw, (int, float)):
        return Value("number", raw)
    if isinstance(raw, (datetime.date, datetime.datetime)):
        return Value("time", raw) if isinstance(raw, datetime.datetime) else Value("date", raw)
    if isinstance(raw, datetime.timedelta):
        return Value("duration", raw)
    s = str(raw).strip()
    if s == "":
        return none(f"no {name}")
    if _NUM.fullmatch(s):
        return Value("number", float(s) if "." in s else int(s))
    m = _DATE.fullmatch(s)
    if m:
        try:
            d = datetime.date.fromisoformat(m.group(1))
        except ValueError:
            return Value("text", s)
        if m.group(2):
            return Value("time", datetime.datetime(d.year, d.month, d.day, int(m.group(2)), int(m.group(3)), int(m.group(4) or 0)))
        return Value("date", d)
    if re.fullmatch(r"(?:\d+(?:\.\d+)?\s*[wdhm]\s*)+", s):
        minutes = sum(float(n) * _UNIT[u] for n, u in _DUR.findall(s))
        return Value("duration", datetime.timedelta(minutes=minutes))
    if s in ("true", "false"):
        return Value("bool", s == "true")
    return Value("text", s)


def fmt(val, reach=True):
    """How a value prints: none as none, numbers without a trailing .0, dates as ISO, durations in the largest unit
    that divides them; with its reach after a dot when it has one."""
    if val.kind == "none":
        s = "none"
    elif val.kind == "bool":
        s = "true" if val.v else "false"
    elif val.kind == "number":
        s = str(int(val.v)) if float(val.v).is_integer() else f"{val.v:.4g}" if abs(val.v) < 1e6 else str(val.v)
    elif val.kind == "date":
        s = val.v.isoformat()
    elif val.kind == "time":       # a5530: a time that has seconds ($now, a moment counted to) keeps them
        s = val.v.strftime("%Y-%m-%d %H:%M" + (":%S" if val.v.second else ""))
    elif val.kind == "duration":
        mins = val.v.total_seconds() / 60
        neg = mins < 0
        mins = abs(mins)
        for u in ("w", "d", "h"):
            if mins and mins % _UNIT[u] == 0:
                s = f"{int(mins // _UNIT[u])}{u}"
                break
        else:
            s = f"{int(mins)}m" if float(mins).is_integer() else f"{mins:.4g}m"
        if neg:
            s = "-" + s
    elif val.kind == "rows":
        s = f"{len(val.v)} rows"
    else:
        s = str(val.v)
    return f"{s} · {val.reach}" if (reach and val.reach) else s


# ---------------------------------------------------------------------------------------------------------------------
# functions: what `derive` named from scene.INTERPS until 9 Oct, as calls over expression values. Each takes a list of
# Values and returns a Value; a wrong argument is none with the reason. The list is closed: a new one is argued for and
# added here (Pike W6), and it prints as every expression does.
# ---------------------------------------------------------------------------------------------------------------------
_FRESH = re.compile(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}))?")


def _date_in(v):
    """The date (and the clock, when there is one) inside a value: a date, a date-time, or text that holds one, as a
    freshness value does (`e412 prop · 2026-09-25 21:40`). -> (date, 'HH:MM' or None), or (None, None)."""
    if v.kind == "date":
        return v.v, None
    if v.kind == "time":
        return v.v.date(), v.v.strftime("%H:%M")
    if v.kind == "text":
        m = _FRESH.search(v.v)
        if m:
            try:
                return datetime.date.fromisoformat(m.group(1)), m.group(2)
            except ValueError:
                return None, None
    return None, None


def _f_weekday(args):
    d, _ = _date_in(args[0])
    return Value("text", d.strftime("%a")) if d else none(f"weekday wants a date; got {fmt(args[0])!r}")


def _f_week_of(args):
    d, _ = _date_in(args[0])
    return Value("date", d - datetime.timedelta(days=d.weekday())) if d else none(f"week-of wants a date; got {fmt(args[0])!r}")


def _f_day_n(args):
    d, _ = _date_in(args[0])
    n = args[1]
    if d is None or n.kind != "number" or not float(n.v).is_integer():
        return none(f"day-n wants <date> <n>; got {fmt(args[0])!r} {fmt(n)!r}")
    return Value("date", d + datetime.timedelta(days=int(n.v) - 1))


def day_rows(a, b):
    """The days from a to b, each a row `n date weekday week`; None with the reason when the span is no span or more
    than a year (a budget, as the node budget is). Shared by days-from(a, b) and the row source days:<a>..<b>."""
    if a is None or b is None:
        return None, "days-from wants <start> <end> as dates"
    if b < a or (b - a).days > 366:
        return None, f"days-from: {a} to {b} is not a span of at most a year"
    out = []
    for k in range((b - a).days + 1):
        d = a + datetime.timedelta(days=k)
        out.append({"n": k + 1, "date": d.isoformat(), "weekday": d.strftime("%a"), "week": (d - datetime.timedelta(days=d.weekday())).isoformat()})
    return out, None


def _f_days_from(args):
    a, _ = _date_in(args[0])
    b, _ = _date_in(args[1])
    if a is None or b is None:
        return none(f"days-from wants <start> <end> as dates; got {fmt(args[0])!r} {fmt(args[1])!r}")
    rows, why = day_rows(a, b)
    return Value("rows", rows) if rows is not None else none(why)


def _f_day_or_time(args):
    """Juniper (day lens a496): the time alone when the day is today, `Mon 28` within a week either way, else the date.
    Today is an argument, so the read is visible; goldens freeze it per world."""
    d, clock = _date_in(args[0])
    today, _ = _date_in(args[1])
    if not d or not today:
        return none(f"day-or-time wants a date-time or a freshness value and today; got {fmt(args[0])!r}, {fmt(args[1])!r}")
    if d == today:
        return Value("text", clock or d.isoformat())
    return Value("text", d.strftime("%a %d").replace(" 0", " ") if abs((d - today).days) <= 7 else d.isoformat())


def _f_time(args):
    d, clock = _date_in(args[0])
    return Value("text", clock) if clock else none(f"time wants a date-time or a freshness value; got {fmt(args[0])!r}")


def _f_date(args):
    d, _ = _date_in(args[0])
    return Value("date", d) if d else none(f"date wants a date, a date-time or a freshness value; got {fmt(args[0])!r}")


def _f_words_of(args):
    """15 Oct (a5398): what someone typed, as one `?` term. A selection splits on spaces and commas and has no quoting,
    so a find box holding `home base` could not reach `?home+base`: `let q = words-of($v.find)`, then `of ?$q`."""
    words = [w for w in re.split(r"[\s,+]+", fmt(args[0], reach=False)) if w]
    return Value("text", "+".join(words)) if words else none("words-of: no words")


def _spaced(s):
    """a5949: a text with every run of white space as one space, and where each of its characters came from."""
    out, at, gap = [], [], False
    for i, ch in enumerate(s):
        if ch.isspace():
            gap = bool(out)
            continue
        if gap:
            out.append(" ")
            at.append(i - 1)
            gap = False
        out.append(ch)
        at.append(i)
    return "".join(out), at


def find_words(text, words):
    """a5949 (Pike c5957, from a5020 section 4: a comment keeps its quoted words and finds them again exactly, never by a
    guess): where `words` first stand in `text`, however the white space falls (a line break where a space was), with
    the case as written. -> (start, end) in `text`, or None."""
    t, at = _spaced(text)
    w = _spaced(words)[0]
    if not w:
        return None
    i = t.find(w)
    return None if i < 0 else (at[i], at[i + len(w) - 1] + 1)


def _anchor_args(name, args):
    text, words = fmt(args[0], reach=False), fmt(args[1], reach=False)
    hit = find_words(text, words)
    return text, hit, (None if hit else none(f"{name}: the words are not in the text"))


def _f_section_of(args):
    """a5949: the heading over the first place the words stand in a Markdown text (a line starting with #), as its
    words; "" when they stand before every heading; none when they are not in the text. Where a comment's words are now."""
    text, hit, no = _anchor_args("section-of", args)
    if no:
        return no
    heads = [m for m in re.finditer(r"(?m)^#{1,6}\s+(.*\S)\s*$", text[:hit[0]])]
    return Value("text", heads[-1].group(1) if heads else "")


def _f_words_before(args):
    """a5949: the (at most) six words just before the first place the words stand; "" at the start; none when absent.
    Kept with a comment, they tell 'changed' (the words around it still stand) from 'gone'."""
    text, hit, no = _anchor_args("words-before", args)
    return no or Value("text", " ".join(text[:hit[0]].split()[-6:]))


def _f_words_after(args):
    """a5949: the (at most) six words just after the first place the words stand; "" at the end; none when absent."""
    text, hit, no = _anchor_args("words-after", args)
    return no or Value("text", " ".join(text[hit[1]:].split()[:6]))


# a6460 (Alex, 17 Oct: 'I need some better way to read these need-you proposals'): what a reader puts above a document.
# Every item tagged for Alex opens with a 'For Alex' block (the Handbook's rule): a heading or a bold line 'For Alex',
# then at most five lines 'What: ...', 'I recommend: ...', 'I need: ...' (a list, a quote or bold keys all read).
_FA_HEAD = re.compile(r"^\s*(?:#{1,6}\s*|>\s*)?(?:\*\*|__)?\s*For Alex\s*(?:\*\*|__)?\s*:?\s*(?:\*\*|__)?\s*$", re.I)
_FA_KEYS = {"what": "what", "what it is": "what", "i recommend": "recommend", "recommend": "recommend",
            "recommendation": "recommend", "i need": "need", "need": "need", "what i need": "need", "needs": "need"}
_FA_LINE = re.compile(r"^\s*(?:>\s*)?(?:[-*+]\s+)?(?:\*\*|__)?([A-Za-z][A-Za-z ]{1,20}?)\s*:\s*(?:\*\*|__)?\s*(.*\S)?\s*$")


def _for_alex_block(text):
    """-> (start, end, {what, recommend, need}) of the first For Alex block, or None. The block runs from its head to a
    blank line after its first key, or the next heading."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not _FA_HEAD.match(line):
            continue
        keys, j = {}, i + 1
        while j < len(lines):
            s = lines[j]
            if re.match(r"^\s*#{1,6}\s", s) or (not s.strip() and keys):
                break
            m = _FA_LINE.match(s.replace("**", "").replace("__", "")) if s.strip() else None
            k = _FA_KEYS.get((m.group(1) or "").strip().lower()) if m else None
            if k and k not in keys:
                keys[k] = (m.group(2) or "").strip()
            j += 1
        return i, j, keys
    return None


def _f_for_alex(args):
    """for-alex(text, what|recommend|need|rest): a line of the document's For Alex block, or (rest) the document
    without it; none when it has no block or no such line."""
    text, key = fmt(args[0], reach=False), fmt(args[1], reach=False).strip().lower()
    if key not in ("what", "recommend", "need", "rest"):
        return none(f"for-alex: the second argument is what, recommend, need or rest; got {key!r}")
    hit = _for_alex_block(text)
    if key == "rest":
        if not hit:
            return Value("text", text)
        lines = text.split("\n")
        return Value("text", "\n".join(lines[:hit[0]] + lines[hit[1]:]).strip("\n"))
    v = (hit[2].get(key) if hit else None)
    return Value("text", v) if v else none(f"for-alex: no {key} line")


def _first_sentence(text, lists):
    """The first sentence of the first line of prose (lists too when `lists`, their marks taken off), or None."""
    fa = _for_alex_block(text)
    lines, fence, opened = text.split("\n"), False, False
    for i, s in enumerate(lines):
        t = s.strip()
        if t.startswith(("```", "~~~")):
            fence = not fence
            continue
        # the opening only: a heading after words (other than a For Alex block) ends the search, so a report whose
        # opening is a byline and lists gives none, never a sentence from its third section
        if not fence and re.match(r"^#{1,6}\s", t) and opened:
            break
        if t and not fence and not re.match(r"^#{1,6}\s", t) and not (fa and fa[0] <= i < fa[1]):
            opened = True
        if lists:
            t = re.sub(r"^([-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+)", "", t)
        if fence or not t or (fa and fa[0] <= i < fa[1]) or re.match(r"^(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||!\[\[)", t):
            continue
        if t.endswith(":") or re.search(r"\[[\w ]+\]\s*=", t) or len(t.split()) < 4:
            continue
        m = re.match(r"(.+?[.!?])(?=\s+[A-Z“\"(\[]|\s*$)", t)
        out = (m.group(1) if m else t).strip()
        if len(out) > 220:
            out = out[:220].rsplit(" ", 1)[0].rstrip(" ,;:-—(") + "…"
        return out
    return None


def _f_lead(args):
    """lead(text): the first sentence of the first paragraph of prose in a Markdown text: past headings, lists, quotes,
    tables, code, a For Alex block, a label line ending ':' and a legend ('[read] = ...'). At most ~220 characters.
    What a reader shows as 'what this is' when the thing has no brief= and no For Alex block; none when there is none."""
    out = _first_sentence(fmt(args[0], reach=False), False)
    return Value("text", out) if out else none("lead: no paragraph of prose")


def _f_gist(args):
    """gist(text): as lead, but a list item counts as prose: what Skim shows under each heading of a section that is
    only a list (the collaboration report's sections are)."""
    out = _first_sentence(fmt(args[0], reach=False), True)
    return Value("text", out) if out else none("gist: no sentence")


def _f_read_minutes(args):
    """read-minutes(text): about how many minutes the words take to read, at 220 a minute; at least 1."""
    n = len(fmt(args[0], reach=False).split())
    return Value("number", max(1, round(n / 220)))


FUNCS = {"weekday": (("date",), _f_weekday), "week-of": (("date",), _f_week_of), "day-n": (("date", "n"), _f_day_n),
         "days-from": (("start", "end"), _f_days_from), "day-or-time": (("when", "today"), _f_day_or_time),
         "time": (("when",), _f_time), "date": (("when",), _f_date), "words-of": (("text",), _f_words_of),
         "section-of": (("text", "words"), _f_section_of), "words-before": (("text", "words"), _f_words_before),
         "words-after": (("text", "words"), _f_words_after), "for-alex": (("text", "key"), _f_for_alex),
         "lead": (("text",), _f_lead), "gist": (("text",), _f_gist), "read-minutes": (("text",), _f_read_minutes)}


def call(name, args):
    """Apply a function by name to Values. Unknown names and wrong counts are none with the reason."""
    if name not in FUNCS:
        return none(f"no function {name!r}; the list is closed: " + ", ".join(f"{k}({', '.join(p)})" for k, (p, _f) in FUNCS.items()))
    params, fn = FUNCS[name]
    if len(args) != len(params):
        return none(f"{name} takes {len(params)} argument(s): {', '.join(params)}; got {len(args)}")
    bad = [a for a in args if a.is_none()]
    if bad:
        return bad[0]
    return fn(args)


# ---------------------------------------------------------------------------------------------------------------------
# tokens
# ---------------------------------------------------------------------------------------------------------------------
_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<date>\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?)
  | (?P<dur>\d+(?:\.\d+)?[wdhm]\b)
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<str>"[^"]*")
  | (?P<name>\$\w+(?:\.\w+)?)
  | (?P<at>@[\w$.-]+)
  | (?P<call>[A-Za-z_][\w-]*)(?=\()
  | (?P<word>[A-Za-z_]\w*)
  | (?P<op><=|>=|!=|!has\b|=|<|>|\+|-|\*|/|\(|\)|,)
""", re.X)


def _close_of(text, i):
    """The index of the `)` that closes the `(` at text[i], counting nested brackets; -1 when there is none."""
    depth = 0
    for k in range(i, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                return k
    return -1


def tokens(text):
    out, i = [], 0
    while i < len(text):
        m = _TOKEN.match(text, i)
        if not m:
            raise ExprError(f"cannot read {text[i:i + 12]!r} in {text!r}")
        kind = m.lastgroup
        tok = m.group(kind)
        i = m.end()
        if kind == "ws":
            continue
        if kind == "call" and tok in AGGREGATES:
            close = _close_of(text, i)          # an aggregate's argument is a selection, kept as written
            if close < 0:
                raise ExprError(f"{tok}( has no closing ) in {text!r}")
            out.append(("agg", tok, text[i + 1:close].strip()))
            i = close + 1
            continue
        out.append((kind, tok))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# parse -> a small tree of tuples
# ---------------------------------------------------------------------------------------------------------------------
_PARSED = {}


def parse(text):
    """-> the tree of `text`. 14 Oct (a4838): a lens evaluates the same few lets and guards for every thing it shows
    (4600 parses of a few dozen texts on a 134-thing page, 15% of its build), so a tree is kept by its text; nothing
    changes a tree once made (evaluate only reads it)."""
    tree = _PARSED.get(text)
    if tree is None:
        tree = _parse(text)
        if len(_PARSED) >= 4096:
            _PARSED.clear()
        _PARSED[text] = tree
    return tree


def _parse(text):
    toks = tokens(text)
    pos = [0]

    def peek():
        return toks[pos[0]] if pos[0] < len(toks) else None

    def take(*want):
        t = peek()
        if t and (t[0] in want or (t[0] in ("op", "word") and t[1] in want)):
            pos[0] += 1
            return t
        return None

    def expect(what):
        t = take(what)
        if not t:
            raise ExprError(f"expected {what!r} at {' '.join(x[1] for x in toks[pos[0]:pos[0] + 3]) or 'the end'} in {text!r}")
        return t

    def p_or():
        n = p_and()
        while take("or"):
            n = ("or", n, p_and())
        return n

    def p_and():
        n = p_not()
        while take("and"):
            n = ("and", n, p_not())
        return n

    def p_not():
        if take("not"):
            return ("not", p_not())
        return p_cmp()

    def p_cmp():
        n = p_sum()
        t = peek()
        if t and ((t[0] == "op" and t[1] in ("=", "!=", "<", ">", "<=", ">=", "!has")) or (t[0] == "word" and t[1] == "has")):
            pos[0] += 1
            return ("cmp", t[1], n, p_sum())
        return n

    def p_sum():
        n = p_term()
        while True:
            t = peek()
            if t and t[0] == "op" and t[1] in ("+", "-"):
                pos[0] += 1
                n = ("bin", t[1], n, p_term())
            else:
                return n

    def p_term():
        n = p_unary()
        while True:
            t = peek()
            if t and t[0] == "op" and t[1] in ("*", "/"):
                pos[0] += 1
                n = ("bin", t[1], n, p_unary())
            else:
                return n

    def p_unary():
        if take("-"):
            return ("neg", p_unary())
        return p_atom()

    def p_atom():
        t = peek()
        if t is None:
            raise ExprError(f"expected a value at the end of {text!r}")
        pos[0] += 1
        kind = t[0]
        if kind == "num":
            return ("lit", typed(t[1]))
        if kind == "dur" or kind == "date":
            return ("lit", typed(t[1]))
        if kind == "str":
            return ("lit", Value("text", t[1][1:-1]))
        if kind == "name":
            return ("name", t[1])
        if kind == "at":
            return ("at", t[1])         # @pike, @$me: a bare word on the right of has, as the old value test allowed
        if kind == "agg":
            name, inner = t[1], t[2]
            if name == "count":
                return ("count", inner)
            m = re.fullmatch(r"\$(\w+)\s+of\s+(.+)", inner)
            if not m:
                raise ExprError(f"{name}(...) takes `$field of <selection>`; got {inner!r}")
            return ("agg", name, m.group(1), m.group(2).strip())
        if kind == "call":
            if t[1] not in FUNCS:
                raise ExprError(f"no function {t[1]!r} in {text!r}; the list is closed: " + ", ".join(f"{k}({', '.join(p)})" for k, (p, _f) in FUNCS.items()))
            expect("(")
            args = []
            if not take(")"):
                args.append(p_or())
                while take(","):
                    args.append(p_or())
                expect(")")
            if len(args) != len(FUNCS[t[1]][0]):
                raise ExprError(f"{t[1]} takes {len(FUNCS[t[1]][0])} argument(s): {', '.join(FUNCS[t[1]][0])}; got {len(args)} in {text!r}")
            return ("call", t[1], args)
        if kind == "word":
            if t[1] == "none":
                return ("lit", none("none, as written"))
            if t[1] in ("true", "false"):
                return ("lit", Value("bool", t[1] == "true"))
            if t[1] in KEYWORDS:
                raise ExprError(f"{t[1]!r} is not a value in {text!r}")
            return ("name", t[1])           # a let named above
        if kind == "op" and t[1] == "(":
            n = p_or()
            expect(")")
            return n
        raise ExprError(f"unexpected {t[1]!r} in {text!r}")

    tree = p_or()
    if peek() is not None:
        raise ExprError(f"unexpected {peek()[1]!r} after the expression in {text!r}")
    return tree


def looks_like(text, lets=()):
    """Does this `only when` text mean an expression rather than a selection? Expressions begin with a $name, a
    bracket, `not`, a number, a quote, none/true/false, an aggregate, or a let named above; selections begin with a
    term like kind:note. The older `$x <op> v` form is this expression (scene._one_test reads it as one)."""
    s = (text or "").strip()
    if not s:
        return False
    head = re.split(r"[\s(]", s, 1)[0]
    if s[0] in "$(-\"" or s[0].isdigit():
        return True
    if head in ("not", "none", "true", "false") or ((head in AGGREGATES or head in FUNCS) and s.startswith(head + "(")):
        return True
    return head in lets and re.fullmatch(r"\w+", head) is not None


def bare_words(text):
    """The bare words of an expression that are not keywords: each must be a let named above, or is refused."""
    try:
        return [t[1] for t in tokens(text) if t[0] == "word" and t[1] not in KEYWORDS]
    except ExprError:
        return []


def names_in(text):
    """Every $name and $frame.field an expression reads, plus bare let names: for resolve and deps."""
    out = []
    try:
        for t in tokens(text):
            if t[0] == "name":
                out.append(t[1])
            elif t[0] == "word" and t[1] not in KEYWORDS:
                out.append("$" + t[1])
            elif t[0] == "agg":
                out += re.findall(r"\$\w+(?:\.\w+)?", t[2]) if t[1] == "count" else re.findall(r"\$\w+(?:\.\w+)?", t[2].split(" of ", 1)[-1])
    except ExprError:
        pass
    return out


# ---------------------------------------------------------------------------------------------------------------------
# evaluate
# ---------------------------------------------------------------------------------------------------------------------
_COMPARABLE = {"number", "date", "time", "duration", "text"}


_ID = re.compile(r"([a-z]+)(\d+)")


def _cmp(op, a, b):
    if op in ("has", "!has"):
        # a5949: however the white space falls, so words quoted across a line break are still found
        hit = _spaced(fmt(b, reach=False).lower())[0] in _spaced(fmt(a, reach=False).lower())[0]
        return Value("bool", hit if op == "has" else not hit)
    if a.kind != b.kind:
        if "number" in (a.kind, b.kind) and "text" in (a.kind, b.kind):
            t = a if a.kind == "text" else b
            return none(f"{fmt(t)!r} is not a number")
        return none(f"cannot compare {a.kind} with {b.kind}")
    if a.kind not in _COMPARABLE and op not in ("=", "!="):
        return none(f"cannot order {a.kind}s")
    x, y = a.v, b.v
    if a.kind == "text" and op not in ("=", "!="):
        # a5530: two ids of one letter compare by their number (e9 < e10, as the events were made), not as letters
        mx, my = _ID.fullmatch(x), _ID.fullmatch(y)
        if mx and my and mx.group(1) == my.group(1):
            x, y = int(mx.group(2)), int(my.group(2))
    return Value("bool", {"=": x == y, "!=": x != y, "<": x < y, ">": x > y, "<=": x <= y, ">=": x >= y}[op])


def _arith(op, a, b):
    ka, kb = a.kind, b.kind
    try:
        if op == "+":
            if ka == kb == "number" or ka == kb == "duration":
                return Value(ka, a.v + b.v)
            if ka in ("date", "time") and kb == "duration":
                return Value(ka, a.v + b.v)
            if ka == "duration" and kb in ("date", "time"):
                return Value(kb, b.v + a.v)
            if "text" in (ka, kb):
                return none("text joins only text; write it in text as \"... $(...)\"")
        elif op == "-":
            if ka == kb == "number" or ka == kb == "duration":
                return Value(ka, a.v - b.v)
            if ka == kb and ka in ("date", "time"):
                d = a.v - b.v
                return Value("duration", d if isinstance(d, datetime.timedelta) else datetime.timedelta(days=d))
            if ka in ("date", "time") and kb == "duration":
                return Value(ka, a.v - b.v)
        elif op == "*":
            if ka == kb == "number":
                return Value("number", a.v * b.v)
            if ka == "duration" and kb == "number":
                return Value("duration", a.v * b.v)
            if ka == "number" and kb == "duration":
                return Value("duration", b.v * a.v)
        elif op == "/":
            if kb == "number" and b.v == 0:
                return none("divided by zero")
            if ka == kb == "number":
                return Value("number", a.v / b.v)
            if ka == "duration" and kb == "number":
                return Value("duration", a.v / b.v)
            if ka == kb == "duration":
                return none("a duration divided by a duration has no unit here") if b.v.total_seconds() == 0 else Value("number", a.v.total_seconds() / b.v.total_seconds())
    except (TypeError, OverflowError) as e:
        return none(str(e))
    return none(f"{ka} {op} {kb} has no meaning")


def _carry(res, *ins):
    """Reach travels: a value built from a partial aggregate says so (a1448, Pike c1475)."""
    part = [v for v in ins if v.partial]
    if part and not res.is_none():
        res.partial = True
        res.reach = res.reach or ("from " + part[0].reach.split(";")[0].strip())
    return res


def evaluate(tree, env):
    """env: get(name) -> raw or Value or None (a $name, $frame.field or let); select(q) -> ids; field(id, f) -> raw;
    reads: a list the evaluator appends (name, printed value) to. -> Value."""
    def ev(n):
        k = n[0]
        if k == "lit":
            return n[1]
        if k == "at":
            def sub(m):
                raw = env["get"](m.group(0))
                return "" if raw is None else str(raw)
            return Value("text", re.sub(r"\$\w+(?:\.\w+)?", sub, n[1]))
        if k == "name":
            raw = env["get"](n[1])
            v = typed(raw, n[1].lstrip("$"))
            env["reads"].append((n[1] if n[1].startswith("$") else n[1], fmt(v)))
            return v
        if k == "neg":
            v = ev(n[1])
            if v.kind == "number":
                return Value("number", -v.v, v.reach, v.partial)
            if v.kind == "duration":
                return Value("duration", -v.v, v.reach, v.partial)
            return v if v.is_none() else none(f"cannot negate {v.kind}")
        if k == "not":
            v = ev(n[1])
            return Value("bool", not v.v) if v.kind == "bool" else (v if v.is_none() else none(f"not needs a test, not {v.kind}"))
        if k == "and":
            a = ev(n[1])
            if a.is_none():
                return a
            if a.kind != "bool":
                return none(f"and needs tests, not {a.kind}")
            if not a.v:
                return Value("bool", False)
            b = ev(n[2])
            return b if b.is_none() else (Value("bool", bool(b.v)) if b.kind == "bool" else none(f"and needs tests, not {b.kind}"))
        if k == "or":
            a = ev(n[1])
            if a.is_none() or (a.kind == "bool" and not a.v):
                return ev(n[2])
            return a
        if k == "cmp":
            a, b = ev(n[2]), ev(n[3])
            if a.is_none():
                return a
            if b.is_none():
                return b
            return _carry(_cmp(n[1], a, b), a, b)
        if k == "bin":
            a, b = ev(n[2]), ev(n[3])
            if a.is_none():
                return a
            if b.is_none():
                return b
            return _carry(_arith(n[1], a, b), a, b)
        if k == "count":
            ids = env["select"](n[1])
            return Value("number", len(ids))
        if k == "call":
            args = [ev(a) for a in n[2]]
            return _carry(call(n[1], args), *args)
        if k == "agg":
            _, name, field, q = n
            ids = env["select"](q)
            vals = [typed(env["field"](i, field), field) for i in ids]
            have = [v for v in vals if not v.is_none()]
            if not ids:
                return none(f"nothing matches {q}")
            if not have:
                return none(f"0 of {len(ids)} have {field}")
            kinds = {v.kind for v in have}
            if len(kinds) > 1 or (name == "sum" and not kinds <= {"number", "duration"}):
                return none(f"{field} is not all one kind: " + ", ".join(sorted(kinds)))
            kind = have[0].kind
            if name == "join":                 # 13 Oct: texts of a selection or a row source, one a line
                res = Value("text", "\n".join(str(v.v) for v in have))
                res.reach = f"{len(have)} of {len(ids)}"
                return res
            if name == "sum":
                total = sum((v.v for v in have), datetime.timedelta() if kind == "duration" else 0)
                res = Value(kind, total)
            elif kind not in _COMPARABLE:
                return none(f"cannot order {kind}s")
            else:
                res = Value(kind, (min if name == "min" else max)(v.v for v in have))
            if len(have) < len(ids):
                res.reach = f"{len(have)} of {len(ids)}; {len(ids) - len(have)} have none"
                res.partial = True
            else:
                res.reach = f"{len(ids)} of {len(ids)}"
            return res
        raise ExprError(f"bad tree {k}")
    return ev(tree)


def run(text, env):
    """Parse and evaluate `text`. -> (Value, inputs string). A parse error becomes none with the reason."""
    env.setdefault("reads", [])
    try:
        v = evaluate(parse(text), env)
    except ExprError as e:
        v = none(str(e))
    seen, inputs = set(), []
    for name, shown in env["reads"]:
        if name not in seen:
            seen.add(name)
            inputs.append(f"{name}={shown}")
    return v, ", ".join(inputs)


def holds(val):
    """A guard's verdict: True, False, or None when it cannot tell (a1397: a guard on a missing value makes no claim)."""
    if val.is_none():
        return None
    if val.kind == "bool":
        return bool(val.v)
    return True
