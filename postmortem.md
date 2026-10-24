---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: "2026-10-12T05:01:00Z"
  detection: "2026-10-12T05:06:19Z"
  acknowledgement: "2026-10-12T05:06:56Z"
  recovery: "2026-10-12T05:08:19Z"
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [adFailure, intlShippingSlowdown]
---
<!-- ai-generated: 90% - Copilot drafted this postmortem from the official template and verified the claims against the snapshot -->

# Postmortem: Checkout latency with concurrent ad failures

## Date

The incident occurred on 12 October 2026. This postmortem was prepared on 24 October 2026 from the assigned recorded snapshot and ticket.

## Authors

Prepared by Szymon Salamacha, acting as the on-call investigator, with Copilot assistance for PromQL checks and documentation.

## Status

Incident service recovery is recorded and ticket ITSM id 3ba75e92-1b55-483b-a69e-6097c02b182c is the incident record. Follow-up work remains open under the action-item IDs below.

## Summary

Checkout requests experienced a severe latency tail and the ad service returned errors. The detecting checkout alert fired at 05:06:19Z and its first firing run ended at 05:08:19Z; the aggregate fault-active signal remained set beyond that alert recovery.

## Impact

At 05:06:19Z, checkout server-span p99 was 8,800 ms, compared with 49.6 ms at 04:56:00Z. Query: `histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_kind="SPAN_KIND_SERVER"}[5m])))`. Shipping server-span p99 was 7,700 ms at 05:06:19Z versus 5.28 ms at 04:56:00Z using the same query filtered to `service_name="shipping"`. Ad server errors were 0.00833 calls/s at detection and the comparison query returned no series at baseline: `sum(rate(traces_span_metrics_calls_total{service_name="ad",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m]))`. The artifact supports markedly slower checkout/shipping and ad failures; it does not provide a reliable total of unique affected customers or orders.

## Root Causes

The service-level evidence and the published flag-to-service mapping support `intlShippingSlowdown`: shipping p99 rose from 5.28 ms to 7,700 ms, while checkout p99 rose from 49.6 ms to 8,800 ms. Ad server errors rose from no returned series at baseline to 0.00833 errors/s at detection, consistent with `adFailure`. The telemetry does not expose flag names or variants directly; these are evidence-based identifications, not direct readings of flag state. No third flag is claimed without comparable evidence.

## Trigger

The aggregate `seeded_fault_active` series first appeared at 2026-10-12T05:01:00Z, which is the recorded onset. The incident combined the unusually slow shipping/checkout path with ad server errors; the snapshot does not expose the individual flag-switch events or their order.

## Resolution

The detecting alert's first firing run ended at 05:08:19Z. The aggregate `seeded_fault_active` query is 1 at 05:10:00Z and 0 by 05:10:30Z, so the fault ended after the alert recovery. The recording contains no per-flag rollback requests or switch-off ordering; this report therefore does not invent which flag was changed first or an exact operator action.

## Detection

`ShopCheckoutSlow` detected the checkout latency symptom 319 seconds after onset. The P1 ticket was acknowledged 37 seconds after detection. Without the page, the recorded evidence offers no earlier human report; affected shop users or support would likely have been the next signal, but no such report is present in the artifacts.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a dashboard panel for checkout and shipping p95/p99 latency alongside ad server error rate | mitigate | SRE on-call | ITSM-4-01 |
| Document and rehearse a flag rollback runbook that records each flag and change timestamp | process | Shop operations | ITSM-4-02 |
| Add a post-incident check that verifies the aggregate fault signal is inactive after alert recovery | prevent | Observability team | ITSM-4-03 |

## Lessons Learned

### What went well

The page was tied to a user-facing checkout symptom, the P1 ticket was acknowledged quickly, and the snapshot preserves timestamps and service telemetry for independent recomputation.

### What went wrong

Checkout latency recovered before the aggregate fault signal cleared, so treating alert recovery as proof that all injected faults ended would have been misleading. The recording also lacks individual flag rollback events.

### Where we got lucky

The snapshot includes both span latency and error metrics, allowing the shipping delay and ad failures to be distinguished without relying on the opaque sealed fault data.

## Timeline

- 05:01:00 UTC — `seeded_fault_active` first appears; recorded incident onset.
- 05:06:19 UTC — `ShopCheckoutSlow` starts its first firing run; MTTD is 319 seconds.
- 05:06:36 UTC — the P1 ticket is created, as recorded in `incident/ticket.json`.
- 05:06:56 UTC — the ticket is acknowledged; MTTA from detection is 37 seconds.
- 05:08:19 UTC — the detecting alert's firing run ends; MTTR from onset is 439 seconds.
- 05:10:00–05:10:30 UTC — the aggregate fault-active signal changes from 1 to 0 between these recorded query samples; individual flag changes are not exposed.

## Supporting information

The timestamps and clocks are the `itsmlab incident 4` recomputation. The impact queries above were evaluated on the served recording at 2026-10-12T04:56:00Z and 2026-10-12T05:06:19Z, never at the present time. The original recorded investigator is preserved in `ai-rca/transcript.md`; its hypotheses are quoted and scored in `ai-rca-eval.json`. A separate investigator transcript and comparison are in `ai-rca/second/transcript.md` and `ai-rca/COMPARISON.md`. Neither transcript's unverified hypothesis was used as an operational action.

## Problem record

- Incident record: 3ba75e92-1b55-483b-a69e-6097c02b182c
- Root cause: Shipping latency and ad server failures coincide with the checkout impact and fit the published `intlShippingSlowdown` and `adFailure` service mappings.
- Known error: The archived metrics do not identify exact flag variants or preserve individual rollback calls, so the per-flag cause sequence remains unverified.
- Workaround: The recorded incident's aggregate fault signal eventually returned to zero; no unsupported flag-specific workaround or ordering is asserted.
