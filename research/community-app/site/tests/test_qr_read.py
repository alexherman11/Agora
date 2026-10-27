"""The scenario's QR reader reads what the encoder draws, and refuses damage."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from PIL import Image

from agora_entry import qr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scenario"))
import qr_read  # noqa: E402


def draw(sym, path: Path, px: float = 6.0, quiet: int = 4) -> Path:
    n = sym.size + 2 * quiet
    side = int(n * px)
    img = Image.new("L", (side, side), 255)
    pix = img.load()
    for y in range(side):
        for x in range(side):
            r, c = int(y / px) - quiet, int(x / px) - quiet
            if 0 <= r < sym.size and 0 <= c < sym.size and sym.modules[r][c]:
                pix[x, y] = 30
    img.save(path)
    return path


@pytest.mark.parametrize("ver", [1, 4, 7, 10])
def test_reads_back_every_mask(tmp_path, ver):
    text = "https://seabright.example.org/join/" + "Ab3dEf9hJkLm"
    text = text[:qr.data_capacity(ver) - (3 if ver >= 10 else 2)]
    for mask in range(8):
        sym = qr.encode(text, version=ver, mask=mask)
        assert qr_read.read(draw(sym, tmp_path / f"q{ver}{mask}.png", px=5.3)) == text


def test_refuses_a_damaged_symbol(tmp_path):
    sym = qr.encode("http://127.0.0.1:8817/join/abcdefghijkl")
    sym.modules[sym.size - 1][sym.size - 1] ^= True  # one data module flipped
    with pytest.raises(qr_read.Unreadable, match="fails its check"):
        qr_read.read(draw(sym, tmp_path / "bad.png"))
