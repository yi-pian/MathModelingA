"""Keep Matplotlib cache inside this self-contained project on restricted systems."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib"))

