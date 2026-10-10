---
lab3_first_draft:
 source: ai
 tool: "GitHub Copilot Chat, model name not exposed, 2026-10-10"
 ladder: [0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10]
 verdict: refuted
 evidence: {p99_seconds: 0.1862, bucket: [0.1, 0.2], relative_width: 0.537}
lab3_flawed_ladder:
 verdict: refuted
 evidence: {p99_seconds: 0.1862, bucket: [0.04, 0.5], relative_width: 2.470}
---
<!-- ai-generated: 25% - Copilot supplied the first-draft proposal; the verdict arithmetic below uses recorded checker output -->

# The assistant's first draft, and two verdicts

## Prompt

Prepare an initial, unmeasured first draft for monitoring a FastAPI endpoint `GET /kb/search` that calls an upstream dependency named `kb-index` on every request.

Propose:
1. A Prometheus histogram bucket ladder with finite boundaries in seconds, in ascending order, using no more than 30 boundaries.
2. One candidate Prometheus alerting rule for elevated latency of `GET /kb/search`.

Use the metric name `http_server_request_duration_seconds` and the route template `/kb/search` in your proposal where appropriate.

Format your response as follows:
- First, a single line in exactly this format: `LADDER_SECONDS: 0.1, 0.2, 0.3, ...` with your actual proposed numerical boundaries.
- Second, a YAML code block containing the proposed alert rule, including its name, expression, duration, labels and annotations.
- Third, a brief explanation of your choices.

Do not claim that the boundaries or alert have been measured or validated. Do not ask me to run measurements. Do not edit any files. This is a preliminary hypothesis that will be evaluated against real measurements later.

## Answer

LADDER_SECONDS: 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10

```yaml
- alert: KbSearchElevatedLatency
 expr: histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{method="GET", route="/kb/search"}[5m]))) > 0.5
 for: 10m
 labels:
    severity: warning
 annotations:
    summary: "Elevated latency for GET /kb/search"
    description: "The 5-minute p95 request latency has exceeded 0.5 seconds for 10 minutes."
```

## Verdict on the draft ladder

The first-draft run measured q = 0.1862 s. It falls in (0.1, 0.2], a 0.1 s bucket; 0.1 / 0.1862 = 0.537, or 53.7% of q, well above the M-11 limit of 0.20 x q. At 0.95q, q and 1.05q the result remains in that same bucket, so the verdict is refuted. The histogram's measured p99 estimate in that run was 0.1667 s; linear interpolation can place an estimate anywhere within the coarse (0.1, 0.2] bucket.

## The draft alert rule

The proposed alert estimates p95 latency and fires when it exceeds 0.5 s for 10 minutes. I kept its route and method scoping as a useful pattern, but did not adopt its single latency threshold: the course requires multiwindow burn alerts tied to declared SLOs, so the implemented rules alert on availability-budget burn instead.

## Verdict on the instructor's flawed ladder

For the same measured q = 0.1862 s, the flawed ladder places it in (0.04, 0.5], whose width is 0.46 s; 0.46 / 0.1862 = 2.470, or 247.0% of q. The bucket is far wider than the 0.20 x q limit, and 0.95q, q and 1.05q all remain in it, so the verdict is refuted. Without counts for this hypothetical ladder, histogram_quantile could interpolate anywhere inside (0.04, 0.5] s; that span does not give a useful estimate near q.
