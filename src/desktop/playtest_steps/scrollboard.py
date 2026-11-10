from playtest_steps import Step
from playtest_steps._support import asyncio, open_panel, press, prove, wheel_helpers


def bind(play, opened):
    w, c = play.w, play.copy
    fixture = wheel_helpers(play)
    checked = fixture.checked
    show = fixture.show
    async def board():
        # Landed deliberately shows only the latest five. Populate the preceding
        # band so reaching Landed needs scrolling even on a quiet copied board.
        for i in range(24):
            checked("look f5204")
            checked(f'do create f5204 kind=note title="Stand-in queued work {i+1}" commission=asked')
        await show("a5080")  # avoid a second board instance in the viewer
        await open_panel(play, "The board", "home-board")
        landed = "pt.parts('lens:home-board').find(e => /\\/landed$/.test(e.dataset.key))"
        # Opening a fold is setup; the subsequent proof uses wheel input only.
        handle = f"({landed}) && ({landed}).querySelector(':scope > button[aria-expanded]')"
        if await play.has(f"({landed}) && ({landed}).dataset.folded === '1'"):
            await press(play, handle, "board's Landed fold")()
        await asyncio.sleep(.5)
        assert await play.has(f"({landed}) && !({landed}).matches('[data-folded=\"1\"]')"), "Landed fold did not open"
        return await prove(play, landed, "board Landed list")
    return board


STEP = Step(name='scrollboard', description="wheel the board's Landed list", order=3300,
            needs=(), script=bind, assertion="wheel the board's Landed list", budget=(100, 300))
