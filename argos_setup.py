"""Point Argos Translate at this project's language-package directory.

Argos reads ARGOS_PACKAGES_DIR when it is first imported, so this module
must be imported before argostranslate.
"""
import os
import sys
import types
from pathlib import Path


def _stub_optional_argos_imports():
    """argostranslate 1.11 hard-imports stanza, which pulls in torch.

    We use MiniSBD for sentence splitting, so stanza is unused at runtime.
    """
    try:
        import stanza  # noqa: F401
    except ImportError:
        stanza_stub = types.ModuleType("stanza")
        stanza_stub.Pipeline = None
        sys.modules["stanza"] = stanza_stub


_stub_optional_argos_imports()


PROJECT_ROOT = Path(__file__).resolve().parent
PACKAGES_DIR = Path(
    os.environ.get("ARGOS_PACKAGES_DIR", PROJECT_ROOT / "argos_packages")
).resolve()

os.environ["ARGOS_PACKAGES_DIR"] = str(PACKAGES_DIR)
os.environ.setdefault("ARGOS_DEVICE_TYPE", "cpu")
# MiniSBD is the lightweight sentence splitter; Stanza/spaCy would pull
# extra models and RAM this host does not have.
os.environ.setdefault("ARGOS_CHUNK_TYPE", "MINISBD")

PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
