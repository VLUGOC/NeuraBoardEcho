# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Core Orchestrator
Versión: 2025-10-21
Autor: vlugoc
Descripción:
  Núcleo principal del sistema NeuraBoardEco.
  Controla el flujo de arranque, memoria global,
  aprendizaje basado en refuerzo tipo colonia de hormigas (Ant-RL),
  registro de métricas, seguridad y beneficio humano.
"""

import os
import time
import json
import subprocess
import shutil
from pathlib import Path
from rich import print

# --- Módulos internos ---
from eco_ant.pheromones import PheromoneTable
from core.metrics import LearningMetrics
from sandbox.virtual_env import VirtualEnv


# ---------- Rutas ----------
HOME = Path.home()
ROOT = HOME / "NeuraBoardEco"
MEM_PATH = ROOT / "memory.json"
LOGS_PATH = ROOT / "logs"
LOGS_PATH.mkdir(parents=True, exist_ok=True)


# ---------- Inicialización de memoria ----------
def init_memory():
    """Inicializa memoria global y carpetas."""
    ROOT.mkdir(parents=True, exist_ok=True)
    LOGS_PATH.mkdir(parents=True, exist_ok=True)
    if not MEM_PATH.exists():
        MEM_PATH.write_text(
            json.dumps({"logs": [], "ant_rl": {}, "metrics": {}}, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


# ---------- Logging ----------
def log(message: str):
    """Registra un evento en memoria.json y lo imprime."""
    init_memory()
    try:
        data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
    except Exception:
        data = {"logs": []}
    data.setdefault("logs", []).append({"msg": message, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[NeuraBoard] {message}")


# ---------- Acciones del sistema ----------
def do_action(choice: str) -> float:
    """Ejecuta una acción simbólica del sistema y devuelve una recompensa."""
    if choice == "optimize_cpu":
        log("🧩 Optimizando recursos del sistema...")
        time.sleep(0.5)
        return 5.0

    elif choice == "backup":
        # Backup robusto: rutas relativas y exclusiones seguras
        log("💾 Realizando respaldo de memoria...")
        dst = ROOT / "backups"
        dst.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = dst / f"backup_{timestamp}.tgz"

        excludes = [
            "--exclude=backups/*",
            "--exclude=.git",
            "--exclude=.venv",
            "--exclude=__pycache__",
            "--exclude=logs/*",
            "--exclude=nohup.out",
        ]
        # Empaquetar desde ROOT con rutas relativas (.) para evitar warnings y “auto-self-archive”
        cmd = f"tar -czf '{backup_file}' {' '.join(excludes)} -C '{ROOT}' ."
        rc = subprocess.call(cmd, shell=True)
        if rc == 0:
            log(f"✅ Backup creado: {backup_file.name}")
            return 2.0
        else:
            log("⚠️ Falló el backup (tar retornó código distinto de 0).")
            return 0.5

    elif choice == "analyze":
        log("🔍 Analizando entorno virtual...")
        time.sleep(0.5)
        return 3.0
    else:
        log(f"⚠️ Acción desconocida: {choice}")
        return 0.2


# ---------- Ciclo principal ----------
def main():
    init_memory()
    log("🧠 Iniciando núcleo NeuraBoardEco...")
    time.sleep(0.3)
    log("⚙️ Cargando módulos principales...")
    time.sleep(0.3)
    log("✅ Sistema operativo y estable.")

    # Configuración del agente Ant-RL
    actions = ["optimize_cpu", "backup", "analyze"]
    heuristic = {"optimize_cpu": 1.1, "backup": 1.0, "analyze": 0.9}

    ant = PheromoneTable(tau0=0.1, rho=0.05, alpha=1.0, beta=1.0, epsilon=0.1)
    state = "boot_cycle"

    # Selección y ejecución de acción
    choice = ant.choose_action(state, actions, heuristic)
    reward = do_action(choice)
    ant.deposit([(state, choice)], reward)

    log(f"🐜 Ant-Colony RL ejecutó acción: {choice} con recompensa {reward}")

    # Registro de métricas
    metrics = LearningMetrics()
    metrics.register_cycle(reward)
    print(metrics.summary())

    # Simulación de entorno virtual
    env = VirtualEnv(cycles=3)
    env.run()


# ---------- Ejecución ----------
if __name__ == "__main__":
    main()
