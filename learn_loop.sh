#!/data/data/com.termux/files/usr/bin/bash
# NeuraBoardEco - Loop de autoaprendizaje

export PYTHONPATH=$HOME/NeuraBoardEco

while true; do
    echo "[LOOP] Ejecutando ciclo NeuraBoardEco..."
    python3 $HOME/NeuraBoardEco/core/orchestrator.py >> $HOME/NeuraBoardEco/logs/learn_loop.log 2>&1
    echo "[LOOP] Ciclo completado — reiniciando en 30s..."
    sleep 30
done
