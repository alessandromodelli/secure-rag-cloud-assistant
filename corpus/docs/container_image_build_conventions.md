# Container Image Build Conventions

This document describes how application container images are built,
tagged, and published in the internal registry. It covers the base
image policy, the multi-stage build pattern used across services, and
the tagging convention that ties an image back to the commit that
produced it. It does not cover deployment or runtime configuration.

## Base images

Application images are built on the organization's curated base
images. The curated set is a small list of distroless and minimal
Debian variants maintained by the platform team, rebuilt weekly with
current security patches. Using a base image outside the curated set
is permitted only with an exception recorded in the service's
inventory entry.

## Multi-stage builds

Every service builds in two stages: a build stage that produces the
compiled artifact and a runtime stage that copies only the artifact
onto a minimal base. The build stage carries the compiler toolchain,
the language runtime used at build time, and any tooling needed for
tests; none of these are present in the runtime stage. This keeps the
production image small and reduces the attack surface at runtime.

## Build-time arguments

Build-time arguments are limited to values that are safe to bake into
the image: the version string, the build timestamp, the commit hash,
and the target platform. Sensitive material is never passed as a
build argument; the risk is that the argument is embedded into an
image layer and survives even if it is overwritten later.

## Tagging

Images are tagged with the git commit hash and, when the commit is on
the main branch, with the semantic version derived from the release
tag. The latest tag is not used in this convention; deployments always
name an image by commit hash or version, never by a moving tag.

## Publishing

Images are published to the internal registry only. The publication
step is part of the continuous integration pipeline and runs
automatically on every merge to the main branch. Publication to any
external registry is not supported.

## Vulnerability scanning

Every published image is scanned as part of the publication step.
Findings above the configured severity threshold block the image from
being deployed until they are either fixed or explicitly waived. The
scan runs against the built image rather than only against the base
so that dependencies pulled during the build are also covered.
