# Support Release and Image Verification

This runbook describes how the support engineering team confirms which
container image and release a customer is running while investigating an
incident. It covers how images are tagged, how a running workload is
traced back to the commit that produced it, and what support can and
cannot conclude from that trace. It does not cover how images are built
or deployed; those are owned by the service teams.

## How images are tagged

Application images are tagged with the git commit hash and, when the
commit is on the main branch, with the semantic version derived from the
release tag. The `latest` tag is not used, so a deployment always names
an image by commit hash or by version, never by a moving tag. This is
what makes an image traceable: the tag on the running pod is enough to
identify the exact source revision.

## Tracing a running workload to a release

Support reads the image reference on the running pod, takes the commit
hash or version from the tag, and matches it against the release notes to
state which release the customer is on. When the reported behavior
matches a change described in a later release, the finding is that the
customer is on an older revision and an upgrade is the likely fix, which
is stated in the escalation with the specific commit hash attached.

## Reading the image provenance

Every service builds in two stages: a build stage that produces the
compiled artifact and a runtime stage that copies only the artifact onto
a minimal base. Support does not rebuild images, but understanding the
multi-stage pattern lets support reason correctly about the running
image — for example, that build-time tooling is not present at runtime,
so a missing build tool is never the cause of a runtime symptom.

## What support does not conclude

Support does not assert that an image is compromised, does not compare
image digests against a signing authority, and does not read build-time
arguments. Sensitive material is never passed as a build argument by
convention, so support treats any apparent secret in an image reference
as a placeholder and escalates rather than acting on it.

## What support records

Support records the running image reference, the resolved commit hash or
version, and the matched release, and attaches them to the escalation so
the service team starts from a confirmed provenance picture.
