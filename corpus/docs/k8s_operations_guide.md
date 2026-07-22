# Kubernetes Operations Guide

Internal reference for service teams deploying workloads to the shared
platform clusters. This document covers deployment standards, health
checking, resource management and rollout procedures. It applies to all
namespaces managed by the Platform Engineering group.

## Cluster Layout

The platform provides three clusters. The `dev` cluster is open to all
engineering teams and is reset every Sunday at 02:00 UTC. The `staging`
cluster mirrors production topology at reduced replica counts and is used
for integration testing before release. The `prod` cluster hosts customer
facing workloads and is subject to change control.

Each service is granted a namespace named after the service itself. Teams
have full control over objects inside their own namespace and read only
visibility elsewhere. Cluster scoped objects such as ClusterRole,
StorageClass and CustomResourceDefinition are managed centrally and cannot
be created by service teams.

## Health Checking

Every container must declare both a readiness probe and a liveness probe.
The two serve different purposes and are frequently confused.

A **readiness probe** determines whether a pod should receive traffic. When
the probe fails the pod is removed from the Service endpoints but is not
restarted. This is the correct mechanism for a service that is running but
temporarily unable to serve requests, for example while it is warming a
cache or waiting for a downstream dependency to become available.

A **liveness probe** determines whether a container should be restarted.
When the probe fails the kubelet kills the container and the restart policy
applies. Use it only for conditions from which the process cannot recover
on its own, such as a deadlocked event loop.

The recommended readiness configuration for an HTTP service is an
`httpGet` probe against a dedicated endpoint that performs a shallow
dependency check:

    readinessProbe:
      httpGet:
        path: /healthz/ready
        port: http
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 3
      successThreshold: 1

Set `initialDelaySeconds` to slightly more than the observed cold start
time of the application. A value that is too low causes the pod to be
marked unready during normal startup, which produces misleading alerts
during a rollout. A value that is too high delays the rollout because the
deployment controller waits for readiness before proceeding to the next
pod.

The readiness endpoint should verify that the process can serve traffic:
that the database connection pool has at least one usable connection, that
required configuration has been loaded, and that any local cache required
for the first request has been populated. It should not perform deep checks
against downstream services. A readiness probe that fails because a remote
dependency is slow will remove the pod from rotation and amplify the
outage rather than contain it.

The liveness configuration should be more permissive than readiness:

    livenessProbe:
      httpGet:
        path: /healthz/live
        port: http
      initialDelaySeconds: 30
      periodSeconds: 20
      timeoutSeconds: 5
      failureThreshold: 5

For services that take a long and variable time to start, prefer a
`startupProbe` over a large `initialDelaySeconds` on the liveness probe.
The startup probe suspends liveness checking until it succeeds once, after
which normal liveness checking resumes.

## Resource Requests and Limits

Every container must declare both requests and limits for CPU and memory.
Requests drive scheduling decisions; limits drive throttling and eviction.

Set the memory request to the steady state resident set size observed under
representative load, plus approximately twenty percent of headroom. Set the
memory limit to roughly one and a half times the request. Memory is an
incompressible resource: a container that exceeds its limit is terminated
with an OOMKilled status rather than throttled, so a limit set too close to
the request produces intermittent restarts under normal traffic variation.

Set the CPU request to the average utilisation observed under
representative load. CPU limits are more contentious. Because CPU is
compressible, a container that exceeds its limit is throttled rather than
killed, which manifests as latency rather than failure. For latency
sensitive services the platform team recommends setting a CPU request
without a CPU limit, allowing the workload to burst into idle capacity on
the node. For batch workloads a limit should always be set.

Values are expressed in cores or millicores for CPU and in binary suffixes
for memory. A request of `250m` denotes a quarter of a core. A limit of
`512Mi` denotes 512 mebibytes.

## Configuration and Secrets

Application configuration is supplied through environment variables. Non
sensitive values may be declared inline in the manifest or sourced from a
ConfigMap. Sensitive values must never appear as literals in a manifest,
because manifests are stored in the service repository and are readable by
anyone with repository access.

Sensitive values are sourced from a Secret object using `secretKeyRef`:

    env:
      - name: DATABASE_PASSWORD
        valueFrom:
          secretKeyRef:
            name: checkout-service-secrets
            key: database-password

Secret objects are provisioned by the platform team through the sealed
secrets pipeline. Service teams request a secret through the standard
access request procedure and reference it by name in the manifest. Teams
do not have permission to read the contents of Secret objects in the
`prod` namespace, only to reference them.

## Rollout Strategy

The default strategy is `RollingUpdate` with `maxUnavailable: 0` and
`maxSurge: 1`. This guarantees that capacity never drops below the declared
replica count during a rollout, at the cost of requiring one pod worth of
spare capacity on the cluster.

Services that cannot tolerate two versions running concurrently, typically
because of an incompatible database migration, must use the `Recreate`
strategy and accept downtime, or implement the migration in two backward
compatible steps.

A rollout is considered complete when all pods report ready. The deployment
controller waits `progressDeadlineSeconds` before marking the rollout as
failed. The platform default is 600 seconds. A rollout that stalls is most
often caused by a readiness probe that never succeeds, by insufficient
cluster capacity to schedule the surge pod, or by an image pull failure.

## Common Failure Modes

A pod stuck in `Pending` has not been scheduled. Inspect the events with
`kubectl describe pod` and look for insufficient CPU or memory on the
nodes, an unsatisfiable node selector, or a PersistentVolumeClaim that
cannot be bound.

A pod in `CrashLoopBackOff` is starting and exiting repeatedly. Retrieve
the logs of the previous instance with `kubectl logs --previous` rather
than the current one, which is usually empty. A liveness probe configured
with an insufficient initial delay is a frequent cause.

A pod that is `Running` but never becomes ready is failing its readiness
probe. Exercise the readiness endpoint directly from inside the container
with `kubectl exec` to distinguish an application problem from a probe
misconfiguration.

Connection failures to a database are more often a NetworkPolicy or
credential problem than a Kubernetes problem. Confirm that the namespace
has an egress policy permitting traffic to the database subnet, and that
the referenced Secret exists in the same namespace as the pod. A Secret
referenced from a different namespace resolves to nothing and the container
starts with an empty environment variable rather than failing outright.
