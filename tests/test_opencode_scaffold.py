import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_opencode_configuration_and_components_exist():
    config = json.loads((ROOT / "opencode.json").read_text(encoding="utf-8"))
    assert config["$schema"] == "https://opencode.ai/config.json"
    assert "docs/OPENCODE_CLI.md" in config["instructions"]
    assert "docs/LITERT_LM_GEMMA4.md" in config["instructions"]

    required = [
        ".opencode/tools/medical_twin.ts",
        ".opencode/tools/medical_twin_runner.py",
        ".opencode/agents/medical-twin.md",
        ".opencode/commands/medical-twin.md",
        ".opencode/commands/medical-twin-validate.md",
        ".opencode/commands/medical-twin-mirofish.md",
        ".opencode/commands/medical-twin-council.md",
        ".opencode/commands/medical-twin-gemma.md",
        ".opencode/skills/medical-digital-twin/SKILL.md",
        "scripts/litert_lm_openai_bridge.py",
        "schemas/specialist_council_result.schema.json",
        "docs/SPEC-002-MULTIMODAL-SPECIALIST-COUNCIL.md",
    ]
    for relative in required:
        assert (ROOT / relative).is_file(), relative


def test_opencode_agent_is_fail_closed():
    agent = (ROOT / ".opencode/agents/medical-twin.md").read_text(encoding="utf-8")
    assert '"*": deny' in agent
    assert "medical_twin_simulate: allow" in agent
    assert "medical_twin_validate: allow" in agent
    assert "medical_twin_council: allow" in agent
    assert "medical_twin_mirofish: ask" in agent
    assert "medical_twin_gemma: ask" in agent
    assert "Nunca use `bash`" in agent


def test_custom_tools_do_not_accept_external_command_arguments():
    tool = (ROOT / ".opencode/tools/medical_twin.ts").read_text(encoding="utf-8")
    bridge = (
        ROOT / "src/opencode_medical_digital_twin_mirofish_reversa/opencode_bridge.py"
    ).read_text(encoding="utf-8")
    assert "mirofish_command" not in tool
    assert "litert_lm_command" not in tool
    assert 'os.environ.get("MIROFISH_COMMAND"' in bridge
    assert 'os.environ.get("LITERT_LM_COMMAND"' in bridge
    assert "_resolve_inside" in bridge


def test_tools_expose_hermetic_and_approved_multimodal_modes():
    tool = (ROOT / ".opencode/tools/medical_twin.ts").read_text(encoding="utf-8")
    assert "export const council" in tool
    assert "export const gemma" in tool
    assert 'adapter: "deterministic"' in tool
    assert 'adapter: "litert_lm"' in tool
