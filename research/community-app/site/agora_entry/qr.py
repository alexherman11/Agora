"""QR codes for invite links, drawn as SVG. Standard library only.

Byte mode, error correction level M (about 15% of the code can be damaged),
versions 1 to 10 (up to 213 bytes, far more than an invite link needs).
Written from ISO/IEC 18004; tests check the Reed-Solomon output against the
standard's worked example and compare whole symbols with an independent
encoder (Kazuhiko Arase's) when one is found on the machine.
"""

from __future__ import annotations

# GF(256) with the QR polynomial x^8 + x^4 + x^3 + x^2 + 1.
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def rs_generator(degree: int) -> list[int]:
    gen = [1]
    for i in range(degree):
        nxt = [0] * (len(gen) + 1)
        for j, c in enumerate(gen):
            nxt[j] ^= c
            nxt[j + 1] ^= gf_mul(c, EXP[i])
        gen = nxt
    return gen


def rs_remainder(data: list[int], degree: int) -> list[int]:
    gen = rs_generator(degree)
    rem = [0] * degree
    for byte in data:
        factor = byte ^ rem[0]
        rem = rem[1:] + [0]
        for i in range(degree):
            rem[i] ^= gf_mul(gen[i + 1], factor)
    return rem


# Level M: version -> (EC codewords per block, [(block count, data codewords per block)])
BLOCKS_M = {
    1: (10, [(1, 16)]), 2: (16, [(1, 28)]), 3: (26, [(1, 44)]), 4: (18, [(2, 32)]),
    5: (24, [(2, 43)]), 6: (16, [(4, 27)]), 7: (18, [(4, 31)]),
    8: (22, [(2, 38), (2, 39)]), 9: (22, [(3, 36), (2, 37)]), 10: (26, [(4, 43), (1, 44)]),
}
ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
         7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
ECL_M_BITS = 0b00


def raw_data_modules(ver: int) -> int:
    result = (16 * ver + 128) * ver + 64
    if ver >= 2:
        n = ver // 7 + 2
        result -= (25 * n - 10) * n - 55
        if ver >= 7:
            result -= 36
    return result


def data_capacity(ver: int) -> int:
    _, groups = BLOCKS_M[ver]
    return sum(count * size for count, size in groups)


def _count_bits(ver: int) -> int:
    return 8 if ver <= 9 else 16


def choose_version(data: bytes) -> int:
    for ver in range(1, 11):
        if 4 + _count_bits(ver) + 8 * len(data) <= data_capacity(ver) * 8:
            return ver
    raise ValueError("too long for a QR code here (max 213 bytes)")


def data_codewords(data: bytes, ver: int) -> list[int]:
    bits: list[int] = []

    def put(value: int, n: int) -> None:
        bits.extend((value >> i) & 1 for i in reversed(range(n)))

    put(0b0100, 4)
    put(len(data), _count_bits(ver))
    for b in data:
        put(b, 8)
    capacity = data_capacity(ver) * 8
    if len(bits) > capacity:
        raise ValueError("data does not fit this version")
    put(0, min(4, capacity - len(bits)))
    put(0, (-len(bits)) % 8)
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(words) < data_capacity(ver):
        words.append(pad)
        pad ^= 0xEC ^ 0x11
    return words


def interleave(words: list[int], ver: int) -> list[int]:
    ec_len, groups = BLOCKS_M[ver]
    blocks, pos = [], 0
    for count, size in groups:
        for _ in range(count):
            blocks.append(words[pos:pos + size])
            pos += size
    ecs = [rs_remainder(b, ec_len) for b in blocks]
    out = []
    for i in range(max(len(b) for b in blocks)):
        out.extend(b[i] for b in blocks if i < len(b))
    for i in range(ec_len):
        out.extend(e[i] for e in ecs)
    assert len(out) == raw_data_modules(ver) // 8
    return out


