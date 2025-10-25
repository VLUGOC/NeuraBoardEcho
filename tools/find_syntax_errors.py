import os, sys, py_compile

ROOT = os.path.expanduser('~/NeuraBoardEco')
errors = []

for root, dirs, files in os.walk(ROOT):
    # saltar entornos virtuales y cachés
    if '/.venv/' in root or '__pycache__' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                py_compile.compile(path, doraise=True)
            except Exception as e:
                print(f"[SYNTAX_ERROR] {path}\n  → {e}\n")
                errors.append(path)

if errors:
    print(f"Total con error: {len(errors)}")
    sys.exit(1)
else:
    print("Sin errores de sintaxis 🎉")
