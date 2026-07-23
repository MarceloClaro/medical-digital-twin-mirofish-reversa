"""Processo JSON isolado chamado pelas custom tools do OpenCode."""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-base64", required=True)
    parser.add_argument("--worktree", required=True)
    args = parser.parse_args()

    worktree = Path(args.worktree).resolve()
    sys.path.insert(0, str(worktree / "src"))

    from opencode_medical_digital_twin_mirofish_reversa.opencode_bridge import (
        OpenCodeBridgeError,
        execute_opencode_request,
    )

    try:
        payload = json.loads(base64.b64decode(args.payload_base64).decode("utf-8"))
        result = execute_opencode_request(payload, worktree=worktree)
    except (ValueError, json.JSONDecodeError, OpenCodeBridgeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
