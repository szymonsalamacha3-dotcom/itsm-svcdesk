---
lab4_comms:
  awareness: "2026-10-12T05:06:56Z"
  detection: "2026-10-12T05:06:19Z"
  classification: "2026-10-12T05:07:15Z"
  nis2:
    early_warning_due: "2026-10-13T05:06:56Z"
    notification_due: "2026-10-15T05:06:56Z"
    notification_sent: "2026-10-12T06:00:00Z"
    final_report_due: "2026-11-12T06:00:00Z"
  ksc:
    early_warning_due: "2026-10-13T05:06:19Z"
    notification_due: "2026-10-15T05:06:19Z"
    notification_sent: "2026-10-12T06:00:00Z"
    final_report_due: "2026-11-12T06:00:00Z"
  dora:
    initial_due: "2026-10-12T09:07:15Z"
    initial_sent: "2026-10-12T05:30:00Z"
    intermediate_due: "2026-10-15T05:30:00Z"
    intermediate_sent: "2026-10-14T09:00:00Z"
    final_due: "2026-11-14T09:00:00Z"
  log:
    - {at: "2026-10-12T05:30:00Z", to: "financial supervisor", what: "DORA initial major ICT incident notification"}
    - {at: "2026-10-12T06:00:00Z", to: "national CSIRT", what: "NIS2 and KSC incident notification"}
    - {at: "2026-10-14T09:00:00Z", to: "financial supervisor", what: "DORA intermediate report with updated impact and remediation"}
---
<!-- ai-generated: 90% - Copilot calculated the UTC regulator deadlines and drafted this log from the official template -->

# Communications log: the regulators' clocks

## The three instants you defend

I treat awareness under NIS2 as 05:06:56Z, when the on-call acknowledged the P1 ticket and had both a confirmed page and a recorded user-impact symptom. KSC detection is the first firing sample of `ShopCheckoutSlow`, 05:06:19Z. The incident is classified as major for DORA at 05:07:15Z, after the ticket is acknowledged and checkout p99 latency is confirmed at 8.8 seconds. These are the timestamps in the incident record and the recorded telemetry; the classification is a documented operational decision rather than a timestamp emitted by Prometheus.

## The log

The DORA initial notification is sent at 05:30Z, before the 09:07:15Z due time. The joint NIS2/KSC notification is sent to the national CSIRT at 06:00Z, before both regimes' notification deadlines. The DORA intermediate report is sent on 14 October at 09:00Z, before its 15 October 05:30Z deadline. The final reports are scheduled one UTC calendar month after their corresponding submitted notifications.
