"""crop: cut a region of a screen shot to look at it closely. python crop.py <in.png> x y w h <out.png> [scale]"""
import sys

from PIL import Image

a = sys.argv[1:]
x, y, w, h = map(int, a[1:5])
im = Image.open(a[0]).crop((x, y, x + w, y + h))
if len(a) > 6:
    s = float(a[6])
    im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
im.save(a[5])
print(a[5], im.size)
