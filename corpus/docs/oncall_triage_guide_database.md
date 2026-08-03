# On-Call Triage Guide — Database Outages

This guide describes the first steps an on-call engineer should take when a
database outage is suspected in production. It covers detection, initial
triage, and escalation. It does not include emergency credentials, bastion
access instructions, or break-glass procedures — those are documented in a
separate runbook restricted to platform and security roles.

## Detecting the outage

The primary signals are alerts from the platform monitoring system and reports
from downstream services that depend on the database. Confirm the outage
before acting:

- Check the status of the primary database instance in the platform dashboard.
- Look at the error rate and latency panels for the affected service.
- Confirm that replicas are reporting fresh replication lag; a stale value
  suggests the primary is unreachable rather than simply slow.
- Cross-check with recent deployments: an incident that began within minutes
  of a rollout is often related to the release rather than to the database
  itself.

## Initial triage

The steps below are safe for any on-call engineer to perform without elevated
access. They are diagnostic, not corrective.

1. Open the incident channel in Slack and post the alert.
2. Confirm the affected service and the user-visible impact.
3. Check whether the database endpoint responds to a connectivity probe from
   the application namespace.
4. Look at recent changes: deployments, schema migrations, configuration
   updates, or infrastructure events in the last thirty minutes.
5. If the issue is clearly caused by a recent deployment, initiate a rollback
   through the standard release process.

## Escalation

If the outage cannot be resolved through a standard rollback, or if the
database itself is unreachable rather than the application, escalate to the
platform team.

- Tier 1: on-call engineer (paged automatically).
- Tier 2: platform team lead, contacted via Slack in the platform on-call
  channel.
- Tier 3: escalate to executive on-call only if customer impact continues
  beyond thirty minutes and payment flows are affected.

The platform team owns the recovery procedures that require privileged access,
including standby promotion and emergency credential use. Do not attempt these
without their involvement.

## Communication

For any incident that affects customer-facing services, the incident commander
opens a public status page entry within fifteen minutes and updates it at
least every thirty minutes until the incident is resolved. Internal updates
are posted in the incident channel; external updates go through the status
page and, when appropriate, through the account management team.

## After the incident

Every incident receives a written postmortem within five business days. The
postmortem is authored by the incident commander and reviewed by the platform
team. Detailed timelines and any references to privileged actions or
credentials are recorded in the restricted incident review; the public
postmortem summarizes cause, impact, and remediation without operational
details.
