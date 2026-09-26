---
# ai-generated: 95% - Lab 2 edge-case write-up for the published DORA rulebook
lab2_edge_cases:
  E1:
    rule: R-08
    count: 3
  E2:
    rule: R-06
    count: 2
  E3:
    rule: R-09
    count: 4
  E4:
    rule: R-10
    count: 4
  E5:
    rule: R-12
    count: 1
  E6:
    rule: R-13
    count: 11
---

# Lab 2 edge cases

## E1
- What the log contains: A negative lead time is present because one commit has an earlier timestamp than the deployment that carried it, and the spec clamps that pair to zero while recording the anomaly.
- What a default definition would have done: A casual interpretation would discard the pair or silently treat it as a missing observation, which would understate delay and hide the clock-skew problem.
- Why the rule is defensible: The rule keeps the affected work in the distribution, records the anomaly count, and treats clock drift as a real operational condition rather than a missing-in-action artifact.

## E2
- What the log contains: The log includes revert commits that inherit the original change_id, so the change population is collapsed back to the original work item instead of being treated as a separate change.
- What a default definition would have done: A simplistic model would count every revert lineage as a new change and overstate instability, especially when a revert is only the correction of a prior feature delivery.
- Why the rule is defensible: The published rule ties the revert to the original change, which preserves the unit of work and keeps the metric aligned with actual production impact.

## E3
- What the log contains: Several production changes were carried on branches other than main and are still counted as valid delivery work because branch name is intentionally irrelevant to lead-time accounting.
- What a default definition would have done: A branch-centric policy would incorrectly exclude hotfixes and unmerged work, creating a false picture of delivery quality and making operational reality look cleaner than it is.
- Why the rule is defensible: The specification explicitly ignores branch names, so the metric reflects what reached production rather than where it was developed.

## E4
- What the log contains: Some production deployments carried no commit list at all, which remains a valid deployment event even though it contributes no lead-time pair.
- What a default definition would have done: A stricter interpretation would drop empty deployments or treat them as invalid, thereby undercounting deployed work and distorting service volume and failure-rate denominators.
- Why the rule is defensible: The rule counts the deployment in throughput and instability metrics without inventing a commit to anchor a delivery that never carried one.

## E5
- What the log contains: At least one failed production deployment has no covering resolved incident, so it is counted as an open failure and excluded from the recovery-time median.
- What a default definition would have done: A naive algorithm would fabricate a recovery timestamp or pretend every failure was recovered, which would make the service look more stable than the incident record supports.
- Why the rule is defensible: The metric measures recoveries that actually happened, while an open failure is still counted in the failure rate but remains explicitly outside the recovery-time distribution.

## E6
- What the log contains: Multiple incidents overlap in time, each covering the same failed deployment set or sharing a common interval, yet the spec still computes recovery per failed deployment rather than per incident.
- What a default definition would have done: A merged-incident approach would collapse overlapping intervals and change the count of overlapped incidents, masking operational concurrency and the effects of repeated failure windows.
- Why the rule is defensible: Recovery is bounded to the failed deployment and the incident intervals are only used to count the overlap anomaly, preserving both the deployment-level and incident-level views without conflating them.
