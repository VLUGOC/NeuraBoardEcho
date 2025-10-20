# -*- coding: utf-8 -*-
"""
Universal Connector - NeuraBoardEco
Conecta a múltiples fuentes públicas (APIs) de forma segura y modular.
- Lee API keys desde variables de entorno
- Valida dominios permitidos
- Respeta timeouts y aplica reintentos básicos
- Persiste resultados en memory.json bajo 'feeds'
- Diseñado para extenderse fácilmente: agrega nuevas fuentes al REGISTRY
"""

from __future__ import annotations
import os, json, time, random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests

ROOT = Path.home() / "NeuraBoardEco"
MEM_PATH = ROOT / "memory.json"
LOGS_PATH = ROOT / "logs"
LOGS_PATH.mkdir(parents=True, exist_ok=True)

ALLOWED_DOMAINS = {
    "en.wikipedia.org",
    "api.nasa.gov",
    "api.spacexdata.com",
    "api.open-meteo.com",
    "api.openweathermap.org",
    "api.openaq.org",
    "api.worldbank.org",
    "query1.finance.yahoo.com",
    "api.github.com",
}
def _domain_ok(url: str) -> bool:
    try:
        host = url.split("//", 1)[1].split("/", 1)[0]
        return any(host.endswith(d) for d in ALLOWED_DOMAINS)
    except Exception:
        return False

def _http_get_json(url: str, params: Optional[Dict[str, Any]] = None,
                   headers: Optional[Dict[str, str]] = None,
                   timeout: int = 12, retries: int = 2) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not _domain_ok(url):
        return None, f"Blocked domain: {url}"
    session = requests.Session()
    last_err = None
    for _ in range(retries + 1):
        try:
            r = session.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code == 200:
                try:
                    return r.json(), None
                except Exception as e:
                    return None, f"JSON parse error: {e}"
            else:
                last_err = f"{r.status_code} - {r.text[:160]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.6)
    return None, last_err

