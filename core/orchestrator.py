# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Core Orchestrator
Versión estable 2025-10-20
Autor: vlugoc
Descripción:
  Núcleo principal del sistema NeuraBoardEco. Ejecuta el ciclo
  de aprendizaje basado en refuerzo tipo colonia de hormigas (Ant-RL),
  mantiene memoria global y registra métricas del entorno.
"""

import os
import time
import json
import subprocess
import shutil
from pathlib import Path
from rich import print

# Importación de módulos internos
from eco_ant.pheromones import PheromoneTable
from core.metrics import LearningMetrics

# Rutas base
HOME = Path.home()
ROOT = HOME / "NeuraBoardEco"
MEM_PATH = ROOT / "memory.json"
LOGS = ROOT / "logs"


# -------------------------------------------------
# Inicialización y logging
# -------------------------------------------------
def init_memory():
    """Inicializa memoria y estructura de carpetas."""
    ROOT.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)
    if not MEM_PATH.exists():
        MEM_PATH.write_text(
            json.dumps({"logs": [], "ant_rl": {}}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


def log(message: str):
    """Registra un evento en memoria.json y lo imprime en consola."""
    data = {}
    if MEM_PATH.exists():
        try:
            data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
        except Exception:
            data = {"logs": []}
    else:
        data = {"logs": []}

    data.setdefault("logs", []).append({"msg": message, "time": time.ctime()})
    MEM_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[NeuraBoard] {message}")


# -------------------------------------------------
# Ejecutor de acciones (dispatcher)
# -------------------------------------------------
def do_action(choice: str) -> float:
    """
    Ejecuta una acción real y devuelve una recompensa (float).
    Mantener acciones seguras y reversibles.
    """
    reward = 1.0

    if choice == "backup":
        dst = ROOT / "backups"
        dst.mkdir(parents=True, exist_ok=True)
        cmd = (
            "tar -czf {}/cfg_$(date +%Y%m%d_%H%M%S).tgz "
            "-C $HOME .bashrc .profile 2>/dev/null || true"
        ).format(dst)
        code = subprocess.call(cmd, shell=True)
        ok = any(dst.glob("cfg_*.tgz"))
        reward = 3.0 if ok and code == 0 else 0.5

    elif choice == "optimize_cpu":
        shutil.rmtree(os.path.expanduser("~/.cache/pip"), ignore_errors=True)
        reward = 5.0

    elif choice == "analyze_market":
        data = {}
        if MEM_PATH.exists():
            try:
                data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
            except Exception:
                data = {"logs": []}
        data.setdefault("logs", []).append(
            {"msg": "Market tick (sim)", "time": time.ctime()}
        )
        MEM_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        reward = 1.5

    else:
        reward = 0.2  # acción desconocida (exploración)

    return reward


# -------------------------------------------------
# Bucle principal
# -------------------------------------------------
if __name__ == "__main__":
    init_memory()
    log("🧠 Iniciando núcleo NeuraBoardEco...")
    time.sleep(0.3)
    log("⚙️ Cargando módulos principales...")
    time.sleep(0.3)
    log("✅ Sistema operativo y estable.")

    # Configuración del agente Ant-RL
    actions = ["optimize_cpu", "backup", "analyze_market"]
    ant = PheromoneTable(
        tau0=0.1, rho=0.05, alpha=1.0, beta=1.0, epsilon=0.1, persist_in_memory=True
    )

    # Estado simple, puede ampliarse
    state = "boot_cycle"
    heuristic = {"optimize_cpu": 1.1, "backup": 1.0, "analyze_market": 1.0}

    # Selección y ejecución
    choice = ant.choose_action(state, actions, heuristic)
    reward = do_action(choice)
    ant.deposit([(state, choice)], reward)

    log(f"🐜 Ant-Colony RL ejecutó acción: {choice} con recompensa {reward}")

    # Métricas de aprendizaje
    metrics = LearningMetrics()
    metrics.register_cycle(reward)
    print(metrics.summary())

from sandbox.virtual_env import VirtualEnv

if __name__ == "__main__":
    env = VirtualEnv(cycles=10)
    env.run()
