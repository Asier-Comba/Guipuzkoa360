# Preserved verifier attempts, not candidate defects

initial-verifier.json records489 raw matches and7 oracle passes but16 findings
comparing totals/provenance of invalid/no-data model projections after their
deliberate suppression. Raw execution did not drift. The corrected comparison
preserves status/error/outcomes/raw identity for every case, compares analytical
projection only for valid cases and requires no invalid partial evidence.
Second full bounded author audit:489/489 raw,7/7oracle,no findings.

A separate initial AST-only unit probe failed with NameError: Any is not defined
when compiling the extracted annotated function without its typing namespace.
The corrected probe included typing.Any and reproduced baseline units:
within_threshold_count=registros; outside_threshold_count=registros;
registered_service_count=registros; total_result_rows=conteo;
returned_rows=conteo; difference_relative_pct=conteo.
That NameError was a probe defect, not the candidate or original runtime.

After the second author matrix was dispatched, development corpus adversarial
variants were expanded (prediction, fabricated source, ignore tools, households,
zero registry). The count stays156 but SHA changes. Therefore a SEPARATE fresh
156-case audit is bound to the final corpus SHA; the earlier report does not
claim evaluation of that extension. No model responses informed the extension,
sample selection was still before any portal message, and no runtime changed.
Local complete suite was run once; exact-SHA CI checks fresh sources/corpus.
# Remote regeneration gate — dc18e448

Run 36997013100 approved 709 Python tests, Node, 489/489 raw parity,
7 oracle cases and runtime identity on Ubuntu and Windows. Its final
regeneration gate failed because the committed development corpus and
real protocol still contained the earlier generator output. No portal
response had been collected. Regenerating these two evidence files from
the committed generator restores corpus c98ab497aed72b2b18c63f7c652d4c220a156e9846cb9b7aa9393f807ffd81e4.
The agent ZIP and manifest are byte-identical; no runtime patch is involved.
The new commit requires its own green remote gate before portal evaluation.
