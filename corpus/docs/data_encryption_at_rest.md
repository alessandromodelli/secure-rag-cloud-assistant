# Data Encryption at Rest

This document describes how data at rest is protected across the storage
services in use. It covers key management, the boundary between managed
and customer-managed keys, and the operational rules that apply to key
material. It concerns the data plane; identity and access control are
handled separately.

## The default posture

Every storage service used by the organization has encryption at rest
enabled. This includes object storage, block volumes, managed databases,
and message queues. Encryption at rest is a baseline requirement and is
enforced by the cloud landing zone rather than left to the individual
workload to configure.

## Managed and customer-managed keys

Two key modes are in use. Managed keys are owned and rotated by the cloud
provider and are the default for stores that do not carry regulated data.
Customer-managed keys are owned by the organization, live in the key
management service under a dedicated key ring, and are used for stores
that carry regulated or high-sensitivity data. Customer-managed keys
allow the organization to revoke access to a key and thereby render the
protected data unreadable, which is a control the managed mode does not
offer.

## Envelope encryption

Storage services use envelope encryption: the data is encrypted with a
data key that is itself encrypted by a key from the key management
service. This lets the encryption of large volumes proceed without a
round-trip to the key service for every operation while keeping the
long-lived key material inside the service.

## Rotation

Managed keys are rotated by the provider according to its own schedule.
Customer-managed keys are rotated on a schedule set by the organization —
annually by default, more often for keys protecting the most sensitive
categories. Rotation of the wrapping key does not require re-encrypting
the data underneath, because only the data keys need to be re-wrapped
with the new material.

## Key policies

Every key in the key management service has an attached policy that
lists the principals allowed to use it and the operations they may
perform. Policies are reviewed on the same cadence as the identity
inventory: keys whose policies drift from the workload they protect are
tightened at review time.
