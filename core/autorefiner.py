# NeuraBoardEco - AutoRefiner (versión segura sin triple quotes en docstrings)
# Funciones:
#   - Normaliza y repara .py (tabs→espacios, EOL, espacios finales, BOM)
#   - Limpia marcadores de merge (<<<<<<<, =======, >>>>>>>)
#   - Cierra triple comillas sin terminar (heurística por conteo)
#   - Valida sintaxis con ast.parse antes/después
#   - Soporta --dry-run y --show-diff

from __future__ import annotations

import ast
import difflib
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "NeuraBoardEco"
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOGS / "autorefiner.log"

SKIP_DIRS = {".git", ".venv", "__pycache__", "logs", "backups", "secrets"}

# Marcadores de merge típicos, anclados a inicio de línea
MERGE_MARKERS_RE = re.compile(r"^(<{7,}|={7,}|>{7,}).*$", re.MULTILINE)

TRI_DQ = '"' * 3   # """
TRI_SQ = "'" * 3   # '''

def log(msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[AutoRefiner {stamp}] {msg}"
    print(line)
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def list_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune directorios a ignorar
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                files.append(Path(dirpath) / name)
    return files

def read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")

def write_text_safe(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")

def normalize_text(text: str) -> str:
    # Eliminar BOM
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    # Normalizar saltos de línea
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Tabs → 4 espacios
    text = text.replace("\t", "    ")
    # Quitar espacios al final de línea
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    # Asegurar salto final
    if not text.endswith("\n"):
        text += "\n"
    return text

def remove_merge_markers(text: str) -> str:
    return MERGE_MARKERS_RE.sub("", text)

def fix_unterminated_triple_quotes(text: str) -> str:
    # Heurística: si el conteo es impar, agregamos un cierre al final
    if text.count(TRI_DQ) % 2 != 0:
        text = text.rstrip() + "\n" + TRI_DQ + "\n"
    if text.count(TRI_SQ) % 2 != 0:
        text = text.rstrip() + "\n" + TRI_SQ + "\n"
    return text

def compile_ok(code: str, filename: str) -> bool:
    try:
        ast.parse(code, filename=filename)
        return True
    except Exception as e:
        log(f"AST fallo en {filename}: {e}")
        return False

def refine_text(original: str, filename: str) -> str:
    t = normalize_text(original)
    t = remove_merge_markers(t)
    t = fix_unterminated_triple_quotes(t)
    return t

def make_backup(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + f".bak.{int(time.time())}")
    try:
        backup.write_text(read_text_safe(path), encoding="utf-8")
        return backup
    except Exception:
        return Path()

def show_diff(a: str, b: str, filename: str) -> str:
    diff = difflib.unified_diff(
        a.splitlines(True),
        b.splitlines(True),
        fromfile=f"{filename} (before)",
        tofile=f"{filename} (after)",
        n=3,
    )
    return "".join(diff)

def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    show_changes = "--show-diff" in argv

    log("🚀 Iniciando AutoRefiner")
    py_files = list_python_files(ROOT)
    log(f"Archivos Python detectados: {len(py_files)}")

    changed = fixed = skipped = failed = 0

    for path in py_files:
        # leer original
        try:
            original = read_text_safe(path)
        except Exception as e:
            log(f"❌ No se pudo leer {path}: {e}")
            failed += 1
            continue

        original_ok = compile_ok(original, str(path))
        refined = refine_text(original, str(path))
        refined_ok = compile_ok(refined, str(path))

        # Mostrar diff si se pidió
        if show_changes and refined != original:
            diff = show_diff(original, refined, str(path))
            if diff.strip():
                log(f"--- DIFF {path} ---\n{diff}")

        if not original_ok:
            if not refined_ok:
                log(f"⛔ Reparación fallida en {path}, se deja igual.")
                failed += 1
                continue
            changed += 1
            if dry_run:
                log(f"✅ (dry-run) {path} sería reparado.")
            else:
                backup = make_backup(path)
                write_text_safe(path, refined)
                log(f"✅ Reparado {path} (backup: {backup.name if backup else 'n/a'})")
            fixed += 1
        else:
            if refined != original and refined_ok:
                changed += 1
                if dry_run:
                    log(f"ℹ️ (dry-run) {path} se normalizaría.")
                else:
                    backup = make_backup(path)
                    write_text_safe(path, refined)
                    log(f"🧹 Normalizado {path} (backup: {backup.name if backup else 'n/a'})")
            else:
                skipped += 1

    log(f"Resumen → cambiados: {changed}, reparados: {fixed}, "
        f"saltados: {skipped}, fallidos: {failed}")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
