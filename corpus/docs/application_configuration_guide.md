# Application Configuration Guide

This guide describes the non-secret runtime configuration for the
application. It covers the environment variables that tune behavior at
startup, the defaults that apply when a value is not set, and the
conventions that keep configuration consistent across environments.
Values that are sensitive — connection strings, tokens, keys — are
covered by a separate reference and are not the subject of this guide.

## Log level

`LOG_LEVEL` controls the verbosity of the application logger. Accepted
values are `debug`, `info`, `warn`, and `error`; the default is `info`.
In production the level is normally `info` and is raised to `debug`
temporarily during investigations. Log level changes take effect on
the next pod restart; there is no hot-reload path.

## Feature flag host

`FEATURE_FLAG_HOST` names the endpoint the application queries for
feature flag evaluation. The default points at the platform's shared
flag service. Overriding it is useful during local development, where
it can be pointed at a local mock, and during integration testing,
where it can be pointed at a scoped test environment.

## HTTP timeouts

`HTTP_CLIENT_TIMEOUT_SEC` sets the default per-call timeout for
outbound HTTP requests; the default is thirty seconds. `HTTP_SERVER_
READ_TIMEOUT_SEC` and `HTTP_SERVER_WRITE_TIMEOUT_SEC` set the
corresponding server-side timeouts and default to sixty seconds. These
values are tuned per environment: staging often uses shorter timeouts
to surface issues early, production uses the defaults.

## Concurrency

`WORKER_CONCURRENCY` sets the size of the worker pool. The default
scales with the container's CPU allocation, so most services do not
override it. Overrides are useful for workloads that are I/O-bound
and can benefit from a larger pool than the CPU-count default.

## Feature switches

Boolean switches that gate specific application behaviors — the shape
`ENABLE_<FEATURE>` — accept `true` or `false`. Switches are
short-lived: once a feature is fully enabled everywhere, the switch
is removed from the code path alongside the feature-flag it wrapped.

## Precedence

Configuration is resolved in a fixed order: platform defaults, then
environment-specific overrides, then values injected at pod start.
No configuration source overrides a value that is explicitly set at
the pod level, which keeps operational overrides predictable.
