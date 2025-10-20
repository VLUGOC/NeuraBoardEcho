# -*- coding: utf-8 -*-
"""
sandbox/virtual_env.py
Simulador de entorno virtual para aprendizaje controlado.
Autor: vlugoc
Versión: 1.0
"""

import random
import time
from rich import print
from pathlib import Path
from core.metrics import LearningMetrics


class VirtualEnv:
    """
    Un entorno aislado donde los agentes pueden probar decisiones.
    Inspirado en colonias de hormigas, cada 'agente' explora, actúa y deja rastros.
    """

    def __init__(self, name="Sandbox-AntColony", cycles=5):
        self.name = name
        self.cycles = cycles
        self.metrics = LearningMetrics()
        self.log_path = Path.home() / "NeuraBoardEco" / "logs" / "sandbox.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _simulate_task(self, step: int):
        """
        Simula una tarea aleatoria dentro del entorno.
        Retorna una 'recompensa' en función del resultado.
        """
        possible_actions = ["analyze_data", "optimize_energy", "repair_node", "backup_memory"]
        action = random.choice(possible_actions)
        reward = random.uniform(-2, 5)  # entre castigo y recompensa
        stability = "🟢" if reward > 2 else "🟡" if reward > 0 else "🔴"

        print(f"[Sandbox] Ciclo {step}: acción '{action}' → recompensa {reward:.2f} {stability}")
        self._log_event(action, reward)

        # guardar recompensa en métricas globales
        self.metrics.register_cycle(reward)

    def _log_event(self, action, reward):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, "a") as f:
            f.write(f"[{timestamp}] acción={action}, recompensa={reward:.2f}\n")

    def run(self):
        print(f"[Sandbox] 🚀 Iniciando entorno virtual: {self.name}")
        for i in range(1, self.cycles + 1):
            self._simulate_task(i)
            time.sleep(0.5)
        print("[Sandbox] ✅ Simulación completada.")
        print(self.metrics.summary())
