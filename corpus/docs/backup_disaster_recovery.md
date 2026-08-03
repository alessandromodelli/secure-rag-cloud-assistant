# Backup and Disaster Recovery

This document describes the recovery objectives and backup practices for
persistent data. It is concerned with data durability and restoration, not with
how services are deployed or configured at runtime.

## Recovery objectives

Two numbers define the target for every data store. The Recovery Point Objective
(RPO) is the maximum amount of data, measured in time, that the business accepts
losing in an incident. The Recovery Time Objective (RTO) is the maximum time the
business accepts being unable to serve that data. Tiering matters: a primary
transactional store carries a tight RPO and RTO, while an analytics warehouse
can tolerate looser ones.

## Snapshot schedule

Managed data stores are snapshotted on an automated schedule aligned to their
RPO tier. Snapshots are incremental after the first full copy, so they are cheap
to take frequently. Retention follows a tiered policy: recent snapshots are kept
at full granularity, older ones are thinned to daily and then weekly, and the
oldest are expired once they pass the compliance retention window.

## Cross-region replication

For tier-one stores, snapshots are copied to a second region so that a
region-wide outage does not also destroy the backups. Replication is
asynchronous, which means the secondary region lags the primary slightly; that
lag is the practical floor on the achievable RPO for a cross-region restore.

## Restore drills

A backup that has never been restored is a hypothesis, not a guarantee.
Restore drills are run on a fixed cadence: a snapshot is restored into an
isolated environment, the data is validated against known checkpoints, and the
measured restore time is recorded and compared against the RTO. Drills that miss
the objective trigger a review of the tier's schedule or replication strategy.

## Runbook ownership

Each data store names an owner responsible for confirming that its objectives,
schedule, and last successful drill are current. Ownership is reviewed whenever
a store changes tier.
