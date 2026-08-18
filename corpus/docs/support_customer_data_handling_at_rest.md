# Support Customer Data Handling at Rest

This document describes the rules the support engineering team follows
when a ticket touches customer data held at rest in the storage
services. It covers the encryption posture support can rely on, the
boundary between what support may read and what it may not, and how key
management constrains support's access. It concerns the data plane;
identity and access control are handled separately.

## The posture support can assume

Every storage service in use has encryption at rest enabled by default —
object storage, block volumes, managed databases, and message queues.
Encryption at rest is enforced by the cloud landing zone rather than left
to the workload, so support can assume any store referenced by a ticket
is encrypted at rest without verifying it per store.

## Managed and customer-managed keys

Two key modes are in use. Managed keys are owned and rotated by the cloud
provider and are the default for stores that do not carry regulated data.
Customer-managed keys are owned by the organization, live in the key
management service under a dedicated key ring, and protect regulated or
high-sensitivity stores. Support cannot read, export, or use key
material in either mode; the relevance of the distinction to support is
that stores under customer-managed keys carry the most sensitive data and
are the ones support most often lacks read access to.

## What support may read

Support reads customer data only through the application's own support
tooling, which enforces the same access boundary as the customer-facing
product, and only for the specific record a ticket concerns. Support does
not query managed databases directly, does not open block volumes, and
does not pull objects from storage buckets, because those paths bypass
the boundary the support tooling enforces.

## Envelope encryption and rotation

Storage uses envelope encryption: data is encrypted with a data key that
is itself wrapped by a key from the key management service, and rotation
of the wrapping key does not require re-encrypting the data underneath.
None of this is operable by support; it is recorded here so that a ticket
mentioning a key rotation is understood as a routine event that does not
change what data support can read.

## Where handling stops

When resolving a ticket would require reading data outside the support
tooling's boundary, support does not seek another path to the data; it
escalates to the team that owns the store, with the record identifier and
the reason access is needed attached.
