---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.995
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.005, minutes: 216}
    latency:
      objective: 0.99
      threshold_seconds: 0.21
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.21"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
  alerts:
    - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 70% - Copilot drafted SLO rationale from checker measurements; objectives, budgets and queries follow the Lab 3 specification -->

# SLO for `GET /kb/search`

## Availability

Availability is the share of `/kb/search` responses that are not 5xx, with a 99.5% objective over 30 days. Its 0.5% error budget is 216 minutes. The measured run returned 4 upstream-derived 502s among 2,399 responses (about 0.17%); because `kb-index` owns that failure probability and this service cannot repair those failures, 99.5% leaves operational headroom without treating every isolated index error as an SLO breach.

## Latency

Latency is the share of requests completed within 0.21 seconds, with a 99% objective and a 1% budget of 432 minutes per 30 days. The final run measured p50 32.8 ms, p95 59.6 ms, p99 176.2 ms and p99.9 194.5 ms; the earlier draft run's p99.9 was 211.5 ms. A 210 ms threshold is a finite histogram boundary just above the measured p99 range and near the slow tail, allowing some run-to-run variation while still flagging sustained tail expansion.

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---|---|---|---|
| KbSearchErrorsBurnFast | availability | 14.4 | 1h / 5m | 7.2% bad requests; budget consumed in about 50 hours | P1 page |
| KbSearchErrorsBurnSlow | availability | 6 | 6h / 30m | 3% bad requests; budget consumed in 5 days | P2 chat |

The fast alert pages because a 14.4x burn exhausts the budget in roughly two days; waiting for office hours risks a prolonged search outage. The slower 6x alert goes to chat because it indicates a serious but less immediate burn, leaving time for investigation without waking someone for a less urgent signal.

## Buckets

The 30-boundary ladder places the final p99 of 176.2 ms in (0.17, 0.18], a 10 ms bucket or 5.7% of q. The ±10% band is 158.6-193.8 ms; the bucket intersecting its lower edge is 20 ms wide, and the remaining buckets through 0.20 seconds are 10 ms wide. All are narrower than 20% of the band's 158.6 ms lower edge. The remaining boundaries cover the fast response bulk and progressively wider long-tail intervals. The 0.21 s latency threshold is itself a finite boundary.
