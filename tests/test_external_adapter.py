import json
from pathlib import Path

import pytest

from opencode_medical_digital_twin_mirofish_reversa.adapters import MiroFishExternalAdapter


def test_external_adapter_accepts_normalized_json(tmp_path: Path):
    script = tmp_path / "fake.py"
    script.write_text(
        "import json,sys\n"
        "payload=json.load(sys.stdin)\n"
        "json.dump({'aggregate':0.6,'consensus':0.8,'dispersion':0.1,'n_agents':25,'trace':payload},sys.stdout)\n",
        encoding="utf-8",
    )
    adapter = MiroFishExternalAdapter(f"python3 {script}")
    result = adapter.simulate(question="q", signal=0.5, seed=42)
    assert result["aggregate"] == 0.6
    assert result["trace"]["domain"] == "medical_simulation"


def test_external_adapter_rejects_invalid_contract(tmp_path: Path):
    script = tmp_path / "bad.py"
    script.write_text("print('{}')\n", encoding="utf-8")
    adapter = MiroFishExternalAdapter(f"python3 {script}")
    with pytest.raises(RuntimeError, match="campo obrigatório"):
        adapter.simulate(question="q", signal=0.5, seed=42)
