# Cloud Cost Optimization Guide

This guide summarizes the practices the platform team uses to keep cloud
spending predictable and aligned with actual usage. It is intended as general
guidance for engineers and does not contain any account-specific figures.

## Commitment-based discounts

Steady-state workloads should be covered by commitment-based pricing rather than
on-demand rates. Reserved Instances and Savings Plans typically reduce compute
cost by a significant margin when the baseline demand is stable across a
one-year or three-year horizon. Before committing, review the trailing ninety
days of utilization so the commitment matches the floor of demand, not the peak.

## Rightsizing

Rightsizing is the process of matching provisioned capacity to observed
utilization. Instances that stay below twenty percent CPU utilization for
extended periods are candidates for a smaller class. Storage volumes that were
over-provisioned at creation should be re-evaluated against their actual growth
curve. Rightsizing is an ongoing activity, not a one-time cleanup.

## Budgets and alerts

Every team owns a monthly budget with alert thresholds at fifty, eighty, and one
hundred percent of the forecast. Alerts are informational and route to the team
channel; they never block deployments. Forecasts are recalculated at the start
of each month from the previous quarter's trend.

## Cost allocation tags

Accurate showback depends on consistent tagging. Each resource must carry an
owner tag, an environment tag, and a cost-center tag at creation time. Untagged
resources are surfaced in the weekly hygiene report and assigned to the team
that created them. Tag consistency is what makes unit-economics reporting
meaningful across the organization.

## Idle resource reclamation

Unattached storage volumes, idle load balancers, and orphaned snapshots
accumulate quietly and are the most common source of avoidable spend. The
weekly hygiene job flags these for review; reclamation is manual and requires
owner confirmation to avoid deleting anything still in use.
