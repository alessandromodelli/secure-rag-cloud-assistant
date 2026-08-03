# Feature Flag Management

This document describes how feature flags are used to control the rollout of
new functionality. It covers the lifecycle of a flag, how flags are targeted,
and the practices that keep the flag inventory from growing without bound.

## Flag lifecycle

A feature flag has four stages: created, rolling out, fully enabled, and
retired. A flag is created before the code that reads it and starts in the
off state for all users. Once the code is merged and validated in staging,
the flag begins its rollout: a small percentage of production traffic sees
the new behavior while the majority continues on the old path. Rollout
proceeds in steps, with each step held long enough to observe error rates,
latency, and product metrics before advancing.

## Targeting

Flags can be targeted by user attribute, by cohort, or by percentage. Attribute
targeting is used when a feature is meant for a specific segment such as
internal users, users in a particular region, or users on a specific plan.
Cohort targeting is used for holdback experiments where a fixed group is kept
on the old behavior for measurement. Percentage targeting is the default for
gradual rollouts and is combined with attribute filters when needed.

## Retirement

A flag that is at one hundred percent and has been for a full observation
window is retired: the flag reads are removed from the code, the flag itself
is deleted from the platform, and the change is recorded in the flag
inventory. Retiring flags is the single most neglected step in the lifecycle;
teams are encouraged to schedule flag cleanup as part of the sprint after the
rollout completes rather than as separate work later.

## Kill switches

A subset of flags are designated as kill switches. Their sole purpose is to
disable a feature quickly if it misbehaves in production. Kill switches are
kept indefinitely and are not subject to the retirement policy. They are
evaluated in a fast path so that flipping one takes effect in seconds rather
than minutes.

## Ownership and hygiene

Every flag has an owning team and an expected retirement date. Flags without
an owner or past their retirement date are surfaced in the monthly hygiene
report. The report is a nudge, not a blocker, but repeated appearance in the
report is a signal that the team should either retire the flag or renew its
ownership record.
