# Cloud Identity Hardening Checklist

This checklist collects the identity and access-management practices that
services in this organization are expected to follow. It supplements the
public cloud provider guidance with organization-specific rules and is
reviewed twice a year.

## Access model

Every workload runs under an identity dedicated to that workload. Shared
identities across services are not permitted. Human access to cloud
resources is granted through group membership, never by attaching policies
directly to individual users. Groups map to job functions and are
themselves reviewed on the same cadence as the roles they contain.

## Least privilege

Permissions are granted at the smallest resource scope that lets the
workload function. A statement that grants an action on all resources in
an account is treated as a finding unless the role's purpose explicitly
requires that scope. When a broad scope is legitimately needed, the
justification is written into the role description so the next reviewer
does not have to re-derive it.

## Wildcards

Wildcards in the action or resource fields are avoided by default. An
action like `s3:*` bundles read, write, and administrative operations that
almost never all belong together in a single workload. When a wildcard is
present, the review checks whether the underlying set of actions can be
enumerated instead.

## Long-lived credentials

Long-lived access keys are the highest-risk credential in the environment
and are used only where a managed identity is not available. When a
long-lived key exists, it is created with the shortest justified lifetime,
tagged with an owner and a rotation date, and stored in the platform
secret manager rather than in environment files or configuration
repositories.

## Multi-factor authentication

Human accounts with any write access require multi-factor authentication.
Administrative operations — deleting resources, modifying permissions,
assuming privileged roles — require an authenticated MFA session at the
time of the operation, not merely at login. Service identities do not use
MFA; their equivalent control is the scope of the role they can assume.

## Rotation

Access keys, where they exist, are rotated on a fixed cadence and
whenever a member of the owning team leaves. The rotation window is
tracked in the identity inventory and surfaced in the monthly hygiene
report. A key that has not been used in ninety days is disabled ahead
of the next rotation cycle and removed if it remains unused.

## Review

Every role, group, and long-lived key has an owning team recorded in a
tag. The identity inventory is reviewed quarterly: roles no longer in use
are retired, roles whose scope has drifted from their description are
rewritten, and any finding raised during the review is tracked to closure.
