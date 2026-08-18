# Support Kubernetes Read-Only Triage

Internal reference for the support engineering team when triaging a
customer-facing incident that appears to originate in a workload running
on the shared platform clusters. It covers what support can read, how to
interpret pod health, and how to describe a rollout's state accurately in
an escalation. Support holds read-only visibility only; any change to a
workload is performed by the owning service team after escalation.

## What support can see

Support engineers have read-only visibility across the namespaces on the
`dev`, `staging` and `prod` clusters. They can list workloads, read pod
status, and view rollout history, but they cannot create, edit or delete
any object, and they cannot exec into a container. Cluster-scoped objects
such as ClusterRole, StorageClass and CustomResourceDefinition are
managed centrally and are not part of triage.

## Reading pod health

Interpreting probe state is the core of triage. A **readiness probe**
determines whether a pod receives traffic; when it fails the pod is
removed from the Service endpoints but is not restarted. A pod that is
running but not ready is usually warming a cache or waiting on a
downstream dependency, and this is frequently the visible cause of a
customer-reported timeout even though nothing has crashed.

A **liveness probe** determines whether a container is restarted; when it
fails the kubelet kills the container and the restart policy applies. A
pod that is repeatedly restarting is failing its liveness probe, and the
restart count is the field that shows it. Support reports the restart
count and the last state rather than guessing at a cause.

## Describing a rollout

When an incident coincides with a deployment, support reads the rollout
history to state which revision is live and whether a rollout is in
progress, paused, or complete. This lets the escalation say precisely
"the current revision began rolling out at 14:02 and three of six pods
are on the new revision" instead of "a deploy might be involved".

## Where triage stops

Support does not roll back, scale, or restart workloads, and does not
read secrets mounted into a pod. When the read-only picture points at a
change that only the service team can make, the triage notes are handed
to that team with the observed pod and rollout state attached.
