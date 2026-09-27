#!/usr/bin/env python3
# Build a reviewer-verifiable SHA-256 inventory for an existing evidence directory.
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("evidence_root", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a=p.parse_args()
    root=a.evidence_root.resolve()
    if not root.is_dir():
        raise SystemExit("evidence_root is not a directory")
    rows=[]
    for f in sorted(x for x in root.rglob("*") if x.is_file()):
        rows.append({"path":str(f.relative_to(root)),"bytes":f.stat().st_size,"sha256":sha256(f)})
    out={
        "format":"covenant-evidence-inventory-v1",
        "evidence_root_name":root.name,
        "artifact_count":len(rows),
        "artifacts":rows,
    }
    encoded=json.dumps(out,indent=2,sort_keys=True)+"\n"
    a.output.write_text(encoded)
    print(encoded,end="")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
