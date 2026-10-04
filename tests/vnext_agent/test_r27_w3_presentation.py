from __future__ import annotations

import ast
from pathlib import Path

import pytest


BASE = Path("agentes/gipuzkoa360_vnext/portal_r26/main.py")
CANDIDATE = Path("agentes/gipuzkoa360_vnext/portal_r27/main.py")


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _prompt_parts(path: Path) -> tuple[str, list[str]]:
    tree = _module(path)
    base = None
    additions: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT":
                    base = ast.literal_eval(node.value)
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) and node.target.id == "SYSTEM_PROMPT":
            additions.append(ast.literal_eval(node.value))
    assert isinstance(base, str)
    return base, additions


def _tool_signatures(path: Path) -> list[tuple[str, tuple[str, ...]]]:
    out: list[tuple[str, tuple[str, ...]]] = []
    for node in _module(path).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not any(isinstance(d, ast.Name) and d.id == "tool" for d in node.decorator_list):
            continue
        out.append((node.name, tuple(arg.arg for arg in node.args.args)))
    return out


def _literal_assignment(path: Path, name: str):
    for node in _module(path).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(name)


BASE_PROMPT, BASE_ADDITIONS = _prompt_parts(BASE)
CANDIDATE_PROMPT, ADDITIONS = _prompt_parts(CANDIDATE)
FULL_ADDITION = "\n".join(ADDITIONS)


CHECKS = [
    ("r26_prompt_exact", lambda: CANDIDATE_PROMPT == BASE_PROMPT),
    ("three_additions_only", lambda: len(ADDITIONS) == 3),
    ("threshold_heading", lambda: "THRESHOLD SCENARIO PRESENTATION" in FULL_ADDITION),
    ("threshold_ledger_authority", lambda: "threshold_transition_ledger" in FULL_ADDITION),
    ("threshold_verified_gate", lambda: "verified=true" in FULL_ADDITION),
    ("threshold_comparison_sentence", lambda: "comparison_sentence" in FULL_ADDITION),
    ("threshold_answer_table", lambda: "answer_table_markdown" in FULL_ADDITION),
    ("threshold_semantic_limit", lambda: "semantic_limit_sentence" in FULL_ADDITION),
    ("threshold_no_preview_reconstruction", lambda: "no reconstruyas clasificaciones desde filas de muestra" in FULL_ADDITION),
    ("threshold_no_omitted_inference", lambda: "ni infieras municipios omitidos" in FULL_ADDITION),
    ("threshold_fail_closed", lambda: "no hay evidencia verificada suficiente" in FULL_ADDITION),
    ("home_heading", lambda: "HOME SCOPE" in FULL_ADDITION),
    ("home_no_address_request", lambda: "no pidas una dirección" in FULL_ADDITION),
    ("home_stops_only", lambda: "paradas u orígenes del catálogo" in FULL_ADDITION),
    ("home_no_door_to_door_implication", lambda: "trayecto puerta a puerta" in FULL_ADDITION),
    ("zero_heading", lambda: "UNVERIFIED ZERO-COUNT PREMISE" in FULL_ADDITION),
    ("zero_explicit_count", lambda: "registered_service_count" in FULL_ADDITION),
    ("zero_distance_not_count", lambda: "Una distancia geométrica" in FULL_ADDITION and "no verifican un recuento" in FULL_ADDITION),
    ("zero_no_absence_inference", lambda: "no infieras ausencia de atención" in FULL_ADDITION),
    ("ten_tools_preserved", lambda: len(_tool_signatures(CANDIDATE)) == 10),
    ("tool_names_preserved", lambda: [x[0] for x in _tool_signatures(CANDIDATE)] == [x[0] for x in _tool_signatures(BASE)]),
    ("tool_signatures_preserved", lambda: _tool_signatures(CANDIDATE) == _tool_signatures(BASE)),
    ("agent_name_preserved", lambda: _literal_assignment(CANDIDATE, "AGENT_NAME") == _literal_assignment(BASE, "AGENT_NAME")),
    ("iterations_preserved", lambda: _literal_assignment(CANDIDATE, "STUDIO_MAX_ITERATIONS") == _literal_assignment(BASE, "STUDIO_MAX_ITERATIONS")),
    ("memory_preserved", lambda: _literal_assignment(CANDIDATE, "STUDIO_MEMORY_ENABLED") == _literal_assignment(BASE, "STUDIO_MEMORY_ENABLED")),
    ("internet_preserved", lambda: _literal_assignment(CANDIDATE, "STUDIO_INTERNET_ENABLED") == _literal_assignment(BASE, "STUDIO_INTERNET_ENABLED")),
    ("context_files_preserved", lambda: _literal_assignment(CANDIDATE, "STUDIO_CONTEXT_FILES") == _literal_assignment(BASE, "STUDIO_CONTEXT_FILES")),
    ("no_legazpi_hardcode", lambda: "Legazpi" not in CANDIDATE.read_text(encoding="utf-8")),
    ("no_distance_hardcode", lambda: "2624.8" not in CANDIDATE.read_text(encoding="utf-8")),
]


@pytest.mark.parametrize("name,check", CHECKS, ids=[name for name, _ in CHECKS])
def test_r27_w3_bounded_presentation_patch(name, check):
    assert check(), name
