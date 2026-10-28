"""Save/load validated scenario data: data/<id>.npz + data/<id>.json.

The JSON sidecar records the configuration hash, dependency versions and a
SHA-256 of every array so that scenes can verify they consume exactly the
generated data.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import scipy

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def array_digest(a: np.ndarray) -> str:
    a = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode() + str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()[:16]


def versions() -> dict:
    return {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__}


def save(arrays: dict[str, np.ndarray], summary: dict, data_dir: Path = DATA_DIR) -> Path:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    sid = summary["id"]
    np.savez_compressed(data_dir / f"{sid}.npz", **arrays)
    meta = dict(summary)
    meta["arrays"] = {k: {"shape": list(v.shape), "sha256_16": array_digest(v)} for k, v in arrays.items()}
    meta["versions"] = versions()
    (data_dir / f"{sid}.json").write_text(json.dumps(meta, indent=2, default=_jsonable) + "\n")
    return data_dir / f"{sid}.json"


def load(sid: str, data_dir: Path = DATA_DIR, verify: bool = True) -> tuple[dict[str, np.ndarray], dict]:
    data_dir = Path(data_dir)
    meta = json.loads((data_dir / f"{sid}.json").read_text())
    with np.load(data_dir / f"{sid}.npz") as z:
        arrays = {k: z[k] for k in z.files}
    if verify:
        if set(arrays) != set(meta["arrays"]):
            raise ValueError(f"{sid}: array set differs from metadata")
        for k, v in arrays.items():
            if array_digest(v) != meta["arrays"][k]["sha256_16"]:
                raise ValueError(f"{sid}: digest mismatch for {k}")
    return arrays, meta


def _jsonable(o):
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, (tuple, set)):
        return list(o)
    raise TypeError(type(o))
