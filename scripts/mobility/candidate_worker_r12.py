"""Cold subprocess worker. Candidate code is loaded unchanged from its extraction."""
from __future__ import annotations

import importlib
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    config = json.load(sys.stdin)
    root = Path(config["root"]).resolve()
    # -I ignores PYTHONPATH/user site; only this explicit package root is added.
    sys.path.insert(0, str(root))
    report = {"python": sys.version, "cwd": str(Path.cwd()), "root": str(root),
              "configured_root": os.environ.get("GIPUZKOA360_VNEXT_ROOT"),
              "isolated": bool(sys.flags.isolated), "records": []}
    stage = "bootstrap"
    roots = []
    caught = []

    def offline(event, args):
        if event in {"socket.connect", "socket.getaddrinfo"}:
            raise RuntimeError("R12 offline worker: network disabled")

    sys.addaudithook(offline)

    def profile(frame, event, arg):
        if event == "return" and frame.f_code.co_name == "_workspace_root":
            # A profiler also emits return(None) when an exception unwinds.
            # Record the actual attempted local root, not a fictitious "None" path.
            selected = arg if arg is not None else frame.f_locals.get("candidate")
            if selected is not None:
                roots.append({"stage": stage, "function": "_workspace_root", "root": str(selected),
                              "resolution": "returned" if arg is not None else "rejected"})
        if event == "call" and frame.f_code.co_name in {"_catalog", "_registry", "validate_evidence", "_ensure_w1_runtime"}:
            value = frame.f_locals.get("root")
            if value is not None:
                row = {"stage": stage, "function": frame.f_code.co_name, "root": str(value)}
                if row not in roots:
                    roots.append(row)

    def trace(frame, event, arg):
        if frame.f_code.co_name not in {"_execute_mobility", "public_result", "_mobility_view", "_validate_result", "consume_plan_visit"}:
            return None
        if event == "exception" and frame.f_code.co_name in {"_execute_mobility", "public_result", "_mobility_view", "_validate_result", "consume_plan_visit"}:
            kind, value, tb = arg
            if kind not in {StopIteration, GeneratorExit} and len(caught) < 30:
                caught.append({"stage": stage, "function": frame.f_code.co_name,
                               "traceback": "".join(traceback.format_exception(kind, value, tb))})
        return trace

    try:
        if config["mode"] == "oracle":
            from prototypes.ir_y_volver import provider_r6
            snapshot = json.loads((root / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json").read_text(encoding="utf-8"))
            label_bytes = (root / "datos_preparados/movilidad/consumer_labels_r7.json").read_bytes()
            if hashlib.sha256(label_bytes).hexdigest() != "f0804b646d0473531e4f9ad12e31dc1ee7ee50cab69576bc95a0485b8da62799":
                raise ValueError("oracle label catalog hash mismatch")
            catalog = json.loads(label_bytes)
            report["labels"] = {"stops": {key: value["name"] for key, value in snapshot["stops"].items()},
                                "routes": {row["route_id"]: row["short_name"] for row in catalog["routes"]}}
            for case in config["cases"]:
                try:
                    raw = provider_r6.plan_visit(case["request"]) if case["operation"] == "plan" else provider_r6.compare_visits(case["requests"])
                    report["records"].append({"case_id": case["case_id"], "raw": raw})
                except Exception:
                    report["records"].append({"case_id": case["case_id"], "error_stage": "oracle", "traceback": traceback.format_exc()})
        else:
            tools = importlib.import_module("tools")
            sys.setprofile(profile)
            sys.settrace(trace)
            for case in config["cases"]:
                roots.clear()
                caught.clear()
                item = {"case_id": case["case_id"], "invocation": {"tool": "plan_visit", "arguments": {"request": case.get("request", case.get("requests"))},
                        "execute_root_argument": str(root) if config.get("pass_root", True) else None}}
                try:
                    stage = "execute"
                    envelope = tools.execute("plan_visit", item["invocation"]["arguments"], "R12_" + case["case_id"],
                                             **({"root": root} if config.get("pass_root", True) else {}))
                    item["envelope"] = envelope
                    stage = "public_result"
                    rendered = tools.public_result(envelope)
                    item["public_output"] = rendered
                    item["view"] = json.loads(rendered, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
                except Exception:
                    item.update(error_stage=stage, traceback=traceback.format_exc())
                item["roots_observed"] = list(roots)
                item["caught_exceptions"] = list(caught)
                report["records"].append(item)
            sys.setprofile(None)
            sys.settrace(None)
    except Exception:
        report.update(error_stage=stage, traceback=traceback.format_exc())
    report["imports"] = {name: str(getattr(module, "__file__", "embedded")) for name, module in sys.modules.items()
                         if name in {"tools", "mobility_adapter", "health_adapter"} or name == "prototypes" or name.startswith("prototypes.")}
    report["import_sha256"] = {name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                               for name, path in report["imports"].items() if Path(path).is_file()}
    print(json.dumps(report, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
