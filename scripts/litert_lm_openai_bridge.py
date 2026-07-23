#!/usr/bin/env python3
"""Bridge JSON stdin/stdout para servidor local OpenAI-compatible do LiteRT-LM.

Uso administrativo:

    export LITERT_LM_BASE_URL=http://127.0.0.1:8000/v1
    export LITERT_LM_MODEL=gemma-4
    export LITERT_LM_COMMAND="python3 scripts/litert_lm_openai_bridge.py"

O script não inicia o servidor e não baixa modelos. Ele somente encaminha um caso
sintético já validado para uma instância local controlada pelo operador.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

_MAX_IMAGE_BYTES = 20 * 1024 * 1024


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("entrada deve ser um objeto JSON")
        base_url = os.environ.get("LITERT_LM_BASE_URL", "http://127.0.0.1:8000/v1")
        _validate_base_url(base_url)
        model = os.environ.get("LITERT_LM_MODEL", "gemma-4").strip()
        if not model:
            raise ValueError("LITERT_LM_MODEL não pode ser vazio")
        messages = _build_messages(payload)
        response = _post_chat_completions(base_url, model, messages)
        opinion = _extract_opinion(response)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(opinion, ensure_ascii=False))
    return 0


def _validate_base_url(base_url: str) -> None:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("LITERT_LM_BASE_URL inválida")
    allow_remote = os.environ.get("LITERT_LM_ALLOW_REMOTE", "0") == "1"
    if not allow_remote and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("LiteRT-LM remoto bloqueado; use loopback ou LITERT_LM_ALLOW_REMOTE=1")


def _build_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
    specialist = payload.get("specialist", {})
    case = payload.get("case", {})
    safety = payload.get("safety", {})
    image_files = payload.get("image_files", [])
    if not isinstance(image_files, list):
        raise ValueError("image_files deve ser uma lista")

    system = (
        "Você é um especialista virtual para ensino e pesquisa metodológica com casos "
        "inteiramente sintéticos. Não diagnostique, não prescreva, não indique procedimento "
        "e não trate consenso como verdade clínica. Responda somente JSON com as chaves: "
        "observations, claims, must_not_miss, missing_information, intervention_questions, "
        "limitations, confidence, evidence_strength. Cada claim deve conter claim_id, label, "
        "stance (support|oppose|uncertain) e confidence. Intervenções devem ser perguntas, "
        "nunca ordens."
    )
    content: list[dict[str, Any]] = []
    for raw_path in image_files:
        path = Path(str(raw_path)).resolve()
        if not path.is_file():
            raise ValueError(f"imagem não encontrada: {path}")
        if path.stat().st_size > _MAX_IMAGE_BYTES:
            raise ValueError("imagem excede 20 MiB")
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if mime not in {"image/png", "image/jpeg", "image/webp"}:
            raise ValueError("formato de imagem não permitido")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{encoded}"},
            }
        )
    content.append(
        {
            "type": "text",
            "text": json.dumps(
                {
                    "specialist": specialist,
                    "case": case,
                    "safety": safety,
                    "task": "produza opinião estruturada e limitada ao domínio informado",
                },
                ensure_ascii=False,
            ),
        }
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": content},
    ]


def _post_chat_completions(
    base_url: str,
    model: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": int(os.environ.get("LITERT_LM_MAX_TOKENS", "2048")),
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("LITERT_LM_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
    timeout = float(os.environ.get("LITERT_LM_TIMEOUT", "180"))
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[-1000:]
        raise ValueError(f"LiteRT-LM HTTP {exc.code}: {detail}") from exc
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("resposta do servidor não é objeto JSON")
    return parsed


def _extract_opinion(response: dict[str, Any]) -> dict[str, Any]:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("resposta OpenAI-compatible sem choices[0].message.content") from exc
    if isinstance(content, list):
        text = "".join(
            str(item.get("text", "")) for item in content if isinstance(item, dict)
        )
    else:
        text = str(content)
    opinion = _extract_json_object(text)
    required = {"observations", "claims", "limitations", "confidence", "evidence_strength"}
    missing = sorted(required.difference(opinion))
    if missing:
        raise ValueError(f"opinião sem campos obrigatórios: {missing}")
    return opinion


def _extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("modelo não retornou objeto JSON")
        try:
            value = json.loads(stripped[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ValueError("modelo retornou JSON inválido") from exc
    if not isinstance(value, dict):
        raise ValueError("modelo deve retornar objeto JSON")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
