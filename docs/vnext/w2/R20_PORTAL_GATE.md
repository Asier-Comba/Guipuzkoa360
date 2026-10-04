# R20 portal preparation blocked — no real-agent acceptance

Runtime tested offline: `81c42da2e8ab7074074d9f114d4ac7990e715da4`.
ZIP `9a271888b414168d06d92dad1b9a9ee594ee0209f78f0abee8d85925cdb6e33e`,
240004 bytes. Manifest
`0362aa249756275f6377cf9b3d3e4859f1f01ad856e0e5663e5cc12150030081`.

## Exact observed blocker

Studio preparation of `agentes/gipuzkoa_360_2/main.py` rejected the twelve
distinct public tools before version creation:

> ValueError: Cada agente admite hasta 10 tools con nombres únicos.

The visible traceback identifies `/opt/studio/runtime_entry.py`, lines461/458,
`_discover_agent`/`captured_tools`. This is a platform compatibility blocker,
not a numeric-engine error, not the historical R19 transport incident and not
an LLM evaluation. Deployment severity: High1. Real-agent Critical/High/Medium
are NOT_EVALUATED, rather than a misleading0/0/0.

Evidence: `outputs/r20/portal/preparation-tool-limit-fail-dom.txt` and
`preparation-tool-limit-fail.png`. Main/tools were copied into a separate new
private draft, clipboard-read back and byte-identical to the frozen files.
`source-readback.json` records both digests. Older agents/versions were not
edited. The new draft remains saved; no version was created, no real user
message sent. No final selection, confirmation, merge or publication.

## What is green, and what is not

Both exact-runtime-SHA CI workflows are COMPLETED/SUCCESS:

- [R20 validation37046444655](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37046444655)
- [Release fast CI37046444701](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37046444701)

Each operating system freshly ran763 Python tests and17 Node tests. R20
validation separately confirms raw parity660/660, unchanged oracle7/7,
eleven metamorphic properties,200 negative cases,5000 malformed-boundary
fuzz calls, no offline findings, identity before/after, jury/artifact gates
and two builds with the exact hashes above. Local encoding/verifier attempts
remain preserved in R20_ATTEMPTS; they are not retrospectively called clean.

The seven targeted real gates and24 general messages are NOT_RUN. Their
frozen protocol/corpus remain unchanged. No served schema success, natural
language accuracy, recovery success or public sanitary conversation claimed.
No presentation created and no Delivery polish performed: those steps are
conditional on a complete real C0/H0/M0 acceptance.

## Narrow decision needed

All three separate scenario actions and both access scopes are explicit user
requirements. Returning to a generic optional-field simulation, using empty
lists as all-territory selectors, hiding callable tools from discovery, or
removing two supported capabilities would violate that intent. Maintaining
all current callable contracts needs12 slots; Studio offers10.

A new10-tool surface must explicitly consolidate other responsibilities and
freeze a new protocol/ZIP/SHA before CI and real acceptance. Such a choice
changes public contracts. R21 has not been used: the mission's contingency
is conditioned on a new real C/H/M with a demonstrably small defect-specific
fix; there has been no real version/model execution here. Obtain direction
for this platform-driven consolidation, rather than silently broadening the
authorized contingency. Do not change W1 datasets, mathematics or v4.

FINAL_PROJECT_STATE=BLOCKED
AGENT_ENGINEERING_COMPLETE=NO
READY_FOR_HUMAN_FINAL_GATE=NO
RELEASE_GO=NO
HOLDOUT=SEALED_NOT_EXECUTED
MAIN_UNCHANGED=YES
FINAL_CONFIRMATION=PENDING_HUMAN
PUBLICATION=PENDING_HUMAN
