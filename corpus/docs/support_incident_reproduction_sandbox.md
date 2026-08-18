# Support Incident Reproduction Sandbox

This runbook describes how the customer support engineering team stands
up a local reproduction sandbox on a laptop to replicate a
customer-reported issue before escalating it. It covers the tooling
prerequisites, the docker-compose topology the team uses, and the
placeholder configuration that lets the stack run without any real
credential. It does not describe how to reach staging or production;
support does not hold access to those environments and requests a
platform escalation when a live environment is required.

## Prerequisites

The sandbox expects Docker (or a compatible engine) and docker-compose
version two or higher on the host. Support engineers do not run any
service outside of a container, so no local JVM or Node runtime is
required beyond what the containers provide. The shell completion
helpers used by the engineering team are convenient but optional.

## Topology

The docker-compose file brings up the same four containers the
engineering team uses locally: the application, a Postgres instance
seeded with a small fixture dataset, a Redis instance used as a cache,
and a local mock of the payment provider that returns canned responses.
The mock listens on `localhost:9999` and needs no setup beyond starting
the container. Support engineers keep the topology identical to the
developer local stack on purpose, so that a reproduction observed in
the sandbox is credible when it is attached to an escalation.

## Placeholder configuration

The reproduction repository ships an `.env.example` file at its root.
The engineer copies it to `.env` on first setup and the compose file
loads it. Every value is a placeholder: the database password is
`local-dev-only`, the API key for the mock payment provider is
`mock-key-for-local`, and the local authentication token is a static
string checked against a hard-coded value inside the mock. No real
credential is ever used in the sandbox, and support engineers are not
permitted to substitute a real one.

## Seed data

The Postgres container is initialized with the same fixture the
developer stack uses: ten demo users, a small product catalog, and one
open order per user. When a ticket references a specific data shape, the
support engineer adds a minimal extra fixture that mirrors the shape
rather than importing any customer data into the sandbox.

## From reproduction to escalation

Once the issue is reproduced against the fixture, the engineer records
the exact steps, the seed state, and the observed behavior, and attaches
them to the escalation. The point of the sandbox is that the developer
who picks up the escalation can rebuild the same state on their own
local stack without re-deriving it from the ticket.
