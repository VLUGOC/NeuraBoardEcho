# -*- coding: utf-8 -*-
"""
NeuraBoardEco - Módulo de Integración de Conocimiento
Versión: 2025-10-20
Autor: vlugoc
Descripción:
  Recolecta información desde APIs públicas (Wikipedia, NASA, etc.)
  y la envía a la memoria cognitiva del sistema.
"""

import requests
import json
import time
from pathlib import Path
from rich import print

MEM_PATH = Path.home() / "NeuraBoardEco" / "memory.json"

class KnowledgeIntegrator:
    def __init__(self):
        self.session = requests.Session()

    def fetch_wikipedia(self, topic: str):
        """Obtiene un resumen desde Wikipedia."""
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        r = self.session.get(url)
        if r.status_code == 200:
            data = r.json()
            content = data.get("extract", "")
            print(f"[🌐] Wikipedia: {topic} → {content[:120]}...")
            self._store("wikipedia", topic, content)
            return content
        else:
            print(f"[⚠️] Error al obtener Wikipedia ({r.status_code})")
            return None

    def fetch_nasa(self):
        """Obtiene la foto astronómica del día (NASA APOD)."""
        API_KEY = "DEMO_KEY"  # puedes reemplazar con tu key real de https://api.nasa.gov
        url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"
        r = self.session.get(url)
        if r.status_code == 200:
            data = r.json()
            title, explanation = data["title"], data["explanation"]
            print(f"[🚀] NASA: {title}")
            self._store("nasa", title, explanation)
            return explanation
        else:
            print(f"[⚠️] Error al conectar NASA ({r.status_code})")
            return None

    def fetch_natgeo(self):
        """Descarga artículos recientes de National Geographic RSS."""
        url = "https://www.nationalgeographic.com/animals/rss"
        r = self.session.get(url)
        if r.status_code == 200:
            print("[🌱] National Geographic feed leído correctamente.")
            self._store("natgeo", "feed", r.text[:500])
        else:
            print(f"[⚠️] Error al conectar NatGeo ({r.status_code})")

    def _store(self, source, title, content):
        """Guarda los datos en memoria.json."""
        data = {}
        if MEM_PATH.exists():
            data = json.loads(MEM_PATH.read_text(encoding="utf-8"))
        data.setdefault("knowledge", []).append({
            "source": source,
            "title": title,
            "content": content,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[🧠] Guardado conocimiento desde {source} → {title}")
