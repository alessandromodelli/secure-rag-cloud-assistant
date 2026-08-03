# Local Development Environment Setup

This document describes how a new engineer stands up the application
stack on a laptop for local development. It covers the tooling
prerequisites, the docker-compose topology, and the placeholder
configuration that lets the stack run without any real credentials.
It does not describe how to reach staging or production; those
environments are managed by the platform team.

## Prerequisites

The local stack expects Docker (or a compatible engine), docker-compose
version two or higher, and either the JVM or Node runtime installed on
the host, depending on which service the engineer intends to run
outside of a container for debugging. A recent version of the shell
completion helpers is convenient but not required.

## Topology

The docker-compose file brings up four containers: the application, a
Postgres instance seeded with a small fixture dataset, a Redis instance
used as a cache, and a local mock of the payment provider that returns
canned responses. The mock listens on `localhost:9999` and requires no
setup beyond starting the container.

## Placeholder configuration

The repository contains an `.env.example` file at its root. The engineer
copies it to `.env` on first setup and the compose file loads it. Every
value in the example file is a placeholder: the database password is
`local-dev-only`, the API key for the mock payment provider is
`mock-key-for-local`, and the token used for local authentication is a
static string that is checked against a hard-coded value inside the
mock. These placeholders let the stack run end-to-end without any real
credential ever leaving a developer's laptop.

## Seed data

The Postgres container is initialized with a fixture that includes ten
demo users, a small product catalog, and one open order per user.
This is enough surface to exercise the main paths in the application
without pulling anonymized production data, which is not permitted
into local environments.

## Common issues

Port conflicts on ports 5432 or 6379 are the most common startup
issue and are resolved by either stopping the conflicting process or
by editing the compose file to remap the port. The compose file
tolerates remapping cleanly; the application reads its port bindings
from the same `.env` file that carries the other placeholders.

## Cleaning up

`docker-compose down --volumes` removes containers, networks, and the
seeded database volume, returning the environment to its initial
state. This is the recommended way to reset when the local database
has drifted from what the tests expect.
