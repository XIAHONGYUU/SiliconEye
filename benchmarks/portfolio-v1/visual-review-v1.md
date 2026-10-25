FAIL

| ID | Severity | Category | Location | Observed | Expected | Evidence | Confidence | Suggested correction |
|---|---|---|---|---|---|---|---|---|
| NAV-01 | P1 | Exact content / interaction | case hash navigation | Loading another case hash in an already open document retains the previous panel | URL case and visible panel correspond | Playwright direct-case assertion failed; initial load and button toggles work | high | Handle hashchange and repeat the browser check |

| Gate | Status | Evidence or missing input |
|---|---|---|
| Artifact integrity | PASS | visual-probe.json SHA; browser renders HTML and assets |
| Exact content | FAIL | NAV-01; candidate/reviewed wording matches frozen inputs |
| Technical relationships | PASS | source-based five-layer geometry and original device schematic; no new connectivity claims |
| Typography and layout | PASS | desktop 1440x1000 and mobile 390x844 screenshots; no horizontal overflow |
| Readability | PASS | full page and critical devices/via views inspected at delivery scale |
| Reference isolation | NOT VERIFIED | no prior portfolio visual is locked; original evidence remains hash-verified |
| Provenance and release | PASS | site/provenance.json identifies fa3e1c7 source baseline; no raster patch chain |

Blocking defect: NAV-01. No full-chip or physical DRC validation is claimed. This audit ends here; fix is handled under the user's separately authorized implementation task, then run a new audit.
