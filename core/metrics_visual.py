# -*- coding: utf-8 -*-
"""
metrics_visual.py — Visualizador en tiempo real del aprendizaje
Muestra una barra de progreso y tendencia basada en el archivo metrics.log
"""

import time
import os
from pathlib import Path

LOG_PATH = Path.home() / "NeuraBoardEco" / "logs" / "metrics.log"


def draw_bar(value: float, max_width: int = 40) -> str:
    """Dibuja una barra visual con caracteres."""
    filled = int((value / 10.0) * max_width)
    empty = max_width - filled
    return "█" * filled + "░" * empty


def follow(file):
    """Sigue los cambios de un archivo tipo tail -f"""
    file.seek(0, os.SEEK_END)
    while True:
        line = file.readline()
        if not line:
            time.sleep(1)
            continue
        yield line


def visualize_learning():
    print("\033[1;36m[NeuraBoardEco Monitor] 📊 Modo Visual en Tiempo Real\033[0m\n")
    print("Esperando recompensas...\n")
    time.sleep(2)

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in follow(f):
                if "Última recompensa" in line:
                    try:
                        reward_str = line.strip().split(":")[-1]
                        reward = float(reward_str)
                    except ValueError:
                        reward = 0.0
                    bar = draw_bar(min(max(reward, 0), 10))
                    print(f"\033[1;33m{line.strip()}\033[0m")
                    print(f"[{bar}]  {reward:.2f}/10.00\n")
    except FileNotFoundError:
        print("⚠️ No se encontró el archivo metrics.log — ejecuta primero el orquestador.")
        return


if __name__ == "__main__":
    visualize_learning()
