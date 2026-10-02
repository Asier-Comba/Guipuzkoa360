# R20 retained attempts — verifier failures are not candidate findings

Before any real model call, the first corpus-generation attempt referred to a
nonexistent ZIP member `servicios_sanitarios.csv`. The actual preserved member is
`runtime_servicios.csv`. Corrected the build-only corpus reader; no data changed.

First observer run failed decoding child stdout on Windows (cp1252 vs UTF-8).
The observer now explicitly launches its child with `-X utf8`. No runtime change.

Initial completed audit: raw660/660, oracle7/7, negative200 and fuzz5000 safe,
eleven metamorphic checks passed; overall FAIL on `defaults:omitted` provenance.
The verifier compared a public Python call (signature defaults materialized in
locals) with a direct engine call that omitted them. These are different caller
provenance, despite identical calculations. Correction mirrors the actual public
boundary before independently calling the frozen engine. This is a verifier
defect, not a candidate defect; the original FAIL report is retained, not erased.
Initial focused candidate suite:26/26 PASS. No result transferred to a real agent.

Final local full-suite attempt:757 PASS,5 FAIL,762 total in231.36s; no skipped
tests. All five failures are historical health/recorder subprocess readers:
parent `-X utf8` does not propagate its flag to children; they emitted cp1252
while the parent expected UTF-8. Tracebacks show UnicodeDecodeError and lost
stdout, not incorrect numerical outputs. Original unedited XML is retained in
outputs/r20/attempts/local-full-encoding-fail.xml.zip (original XML preserved
locally too). Only those five
tests are rechecked with inherited PYTHONUTF8=1; do not call that one full local
762PASS run. The R20 CI workflow sets this environment explicitly and must run
the entire suite freshly on the exact frozen SHA on both operating systems.

Target-only encoding recheck:5/5 PASS in32.89s, no candidate change. Recovery
distinction additionally receives an explicit synthetic transport-vs-contract
test before final commit; not presented as a real platform503 reproduction.
Latest focused suite, including that test:27/27 PASS in22.09s. No frozen
runtime bytes changed while correcting the verifier/environment observations.
