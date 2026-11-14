---
lab5_triage:
  image: ghcr.io/szymonsalamacha3-dotcom/itsm-svcdesk@sha256:61f50d349cb3f80ef302dd1008fa017caccb05cd890f342a1007ac0da16c91ee
  sarif_receipt: 385
---
<!-- ai-generated: 100% - OpenAI Copilot drafted this evidence-based triage and bake-off from receipt 385, its SARIF reports and labels -->
# Triage

This triage records the seven HIGH findings from image job run `43595006790` and every non-canary tool/rule pair
in SARIF receipt `385`. Of the receipted results, only the two Semgrep pairs on this repository's `Dockerfile` and
`src/persistence.py` are outside `lab5-canary/`; the remaining SARIF results target the canary set and are scored
in the Bake-off below.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | CVE-2026-76844 | fix | CI found `zlib1g` `1:1.3.dfsg+really1.3.1-1+b1`; Dockerfile:6-8 installs Debian's fixed `1:1.3.dfsg+really1.3.1-1+deb13u1`, and the local pinned Trivy image scan is clean. |
| trivy | CVE-2026-85091 | fix | The same `zlib1g` update in Dockerfile:6-8 replaces the affected base package; the final local image scan reports zero Debian vulnerabilities. |
| trivy | CVE-2026-114613 | fix | CI found pip-vendored `msgpack` 1.1.2 (Trivy fix: 1.2.3); Dockerfile:11-12 removes build-only pip and its vendor tree after installation, and the final scan reports no finding. |
| trivy | GHSA-6v7p-g79w-8964 | fix | Trivy listed `msgpack` 1.2.1 as fixed; Dockerfile:11-12 instead removes the pip-vendored 1.1.2 copy, absent from the scanned runtime image. |
| trivy | CVE-2025-47273 | fix | CI traced setuptools/pkg_resources 70.3.0 to base-image pip (Trivy fix: 78.1.1); Dockerfile:11-12 removes pip, leaving no vendor tree or Trivy finding. |
| trivy | CVE-2026-97687 | fix | CI found pip-vendored `urllib3` 2.7.0 (Trivy fix: 2.8.0); Dockerfile:11-12 removes pip and its vendor tree, and the final image scan is clean. |
| trivy | CVE-2026-97689 | fix | Trivy listed `urllib3` 2.8.0 as fixed; Dockerfile:11-12 removes the pip-vendored 2.7.0 copy, and no Python package vulnerabilities remain in the scan. |
| semgrep | dockerfile.security.missing-user.missing-user | accept | The receipted alert is at `Dockerfile:22`; no `USER` is declared, so the service runs as root. Accept this hardening risk until 2026-12-14 because non-root ownership of the `/data` volume has not been validated. |
| semgrep | python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query | false-positive | The alert at `src/persistence.py:159` is false: only fixed `state = ?` and `priority = ?` clauses are joined; request values are bound through placeholders and `tuple(parameters)`. |

## Image remediation evidence

The remediated local image reports `zlib1g` `1:1.3.dfsg+really1.3.1-1+deb13u1`; pip and its vendor directory are
absent, and FastAPI, Uvicorn, and HTTPX imports succeed. A Docker archive of that image passed the pipeline-pinned
Trivy 0.74.0 scan with `.github/actions/image/trivy.yaml`, `.trivyignore`, and
`--scanners vuln --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`: zero vulnerabilities were reported
for Debian 13.7 and all Python package targets. No vulnerability ignores were added. This is local remediation
evidence; the front-matter digest is the supplied GHCR image digest.

## Bake-off

On the nine labeled canary defects, ai-reviewer scored 9 TP, 1 FP and 0 FN (precision 0.9000, recall 1.0000,
F1 0.9474), the strongest result here. It found all five defects none of the conventional scanners found:
path traversal in `attachment_read.py`, missing ticket ownership in `ticket_access.py`, webhook SSRF in
`webhook_relay.py`, and the JWT and SMTP secrets in `jwt_secret.py` and `mailer.py`. Its extra weak-crypto alert
for the 512-bit key at `signing_key.py:2-10` was an FP under the supplied labels, which classify that seeded
finding as `secret`, not `weak-crypto`; the perfect recall therefore depends on the published matching classes.
Gitleaks scored 1 TP, 1 FP and 8 FN (precision 0.5000, recall 0.1111, F1 0.1818), finding the private signing
key. Grype and OSV-Scanner each scored 2 TP, 0 FP and 7 FN (precision 1.0000, recall 0.2222, F1 0.3636); both
detected the same Jinja2 and Requests pins, so their agreement adds confidence but no distinct coverage.
Semgrep scored 2 TP, 2 FP and 7 FN (precision 0.5000, recall 0.2222, F1 0.3077), detecting the
TLS-verification defect and signing-key secret, while Trivy scored 3 TP, 1 FP and 6 FN (precision 0.7500,
recall 0.3333, F1 0.4615), detecting both vulnerable pins and the signing-key secret. The five
conventional scanners thus complement one another but still miss several application authorization, traversal,
SSRF and credential defects. Keep the existing narrowly scoped Trivy dependency/image and Gitleaks secret gates;
do not make Semgrep or AI review a blocking gate from this small sample, and keep Grype/OSV-Scanner as
reporting detectors. This seeded set has only nine recognizable defects and deliberately includes decoys: a
single match shifts recall by 1/9, false positives heavily affect precision, and the matrix has no true-negative
count. Scores describe this set and its exact path/class/package matching rules, not expected production
performance; they are an upper bound on what these detectors might find in less curated code.
