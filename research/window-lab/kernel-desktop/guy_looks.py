"""Hand-pixelled clothing for the original guy. Coordinates follow art.HEAD;
his head never shifts between poses. Dots are transparent, never erasers.
This is also exported inline to the sandbox, so preview and desktop agree.
"""
import re

DEFAULTS = dict(hat='none', hair='original', coat='#3f5d73', skin='#f2c894',
                eyes='dots', accessory='none', shoes='#7a5c2e', name='Guy',
                speed='95', chatty='normal', phrases='hello, Alex\nooh, a new window', custom_hat='')
FIELDS = tuple(DEFAULTS)


def layer(*rows):
    assert len(rows) == 8 and all(len(r) <= 16 for r in rows)
    return [r.ljust(16, '.') for r in rows]


# All hats occupy y=-5..2. Their last two rows follow the existing crown.
HATS = {
    'none': layer(*(['.' * 16] * 8)),
    'cap': layer('', '', '', '.....kkkkkk', '....kbbbbbbk', '....kbbbbbbk', '...kbbbbbbbbkkk', '....kkkkkkkkkk'),
    'beanie': layer('', '', '.......rr', '.....krrrrk', '....krrrrrrk', '....krrrrrrk', '...kssssssssk', '....kkkkkkkk'),
    'top hat': layer('.....kkkkkk', '.....kbbbbk', '.....kbbbbk', '.....kbbbbk', '.....krrrrk', '.....krrrrk', '...kkkkkkkkkk', ''),
    'wizard': layer('.......k', '......kbk', '......kbbk', '.....kbobk', '.....kbbbbk', '....kbbobbbk', '..kkbbbbbbbbkk', '...kkkkkkkkkk'),
    'crown': layer('', '', '', '....k..k..k', '....skssksk', '....sosssos', '....sssssss', '....kkkkkkk'),
    'propeller cap': layer('....rrrskrrr', '.......s', '', '.....kkkkkk', '....kbbrrbbk', '....kbbrrbbk', '...kbbbbbbbbkkk', '....kkkkkkkkkk'),
    'flower': layer('', '', '.........rr', '........ror', '.........rr', '.........s', '.....kkkkks', ''),
    'headphones': layer('', '', '', '.....ssssss', '....skkkkkks', '...s........s', '..ksk......ksk', '..kbk......kbk'),
    'custom': layer(*(['.' * 16] * 8)),
}
ACCESSORIES = {
    'none': layer(*(['.' * 16] * 8)),
    'scarf': layer('.....rrrrrr', '....krrrrrrk', '........rr', '........rr', '........rr', '........kk', '', ''),
    'bow tie': layer('', '.....r..r', '.....rrrr', '.....r..r', '', '', '', ''),
    'backpack': layer('', '..ssss', '..skks', '..sbbs', '..sbbs', '..ssss', '', ''),
}


def clean(facts):
    out = dict(DEFAULTS)
    out.update({k: str(v) for k, v in facts.items() if k in out})
    for key in ('coat', 'skin', 'shoes'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}', out[key]):
            out[key] = DEFAULTS[key]
    for key, choices in (('hat', HATS), ('accessory', ACCESSORIES),
                         ('hair', ('original', 'brown', 'gold', 'silver', 'red', 'none')),
                         ('eyes', ('dots', 'happy', 'sleepy', 'sunglasses')),
                         ('chatty', ('quiet', 'normal', 'chatty'))):
        if out[key] not in choices:
            out[key] = DEFAULTS[key]
    try:
        out['speed'] = str(max(20, min(220, float(out['speed']))))
    except ValueError:
        out['speed'] = DEFAULTS['speed']
    return out


def pixels(head, body, pose, blink=False, facts=None):
    """Return coordinate/palette triples; default yields exactly the old pixels."""
    f = clean(facts or {})
    grid = {}
    for y, row in enumerate(head + body.get(pose, body['stand'])):
        for x, c in enumerate(row):
            if c != '.':
                grid[x, y] = 'o' if blink and y == 4 and c == 'k' and 4 < x < 12 else c
    if f['hair'] != 'original':
        for y, xs in ((1, range(5, 11)), (2, (4, 11)), (3, (3, 12))):
            for x in xs:
                grid[x, y] = 'o' if f['hair'] == 'none' else 'h'
    if f['eyes'] != 'dots':
        for x in (6, 10):
            grid[x, 4] = 'o'
        marks = {'happy': [(5, 4), (6, 3), (7, 4), (9, 4), (10, 3), (11, 4)],
                 'sleepy': [(5, 4), (6, 4), (9, 4), (10, 4)],
                 'sunglasses': [(x, 4) for x in range(3, 13)] + [(5, 5), (6, 5), (9, 5), (10, 5)]}
        if not blink or f['eyes'] == 'sunglasses':
            for xy in marks[f['eyes']]:
                grid[xy] = 'k'
    hat = HATS[f['hat']]
    custom = f['custom_hat'].split('/')
    if f['hat'] == 'custom' and len(custom) == 8 and all(re.fullmatch(r'[.kobrs]{16}', r) for r in custom):
        hat = custom
    for rows, dy in ((ACCESSORIES[f['accessory']], 8), (hat, -5)):
        for y, row in enumerate(rows):
            for x, c in enumerate(row):
                if c != '.':
                    grid[x, y + dy] = c
    return [(x, y, c) for (x, y), c in grid.items()]


def palette(original, facts=None):
    f = clean(facts or {})
    pal = dict(original)
    for token, key in (('b', 'coat'), ('o', 'skin'), ('s', 'shoes')):
        pal[token] = tuple(bytes.fromhex(f[key][1:]))
    pal['h'] = {'brown': (99, 65, 42), 'gold': (222, 177, 78), 'silver': (185, 191, 198),
                'red': (169, 71, 44)}.get(f['hair'], pal['k'])
    return pal
