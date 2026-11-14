---
lab5_triage:
  image: PENDING_MAIN_CI_IMAGE_DIGEST
  sarif_receipt: 0
---
<!-- ai-generated: 100% - OpenAI Copilot prepared the official template and practice-only reasoning; evidence fields are intentionally pending -->
# Triage

This file is prepared from the official Lab 5 template. No pipeline scanner SARIF, image digest, attestation, or
SARIF receipt has been produced in this phase. The rows below record only the findings printed by the local,
custom P-31 Semgrep scan; they are not claims about the pipeline's `p/default` scan. Add the actual tool/rule rows
from the finished CI run and receipted SARIF when that evidence exists; do not substitute practice-set findings.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| semgrep | semgrep.broad-exception-handler | accept | Both matches in `src/main.py` wrap only JSON parsing and preserve the existing 400 response for malformed bodies; narrow the catches during the next request-error refactor. |
| semgrep | semgrep.assume-utc-for-naive-time | accept | `src/service.py` keeps treating legacy naive timestamps as UTC for compatibility; request test clocks already require an explicit zone, and this policy should be revisited with any data migration. |
| semgrep | semgrep.deprecated-fastapi-startup-hook | accept | `src/main.py` still uses FastAPI's supported but deprecated startup event; retain current startup behavior for this phase and migrate initialization to lifespan before the next framework upgrade. |

## Bake-off

The published practice matrix is a calibration example, not a result for this repository or for a canary. On that
set, the AI-reviewer matched 6 of 9 labelled defects, with 3 false positives and 3 false negatives
(precision 0.6667, recall 0.6667, F1 0.6667). Semgrep matched 5, produced 2 false positives and missed 4
(precision 0.7143, recall 0.5556, F1 0.6250); its SHA-1 alert was useful on a password hash but was also reported
on a benign e-mail fingerprint, an instructive precision cost. Trivy matched 3 with no false positives, but missed
6 (precision 1.0000, recall 0.3333, F1 0.5000). Gitleaks, Grype and OSV-Scanner each matched 2 with no false
positives and missed 7 (precision 1.0000, recall 0.2222, F1 0.3636). Those results support keeping narrow,
high-confidence checks such as the secret and dependency gates, while treating Semgrep as a useful reporting
detector whose alerts need review rather than assuming it is a complete blocker. No one tool found all defect
classes: code weaknesses, credentials and vulnerable package pins require different signals, and duplicated OSV
results do not add recall. The injected practice defects are intentionally recognizable and therefore flatter
detectors; these recall values are an upper bound, not a forecast of real-world detection. I will replace this
practice-only comparison with the measured canary matrix after its SARIF receipt and labels are available, then
revisit the gate recommendation using those numbers rather than extrapolating them.
