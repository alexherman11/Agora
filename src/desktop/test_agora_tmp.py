"""Verify scratch files and child temp inheritance without opening a browser."""
import os
from pathlib import Path
import subprocess
import shutil
import sys

import agora_tmp


def main():
    root = agora_tmp.configure()
    assert root.is_relative_to(Path(__file__).resolve().parents[2])
    folder = agora_tmp.directory("temp-proof-")
    try:
        output = Path(folder) / "child.txt"
        code = (
            "import os,pathlib,sys,tempfile; "
            "assert os.environ['TMP'] == os.environ['TEMP'] == tempfile.gettempdir(); "
            "pathlib.Path(sys.argv[1]).write_text(tempfile.gettempdir())"
        )
        subprocess.run([sys.executable, "-c", code, str(output)], check=True)
        assert output.read_text() == str(root)
        painter = Path(__file__).resolve().parents[1] / "text-desk/notation/desk-shell"
        shutil.copytree(painter, Path(folder) / "desk-shell")
        assert (Path(folder) / "desk-shell/lens.js").is_file()
        os.environ["AGORA_TMP"] = folder
        assert agora_tmp.configure() == Path(folder)
        print("temp: child write, parent read, painter copytree, inherited TMP/TEMP, Python temp, override: ok")
    finally:
        os.environ["AGORA_TMP"] = str(root)
        agora_tmp.configure()
        shutil.rmtree(folder)


if __name__ == "__main__":
    main()
