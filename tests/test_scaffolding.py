import importlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_scripts_package_importable():
    module = importlib.import_module("scripts")
    assert module is not None


def test_fetch_subpackage_importable():
    module = importlib.import_module("scripts.fetch")
    assert module is not None


def test_alice_assets_present():
    for name in ("alice_face.png", "alice_upper.png", "alice_fullbody.png"):
        assert (REPO_ROOT / "assets" / name).exists(), f"missing {name}"
        assert (REPO_ROOT / "assets" / name).stat().st_size > 0
