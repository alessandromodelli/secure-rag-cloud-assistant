# DNS and CDN Configuration

This runbook describes how public-facing domains are resolved and cached at the
edge. It covers hosted zones, record types, and cache behavior. It does not
cover application deployment or service internals.

## Hosted zones and records

Each public domain is served from a managed hosted zone. The most common record
types in use are A and AAAA records for apex domains, CNAME records for
subdomains that point at edge distributions, and TXT records for domain
verification and mail policy. Changes to records propagate according to the
record's TTL, so lowering the TTL a day before a planned migration reduces the
window during which stale answers are served.

## Time to live

TTL is the number of seconds a resolver may cache an answer before asking again.
A long TTL reduces query volume but slows down propagation of changes; a short
TTL does the opposite. The convention here is a moderate default TTL for stable
records and a deliberately short TTL only in the days surrounding a planned
change, after which it is raised again.

## Edge distribution and caching

Static assets are served through a content delivery network that caches objects
at edge locations close to the user. Cache behavior is controlled by origin
response headers: the max-age directive sets how long the edge keeps an object,
and a cache invalidation forces the edge to fetch a fresh copy before the object
would otherwise expire. Invalidations are used sparingly because they are slower
and more expensive than simply versioning asset filenames.

## TLS at the edge

Public endpoints terminate TLS at the edge using managed certificates that renew
automatically. The origin connection is re-encrypted, so traffic is protected
both from the client to the edge and from the edge to the origin. Certificate
renewal is automatic and requires no manual rotation.

## Failover

Health-checked records allow traffic to shift to a secondary region if the
primary origin stops responding. Failover is based on the health check status,
not on latency, and returns to the primary automatically once it recovers.
