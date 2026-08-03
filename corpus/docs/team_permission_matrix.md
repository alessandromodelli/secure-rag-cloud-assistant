# Team Permission Matrix

This matrix summarizes what each engineering team is expected to be
able to do in the cloud environment. It is a reference for onboarding
and for access reviews, not the source of truth for the actual grants;
the actual grants live in the identity system and are reviewed against
this matrix at each cycle.

## How to read this matrix

Each row is a team. Each column is a capability. A team either has
that capability, has it in read-only form, or does not have it. A team
that has a capability in read-only form can inspect the state of the
system but cannot change it. Capabilities that require additional
approvals — such as production write access outside a deploy window —
are noted separately in the team's onboarding page.

## Teams and capabilities

**Application teams** (`application-*` groups) have read-only access to
their own workloads' logs and metrics, read-only access to configuration
in their own namespaces, and write access to their own deployments
only during a deploy window. They do not have access to secrets in
production directly; they consume secrets through the platform's
delivery model.

**Platform team** (`platform-team` group) has read-write access to
the shared infrastructure that other teams depend on: the identity
system, the secret manager, the observability stack, and the cluster
control plane. Platform team members do not by default have access to
application data at rest; that access is granted on a per-incident
basis and expires with the incident.

**Security team** (`security-team` group) has read-only access
everywhere that read is meaningful, including the audit trails, the
identity configuration, and the network configuration. Write access is
limited to the security controls themselves.

**Data team** (`data-team` group) has read access to the analytics
warehouse, write access to the ingest layer they own, and no direct
access to the operational data stores. Cross-boundary access between
operational and analytical stores runs through the platform's
replication pipeline.

## Exceptions

Exceptions to the matrix are recorded in the identity inventory with
the granting authority and the expiration date. An exception without
an expiration date is treated as a finding and surfaced in the next
access review.
