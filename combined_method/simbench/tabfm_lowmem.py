"""Load the TabFM v1.0.0 classifier (PyTorch, CPU) once per process.

Default: the official loader, which downloads google/tabfm-1.0.0-pytorch from Hugging Face on first use,
in float32 (about 7 GB of RAM; TABFM_DTYPE=bfloat16 for about half).
Low-memory option: set TABFM_BF16 to a folder with a pre-converted bfloat16 copy (config.json +
model.safetensors); the weights are then loaded straight into bfloat16 tensors (about 3.3 GB of RAM).
"""
import json
import os

import torch

_M = None


def _load_bf16(d):
    from safetensors import safe_open
    from tabfm.src.pytorch.tabfm_v1_0_0 import TabFM_HF
    cfg = json.load(open(os.path.join(d, "config.json")))
    with torch.device("meta"):
        m = TabFM_HF(**cfg)
    sd = {}
    with safe_open(os.path.join(d, "model.safetensors"), "pt") as s:
        for k in s.keys():
            sd[k] = s.get_tensor(k).to(torch.bfloat16)
    m.load_state_dict(sd, strict=True, assign=True)
    return m.eval()


def load():
    d = os.environ.get("TABFM_BF16")
    if d and os.path.exists(os.path.join(d, "model.safetensors")):
        return _load_bf16(d)
    from tabfm.src.pytorch.tabfm_v1_0_0 import load as official
    # float32 by default: CPUs without native bfloat16 (most laptops) gain nothing from it;
    # TABFM_DTYPE=bfloat16 halves the memory (about 3.5 GB instead of 7)
    dt = {"float32": torch.float32, "bfloat16": torch.bfloat16}[os.environ.get("TABFM_DTYPE", "float32")]
    return official("classification", device="cpu", dtype=dt)


def load_cached():
    global _M
    if _M is None:
        _M = load()
    return _M
