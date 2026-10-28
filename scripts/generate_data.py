"""Solve every preset and write data/<id>.npz + data/<id>.json."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from opc_osc import store  # noqa: E402
from opc_osc.pipeline import run_scenario  # noqa: E402
from opc_osc.scenarios import PRESETS  # noqa: E402


def main(ids=None):
    for sid in ids or PRESETS:
        arrays, summary = run_scenario(PRESETS[sid])
        path = store.save(arrays, summary)
        it = summary.get("final_iter", "-")
        print(f"{sid:11s} hash={summary['config_hash']} final_iter={it} -> {path.relative_to(store.DATA_DIR.parent)}")


if __name__ == "__main__":
    main(sys.argv[1:])
