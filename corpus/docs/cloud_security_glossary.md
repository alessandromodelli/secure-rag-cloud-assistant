# Cloud Security Glossary

A shared vocabulary for engineers working with the platform. Terms are
listed alphabetically. This document is public within the organisation and
carries no operational detail: it defines concepts, it does not describe
our configuration.

## Access Control Terms

**Access control list (ACL).** An enumeration of the principals permitted
to act on a resource. An ACL is attached to the resource and answers the
question "who may touch this", in contrast to a capability, which is held
by the principal and answers "what may I touch".

**Attribute based access control (ABAC).** An authorisation model in which
the decision is computed from attributes of the subject, the resource and
the environment, rather than from a role assignment. ABAC expresses
policies such as "an engineer may read resources tagged with their own
team" without enumerating either engineers or resources.

**Clearance.** The level of a subject in a hierarchical classification
scheme. A subject with a given clearance may read material at that level
and below. Clearance is a property of the identity, not of the session.

**Classification.** The level assigned to an object in a hierarchical
scheme. Classification and clearance are compared to produce an
authorisation decision; the comparison is the whole of the model in a
purely multilevel system.

**Confused deputy.** A situation in which a privileged component performs
an action on behalf of a less privileged caller without checking whether
the caller was entitled to request it. The deputy's authority is borrowed
rather than the caller's, and the check that should have happened does not.

**Complete mediation.** The principle that every access to every object is
checked for authority, with no cached or bypassed path. A design that
checks on first access and trusts thereafter violates it.

**Defence in depth.** The arrangement of multiple independent controls so
that the failure of any one does not by itself result in compromise. The
controls must be genuinely independent: two controls that fail for the same
reason provide one layer, not two.

**Fail closed.** A design in which an error, an unknown input or a missing
value results in denial. The opposite, fail open, results in permission and
is almost always the wrong default for an authorisation component.

**Least privilege.** The principle that a subject is granted the minimum
authority required for its task, for the minimum duration. Least privilege
is a property of a grant, not of a system, and is evaluated grant by grant.

**Multilevel security.** A model in which subjects and objects carry levels
from an ordered set and information is permitted to flow only in one
direction relative to that order. The Bell LaPadula formulation protects
confidentiality by forbidding a subject to read above its level and to
write below it.

**Principal.** An entity that can be authenticated and to which authority
can be attributed: a human user, a service account, a workload identity.

**Privilege escalation.** The acquisition of authority beyond that
intended for a principal. Vertical escalation acquires a higher level;
horizontal escalation acquires the authority of a peer.

**Role based access control (RBAC).** An authorisation model in which
permissions are assigned to roles and roles to principals. RBAC scales
administration well and expresses "who they are" naturally, but expresses
"under what conditions" poorly, which is why it is frequently combined with
attribute or level based rules.

**Separation of duties.** The requirement that a sensitive operation
involve more than one principal, so that no single compromised or
malicious identity can complete it alone.

**Standing privilege.** Authority held continuously rather than acquired
for a task and released after it. Standing privilege is the dominant
contributor to blast radius in most incident analyses, because it is
available to an attacker at the moment of compromise regardless of what
the legitimate holder was doing.

## Identity and Credential Terms

**Blast radius.** The set of resources an attacker reaches given the
compromise of a particular identity or component. Reducing blast radius is
usually more tractable than reducing the probability of compromise.

**Credential.** Material that proves an identity claim: a password, a
private key, a token. Credentials are secrets; identities are not.

**Just in time elevation.** The grant of additional authority for a bounded
window against a stated reason, after which it is withdrawn automatically.
It converts standing privilege into transient privilege at the cost of a
request step.

**Rotation.** The scheduled replacement of a credential, limiting the
window during which a leaked value remains useful. Rotation is only
effective if every consumer of the credential is known, which is why
unmanaged credentials are treated as a control failure rather than an
inconvenience.

**Secret sprawl.** The accumulation of credential material in places not
designed to hold it: repositories, ticket systems, chat logs, environment
files committed by accident. Sprawl defeats rotation because the inventory
of copies is unknown.

**Workload identity.** An identity assigned to a running process rather
than to a person, allowing the process to authenticate without a long lived
credential embedded in its configuration.

## Data and Retrieval Terms

**Data classification.** The assignment of a sensitivity level to data,
from which handling requirements follow. Classification is a property of
the data, distinct from the authorisation of any particular reader.

**Exfiltration.** The unauthorised transfer of data out of a controlled
environment. Exfiltration is distinguished from unauthorised access in that
the data leaves rather than merely being read.

**Indirect prompt injection.** The insertion of instructions into content
that a language model will later process as context, such that the model
treats the inserted text as direction rather than as data. The instruction
reaches the model through a legitimate retrieval path rather than through
the user's input.

**Redaction.** The removal or masking of sensitive material from a document
or response, leaving the surrounding content intact. Redaction based on the
shape of the material detects what it recognises and misses what it does
not.

**Retrieval augmented generation.** An architecture in which a language
model's response is conditioned on documents retrieved from a corpus at
query time, rather than on parametric knowledge alone.

**Retrieval poisoning.** The insertion of adversarial documents into a
corpus so that they are retrieved and influence generated output. The
attack is on the data store rather than on the model or the query.
