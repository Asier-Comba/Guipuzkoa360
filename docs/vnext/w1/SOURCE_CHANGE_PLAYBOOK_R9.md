# Source change playbook R9

Ningún drift sustituye un pin silenciosamente.

| Caso | Qué hacer | Qué no hacer | Owner | Rebuild | Evidencia histórica | Repetir W2/W3 | Aprobación humana |
|---|---|---|---|---|---|---|---|
| GTFS upstream unchanged | Keep pin; record observation. | Do not refresh timestamps. | W1 | No | Yes | No | No |
| GTFS bytes changed, used rows same | Record semantic equivalence and preserve pin. | Do not claim the whole source is unchanged. | W1 | No | Yes | No | No |
| GTFS used rows changed | Raise human review; assess a new dated candidate. | Do not replace the pin silently. | W1 + release owner | Decision required | Yes | Yes if adopted | Yes |
| Health centre coordinates changed | Verify primary source and impact before any new snapshot. | Do not move anchor automatically. | W1 + human reviewer | Decision required | Yes | Yes if adopted | Yes |
| Health address changed | Retain conflict and investigate entity/site continuity. | Do not infer relocation. | W1 + human reviewer | Not automatically | Yes | If wording changes | Yes |
| PADI conflict resolved | Verify document/version and close conflict only in a new candidate. | Do not rewrite historical evidence. | W1 + human reviewer | Only for new candidate | Yes | If adopted | Yes |
| OSM topology changed | Record current observation; assess routes separately. | Do not rebuild the pinned model automatically. | W1 | Decision required | Yes | If adopted | Yes |
| Source unavailable | Record exact HTTP/fetch status and retain pin. | Do not say the network is down or data absent globally. | W1 | No | Yes | No | If prolonged |
| License terms changed | Freeze distribution and obtain human/legal review. | Do not delete history or relicense data. | Release owner | No runtime rebuild | Yes | Package review | Yes |
| License ambiguous | Use reference/hash-only or exclude from bundle pending review. | Do not infer permission. | Release owner | No | Yes | Package review | Yes |
