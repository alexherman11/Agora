# Packed repeat items (a11702, source candidate)

What a desk author can express after this: `grid fill 18ch pack` fits
variable-height list items into available gaps, using each item's measured
height and minimum content width. This is opt-in list layout, not partition
navigation. No Board-specific code or world layout writes are involved.

```text
tiles : grid fill 18ch pack
  of tag:example as card
  each tile
tile : column
  title : text "$card.title"
  body : text "$card.text"
```

All existing fill minimum units work: `ch`, `gap`, `px`, or bare pixels.
Without `pack`, ordinary row-aligned grid behavior is unchanged.

The painter counts real auto-fill columns, measures minimum-content widths,
then measures heights at the assigned column spans. A deterministic bottom-left
first-fit places each item without overlap, including usable gaps under spanning
items. This is greedy packing, not a claim of globally optimal packing.
DOM/list/Tab order stays unchanged even when visual positions differ. Nodes,
editors, selection and focus are never cloned, reparented or replaced by packing.

Wide items span available columns. Content intrinsically wider than the entire
panel gets local horizontal overflow access; it is not scaled or hidden.
Parents still own their overall height and scroll policy.

ResizeObserver batches actual size changes into one animation-frame pass,
ignores resulting unchanged measurements, and handles initially hidden lists
and later reveals. Child/text/class/hidden changes, loaded fonts and viewport
resize also invalidate measurement. Removed children have their authored inline
styles restored; removed roots disconnect their size observer.

`window.GridPack.geometry(element)` is the future carry seam: returns item keys,
zero-based column `x`, column `span`, and CSS-pixel `y`/`height` offsets for the
last completed measurement. Gap is included between items, not in their height.
The seam does not reorder or implement a drop policy. Read actual DOM bounds
for pointer hit-testing, especially before a newly scheduled measurement.

Offline checks:

```text
python src/text-desk/notation/test_grid_fill.py
node src/text-desk/notation/desk-shell/test_grid_pack.cjs
```

The six compiler tests exercise accepted/refused forms, print/IR roundtrips,
unchanged ordinary grids and zero new world events. The Node tests exercise
variable heights, spanning items, deterministic non-overlap, widths one through
eight columns, resize, local overflow, empty/one item, hidden reveal, content
changes and observer cleanup/coalescing. Fake CSS/DOM is not browser proof.

Painted acceptance remains owed: at 1280x800 and 2560x1440, scale 1.5,
use only the admitted shared guarded paint lane on a disposable world. Include
mixed heights and wide content, resize/narrow/reveal, verify no overlapping
items or panel spill, Tab order, selection and unsent composer caret. Inspect
actual shots and geometry, record viewport/DPR/Guard and cleanup receipts.
The shared lane is currently held (a10672/a11403); no launch was attempted here.

Resident rollout after source landing: opt one synthetic list into `pack` and
paint it before changing the live Board. Reversal is the exact removal of that
list's trailing `pack`; no stored layout or data migration is required.
No live lens/style changed as part of this source candidate.

Staged help update for the resident after landing, based on the current
`lens|lenses` note (a1853): in its word list, replace the exact
`grid <tracks: 1 3 3 1 | 1fr fit 2fr | fill 18ch>` with
`grid <tracks: 1 3 3 1 | 1fr fit 2fr | fill 18ch [pack]>`.
Follow the existing `grid fill <min>` paragraph with:

> `grid fill <min> pack` packs variable-height repeat items into gaps by measured
> size. Wide minimum-content items span columns; content wider than the entire
> panel remains locally scrollable. The DOM and keyboard order stay in list
> order; only visual placement changes. Resize and content measurement are
> painter-local with no world events. This does not change partition panels or
> add carry/reorder behavior.

Undo that exact help insertion and word-list change if the source is reversed.
Re-read the live paragraph before applying; this document does not replace
another author's whole help note.
