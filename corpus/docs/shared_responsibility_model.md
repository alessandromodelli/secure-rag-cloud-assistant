# Shared Responsibility Model

Who is accountable for what, between the cloud provider, the platform team
and the service teams. This document is public within the organisation. It
describes the division of responsibility in general terms and does not
document any specific control.

## Why the Division Matters

Most cloud security incidents are not failures of the provider. They are
failures at the boundary: a control that each party assumed the other was
operating. The division below exists so that every control has exactly one
accountable owner, and so that an engineer can determine in seconds whether
a given concern is theirs.

The division has three layers rather than the two that provider
documentation usually describes, because our platform team operates a
substantial layer between the provider and the service teams.

## Provider Responsibility

The cloud provider is responsible for the security *of* the cloud: the
physical facilities, the host hardware, the hypervisor, the network
fabric between regions and availability zones, and the availability and
correctness of the managed services themselves.

When a managed database is patched against a vulnerability in the engine,
that is provider responsibility. When the same database is reachable from
the public internet because a security group was written that way, that is
not.

The provider is also responsible for the correctness of the authorisation
primitives it offers. If an IAM policy evaluates to deny, the provider
guarantees the action is denied. The provider does not guarantee that the
policy expresses what the author intended.

## Platform Team Responsibility

The platform team is responsible for the shared substrate: the Kubernetes
clusters, the network topology, the identity federation, the secret
management pipeline, the observability stack and the deployment tooling.

Concretely, the platform team owns cluster upgrades and node patching,
the default network policies applied to every namespace, the provisioning
and rotation of credentials, the enforcement of organisation wide guard
rails such as account level public access blocks, and the audit pipeline
that records who did what.

The platform team is also responsible for making the secure path the easy
path. A control that service teams routinely work around is a platform
failure rather than a service team failure, and is treated as such in
review.

The platform team is not responsible for what a service does with the
authority it has been granted, nor for the correctness of application
logic, nor for data handled inside a service.

## Service Team Responsibility

Service teams are responsible for the security *in* their own workloads:
application code, dependencies, the configuration they declare, the data
they handle, and the authority they request.

Concretely, a service team owns the correctness of its manifests, the
timeliness of its dependency updates, the classification of the data its
service processes, the scope of the IAM permissions it requests, and the
handling of credentials inside its own code.

A service team is expected to request the least authority that lets its
workload function, and to notice when a granted permission is broader than
needed. Nobody else is positioned to notice this: the platform team knows
what was requested, not what was required.

## The Boundary Cases

**Credentials.** The platform team provisions and rotates them. The service
team references them correctly and does not copy them elsewhere. A
credential leaked because it was pasted into a ticket is a service team
matter; a credential leaked because rotation failed silently is a platform
matter.

**Network policy.** The platform team applies a default deny policy to
every namespace. The service team declares the egress it needs. A service
unable to reach a dependency because it never declared the egress is a
service team matter.

**Data classification.** The service team classifies the data it handles,
because only the team knows what the data is. The platform team enforces
the handling requirements that follow from the classification. A
misclassification is a service team matter; a classification that is
correct but unenforced is a platform matter.

**Vulnerable dependency.** The service team updates it. The platform team
provides the scanning that surfaces it and the deployment path that makes
updating cheap. A vulnerability that was reported and not acted on is a
service team matter; a vulnerability that scanning failed to report is a
platform matter.

**Over-broad permission.** Both. The service team requested it, the
platform team granted it. Reviews of over-broad permissions therefore
involve both parties and produce actions for both, and this is deliberate:
assigning it to one side has historically produced either rubber stamping
or resentment.

## How to Use This Document

When something goes wrong, the first question is not who is at fault but
which layer the control belonged to, because that determines who can fix
it. The second question is whether the control had an owner at all.
Controls without owners are the most common finding in our incident
reviews, and they are found at boundaries, which is why the boundaries are
enumerated above rather than left to inference.

Disagreement about which layer owns a control is resolved by the platform
architecture group, and the resolution is recorded here rather than in the
incident. A boundary that produced disagreement once will produce it again.
