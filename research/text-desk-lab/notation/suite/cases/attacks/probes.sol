# The attacks, typed as a person would meet them, in a fresh desk. Each probe is one open route.
recorded M4=1

step a4
T do create f01 kind=note title="Alpha" tags=t start=2026-10-01 week=6
T do create f01 kind=note title="Beta" tags=t start=2026-10-01 week=2
T do create f01 kind=note title="tidy" tags=verb text="do tag $1 add=done\ndo retitle $1 title=\"(done) $1.title\"\ndo prop $1 week=0"
T do create f01 kind=note title="Beta to week 99" tags=rule text="on tag do prop Beta week=99"
T do create f01 kind=note title="innocent" tags=lens text="x : column, of tag:t, each r\nr : text \"$title\", on click do tidy $item"
probe definitions-have-history
probe click-says-all

step trap
probe look-clears-the-fence
