#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "contracts" / "covenant_authorization.py"
MAND = ROOT / "contracts" / "covenant_mandates.py"
GLSIM = ROOT / "tests" / "test_covenant_authorization_glsim.py"
VENV = ROOT / ".venv"
GENVM_VERSION = "v0.2.16"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(cmd: list[str], *, env: dict[str, str] | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )

def expected_sdk_hash() -> str:
    text = GLSIM.read_text()
    match = re.search(
        r'EXPECTED_SDK_FRAGMENT\s*=\s*"/extracted/v0\.2\.16/py-lib-genlayer-std/([^/]+)/genlayer/"',
        text,
    )
    if not match:
        raise SystemExit("SDK fragment pin not found")
    return match.group(1)

def resolve_sdk_root() -> Path:
    pinned = expected_sdk_hash()
    path = Path.home() / ".cache" / "gltest-direct" / "extracted" / GENVM_VERSION / "py-lib-genlayer-std" / pinned
    if not (path / "genlayer" / "py" / "get_schema.py").is_file():
        raise SystemExit(
            "exact pinned SDK cache missing; run the Direct Mandates test first "
            f"with GENVM_VERSION={GENVM_VERSION}"
        )
    return path

def make_genvmroot(sdk_root: Path, base: Path) -> Path:
    root = base / "genvmroot"
    target = root / "runners" / "py-lib-genlayer-std"
    target.mkdir(parents=True, exist_ok=True)
    link = target / "src"
    link.symlink_to(sdk_root, target_is_directory=True)
    return root

def pyright_strict(pyright: str, sdk_root: Path, contract: Path, work: Path) -> None:
    config = {
        "extraPaths": [str(sdk_root)],
        "typeCheckingMode": "strict",
        "reportMissingModuleSource": False,
        "pythonVersion": "3.12",
        "reportAttributeAccessIssue": "none",
        "reportArgumentType": "none",
        "reportReturnType": "none",
    }
    cfg = work / f"{contract.stem}.pyrightconfig.json"
    cfg.write_text(json.dumps(config, indent=2) + "\n")
    result = run(
        [pyright, "--project", str(cfg), str(contract), "--outputjson"],
        capture=True,
    )
    if not result.stdout:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"pyright produced no JSON for {contract.name}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"invalid pyright JSON for {contract.name}")
    diagnostics = [
        d for d in payload.get("generalDiagnostics", [])
        if contract.name in d.get("file", "")
    ]
    if diagnostics:
        print(json.dumps(diagnostics, indent=2))
        raise SystemExit(f"strict typecheck failed for {contract.name}")
    print(f"STRICT_TYPECHECK_{contract.stem.upper()}=PASS")

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--genvm-lint", default=str(VENV / "bin" / "genvm-lint"))
    p.add_argument("--pyright", default=str(VENV / "bin" / "pyright"))
    args = p.parse_args()

    sdk_root = resolve_sdk_root()
    with tempfile.TemporaryDirectory(prefix="covenant-gate-c-") as td:
        work = Path(td)
        genvmroot = make_genvmroot(sdk_root, work)
        env = os.environ.copy()
        env["GENVMROOT"] = str(genvmroot)
        env["GENVM_VERSION"] = GENVM_VERSION

        for contract in (MAND, AUTH):
            r = run([args.genvm_lint, "check", str(contract)], env=env)
            if r.returncode != 0:
                raise SystemExit(r.returncode)

        for contract in (MAND, AUTH):
            pyright_strict(args.pyright, sdk_root, contract, work)

        schemas: dict[str, str] = {}
        for contract in (MAND, AUTH):
            out = work / f"{contract.stem}.abi.json"
            r = run([args.genvm_lint, "schema", str(contract), "--output", str(out)], env=env)
            if r.returncode != 0:
                raise SystemExit(r.returncode)
            schemas[contract.name] = sha(out)

        result = {
            "status": "PASS",
            "genvm_version": GENVM_VERSION,
            "sdk_hash": expected_sdk_hash(),
            "source": {
                MAND.name: {"bytes": MAND.stat().st_size, "sha256": sha(MAND)},
                AUTH.name: {"bytes": AUTH.stat().st_size, "sha256": sha(AUTH)},
            },
            "schema_sha256": schemas,
        }
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
