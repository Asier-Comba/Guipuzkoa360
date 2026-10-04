"""Offline B1 lexical section retrieval over four public repository documents.

This is an experiment, not a runtime tool or a measure of generated-answer fidelity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "datos_preparados/vnext/document_corpus.json"
STOP = {"que", "con", "para", "los", "las", "del", "una", "por", "como", "puede", "cual", "son", "hay", "entre", "sobre", "tiene", "datos"}


def tokens(value: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return [word for word in re.findall(r"[a-z0-9]+", normalized) if len(word) >= 3 and word not in STOP]


def sections(text: str) -> list[tuple[str, str]]:
    result = []
    heading = "Introducción"
    lines = []
    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            if any(part.strip() for part in lines):
                result.append((heading, "\n".join(lines).strip()))
            heading = re.sub(r"^#{1,3}\s+", "", line).strip()
            lines = []
        else:
            lines.append(line)
    if any(part.strip() for part in lines):
        result.append((heading, "\n".join(lines).strip()))
    return result


def load_corpus(root: Path = ROOT) -> list[dict]:
    manifest = json.loads((root / "datos_preparados/vnext/document_corpus.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "W2_DOCUMENT_CORPUS_1" or manifest.get("external_sources_ingested") is not False or not 4 <= len(manifest["documents"]) <= 8:
        raise ValueError("Unapproved or malformed corpus")
    chunks = []
    for document in manifest["documents"]:
        path = (root / document["path"]).resolve()
        if root.resolve() not in path.parents or not path.is_file():
            raise ValueError("Corpus path outside approved root")
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != document["sha256"]:
            raise ValueError("Corpus document hash mismatch")
        for index, (heading, body) in enumerate(sections(payload.decode("utf-8")), start=1):
            chunks.append({"source_id": document["source_id"], "issuer": document["issuer"], "title": document["title"], "version": document["version"], "date": document["date"], "url": document["url"], "document_sha256": document["sha256"], "section_id": f"{document['source_id']}:section-{index}", "section": heading, "text": body})
    return chunks


def retrieve(question: str, *, root: Path = ROOT, k: int = 3) -> dict:
    if type(question) is not str or not question.strip() or type(k) is not int or not 1 <= k <= 8:
        raise ValueError("Invalid retrieval request")
    wanted = set(tokens(question))
    scored = []
    for chunk in load_corpus(root):
        heading_terms = set(tokens(chunk["section"]))
        body_terms = set(tokens(chunk["text"]))
        overlap = wanted & (heading_terms | body_terms)
        score = 3 * len(wanted & heading_terms) + len(overlap)
        if len(overlap) >= 2 and score > 0:
            scored.append((score, chunk["source_id"], chunk["section_id"], chunk))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    hits = []
    for score, _, _, chunk in scored[:k]:
        hits.append({"source_id": chunk["source_id"], "title": chunk["title"], "issuer": chunk["issuer"], "version": chunk["version"], "date": chunk["date"], "url": chunk["url"], "document_sha256": chunk["document_sha256"], "section_id": chunk["section_id"], "section": chunk["section"], "excerpt": chunk["text"][:500], "score": score})
    return {"mode": "B1_LEXICAL_SECTION", "status": "evidence_found" if hits else "abstain", "question": question, "hits": hits, "answer_generated": False, "corpus_documents": 4}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(retrieve(args.question, k=args.k), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
