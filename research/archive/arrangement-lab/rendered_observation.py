"""Compare actual browser geometry with a native snapshot; never claim paint from commit."""

from agora3.world import Refusal


def observe(arrangements):
    if arrangements.browser is None:
        raise Refusal("No browser is attached to this candidate world.")
    with arrangements.g.lock:
        snapshot = arrangements.inspect()
        watermark = arrangements.g.world.query(limit=1)["watermark"]
    rendered = arrangements.browser.call(
        op="evaluate",
        expression="""(() => {
      const board=document.getElementById('board'); if(!board)return [];
      const frame=board.getBoundingClientRect();
      return [...document.querySelectorAll('[data-view]')].map(el=>{
        const r=el.getBoundingClientRect(), s=getComputedStyle(el);
        return {id:el.dataset.view,bounds:{x:r.x-frame.x+board.scrollLeft,
          y:r.y-frame.y+board.scrollTop,width:r.width,height:r.height},
          z:Number(s.zIndex)||0,displayed:s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0};
      });})()""",
    )
    actual = {item["id"]: item for item in rendered}
    differences = []
    for item in snapshot["items"]:
        row = actual.get(item["id"])
        if not row or not row["displayed"]:
            differences.append({"id": item["id"], "reason": "not rendered"})
        elif any(abs(row["bounds"][k] - item["bounds"][k]) > 1 for k in item["bounds"]):
            differences.append({"id": item["id"], "reason": "rendered bounds differ"})
    z = [actual[oid]["z"] for oid in snapshot["order"] if oid in actual]
    if any(a >= b for a, b in zip(z, z[1:], strict=False)):
        differences.append({"reason": "rendered stack differs"})
    stable = watermark == arrangements.g.world.query(limit=1)["watermark"]
    return {
        "surface": "desk",
        "native_watermark": watermark,
        "stable_native_snapshot": stable,
        "rendered_matches_snapshot": stable and not differences,
        "occurrences": rendered,
        "differences": differences,
        "scope": "DOM bounds and stacking only. Does not prove legibility, content paint, unobscured text, or future stability.",
    }
