"""Exercise the real shared drag-watcher method without opening a host or window."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock


class SourceSeam(unittest.TestCase):
    def test_leased_geometry_never_becomes_world_facts(self):
        source=Path(__file__).resolve().parent.parent/'kernel-desktop'/'kd_window.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        host=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WindowHost')
        method=next(n for n in host.body if isinstance(n,ast.FunctionDef) and n.name=='watch_drags')
        for leased in (True,False):
            sleeps=[0]
            def sleep(_):
                sleeps[0]+=1
                if sleeps[0]>4:raise StopIteration
            user=Mock();user.GetPropW.return_value=1 if leased else 0
            namespace={'time':NS(sleep=sleep),'user32':user,'log':lambda *_:None}
            module=ast.Module(body=[method],type_ignores=[]);exec(compile(ast.fix_missing_locations(module),str(source),'exec'),namespace)
            instance=NS(rows={'wt123':{'rev':1}},screen=NS(wins={'wt123':{'hwnd':123}},box=lambda _: (30,40,500,600)),
                applied={},settle={},m=Mock())
            with self.assertRaises(StopIteration):namespace['watch_drags'](instance)
            if leased:instance.m.do.assert_not_called()
            else:instance.m.do.assert_called_once()


if __name__=='__main__':unittest.main()
