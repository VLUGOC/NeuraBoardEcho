# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Learning Metrics
Versión: 2025-10-20
Autor: vlugoc
Descripción:
  Sistema de métricas adaptativas para el aprendizaje por refuerzo
  dentro del ecosistema NeuraBoardEco.
"""

import json
import time
from pathlib import Path
from statistics import mean

ROOT = Path.home() / "NeuraBoardEco"
MEM_PATH = ROOT / "memory.json"


class LearningMetrics:
    """Clase de métricas de aprendizaje para NeuraBoardEco."""

    def __init__(self):
        self.cycles = 0
        self.rewards = []
        self.last_avg = None

    def register_cycle(self, reward: float):
        """Registra una nueva recompensa de aprendizaje."""
        self.cycles += 1
        self.rewards.append(reward)
        self.save_to_memory()

    def summary(self) -> str:
        """Devuelve un resumen de rendimiento actual."""
        if not self.rewards:
            return "[📊] Sin métricas registradas."
        avg_reward = mean(self.rewards)
        best = max(self.rewards)
        worst = min(self.rewards)
        return (
            f"[📊] Ciclos: {self.cycles} | "
            f"Promedio: {avg_reward:.2f} | "
            f"Mejor: {best:.2f} | "
            f"Peor: {worst:.2f}"
        )

    def save_to_memory(self):
        """Guarda las métricas en memory.json."""
        if MEM_PATH.exists():
            data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
        else:
            data = {}
        data["metrics"] = {
            "cycles": self.cycles,
            "avg_reward": mean(self.rewards) if self.rewards else 0,
            "history": self.rewards,
        }
        MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def adaptive_adjustment(self, ant):
        """
        Ajusta dinámicamente parámetros del agente Ant-RL
        según el rendimiento promedio de las recompensas.
        - Si el promedio sube → baja exploración (ε) y evaporación (ρ)
        - Si el promedio baja → aumenta exploración
        """
        if not self.rewards:
            return

        avg = sum(self.rewards) / len(self.rewards)
        trend = avg - (self.last_avg if self.last_avg is not None else avg)
        self.last_avg = avg

        if trend > 0:
            ant.epsilon = max(0.01, ant.epsilon * 0.9)
            ant.rho = max(0.01, ant.rho * 0.95)
            msg = f"📈 Rendimiento ↑ | Ajuste: epsilon={ant.epsilon:.3f}, rho={ant.rho:.3f}"
        else:
            ant.epsilon = min(0.3, ant.epsilon * 1.1)
            ant.rho = min(0.2, ant.rho * 1.05)
            msg = f"📉 Rendimiento ↓ | Ajuste: epsilon={ant.epsilon:.3f}, rho={ant.rho:.3f}"

        print(f"[Metrics] {msg}")
