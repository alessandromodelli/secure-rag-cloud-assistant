# Engineering Onboarding Handbook

What a new engineer needs in the first two weeks. Public within the
organisation. This handbook points at other documents rather than
duplicating them; where it summarises, the referenced document governs.

## Week One

**Day one** is accounts and hardware. Identity is provisioned by IT before
you arrive and federates to every internal system, so there is no separate
password for the cloud console, the cluster or the repository host. If a
system asks you to create a local account, that system is misconfigured and
should be reported rather than worked around.

**Day two and three** are environment setup. Install the platform command
line tool, authenticate once, and confirm you can list workloads in your
team's namespace in the `dev` cluster. If the listing is empty, your team
membership has not propagated; this takes up to four hours and is not a
problem until it has been longer than that.

**Day four and five** are your first change. Every new engineer ships a
small change to a real service in their first week, through the normal
review and deployment path, with a buddy watching. The change is chosen to
be genuinely small and genuinely real. The point is not the change; the
point is that you have exercised the whole path once before you need it
under pressure.

## What Access You Have Immediately

Standard access is provisioned automatically with your identity. It covers
read and write in your team's namespace in the `dev` and `staging`
clusters, read access to the corresponding cloud resources, read access to
all internal documentation, and read access to every repository in the
engineering organisation.

Standard access does not cover the production cluster, secret material, or
cloud resources belonging to other teams. Access beyond the standard tier
is requested through the access portal, and the procedure is documented
separately. New engineers are encouraged not to request production access
in the first two weeks: almost nothing in the first two weeks requires it,
and the request is quicker to make later than it is to justify now.

## How We Work

**Changes go through review.** Every change to a service is reviewed by
someone other than the author before it merges. Review is about
correctness and comprehensibility, not about approval authority; a
reviewer who does not understand a change is expected to say so rather
than approve it.

**Deployment is continuous and reversible.** Merging to the main branch
deploys to `dev` automatically and to `staging` after the test suite
passes. Production deployment is a separate, explicit action. Every
deployment is reversible by redeploying the previous image, and doing so
is not an admission of failure.

**Incidents are blameless.** When something breaks, the review examines
the system that permitted the break, not the person who triggered it.
Engineers who broke something are expected to be the ones explaining what
happened, and this is treated as valuable rather than punitive. An engineer
who has never caused an incident has probably not shipped enough.

**Documentation lives with the thing it documents.** Service documentation
is in the service repository. Platform documentation is in the platform
repository and surfaced through the internal search. Documentation that
lives in a chat message does not exist.

## Where Things Are

The **access portal** handles requests for access beyond the standard
tier, including elevation to production namespaces. The access request
procedure document describes the tiers, the fields the request form
requires, and the approval paths.

The **platform documentation** covers the clusters, deployment standards,
health checking, resource management and naming conventions. Start with the
Kubernetes operations guide if you are deploying anything.

The **security glossary** defines the vocabulary used across all of the
above. It is worth twenty minutes early rather than a confused hour later.

The **service catalogue** lists every service, its owning team, its
dependencies and its on call rotation. If you need to know who owns
something, start there rather than asking in a channel.

## Things That Surprise New Engineers

Namespaces are named after services, without an environment prefix, because
the cluster already encodes the environment. A namespace called
`payment-service` exists in all three clusters and means something
different in each.

Secret objects can be referenced but not read. A service can consume a
credential without any engineer on the team being able to see its value.
This is deliberate and is not a permissions bug.

The `dev` cluster is reset every Sunday. Anything you leave running there
disappears, including anything you were debugging on Friday.

Elevated access expires on a timer regardless of what you are doing. The
thirty minute warning is your cue to finish or to request an extension, not
a suggestion.

## Asking for Help

Ask in your team channel first and the platform channel second. Questions
in the platform channel should say what you tried, which cluster and
namespace, and what the error was. Questions without those three things
receive a request for them, which costs everyone a round trip.

There is no expectation that you know any of this in the first month. There
is an expectation that you ask rather than guess when the guess involves
production.
