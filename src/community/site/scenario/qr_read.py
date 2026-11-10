"""Read a QR code from a screenshot, as a phone camera would read the printed poster.

Small and strict: it expects an upright, unrotated symbol (a screenshot of
the poster, not a photo), finds it by its dark modules, samples each module's
centre, reads the format bits, unmasks, takes the codewords in the standard's
zigzag order, checks every block's Reed-Solomon syndromes and decodes byte
mode. It corrects no errors: a symbol that needs correcting fails loudly.
Only level M, versions 1 to 10, the symbols the entry service draws.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agora_entry import qr  # noqa: E402  (tables and the function-pattern map, not the encoder)


class Unreadable(Exception):
    pass


def _format_code(ecl_bits: int, mask: int) -> int:
    data = ecl_bits << 3 | mask
    rem = data
    for _ in range(10):
        rem = (rem << 1) ^ ((rem >> 9) * 0x537)
    return (data << 10 | rem) ^ 0x5412


def grid_from_image(path: Path) -> list[list[bool]]:
    img = Image.open(path).convert("L")
    w, h = img.size
    px = img.load()
    dark = [[px[x, y] < 128 for x in range(w)] for y in range(h)]
    ys = [y for y in range(h) if any(dark[y])]
    xs = [x for x in range(w) if any(dark[y][x] for y in ys)]
    if not ys:
        raise Unreadable("no dark pixels")
    top, bottom, left, right = ys[0], ys[-1] + 1, xs[0], xs[-1] + 1
    # The top-left finder's top edge is 7 modules of dark in a row.
    run = 0
    while left + run < right and dark[top][left + run]:
        run += 1
    module = run / 7
    size = round((right - left) / module)
    if size < 21 or (size - 17) % 4:
        raise Unreadable(f"symbol of {size} modules is not a QR size")
    step_x, step_y = (right - left) / size, (bottom - top) / size
    return [[dark[int(top + (r + 0.5) * step_y)][int(left + (c + 0.5) * step_x)] for c in range(size)]
            for r in range(size)]


def decode_grid(m: list[list[bool]]) -> str:
    size = len(m)
    ver = (size - 17) // 4
    if ver not in qr.BLOCKS_M:
        raise Unreadable(f"version {ver} is beyond what this reader knows")
    cells = [(0, 8), (1, 8), (2, 8), (3, 8), (4, 8), (5, 8), (7, 8), (8, 8), (8, 7),
             (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0)]
    seen = int("".join("1" if m[y][x] else "0" for x, y in cells), 2)
    best = min((bin(seen ^ _format_code(e, k)).count("1"), e, k) for e in range(4) for k in range(8))
    dist, ecl_bits, mask = best
    if dist > 3:
        raise Unreadable("format bits unreadable")
    if ecl_bits != qr.ECL_M_BITS:
        raise Unreadable("only level M is known here")
    # Which modules carry data: the standard's layout for this version.
    layout = qr.Symbol(ver)
    layout.draw_function_patterns()
    test = qr.MASKS[mask]
    bits = []
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                upward = ((right + 1) & 2) == 0
                y = size - 1 - vert if upward else vert
                if not layout.function[y][x]:
                    bits.append(m[y][x] ^ test(x, y))
        right -= 2
    total = qr.raw_data_modules(ver) // 8
    words = [int("".join("1" if b else "0" for b in bits[i * 8:i * 8 + 8]), 2) for i in range(total)]
    ec_len, groups = qr.BLOCKS_M[ver]
    sizes = [size_ for count, size_ in groups for _ in range(count)]
    blocks = [[] for _ in sizes]
    pos = 0
    for i in range(max(sizes)):
        for b, n in enumerate(sizes):
            if i < n:
                blocks[b].append(words[pos])
                pos += 1
    for _ in range(ec_len):
        for b in range(len(sizes)):
            blocks[b].append(words[pos])
            pos += 1
    for b, block in enumerate(blocks):
        for i in range(ec_len):  # every syndrome of a clean block is zero
            s = 0
            for word in block:
                s = qr.gf_mul(s, qr.EXP[i]) ^ word
            if s:
                raise Unreadable(f"block {b} fails its check (this reader corrects nothing)")
    data = [w for b, n in zip(blocks, sizes, strict=True) for w in b[:n]]
    stream = "".join(f"{w:08b}" for w in data)
    if stream[:4] != "0100":
        raise Unreadable("not byte mode")
    count_bits = 8 if ver <= 9 else 16
    n = int(stream[4:4 + count_bits], 2)
    start = 4 + count_bits
    raw = bytes(int(stream[start + 8 * i:start + 8 * i + 8], 2) for i in range(n))
    return raw.decode("utf-8")


def read(path: Path) -> str:
    return decode_grid(grid_from_image(Path(path)))


if __name__ == "__main__":
    print(read(Path(sys.argv[1])))
