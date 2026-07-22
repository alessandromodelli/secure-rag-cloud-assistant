# Access Request Procedure

How engineers request, receive and relinquish access to cloud and cluster
resources. This document describes the process itself; the authorisation
model that the process implements is documented separately by the security
team.

## Access Tiers

Access is granted at four tiers, and the tier determines both the approval
path and the duration of the grant.

**Standard access** is granted automatically on joining an engineering
team. It includes read and write access to the team's own namespace in the
`dev` and `stg` clusters, read access to the corresponding cloud resources,
and read access to platform documentation. No request is required.

**Extended access** covers read and write access to the team's own
namespace in the `prd` cluster. It is requested once per engineer, approved
by the team lead, and remains in force while the engineer stays on the
team. It permits deploying, scaling and restarting the team's own
workloads. It does not permit reading Secret objects or modifying
NetworkPolicy.

**Elevated access** covers operations that can affect other teams or that
expose sensitive material: reading Secret objects in `prd`, modifying
cluster scoped resources, assuming roles with broad IAM capability, or
querying production data stores directly. Elevated access is never
standing. It is granted for a bounded window against a stated reason.

**Break glass access** is a superset of elevated access, granted without
prior approval during a declared incident. Its use is reviewed after the
fact, without exception and without implication of fault.

## Requesting Elevated Access to the Production Namespace

Elevated access is requested through the access portal at
`https://access.internal.acme.example/request`. The request form requires
four fields, and requests missing any of them are returned rather than
rejected.

The **target** identifies what is being requested: the cluster, the
namespace, and the specific capability. Requests phrased as a role name
rather than a capability are returned, because the mapping between roles
and capabilities changes and the approver needs to know what the requester
intends to do.

The **reason** states the operational need in one or two sentences. A
reference to an incident or change ticket is sufficient when one exists.
"Debugging" without further detail is returned.

The **duration** is chosen from four, eight or twenty four hours. Requests
longer than twenty four hours require the security team as an additional
approver and are expected to be rare; a recurring need for long lived
elevated access indicates a missing capability at the extended tier and
should be raised as such.

The **approver** defaults to the requester's team lead. Requests touching
namespaces owned by another team route to that team's lead instead.
Requests for IAM capability beyond a single namespace route to the security
team regardless of the requester.

Once submitted, the request appears in the approver's queue and in the
team channel. Approval grants the capability within approximately two
minutes through the just in time elevation pipeline. The requester receives
a notification containing the expiry time. No credentials are transmitted
in the notification: elevation modifies the requester's existing identity
rather than issuing a new one.

## What Elevation Does and Does Not Do

Elevation adds capability to the requester's own identity for the duration
of the grant. Every action taken under elevation is attributed to the
requester in the audit log, exactly as actions taken under standard access
are. There is no shared account and no impersonation.

Elevation does not bypass the classification of documents or data. An
engineer elevated to read Secret objects in the `prd` namespace can read
the secrets referenced by their own team's workloads. They do not thereby
gain access to other teams' secrets, to the security team's records, or to
customer data in the data warehouse. Those are separate capabilities with
separate approval paths.

Elevation does not survive a session. Closing the terminal does not revoke
the grant, but the grant expires at the stated time regardless of activity,
and the pipeline does not extend it silently. An engineer who needs more
time submits a new request, which is deliberately more visible than an
automatic extension would be.

## Expiry and Revocation

Grants expire automatically. Thirty minutes before expiry the requester
receives a warning in the team channel, which is enough time to finish or
to request an extension. On expiry the capability is withdrawn and any
subsequent operation fails with a permission error rather than a
connection error, which is the intended signal.

A grant may be revoked before expiry by the approver, by the security team,
or by the requester themselves. Self revocation is encouraged as soon as
the work is complete and is recorded as a positive signal in the quarterly
access review.

The quarterly access review examines standing extended access rather than
elevated grants. Extended access held by an engineer who has not exercised
it in ninety days is withdrawn automatically, on the reasoning that unused
standing capability is pure risk. Restoring it is a one click request to
the team lead.

## Common Reasons a Request Is Returned

A request naming a role rather than a capability is returned with a
prompt to restate it, because the approver cannot evaluate a role name
against a reason.

A request whose duration exceeds the stated need is returned. Selecting
twenty four hours for a task expected to take twenty minutes is the most
common cause of return and the easiest to avoid.

A request for a namespace the team does not own, without prior agreement
from the owning team, is routed to that team rather than returned. The
requester is not expected to know namespace ownership in advance; the
portal resolves it.

A request submitted during a declared incident is approved automatically
under break glass and reviewed afterwards. Engineers should not delay
incident response waiting for an approval.
