"""Start the entry service from anywhere: python research/community-app/site/run.py"""

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)

from agora_entry.__main__ import main  # noqa: E402

main()
