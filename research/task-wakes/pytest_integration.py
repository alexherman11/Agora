"""Fake-pipe integration tests, using inherited-ACL scratch and optional frozen baseline."""
from pathlib import Path
import shutil
import sys
from types import ModuleType
import pytest

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / "text-desk-lab" / "notation"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(HERE.parent / "window-lab"))
import agora_tmp
agora_tmp.configure()


class Scratch:
    @pytest.fixture
    def tmp_path(self):
        # tempfile mode 0700 excludes the Windows sandbox token; inherit ACLs.
        owned = Path(agora_tmp.directory("quiet-integration-"))
        try:
            yield owned
        finally:
            shutil.rmtree(owned, ignore_errors=True)


if sys.argv[1] == "baseline":
    for name in ("task_flow", "rooms", "house"):
        path = HERE / ("integration-base-" + name + ".py.txt")
        module = ModuleType(name)
        module.__file__ = str(LAB / (name + ".py"))
        sys.modules[name] = module
        exec(compile(path.read_text(), module.__file__, "exec"), module.__dict__)

files = ["test_house_conversation_flow.py", "test_resident_delivery_handoff.py",
         "test_resident_portable.py", "test_conversation_queue.py", "test_charter.py",
         "test_notice_routing.py", "test_task_flow.py", "test_task_flow_verbs.py"]
raise SystemExit(pytest.main(["-q", "--tb=short", *[str(LAB / f) for f in files]],
                             plugins=[Scratch()]))
