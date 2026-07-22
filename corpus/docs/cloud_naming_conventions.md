# Cloud Resource Naming Conventions

Internal standard for naming resources across the organisation's cloud
accounts. Consistent names are what make cost attribution, automated policy
enforcement and incident triage possible. Resources that do not conform are
flagged by the nightly compliance scan and may be quarantined.

## General Principles

Names are lowercase. Words are separated by hyphens. Underscores are used
only where a provider forbids hyphens. Names never contain personal
identifiers, ticket numbers, or dates, because all three become misleading
as soon as ownership or purpose changes.

Every name encodes, in order: the organisation prefix, the environment, the
owning team or service, and the resource purpose. The organisation prefix
is `acme` in all accounts. The environment is one of `dev`, `stg` or `prd`.
Abbreviations are fixed and must not be expanded or varied.

The general form is:

    acme-<env>-<owner>-<purpose>

Names are read left to right by both humans and automation, so the most
stable component comes first and the most volatile last.

## S3 Buckets

Bucket names occupy a single global namespace shared by every AWS customer,
so they require an additional component to guarantee uniqueness. The
convention adds the account identifier and, where the bucket is not
replicated, the region:

    acme-<env>-<owner>-<purpose>-<account-id>

For example, the bucket holding raw payment events in production, owned by
the payments team, in account 401255892210, is named:

    acme-prd-payments-events-raw-401255892210

Bucket names may not contain uppercase letters or underscores, may not be
formatted as an IP address, and are limited to 63 characters. When the
composed name would exceed the limit, abbreviate the purpose component
rather than the owner or environment component: attribution matters more
than description.

Every bucket must carry the tags `Environment`, `Owner`, `CostCentre` and
`DataClassification`. Buckets holding personal data must additionally set
`DataClassification` to `restricted`, which causes the compliance scan to
verify that default encryption and access logging are enabled.

Buckets are private by default. Public access block is enforced at the
account level and cannot be disabled by service teams. A bucket that must
serve public content is fronted by a CloudFront distribution with an origin
access identity, and the bucket itself remains private.

## IAM Roles and Policies

Role names describe the principal that assumes them, not the permissions
they grant. Permissions change; the identity of the workload does not.

    acme-<env>-<owner>-<workload>-role

For example, the role assumed by the checkout service running in the
production EKS cluster is `acme-prd-checkout-service-role`.

Customer managed policy names describe the capability granted:

    acme-<env>-<capability>-policy

For example, `acme-prd-events-bucket-read-policy`. A policy that grants
access to a single named resource carries that resource in the capability
component. A policy that grants a broad capability across many resources
requires review by the security team before creation, and its name must
begin with `acme-<env>-broad-`.

Service linked roles created by AWS itself are exempt from this convention
and must not be renamed.

## Kubernetes Namespaces and Objects

The namespace is named after the service, without environment or
organisation prefix, because the cluster already encodes both:

    <service-name>

For example, `checkout-service` and `payment-service`. Objects inside a
namespace are named after the service and, where more than one object of a
kind exists, the specific role of the object:

    <service-name>[-<role>]

A Deployment is therefore `checkout-service`, its primary Service is
`checkout-service`, its metrics Service is `checkout-service-metrics`, and
its Secret is `checkout-service-secrets`.

## RDS and Data Stores

Database instance identifiers follow the general form with the engine
appended, because engine migrations are rare and the information is useful
at a glance:

    acme-<env>-<owner>-<purpose>-<engine>

For example, `acme-prd-payments-primary-postgres`. Read replicas append an
ordinal: `acme-prd-payments-primary-postgres-ro-1`.

Database names inside an instance follow the same convention with
underscores, because PostgreSQL identifiers containing hyphens require
quoting in every statement:

    <owner>_<purpose>

For example, `payments_ledger`.

## Tags

Four tags are mandatory on every resource that supports tagging:

`Environment` takes one of `dev`, `stg`, `prd`. `Owner` names the team, not
an individual. `CostCentre` is the four digit finance code. `ManagedBy`
records the provisioning mechanism, typically `terraform` or the name of
the platform component that created the resource.

Resources created outside Terraform must set `ManagedBy` to `manual` and
carry an additional `TicketRef` tag. The compliance scan reports manually
created resources weekly and they are expected to be either imported into
Terraform or removed within thirty days.

## Deprecation and Renaming

Cloud resources generally cannot be renamed in place. A resource whose name
does not conform is corrected at the next replacement opportunity rather
than immediately, unless it holds a `DataClassification` of `restricted`,
in which case the security team schedules the migration.

Names of decommissioned resources are not reused for twelve months. Reuse
causes stale references in dashboards, alerting rules and IAM policies to
resolve to the wrong resource, which is difficult to detect and has
produced two incidents in the past.
