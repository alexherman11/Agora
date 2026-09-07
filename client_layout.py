"""A shared client default for placing new appearances in free desk slots."""


def free_slot(tree: dict) -> dict:
    occupied = [(n["transform"].get("x", 0), n["transform"].get("y", 0)) for n in tree["nodes"]]
    for index in range(3 * (len(occupied) + 1)):
        x, y = 24 + (index % 3) * 240, 24 + (index // 3) * 116
        if all(abs(x - ox) >= 220 or abs(y - oy) >= 100 for ox, oy in occupied):
            return {"x": x, "y": y, "scale": 1}
    return {"x": 24, "y": 24 + (len(occupied) + 1) * 116, "scale": 1}
