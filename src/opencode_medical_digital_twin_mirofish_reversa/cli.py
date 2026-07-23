"""CLI do projeto standalone."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import MiroFishExternalAdapter
from .engine import MedicalDigitalTwinEngine
from .models import SimulationCase


def main() -> int:
    parser = argparse.ArgumentParser(description="Gêmeo digital médico exclusivamente simulado")
    parser.add_argument("case_file", type=Path, help="JSON do caso sintético")
    parser.add_argument("--horizon", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mirofish-command", default=None, help="Comando externo JSON stdin/stdout")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    payload = json.loads(args.case_file.read_text(encoding="utf-8"))
    case = SimulationCase(**payload)
    adapter = MiroFishExternalAdapter(args.mirofish_command) if args.mirofish_command else None
    result = MedicalDigitalTwinEngine(swarm=adapter, seed=args.seed).simulate(case, horizon_steps=args.horizon)
    serialized = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
