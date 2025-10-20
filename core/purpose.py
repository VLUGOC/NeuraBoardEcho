# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Beneficio Humano
Versión: 2025-10-20
Autor: vlugoc
Propósito:
  Evalúa el impacto positivo de las acciones del sistema
  sobre sostenibilidad, educación y cooperación.
"""

import json
import time
from pathlib import Path
from rich import print

MEM_PATH = Path.home() / "NeuraBoardEco" / "memory.json"

class HumanPurpose:
    def __init__(self):
        self.values = {
            "sustainability": 0.4,
            "education": 0.3,
            "cooperation": 0.3
        }

    def evaluate_action(self, action: str, reward: float):
        """Evalúa si una acción contribuye al beneficio humano."""
        score = 0
        if "analyze" in action:
            score += reward * self.values["education"]
        elif "backup" in action:
            score += reward * self.values["cooperation"]
        elif "optimize" in action:
            score += reward * self.values["sustainability"]

        # Guarda en memoria global
        data = {}
        if MEM_PATH.exists():
            data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
        data.setdefault("purpose", []).append({
            "action": action,
            "benefit_score": round(score, 3),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"[💠] Acción {action} → beneficio humano: {score:.3f}")
