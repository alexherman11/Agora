"""reaches (9 Oct, a3806): the lines the desk did not do, counted by shape, the most met first (verbs.record_reach): which
refusal or missing word is worth curing shows itself, without anyone deciding whose fault each one was.
A row source of its own file (scene.SOURCE_DIR, a5296)."""
USAGE = "reaches"
FIELDS = ("shape", "n", "who", "kind", "last", "line")
ARG = "none"


def rows(desk, arg, session):
    import verbs
    return verbs.reach_rows(desk)
