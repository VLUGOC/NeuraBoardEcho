from pathlib import Path
import json, time

HOME = Path.home() / "NeuraBoardEco"
RBANK = HOME / "reasonybank"
MEM   = HOME / "memory.json"

RBANK.mkdir(parents=True, exist_ok=True)

def append_reasonybank(topic: str, payload: dict) -> Path:
    """Guarda un registro atómico en reasonybank/<topic>.jsonl (1 JSON por línea)."""
    RBANK.mkdir(parents=True, exist_ok=True)
    f = RBANK / f"{topic}.jsonl"
    payload = {"_ts": time.time(), **payload}
    with f.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return f

def memory_update(patch: dict):
    """Aplica un parche superficial a memory.json (crea si no existe)."""
    data = {}
    try:
        if MEM.exists():
            data = json.loads(MEM.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    for k, v in patch.items():
        data[k] = v
    MEM.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
