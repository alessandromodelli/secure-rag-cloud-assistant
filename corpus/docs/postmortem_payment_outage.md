# Postmortem: Payment Processing Outage, 2024-10-17

**Classification: Confidential — Security and Platform leadership only**

Distribution outside the incident review group requires approval from the
Head of Platform Engineering. This document contains details of a control
failure and of the compensating controls introduced in response.

## Summary

Between 14:22 and 16:48 UTC on 17 October 2024, the payment service was
unable to process transactions. Customer facing impact was a checkout
failure rate of 94% for two hours and twenty six minutes. Approximately
41,000 transactions failed. Revenue impact is estimated at 310,000 EUR.

The proximate cause was the expiry of a database credential that had been
provisioned manually in 2022 and was not tracked by the rotation pipeline.
The contributing cause, and the more important finding, is that the
credential was reachable by a broader set of principals than its
sensitivity warranted, which delayed diagnosis because the on call engineer
could not determine from the audit log which workload had last used it.

## Timeline

14:22 — The payment service begins returning authentication failures from
the primary database. Error rate crosses the alerting threshold within
ninety seconds.

14:24 — On call paged. Initial hypothesis is a network partition, based on
the similarity of the error signature to the incident of 3 August.

14:41 — Network hypothesis discarded. Connectivity to the database host is
confirmed intact from within the namespace.

14:55 — The on call engineer identifies an authentication failure rather
than a connectivity failure, and requests elevated access to read the
Secret object in the payment-service namespace.

15:12 — Elevated access granted after a seventeen minute delay caused by
the approver being off shift and the escalation path to the secondary
approver not being documented in the runbook.

15:30 — The credential in the Secret is confirmed to match the credential
the database is rejecting. The credential is determined to have expired at
14:22 exactly, consistent with a ninety day validity set at creation.

15:44 — Attempt to rotate the credential through the standard pipeline
fails: the pipeline has no record of the credential and refuses to rotate
an unmanaged secret.

16:20 — Decision taken to provision a replacement credential manually,
accepting that this reproduces the original control failure, on the
grounds that the outage cost exceeds the marginal risk.

16:41 — Replacement credential provisioned and Secret updated.

16:48 — Rolling restart completes. Error rate returns to baseline.

## Findings

**F1. An unmanaged credential existed in a production path.** The
credential was created during the 2022 migration and predates the rotation
pipeline. No inventory reconciliation had ever been performed between the
credentials the pipeline manages and the credentials actually referenced by
production workloads. Three further unmanaged credentials were discovered
during the subsequent audit, two in the ledger service and one in the
reconciliation batch job.

**F2. Credential sensitivity was not reflected in access control.** The
Secret object was readable by any principal with extended access to the
payment-service namespace, which at the time of the incident was fourteen
engineers across three teams. The credential grants read and write access
to the payments ledger. The blast radius of a compromise of any one of
those fourteen identities was therefore the full transaction history.

**F3. Diagnosis was delayed by the absence of usage attribution.** Because
many principals could read the Secret, the audit log did not identify which
workload was using the credential, and the engineer could not rule out that
a second consumer would break when the credential was rotated. This
uncertainty accounts for approximately thirty minutes of the outage.

**F4. The escalation path for out of hours approval was undocumented.**
Seventeen minutes were lost waiting for an approver who was off shift.

## Actions

A1. Reconcile the credential inventory against all production workload
references, quarterly, automated. Owner: Platform Engineering. Complete.

A2. Move all credentials granting write access to a production data store
behind a dedicated access tier, readable only under time bounded elevation
rather than as part of standing extended access. Owner: Security.
In progress.

A3. Emit a usage record whenever a Secret is read by a workload, retained
for ninety days, queryable by the on call engineer without elevation.
Owner: Platform Engineering. In progress.

A4. Document the secondary approver for every approval path and verify the
path quarterly through a rehearsal. Owner: Engineering Management.
Complete.

## Note on Disclosure

Finding F2 describes a standing over-authorisation that was not exploited
but was exploitable throughout the period between the 2022 migration and
the completion of A2. The security team assessed the likelihood of prior
exploitation as low based on the absence of anomalous access patterns in
the retained audit log, while noting that the retention window of ninety
days does not cover the full exposure period. This assessment is the reason
for the confidential classification of this document.
