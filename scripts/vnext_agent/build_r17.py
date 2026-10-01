"""Two-editor public presentation delta over the exact, immutable R16 package."""
import ast
import io
import json
import sys
import zipfile

from scripts.vnext_agent.build_r16 import ROOT, sha
import subprocess

BASE = "c859a26396838d59a52b8d91f1eda5ef6b69e4cd"
BASE_ZIP = "scripts/vnext_agent/dist/r16/gipuzkoa360-r16-final-agent.zip"
BASE_MANIFEST = "scripts/vnext_agent/dist/r16/gipuzkoa360-r16-final-agent-manifest.json"
BASE_HASH = "374af43fa6ce58b513a10477fc216215c7472f54bd28eada4fc0908da6f3dd6c"
BASE_MANIFEST_HASH = "a46415845f86c5c22ad648965b45e5bd109c839e9cb6cc14daee0ef37d7f788e"
OUT = ROOT / "scripts/vnext_agent/dist/r17"
ZIP = OUT / "gipuzkoa360-r17-final-agent.zip"
MANIFEST = OUT / "gipuzkoa360-r17-final-agent-manifest.json"
PORTAL = ROOT / "agentes/gipuzkoa360_vnext/portal_r17"
DELTA = ROOT / "scripts/vnext_agent/r17_public_schema.py"


def blob(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


def generated_main(data):
    text = data.decode("utf-8")
    old = '''def obtener_resumen_territorial(municipio: str, periodo: str | None = None) -> str:
    """Resumen observado de un municipio (nombre o código string). periodo selecciona demografía: fecha del catálogo; omitido/null usa el único disponible, si hay varios pide periodo. Nunca un periodo vacío. Fuentes sanitarias tienen su propio periodo."""
    return _run("obtener_resumen_territorial", {"municipio": municipio, "periodo": periodo})'''
    new = '''def obtener_resumen_territorial(municipio: str) -> str:
    """Resumen observado de un municipio por nombre o código. Usa la única referencia demográfica disponible, indicada en el resultado. Las fuentes sanitarias conservan sus propias fechas."""
    return _run("obtener_resumen_territorial", {"municipio": municipio})'''
    changes = {
        old: new,
        "Eres GIPUZKOA 360 vNext,": "Eres GIPUZKOA 360,",
        "Usa únicamente los argumentos de las firmas públicas (PUBLIC_AGENT_CONTRACT). Los archivos\ndel motor (ENGINE_CONTRACT) documentan opciones internas, no herramientas adicionales.":
        "Usa únicamente los argumentos de las firmas públicas. La documentación técnica puede\ndescribir opciones internas: no son argumentos ni herramientas adicionales.",
        "El hash identifica bytes, no demuestra verdad.": "La procedencia documenta el dato, no demuestra por sí sola su veracidad.",
        "Provider defaults stay internal.": "Calculation assumptions stay internal.",
        "cuando cambie la interpretación, sin volcar fichas enteras.":
        "cuando cambie la interpretación, sin volcar fichas enteras. Para explicar un grupo de edad,\nusa age_group_derivation si está presente: indica campo de origen, condición, fecha y límites.\nNo afirmes conocer la edad exacta individual a partir de recuentos agregados.",
    }
    for before, after in changes.items():
        assert text.count(before) == 1, before
        text = text.replace(before, after)
    ast.parse(text)
    return text.encode("utf-8")


def generated_tools(data):
    text = data.decode("utf-8")
    assert text.count("def _public_result(") == 1
    text = text.replace("def _public_result(", "def _r16_public_result(")
    text += "\n\n" + DELTA.read_text(encoding="utf-8").replace("\r\n", "\n")
    ast.parse(text)
    return text.encode("utf-8")


def build():
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Canonical bundle requires CPython 3.12")
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    base_report = json.loads(metadata)
    OUT.mkdir(parents=True, exist_ok=True)
    PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, "w") as new:
        # Audit the frozen data, rather than selecting a default in the wrapper.
        import csv
        rows = list(csv.DictReader(io.StringIO(old.read("datos_preparados/demografia.csv").decode("utf-8"))))
        assert len(rows) == 88
        assert {r["reference_period"] for r in rows} == {"2025-01-01"}
        sources = json.loads(old.read("datos_preparados/metadata_sources.json"))
        eu = next(r for r in sources if r["source_id"] == "EUSTAT_EMH_2025")
        assert "1949" in eu["method"] and "<=1949" in " ".join(eu["limitations"])
        overrides = {"main.py": generated_main(old.read("main.py")), "tools.py": generated_tools(old.read("tools.py"))}
        members, changed = {}, []
        for info in old.infolist():
            before = old.read(info.filename)
            data = overrides.get(info.filename, before)
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {"bytes": len(data), "sha256": sha(data)}
            if before != data:
                changed.append(info.filename)
    assert changed == ["main.py", "tools.py"] and len(members) == 25
    for name, data in overrides.items():
        (PORTAL / name).write_bytes(data)
    report = {
        "package": "GIPUZKOA360_R17_final_agent", "base_r16_head": BASE,
        "base_r16_zip_sha256": BASE_HASH, "base_r16_manifest_sha256": BASE_MANIFEST_HASH,
        "sha256": sha(ZIP.read_bytes()), "bytes": ZIP.stat().st_size,
        "members": members, "members_count": len(members), "changed_members": changed,
        "context_paths": base_report["context_paths"], "context_assets_changed": [],
        "uncompressed_bytes": sum(v["bytes"] for v in members.values()), "limit_bytes": base_report["limit_bytes"],
        "public_tools": 9, "public_resumen_fields": ["municipio"],
        "single_demographic_period": "2025-01-01", "demographic_rows": len(rows),
        "source_delta_sha256": sha(DELTA.read_bytes().replace(b"\r\n", b"\n")),
        "runtime_delta": "Summary wrapper removes redundant period; public metadata only; original engine and R16 temporal projection unchanged",
        "w1_runtime_changed": False, "v4_changed": False,
        "technical_traceability": "Full original raw/envelope/assets preserved; source IDs retained even when their historical identifier contains W1/W2",
        "author_delta_check": "NOT_INDEPENDENT_ACCEPTANCE", "portal_real_agent": "NOT_RUN",
        "real_tranche": {"maximum_user_messages": 4},
    }
    assert report["bytes"] < report["limit_bytes"]
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"zip_sha256": report["sha256"], "manifest_sha256": sha(MANIFEST.read_bytes()), "bytes": report["bytes"]}


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
