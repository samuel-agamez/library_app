#!/usr/bin/env python3
"""
Reproduce una guía EXACTAMENTE como la seguiría un estudiante y comprueba que el resultado funciona.

    python docs/replay.py app docs/guia-app-movil.md /ruta/vacia/work-app
    python docs/replay.py api ../library_api/docs/guia-api-web.md /ruta/vacia/work-api [--upto semana-10]

Qué hace:
  1. Extrae el esqueleto original del proyecto (primer commit de git) en el directorio de trabajo.
  2. Instala sus dependencias y recorre la guía en orden, aplicando cada directiva:
       create / path (crear archivos), merge (JSON), append, delete y run (comandos de terminal).
  3. En cada {{checkpoint:...}} ejecuta las comprobaciones (tipos, pruebas, lint, build).
  4. Al final compara contra el proyecto real: archivos que la guía OMITIÓ y archivos sobrantes.

Si todo pasa, un estudiante que siga la guía al pie de la letra obtiene el proyecto completo y funcionando.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import io
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPOS = {"app": HERE.parent, "api": HERE.parent.parent / "library_api"}

EXPO_TYPES = "(CI=1 timeout 45 npx expo start --offline --port 8099 >/dev/null 2>&1 || true)"
CHECKS = {
    "api": {
        "typecheck": "pnpm typecheck",
        "test": "pnpm test",
        "lint": "pnpm lint",
        "build": "pnpm build",
    },
    "app": {
        "typecheck": f"{EXPO_TYPES}; npx tsc --noEmit",
        "test": "npx jest",
        "lint": "CI=1 npx expo lint",
        "export": "EXPO_PUBLIC_API_URL=http://localhost:3000 npx expo export --platform android --output-dir .check-export",
    },
}
INSTALL = {"api": "pnpm install --frozen-lockfile", "app": "npm ci"}

# Archivos que NO forman parte de lo que la guía debe reproducir (se ignoran en AMBOS lados de la comparación).
IGNORE = re.compile(
    r"^(docs/|README\.md|AGENTS\.md|LICENSE|\.claude/|\.vscode/|assets/|public/|scripts/reset-project\.js|"
    r"app/favicon\.ico|MICRO |\.~lock|package-lock\.json|pnpm-lock\.yaml|\.env$|Guia_.*\.pdf$)"
)
GENERATED = re.compile(
    r"(^|/)(node_modules|\.expo|\.next|\.check-export|dist)(/|$)|expo-env\.d\.ts|next-env\.d\.ts|tsconfig\.tsbuildinfo"
)

failures: list[str] = []


def sh(cmd: str, cwd: Path, label: str | None = None, check: bool = True) -> int:
    print(f"   $ {cmd if len(cmd) < 140 else cmd[:137] + '...'}", flush=True)
    t0 = time.time()
    p = subprocess.run(["bash", "-lc", cmd], cwd=cwd, env={**os.environ, "CI": "1"}, capture_output=True, text=True)
    out = (p.stdout + p.stderr).strip()
    if p.returncode != 0:
        tail = "\n".join(out.splitlines()[-25:])
        print(f"   ✗ falló ({p.returncode}) en {time.time() - t0:.0f}s\n{tail}")
        if check:
            failures.append(f"{label or cmd}")
    return p.returncode


def deep_merge(base, extra):
    if isinstance(base, dict) and isinstance(extra, dict):
        for k, v in extra.items():
            base[k] = deep_merge(base.get(k), v) if k in base else v
        return base
    return extra


def run_lines(block: str) -> list[str]:
    """Une líneas con '\\' final y descarta comentarios y vacías."""
    cmds, cur = [], ""
    for raw in block.split("\n"):
        line = raw.rstrip()
        if cur:
            cur += " " + line.strip()
        elif line.strip() and not line.strip().startswith("#"):
            cur = line.strip()
        else:
            continue
        if cur.endswith("\\"):
            cur = cur[:-1].rstrip()
            continue
        cmds.append(cur)
        cur = ""
    return cmds


def repo_files(root: Path) -> set[str]:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, text=True).stdout
    # git ls-files puede escapar nombres con caracteres especiales; los tratamos tal cual.
    files = {f.strip('"') for f in out.split("\n") if f}
    return {f for f in files if (root / f).exists() and not IGNORE.match(f) and not GENERATED.search(f)}


def work_files(work: Path) -> set[str]:
    found = set()
    for path in work.rglob("*"):
        if path.is_file():
            rel = path.relative_to(work).as_posix()
            if not IGNORE.match(rel) and not GENERATED.search(rel):
                found.add(rel)
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", choices=["app", "api"])
    ap.add_argument("guide")
    ap.add_argument("work")
    ap.add_argument("--upto", help="detenerse tras este punto de control")
    ap.add_argument("--skip-install", action="store_true", help="no ejecutar la instalación inicial (para depurar)")
    args = ap.parse_args()

    key, repo, work = args.key, REPOS[args.key], Path(args.work)
    if work.exists() and any(work.iterdir()):
        sys.exit(f"{work} no está vacío")
    work.mkdir(parents=True, exist_ok=True)

    print(f"▶ Esqueleto original de {repo.name} (primer commit) → {work}")
    # Siempre el PRIMER commit (esqueleto), aunque el proyecto ya tenga más commits.
    root = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=repo, capture_output=True, text=True, check=True).stdout.split()[0]
    tar = subprocess.run(["git", "archive", root], cwd=repo, capture_output=True, check=True).stdout
    tarfile.open(fileobj=io.BytesIO(tar)).extractall(work)
    if not args.skip_install:
        print("▶ Instalando dependencias del esqueleto")
        if sh(INSTALL[key], work, "instalación inicial") != 0:
            return 1

    lines = Path(args.guide).read_text(encoding="utf8").split("\n")
    pending: tuple[str, str, str] | None = None
    created: set[str] = set()
    i, steps = 0, 0
    while i < len(lines):
        line = lines[i].strip()
        d = re.fullmatch(r"\{\{(create|path|merge|append|delete|run|checkpoint):([^}]*)\}\}", line)
        if d:
            kind, arg = d.group(1), d.group(2)
            if kind == "checkpoint":
                _, _, rest = arg.partition(":")
                name, _, checks = rest.partition("|")
                print(f"■ Punto de control «{name}»")
                for c in [c for c in checks.split(",") if c]:
                    if sh(CHECKS[key][c], work, f"{name}: {c}") == 0:
                        print(f"   ✓ {c}")
                if args.upto == name:
                    print("— detenido por --upto")
                    break
                if failures:
                    break
            else:
                k, _, rel = arg.partition(":")
                rel = rel.split("|")[0]
                if kind == "create":
                    src = REPOS[k] / rel
                    dst = work / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_text(src.read_text(encoding="utf8"), encoding="utf8")
                    created.add(rel); steps += 1
                    print(f"   + {rel}")
                elif kind == "delete":
                    target = work / rel
                    if target.exists():
                        target.unlink()
                        print(f"   - {rel}")
                    else:
                        failures.append(f"delete: {rel} no existe en el esqueleto")
                        print(f"   ✗ delete: {rel} no existe")
                else:
                    pending = (kind, k, rel)
            i += 1
            continue

        if line.startswith("```"):
            body, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                body.append(lines[i]); i += 1
            i += 1
            if pending:
                kind, k, rel = pending
                pending = None
                text = "\n".join(body)
                steps += 1
                if kind == "path":
                    dst = work / rel
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_text(text + "\n", encoding="utf8")
                    created.add(rel)
                    print(f"   + {rel} (escrito en la guía)")
                elif kind == "append":
                    with open(work / rel, "a", encoding="utf8") as f:
                        f.write("\n" + text + "\n")
                    print(f"   ~ {rel} (agregado al final)")
                elif kind == "merge":
                    target = work / rel
                    data = json.loads(target.read_text(encoding="utf8"))
                    deep_merge(data, json.loads(text))
                    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
                    print(f"   ~ {rel} (JSON fusionado)")
                elif kind == "run":
                    for cmd in run_lines(text):
                        if sh(cmd, work, f"comando: {cmd}") != 0:
                            break
                if failures:
                    break
            continue
        i += 1

    print()
    if failures:
        print("✗ FALLÓ:", *failures, sep="\n  - ")
        return 1

    if args.upto is None:
        print("▶ Comparación con el proyecto real")
        repo_set, work_set = repo_files(repo), work_files(work)
        missing = sorted(repo_set - work_set)
        extra = sorted(work_set - repo_set)
        different = sorted(
            f for f in repo_set & work_set
            if not f.endswith(".json") and (repo / f).read_bytes() != (work / f).read_bytes()
        )
        print(f"   archivos del proyecto: {len(repo_set)} · reproducidos: {len(repo_set & work_set)}")
        for title, items in (("OMITIDOS por la guía", missing), ("SOBRANTES (la guía no los elimina)", extra), ("DIFERENTES al proyecto real", different)):
            if items:
                print(f"   ✗ {title}:")
                for f in items:
                    print(f"       {f}")
        if missing or extra or different:
            return 1
        print("   ✓ el resultado es idéntico al proyecto real")
    print(f"✅ Guía reproducida sin errores ({steps} pasos de archivos/comandos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
