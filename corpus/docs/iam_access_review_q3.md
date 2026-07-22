# IAM Access Review — Q3 2024 Findings

**Classification: Confidential — Security team and audit function only**

Findings of the quarterly review of standing IAM grants across the three
production accounts. Distribution outside the security team and the audit
function requires approval from the Head of Security. This document
enumerates specific over-authorisations that were live at the time of
review and are therefore exploitable until remediated.

## Scope

The review covered all customer managed IAM policies and all role trust
relationships in accounts 401255892210 (production), 401255892211
(staging) and 401255892212 (shared services). Service linked roles and
AWS managed policies were excluded.

Method: policy documents were evaluated statically for wildcard actions,
wildcard resources and permissive trust relationships, then cross
referenced against ninety days of CloudTrail to determine which granted
permissions had actually been exercised.

## Summary of Findings

Of 147 customer managed policies reviewed, 23 grant at least one wildcard
action, 11 grant a wildcard action on a wildcard resource, and 4 do both
while being attached to a role assumable by a human principal. The last
category is the material one and is enumerated below.

Of 89 roles reviewed, 31 have not been assumed in ninety days. Unused roles
are not harmless: they are unmonitored, their trust relationships drift out
of review, and they are attractive because nobody is watching.

## F1 — Broad administrative grant on a human assumable role

The policy `acme-prd-platform-admin-policy` grants `*:*` on `*` and is
attached to `acme-prd-platform-admin-role`, whose trust relationship
admits any principal in the shared services account with the tag
`team=platform`. Eleven engineers currently carry that tag.

CloudTrail shows the role assumed 340 times in ninety days. Of the actions
taken under it, 96% fall within a set of 14 API calls related to cluster
node management. The remaining 4% are read operations that a read only
role would satisfy.

The grant is therefore approximately three orders of magnitude broader
than its observed use. Remediation is to replace it with a scoped policy
covering the 14 observed actions, plus a break glass role retained at full
breadth with alerting on assumption.

**Status: remediation drafted, not applied.**

## F2 — Cross account trust without external identifier

The role `acme-prd-data-export-role` trusts the entire staging account
without an external identifier and without a condition on the source
principal. Any principal in staging that can assume roles can assume it,
including principals belonging to teams unrelated to data export.

The role grants read access to the analytics bucket, which contains
customer transaction records at `restricted` classification.

CloudTrail shows no assumption of this role from staging in the review
window, so there is no evidence of exploitation. The exposure has existed
since the role was created in March 2023.

**Status: condition added on 2024-09-30. Closed.**

## F3 — Ledger write permission attached to a read oriented role

The policy `acme-prd-ledger-read-policy` grants, in addition to the read
actions its name implies, `dynamodb:PutItem` and `dynamodb:UpdateItem` on
the ledger table. The write actions appear to have been added during a
2023 migration and never removed.

The role carrying this policy is assumed by seven engineers across two
teams under standing extended access, not under elevation. Any of the seven
can write to the payments ledger without approval and without the write
being distinguishable in the audit log from a legitimate application write,
because the application assumes the same role.

This is the same class of finding as F2 in the October payment outage
postmortem, and the two should be remediated together.

**Status: open. Owner: Security. Target Q4.**

## F4 — Permissions boundary absent on delegated administration

Three roles delegate policy creation to team leads without a permissions
boundary. A principal holding one of them can create a policy granting
itself any permission and attach it, which is equivalent to full
administrative capability reached in two steps rather than one.

The delegation was introduced to reduce platform team toil and achieved
that. The boundary was not applied because the boundary policy did not
exist at the time.

**Status: boundary policy written, application scheduled.**

## Note on Handling

Findings F1, F3 and F4 describe live exploitable conditions. This document
should not be circulated to the engineering organisation before those
findings are closed, on the reasoning that enumerating an exploitable
over-authorisation to a wide audience increases the probability of
exploitation more than it increases the probability of remediation.
Remediation is tracked separately and does not require the detail here.
