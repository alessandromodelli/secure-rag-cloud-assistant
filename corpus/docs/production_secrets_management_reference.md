# Production Secrets Management Reference

This reference describes the secrets that the production application
depends on: what each secret is used for, where its value is stored, and
how it is delivered to the running workload. It does not contain the
secret values themselves; those live only in the platform secret manager
and are surfaced to the workload at runtime through the mechanisms
described below.

## Delivery model

Application workloads never read secrets from repository-committed
files. At pod startup, an init container fetches the current secret
material from the platform secret manager and writes it to a tmpfs
volume; the application container mounts that volume read-only and
consumes the values as environment variables. Rotation is transparent
to the application: the operator updates the value in the secret
manager and the next scheduled pod restart picks it up.

## DATABASE_URL and DATABASE_READONLY_URL

The application connects to the primary Postgres instance using
`DATABASE_URL` and to the read replica pool using
`DATABASE_READONLY_URL`. Both variables carry a connection string
whose value is stored at the secret manager path
`app/production/database`. The primary URL points at the write endpoint
in the private subnet; the read-only URL points at the reader endpoint
that fronts the replica set. The connection strings include the
service-scoped user, not the database owner.

## AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION

These variables carry the AWS credentials the application uses for
object storage and message queue access. Their values are stored at
`app/production/aws`. In production these credentials are long-lived
by exception only: the standard is to rely on the pod's assumed role,
and the environment variables exist as a fallback for the small set of
SDK paths that do not yet honor the role. `AWS_REGION` is set to the
primary region and does not carry sensitive material.

## STRIPE_SECRET_KEY

The payment processor secret key is stored at
`app/production/stripe`. The variable is consumed by the payments
subsystem only; other services do not receive it. A separate,
lower-privilege publishable key is used by front-end code and is not
managed under this reference.

## GITHUB_TOKEN

The GitHub token used by the deployment pipeline for release tagging
is stored at `app/production/github`. Its scope is limited to the
release repositories and to the write operations needed by the tag
step; it does not carry broader permissions on the organization.

## JWT_SIGNING_KEY

The signing key used to issue authentication tokens for the
application's own users is stored at `app/production/jwt`. Rotation of
this key invalidates all outstanding sessions and is therefore
performed only on a scheduled maintenance window.

## Rotation

All values described above rotate on the platform's standard cadence.
The rotation schedule is tracked in the identity inventory; a rotation
that misses its window is surfaced in the weekly hygiene report and
resolved by the owning team.

## Access

Read access to the secret manager paths listed here is granted through
role membership. Application service accounts have read on the paths
their workload depends on; human access to production secret values is
limited to platform and security roles and is audited on retrieval.
