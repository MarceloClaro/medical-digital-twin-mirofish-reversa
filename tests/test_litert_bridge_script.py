import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "litert_lm_openai_bridge.py"
SPEC = importlib.util.spec_from_file_location("litert_bridge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_extracts_json_from_fenced_model_output():
    value = module._extract_json_object('```json\n{"observations": [], "claims": []}\n```')
    assert value["observations"] == []


def test_remote_litert_is_blocked_by_default(monkeypatch):
    monkeypatch.delenv("LITERT_LM_ALLOW_REMOTE", raising=False)
    with pytest.raises(ValueError, match="remoto bloqueado"):
        module._validate_base_url("https://example.org/v1")


def test_images_are_ordered_before_text(tmp_path: Path):
    image = tmp_path / "synthetic.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic")
    messages = module._build_messages({
        "specialist": {"specialist_id": "radiology"},
        "case": {"synthetic": True},
        "safety": {"simulation_only": True},
        "image_files": [str(image)],
    })
    content = messages[1]["content"]
    assert content[0]["type"] == "image_url"
    assert content[-1]["type"] == "text"
