"""Job level: an actual Manim render in the pinned environment (slow; run with `pytest -m slow`).

Also checks that every scene module imports and only reads digest-verified data.
"""

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCENES = ROOT / "scenes"
ALL = {
    "s1_measured": "S1Measured", "s2_coupling": "S2Coupling", "s3_iterations": "S3Iterations",
    "s4_two_decays": "S4TwoDecays", "s5_contrast": "S5Contrast", "s6_held_fixed": "S6HeldFixed",
    "s7_observations": "S7Observations", "s8_action": "S8Action",
}

manim = pytest.importorskip("manim")


def test_scene_modules_import_and_define_scenes():
    sys.path.insert(0, str(SCENES))
    for mod, cls in ALL.items():
        m = importlib.import_module(mod)
        assert issubclass(getattr(m, cls), manim.Scene)


def test_scenes_do_not_bypass_the_store():
    for mod in ALL:
        src = (SCENES / f"{mod}.py").read_text()
        assert "np.load" not in src and "solve_direct" not in src and "p_iterate" not in src


@pytest.mark.slow
@pytest.mark.parametrize("mod,cls", [("s2_coupling", "S2Coupling"), ("s8_action", "S8Action")])
def test_actual_render(tmp_path, mod, cls):
    exe = shutil.which("manim", path=str(Path(sys.executable).parent))
    assert exe, "manim CLI not found in the active environment"
    r = subprocess.run([exe, "render", "-ql", "--media_dir", str(tmp_path), f"{mod}.py", cls],
                       cwd=SCENES, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    clip = tmp_path / "videos" / mod / "480p15" / f"{cls}.mp4"
    assert clip.stat().st_size > 10_000
    probe = subprocess.run([shutil.which("ffprobe", path=str(Path(sys.executable).parent)), "-v", "error",
                            "-show_entries", "format=duration:stream=width,height", "-of", "csv=p=0", str(clip)],
                           capture_output=True, text=True)
    lines = probe.stdout.split()
    assert "854,480" in lines
    assert float(lines[-1]) > 10.0
