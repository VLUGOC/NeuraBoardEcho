# -*- coding: utf-8 -*-
"""
core/metrics.py - Módulo de métricas de aprendizaje para NeuraBoardEco.
Autor: vlugoc
Versión: 1.0
"""

import json
import time
from pathlib import Path
from statistics import mean

ROOT = Path.home() / "NeuraBoardEco"
MEM_PATH = ROOT / "memory.json"


class LearningMetrics:
    """
    Mide y guarda estadísticas básicas del aprendizaje del sistema:
    - Recompensas promedio
    - Número de ciclos
    - Última acción y recompensa
    """

    def __init__(self):
        self.memory = self._load_memory()

    def _load_memory(self):
        if MEM_PATH.exists():
            try:
                return json.loads(MEM_PATH.read_text(encoding="utf-8"))
            except Exception:
                return {"logs": []}
        return {"logs": []}

    def register_cycle(self, reward: float):
        """
        Registra un nuevo ciclo de aprendizaje en memoria.json
        """
        data = self.memory
        metrics = data.get("metrics", {"total_cycles": 0, "rewards": []})

        metrics["total_cycles"] += 1
        metrics["rewards"].append(reward)

        data["metrics"] = metrics
        data["last_update"] = time.ctime()

        MEM_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self.memory = data

    def summary(self) -> str:
        """
        Devuelve un resumen visual del estado actual del aprendizaje
        """
        metrics = self.memory.get("metrics", {"total_cycles": 0, "rewards": []})
        total = metrics.get("total_cycles", 0)
        rewards = metrics.get("rewards", [])

        avg_reward = mean(rewards) if rewards else 0.0
        stability = "🟢 Estable" if avg_reward >= 2 else "🟡 Variable" if avg_reward > 0 else "🔴 Inactiva"

        return (
            f"[NeuraBoard] 📊 Ciclos: {total} | "
            f"Recompensa Promedio: {avg_reward:.2f} | Estado: {stability}"
        )