def _load_memory() -> Dict[str, Any]:
    if not MEM_PATH.exists():
        MEM_PATH.write_text(json.dumps({
            "logs": [], "agents": {}, "ant_rl": {}, "metrics_history": [],
            "metrics": {"total_cycles": 0, "rewards": []},
            "feeds": {}
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        return json.loads(MEM_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"feeds": {}}

def _save_memory(data: Dict[str, Any]) -> None:
    MEM_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def _append_feed(source: str, payload: Dict[str, Any]) -> None:
    data = _load_memory()
    feeds = data.get("feeds", {})
    if source not in feeds:
        feeds[source] = []
    feeds[source].append({"ts": time.time(), "data": payload})
    feeds[source] = feeds[source][-50:]  # limitar tamaño
    data["feeds"] = feeds
    _save_memory(data)

def _log(msg: str):
    print(f"[Connector] {msg}")
    data = _load_memory()
    data.setdefault("logs", [])
    data["logs"].append({"msg": f"[Connector] {msg}", "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    _save_memory(data)

# ---------- Conectores ----------
def wikipedia_summary(topic: str = "Artificial intelligence") -> None:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
    j, err = _http_get_json(url)
    if j:
        payload = {
            "title": j.get("title"),
            "extract": j.get("extract", "")[:800],
            "lang": j.get("lang"),
            "url": j.get("content_urls", {}).get("desktop", {}).get("page"),
        }
        _append_feed("wikipedia", payload)
        _log(f"Wikipedia OK: {topic}")
    else:
        _append_feed("wikipedia_errors", {"topic": topic, "error": err})
        _log(f"Wikipedia FAIL: {err}")

def nasa_apod() -> None:
    api_key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    url = "https://api.nasa.gov/planetary/apod"
    j, err = _http_get_json(url, params={"api_key": api_key})
    if j:
        payload = {
            "title": j.get("title"),
            "date": j.get("date"),
            "explanation": j.get("explanation", "")[:800],
            "media_type": j.get("media_type"),
            "hdurl": j.get("hdurl"),
            "url": j.get("url"),
        }
        _append_feed("nasa_apod", payload)
        _log("NASA APOD OK")
    else:
        _append_feed("nasa_errors", {"endpoint": "apod", "error": err})
        _log(f"NASA APOD FAIL: {err}")

def spacex_latest() -> None:
    url = "https://api.spacexdata.com/v5/launches/latest"
    j, err = _http_get_json(url)
    if j:
        payload = {
            "name": j.get("name"),
            "date_utc": j.get("date_utc"),
            "success": j.get("success"),
            "details": (j.get("details") or "")[:800],
            "links": j.get("links", {}).get("webcast"),
        }
        _append_feed("spacex", payload)
        _log("SpaceX latest OK")
    else:
        _append_feed("spacex_errors", {"error": err})
        _log(f"SpaceX FAIL: {err}")

def openweather_city(city: str = "Bogota") -> None:
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        _append_feed("openweather_errors", {"city": city, "error": "missing OPENWEATHER_API_KEY"})
        _log("OpenWeather SKIP: missing key")
        return
    url = "https://api.openweathermap.org/data/2.5/weather"
    j, err = _http_get_json(url, params={"q": city, "appid": key, "units": "metric", "lang": "es"})
    if j:
        payload = {
            "city": city,
            "temp": j.get("main", {}).get("temp"),
            "humidity": j.get("main", {}).get("humidity"),
            "weather": (j.get("weather") or [{}])[0].get("description"),
        }
        _append_feed("openweather", payload)
        _log(f"OpenWeather OK: {city}")
    else:
        _append_feed("openweather_errors", {"city": city, "error": err})
        _log(f"OpenWeather FAIL: {err}")

def worldbank_indicator(country: str = "COL", indicator: str = "SP.POP.TOTL") -> None:
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    j, err = _http_get_json(url, params={"format": "json"})
    if j and isinstance(j, list) and len(j) > 1:
        series = j[1] or []
        latest = next((row for row in series if row.get("value") is not None), None)
        payload = {
            "country": country,
            "indicator": indicator,
            "latest_year": latest.get("date") if latest else None,
            "latest_value": latest.get("value") if latest else None,
            "points": max(0, len(series)),
        }
        _append_feed("worldbank", payload)
        _log(f"WorldBank OK: {country}/{indicator}")
    else:
        _append_feed("worldbank_errors", {"country": country, "indicator": indicator, "error": err or "no data"})
        _log(f"WorldBank FAIL: {err or 'no data'}")

def openaq_city(city: str = "Bogota") -> None:
    url = "https://api.openaq.org/v2/latest"
    j, err = _http_get_json(url, params={"city": city, "limit": 1})
    if j and j.get("results"):
        r = j["results"][0]
        payload = {
            "city": r.get("city"),
            "measurements": [
                {"parameter": m.get("parameter"), "value": m.get("value"), "unit": m.get("unit")}
                for m in (r.get("measurements") or [])[:6]
            ]
        }
        _append_feed("openaq", payload)
        _log(f"OpenAQ OK: {city}")
    else:
        _append_feed("openaq_errors", {"city": city, "error": err or "no data"})
        _log(f"OpenAQ FAIL: {err or 'no data'}")

def yahoo_quote(symbols: List[str] = ["AAPL", "MSFT"]) -> None:
    syms = ",".join(symbols[:20])
    url = "https://query1.finance.yahoo.com/v7/finance/quote"
    j, err = _http_get_json(url, params={"symbols": syms})
    if j and j.get("quoteResponse", {}).get("result"):
        rows = j["quoteResponse"]["result"]
        payload = [{"symbol": r.get("symbol"), "price": r.get("regularMarketPrice"), "chg": r.get("regularMarketChangePercent")} for r in rows]
        _append_feed("yahoo_finance", {"quotes": payload})
        _log(f"Yahoo Finance OK: {len(payload)} tickers")
    else:
        _append_feed("yahoo_finance_errors", {"symbols": symbols, "error": err or "no data"})
        _log(f"Yahoo Finance FAIL: {err or 'no data'}")

def github_repo(repo: str = "VLUGOC/NeuraBoardEcho") -> None:
    url = f"https://api.github.com/repos/{repo}"
    j, err = _http_get_json(url)
    if j and j.get("full_name"):
        payload = {
            "full_name": j.get("full_name"),
            "stars": j.get("stargazers_count"),
            "forks": j.get("forks_count"),
            "open_issues": j.get("open_issues_count"),
            "updated_at": j.get("updated_at"),
        }
        _append_feed("github", payload)
        _log(f"GitHub OK: {repo}")
    else:
        _append_feed("github_errors", {"repo": repo, "error": err or "no data"})
        _log(f"GitHub FAIL: {err or 'no data'}")

REGISTRY = {
    "wikipedia": lambda cfg: wikipedia_summary(cfg.get("topic", "Artificial intelligence")),
    "nasa_apod": lambda cfg: nasa_apod(),
    "spacex_latest": lambda cfg: spacex_latest(),
    "openweather": lambda cfg: openweather_city(cfg.get("city", "Bogota")),
    "openaq": lambda cfg: openaq_city(cfg.get("city", "Bogota")),
    "worldbank": lambda cfg: worldbank_indicator(cfg.get("country", "COL"), cfg.get("indicator", "SP.POP.TOTL")),
    "yahoo_finance": lambda cfg: yahoo_quote(cfg.get("symbols", ["AAPL", "MSFT"])),
    "github_repo": lambda cfg: github_repo(cfg.get("repo", "VLUGOC/NeuraBoardEcho")),
}
DEFAULT_SOURCES = ["wikipedia", "nasa_apod", "spacex_latest", "openweather", "openaq", "worldbank", "yahoo_finance", "github_repo"]

def fetch_all(enabled_sources: Optional[List[str]] = None, config: Optional[Dict[str, Any]] = None, shuffle: bool = True) -> Dict[str, Any]:
    enabled = enabled_sources or DEFAULT_SOURCES[:]
    if shuffle:
        random.shuffle(enabled)
    cfg = config or {}
    results = {"ok": [], "fail": []}
    _log(f"Conector universal iniciando: {len(enabled)} fuentes")
    for name in enabled:
        fn = REGISTRY.get(name)
        if not fn:
            results["fail"].append({"source": name, "error": "not in registry"})
            continue
        try:
            fn(cfg)
            results["ok"].append(name)
        except Exception as e:
            _append_feed(f"{name}_errors", {"error": str(e)})
            results["fail"].append({"source": name, "error": str(e)})
    _log(f"Conector universal finalizado. OK={len(results['ok'])} FAIL={len(results['fail'])}")
    return results

if __name__ == "__main__":
    fetch_all(
        enabled_sources=DEFAULT_SOURCES,
        config={
            "topic": "Neural network",
            "city": "Bogota",
            "country": "COL",
            "indicator": "SP.POP.TOTL",
            "symbols": ["AAPL", "MSFT", "GOOG"],
            "repo": "VLUGOC/NeuraBoardEcho",
        }
    )
