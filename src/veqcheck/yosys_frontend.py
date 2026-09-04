from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any


class YosysError(RuntimeError):
    pass


def synthesize_to_json(path: str) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise YosysError(f"Verilog file not found: {path}")

    with tempfile.TemporaryDirectory(prefix="veqcheck_") as tmp:
        output = Path(tmp) / "netlist.json"
        script = (
            f"read_verilog -sv {source}; "
            "hierarchy -auto-top; "
            "proc; flatten; opt; techmap; opt; "
            f"write_json {output}"
        )
        completed = subprocess.run(
            ["yosys", "-q", "-p", script],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip()
            raise YosysError(f"Yosys failed for {path}: {detail}")
        return json.loads(output.read_text(encoding="utf-8"))