MASKS = [
    lambda x, y: (x + y) % 2 == 0,
    lambda x, y: y % 2 == 0,
    lambda x, y: x % 3 == 0,
    lambda x, y: (x + y) % 3 == 0,
    lambda x, y: (x // 3 + y // 2) % 2 == 0,
    lambda x, y: x * y % 2 + x * y % 3 == 0,
    lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
    lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
]


class Symbol:
    """A QR symbol as rows of booleans: modules[y][x], True is dark."""

    def __init__(self, ver: int):
        self.ver = ver
        self.size = ver * 4 + 17
        self.modules = [[False] * self.size for _ in range(self.size)]
        self.function = [[False] * self.size for _ in range(self.size)]

    def set_fn(self, x: int, y: int, dark: bool) -> None:
        self.modules[y][x] = dark
        self.function[y][x] = True

    def draw_function_patterns(self) -> None:
        n = self.size
        for i in range(n):
            self.set_fn(6, i, i % 2 == 0)
            self.set_fn(i, 6, i % 2 == 0)
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n:
                        d = max(abs(dx), abs(dy))
                        self.set_fn(x, y, d not in (2, 4))
        pos = ALIGN[self.ver]
        last = len(pos) - 1
        for i, ay in enumerate(pos):
            for j, ax in enumerate(pos):
                if (i, j) in ((0, 0), (0, last), (last, 0)):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self.set_fn(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)
        self.draw_format(0)  # reserve; redrawn with the real mask later
        self.draw_version()

    def draw_format(self, mask: int) -> None:
        data = ECL_M_BITS << 3 | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        bit = lambda i: (bits >> i) & 1 == 1  # noqa: E731
        n = self.size
        for i in range(6):
            self.set_fn(8, i, bit(i))
        self.set_fn(8, 7, bit(6))
        self.set_fn(8, 8, bit(7))
        self.set_fn(7, 8, bit(8))
        for i in range(9, 15):
            self.set_fn(14 - i, 8, bit(i))
        for i in range(8):
            self.set_fn(n - 1 - i, 8, bit(i))
        for i in range(8, 15):
            self.set_fn(8, n - 15 + i, bit(i))
        self.set_fn(8, n - 8, True)

    def draw_version(self) -> None:
        if self.ver < 7:
            return
        rem = self.ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        bits = self.ver << 12 | rem
        for i in range(18):
            dark = (bits >> i) & 1 == 1
            a, b = self.size - 11 + i % 3, i // 3
            self.set_fn(a, b, dark)
            self.set_fn(b, a, dark)

    def place(self, codewords: list[int]) -> None:
        n, i, total = self.size, 0, len(codewords) * 8
        right = n - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = n - 1 - vert if upward else vert
                    if not self.function[y][x] and i < total:
                        self.modules[y][x] = (codewords[i >> 3] >> (7 - (i & 7))) & 1 == 1
                        i += 1
            right -= 2

    def apply_mask(self, mask: int) -> None:
        test = MASKS[mask]
        for y in range(self.size):
            for x in range(self.size):
                if not self.function[y][x] and test(x, y):
                    self.modules[y][x] = not self.modules[y][x]

    def penalty(self) -> int:
        m, n, score = self.modules, self.size, 0
        lines = [row[:] for row in m] + [[m[y][x] for y in range(n)] for x in range(n)]
        finder_a = [True, False, True, True, True, False, True, False, False, False, False]
        finder_b = finder_a[::-1]
        for line in lines:
            run, prev = 0, None
            for v in line:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + run - 5
                    run, prev = 1, v
            if run >= 5:
                score += 3 + run - 5
            padded = [False] * 4 + line + [False] * 4
            for k in range(len(padded) - 10):
                window = padded[k:k + 11]
                if window == finder_a or window == finder_b:
                    score += 40
        for y in range(n - 1):
            for x in range(n - 1):
                c = m[y][x]
                if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]:
                    score += 3
        dark = sum(sum(row) for row in m)
        score += int(abs(dark * 100 / (n * n) - 50) // 5) * 10
        return score


def encode(text: str | bytes, version: int | None = None, mask: int | None = None) -> Symbol:
    data = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    ver = version or choose_version(data)
    codewords = interleave(data_codewords(data, ver), ver)
    best: Symbol | None = None
    best_score = None
    for m in ([mask] if mask is not None else range(8)):
        sym = Symbol(ver)
        sym.draw_function_patterns()
        sym.place(codewords)
        sym.apply_mask(m)
        sym.draw_format(m)
        sym.mask = m
        if mask is not None:
            return sym
        score = sym.penalty()
        if best_score is None or score < best_score:
            best, best_score = sym, score
    return best


def svg(text: str, dark: str = "#1d2b33", light: str = "#ffffff", quiet: int = 4,
        title: str = "QR code") -> str:
    sym = encode(text)
    n = sym.size + 2 * quiet
    path = []
    for y, row in enumerate(sym.modules):
        x = 0
        while x < sym.size:
            if row[x]:
                start = x
                while x < sym.size and row[x]:
                    x += 1
                path.append(f"M{start + quiet},{y + quiet}h{x - start}v1h-{x - start}z")
            else:
                x += 1
    from html import escape
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" role="img" '
            f'shape-rendering="crispEdges"><title>{escape(title)}</title>'
            f'<rect width="{n}" height="{n}" fill="{light}"/>'
            f'<path fill="{dark}" d="{"".join(path)}"/></svg>')
