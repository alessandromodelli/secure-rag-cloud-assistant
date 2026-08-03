# API Versioning and Deprecation Policy

This policy describes how public and internal APIs are versioned, how
breaking changes are communicated, and how endpoints are eventually retired.
It applies to REST and gRPC interfaces exposed by any service in the
organization.

## Versioning scheme

Public APIs are versioned in the URL path with a major version prefix, for
example `/v1/` or `/v2/`. The major version changes only for breaking
changes. Non-breaking additions — new optional fields, new endpoints, new
enum values with a documented default — happen within a version without a
new prefix. Internal APIs may use header-based versioning where the caller
and callee are both in-house, but the same rule applies: a major version
change is reserved for breaking changes.

## What counts as a breaking change

Breaking changes include removing an endpoint, removing or renaming a field
in a response, tightening a validation rule so previously accepted requests
are rejected, changing the type or semantics of an existing field, and
changing an error code from one class to another. Adding an optional field,
adding a new endpoint, or adding a new enum value with an existing default
is not breaking.

## Deprecation window

An endpoint or field marked deprecated remains supported for at least six
months from the announcement date. During that window it continues to
function as before, but responses include a deprecation warning header and
the documentation lists the recommended replacement. For public APIs the
minimum window is twelve months and the announcement is published on the
developer portal.

## Sunset

At the end of the deprecation window the endpoint is sunset. Sunset means
that requests to the endpoint return a permanent error and are logged for
follow-up with the client. Before sunset the platform team contacts the
top consumers directly to confirm that they have migrated.

## Client SDKs

The organization publishes client SDKs for the most common languages.
SDKs follow the same versioning scheme as the API they wrap: an SDK release
whose major version increases indicates that the underlying API contract
has changed. SDKs are supported for one major version behind the current
one; older versions receive security fixes only.
