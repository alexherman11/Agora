"""paint_clear: forget the old paint-report things in Alex's desktop world, in one act (one record). For Claude to run.

    C:/Projects/Agora4/.venv/Scripts/python.exe paint_clear.py            says what it would do; changes nothing
    C:/Projects/Agora4/.venv/Scripts/python.exe paint_clear.py --live     says `paint-clear` once against 127.0.0.1:8810

Why: the painter used to write each part's painted text and computed styles into the world as `paint-report` things
(313 on 26 Oct). That is screen state, which does not belong in the world (Alex, 26 Oct). Paint health is now kept on
the screen (src/agora/painter/health.py); this removes the old things. `paint-report` is a reserved kind, so
`forget` refuses them; the steward word `paint-clear` forgets them all in one act. Undo: `undo r<the record it prints>`.
The log keeps its old records (it is append-only); compacting it is one of Alex's open store decisions.

Needs the kernel with paint-clear (restart kdesk with this code first). Reads before it acts, and acts once.
"""
import argparse
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1] / 'agora'
_spec = importlib.util.spec_from_file_location('paint_clear_taskboard', LAB / 'apps/taskboard/install.py')
_tb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tb)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--live', action='store_true', help='say paint-clear on the live desktop (127.0.0.1:8810)')
    args = ap.parse_args()
    door = _tb.live_door()
    see = lambda line: door.request('/see', {'line': line})
    if not see('help paint-clear').get('ok'):
        sys.exit('paint-clear is not a word here yet: restart kdesk with the new kernel code first. Nothing changed.')
    rows = see('rows paint-report').get('rows') or []
    off = [r for r in rows if r.get('disabled')]
    quarantined = [r for r in rows if r.get('quarantined')]
    lenses = sorted({str(r.get('lens')) for r in rows})
    print(f'{len(rows)} paint reports in view, over {len(lenses)} lenses ({", ".join(lenses)}); '
          f'{len(off)} say a part was turned off, {len(quarantined)} say quarantined.')
    for r in off:
        # a part someone turned off is their intent: say it again as their own preference before the report goes
        print(f'  note: {r.get("id")} turned off {r.get("path")} in {r.get("lens")} for {r.get("viewer")}; '
              f'use: personal-view {r.get("lens")} <that part\'s name>.enabled=no')
    if not args.live:
        print('Dry run: nothing changed. Run again with --live to say paint-clear once.')
        return
    from gaming_gate import assert_clear
    sys.path.insert(0, str(HERE))
    assert_clear()
    out = door.say('paint-clear')
    print(out.get('text'), out.get('records'))
    left = see('rows paint-report').get('rows') or []
    print(f'paint reports left in view: {len(left)}')


if __name__ == '__main__':
    sys.path.insert(0, str(HERE))
    main()
