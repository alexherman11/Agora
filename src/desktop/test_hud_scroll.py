"""Check the wheel verdict against stand-ins. This is NOT browser acceptance."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from hud_scroll import prove


class WheelVerdict(unittest.IsolatedAsyncioTestCase):
    async def run_proof(self, after):
        start = {"x":100, "y":200, "dy":720, "key":"panel/body", "before":{"scroll":0, "top":40}}
        win = SimpleNamespace(js=AsyncMock(side_effect=[start] + [after]*25),
                              wheel=AsyncMock(), shot=AsyncMock())
        play = SimpleNamespace(w=win, out=Path("."), n=1)
        with patch("hud_scroll.asyncio.sleep", new=AsyncMock()):
            result = await prove(play, "pt.part('lens:fixture')", "stand-in")
        win.wheel.assert_awaited_once_with(100,200,720)
        return result

    async def test_content_and_container_move(self):
        result = await self.run_proof(dict(scroll=120, top=-80, pageX=0, pageY=0, wheel=1))
        self.assertIn("content moved 120.0 px", result["note"])

    async def test_clipped_content_fails(self):
        with self.assertRaisesRegex(AssertionError, "did not move"):
            await self.run_proof(dict(scroll=0, top=40, pageX=0, pageY=0, wheel=1))

    async def test_page_scroll_fails(self):
        with self.assertRaisesRegex(AssertionError, "HUD page"):
            await self.run_proof(dict(scroll=120, top=-80, pageX=0, pageY=20, wheel=1))

    async def test_scrollbar_without_content_movement_fails(self):
        with self.assertRaisesRegex(AssertionError, "content did not follow"):
            await self.run_proof(dict(scroll=120, top=40, pageX=0, pageY=0, wheel=1))

    async def test_no_wheel_event_fails(self):
        with self.assertRaisesRegex(AssertionError, "no wheel event"):
            await self.run_proof(dict(scroll=120, top=-80, pageX=0, pageY=0, wheel=0))


if __name__ == "__main__":
    unittest.main()
