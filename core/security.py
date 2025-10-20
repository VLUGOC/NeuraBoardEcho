# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Módulo de Seguridad y Ética
Versión: 2025-10-20
Autor: vlugoc
Propósito:
  - Proteger el entorno del sistema
  - Supervisar las conexiones externas
  - Mantener cumplimiento ético
"""

import json
import time
from pathlib import Path
from rich import print

MEM_PATH = Path.home() / "NeuraBoardEco" / "memory.json"

class SecurityCore:
    SAFE_APIS = {
        "wikipedia.org": True,
        "nasa.gov": True,
        "nationalgeographic.com": True,
        "yahoo.com": True
    }

    def __init__(self):
        self.alerts = []

    def verify_api(self, url: str) -> bool:
        """Verifica si la API es segura antes de conectarse."""
        for domain in self.SAFE_APIS:
            if domain in url:
                print(f"[🔒] Verificación de seguridad aprobada: {domain}")
                return True
        self.alerts.append({"url": url, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
        print(f"[⚠️] Bloqueado: dominio no autorizado → {url}")
        self._log_security("blocked_api", url)
        return False

    def _log_security(self, event, detail):
        """Registra eventos de seguridad en memoria."""
        data = {}
        if MEM_PATH.exists():
            data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
        data.setdefault("security", []).append({
            "event": event,
            "detail": detail,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def ethics_check(self, text: str):
        """Analiza el texto y alerta si detecta contenido inapropiado o sesgado."""
        risky = any(word in text.lower() for word in ["hate", "violence", "weapon", "sex", "terror"])
        if risky:
            print("[🚨] Contenido sensible detectado, omitiendo texto.")
            self._log_security("ethical_filter", text[:80])
            return "[Contenido filtrado por seguridad ética]"
        return text
