# -*- coding: utf-8 -*-
"""
Módulo: eco_ant.pheromones
----------------------------------------
Simulación de aprendizaje por refuerzo basada en colonia de hormigas (Ant Colony Reinforcement Learning).

- Tabla de feromonas τ(s,a)
- Evaporación y depósito proporcional a la recompensa
- Política de selección con regla proporcional (τ^α * η^β)
- Exploración epsilon-greedy
- Persistencia en memory.json del entorno NeuraBoardEco
"""

import json, math, random
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ==== CONFIGURACIÓN GLOBAL ====
NEURABOARD_HOME = Path.home() / "NeuraBoardEco"
MEM_PATH = NEURABOARD_HOME / "memory.json"


def _load_global_memory() -> dict:
    """Carga memoria global si existe."""
    if MEM_PATH.exists():
        try:
            return json.loads(MEM_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_global_memory(data: dict) -> None:
    """Guarda datos globales de feromonas."""
    MEM_PATH.parent.mkdir(parents=True, exist_ok=True)
    MEM_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ==== CLASE PRINCIPAL ====
class PheromoneTable:
    """
    Representa una tabla τ(s,a) de feromonas.
    """

    def __init__(
        self,
        tau0: float = 0.1,
        rho: float = 0.05,
        alpha: float = 1.0,
        beta: float = 1.0,
        epsilon: float = 0.05,
        min_tau: float = 1e-6,
        max_tau: float = 10.0,
        persist_in_memory: bool = True,
    ):
        self.tau0 = tau0
        self.rho = rho
        self.alpha = alpha
        self.beta = beta
        self.epsilon = epsilon
        self.min_tau = min_tau
        self.max_tau = max_tau
        self.persist_in_memory = persist_in_memory

        self.table: Dict[str, Dict[str, float]] = {}
        if self.persist_in_memory:
            self._load_from_memory()

    # ---------- Persistencia ----------
    def _load_from_memory(self):
        data = _load_global_memory()
        ant = data.get("ant_rl", {})
        self.table = ant.get("pheromones", {}) or {}

    def _save_to_memory(self):
        if not self.persist_in_memory:
            return
        data = _load_global_memory()
        if "ant_rl" not in data:
            data["ant_rl"] = {}
        data["ant_rl"]["pheromones"] = self.table
        _save_global_memory(data)

    # ---------- Funciones base ----------
    def get_tau(self, state: str, action: str) -> float:
        """Obtiene τ(s,a), o valor base si no existe."""
        return self.table.get(state, {}).get(action, self.tau0)

    def set_tau(self, state: str, action: str, value: float):
        """Establece valor de τ(s,a) dentro de límites."""
        v = max(self.min_tau, min(self.max_tau, float(value)))
        if state not in self.table:
            self.table[state] = {}
        self.table[state][action] = v

    def evaporate(self):
        """Evapora feromonas globalmente: τ ← (1 - ρ) * τ"""
        for s, actions in self.table.items():
            for a in list(actions.keys()):
                self.table[s][a] = max(self.min_tau, (1.0 - self.rho) * actions[a])
        self._save_to_memory()

    def deposit(self, trajectory: List[Tuple[str, str]], reward: float, scale: float = 1.0):
        """Deposita feromonas a lo largo de una trayectoria con refuerzo."""
        reward_norm = math.tanh(reward / 10.0)
        delta = scale * reward_norm
        for s, a in trajectory:
            tau = self.get_tau(s, a)
            self.set_tau(s, a, tau + delta)
        self._save_to_memory()

    def choose_action(self, state: str, actions: List[str],
                      heuristic: Optional[Dict[str, float]] = None) -> str:
        """
        Selección de acción proporcional a (τ^α)*(η^β), con fallback epsilon-greedy.
        - heuristic: dict opcional {action: η(action)} con valores >= 1e-6
        """
        if not actions:
            raise ValueError("No hay acciones disponibles.")

        # Exploración aleatoria (epsilon-greedy)
        if random.random() < self.epsilon:
            return random.choice(actions)

        # Cálculo de puntuaciones
        scores = []
        for a in actions:
            tau = max(self.min_tau, self.get_tau(state, a))
            eta = 1.0
            if heuristic and a in heuristic:
                eta = max(1e-6, float(heuristic[a]))
            score = (tau ** self.alpha) * (eta ** self.beta)
            scores.append(max(1e-12, score))

        total = sum(scores)
        r = random.random() * total
        acc = 0.0

        for a, sc in zip(actions, scores):
            acc += sc
            if r <= acc:
                return a
        return actions[-1]
