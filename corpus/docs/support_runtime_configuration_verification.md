# Support Runtime Configuration Verification

This checklist describes how the support engineering team verifies the
non-secret runtime configuration of a service while investigating a
customer-reported incident. It covers the environment variables worth
checking first, the defaults that apply when a value is not set, and how
a wrong value tends to surface as a symptom. Sensitive configuration —
connection strings, tokens, keys — is out of scope for support and is
never read during verification.

## Log level

`LOG_LEVEL` controls logger verbosity; accepted values are `debug`,
`info`, `warn`, and `error`, and the default is `info`. During an
investigation support confirms the level is `info` and asks the service
team to raise it to `debug` temporarily if the logs are too sparse to
explain the symptom. The change takes effect on the next pod restart;
there is no hot-reload path, so a level change will not appear in the
logs until the pod cycles.

## Feature flag host

`FEATURE_FLAG_HOST` names the endpoint queried for feature flag
evaluation, and the default points at the platform's shared flag
service. A value pointing at a local mock or a scoped test environment
is normal in local development and integration testing but is a red flag
in production, and support notes it when a production symptom coincides
with an unexpected flag host.

## HTTP timeouts

`HTTP_CLIENT_TIMEOUT_SEC` sets the per-call outbound timeout, defaulting
to thirty seconds; `HTTP_SERVER_READ_TIMEOUT_SEC` and
`HTTP_SERVER_WRITE_TIMEOUT_SEC` set the server-side timeouts and default
to sixty seconds. A customer-reported timeout that clusters around a
round number often points at one of these being tuned shorter than the
default for the environment, so support checks them early.

## Concurrency

`WORKER_CONCURRENCY` sets the worker pool size and by default scales
with the container's CPU allocation. An override far from the default
is worth flagging when the symptom is queue backlog or latency under
load, because a pool that is too small starves an I/O-bound workload.

## What support records

Support records the observed value of each variable against its expected
default and attaches the comparison to the escalation, so the service
team starts from a confirmed configuration picture rather than
re-checking it.
