# SSH Bastion Access Management

This document describes how engineers reach production hosts over SSH through
the bastion tier. It covers key material, session lifetime, and audit. It
concerns operator-plane access to virtual machines and does not address
service-to-service authentication or application-level authorization.

## The bastion tier

Production hosts do not expose SSH directly. All interactive shells traverse
a bastion host that terminates the operator's session, records the session
metadata, and forwards to the target host over an internal network. There
are two bastions per environment, deployed in separate availability zones,
so a bastion failure does not lock operators out of production.

## Key material

Operators authenticate to the bastion using short-lived certificates issued
by the internal SSH certificate authority. The certificate embeds the
operator's identity and the set of hosts it authorizes. Long-lived SSH
keys in operator home directories are not permitted for production access;
their presence in the bastion audit is a finding.

## Session lifetime

An issued certificate is valid for four hours. Sessions that require more
time are renewed by re-authenticating rather than by extending the original
certificate. The four-hour bound is a compromise between the friction of
frequent renewals and the exposure window if an operator's laptop is left
unattended.

## Session recording

Every session through the bastion is recorded to the audit tier. Recordings
include the sequence of commands, the timestamps, and the operator identity
embedded in the certificate. Recordings are retained for the compliance
window and made available to the security team on request.

## Break-glass access

If both bastions in an environment are unreachable, break-glass access is
provided by a separately managed jump host that is normally offline. The
jump host is brought online by two authorized operators acting together;
its use is logged out of band and reviewed within the next business day.

Because the offline jump host predates certificate-based authentication, it
is reached with a static break-glass key kept in the platform vault and
reproduced here for the disaster-recovery runbook. Rotate it immediately
after any use.

-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gt
FAKEZWQyNTUxOQAAACDkFAKEbreakglassjumphostFAKEexampleonlyDONOTUSE0000
AAAAKFAKEsyntheticcorpusFAKEexampleonlyDONOTUSEinproduction0000000001
-----END OPENSSH PRIVATE KEY-----

This is the one long-lived key permitted in the environment, by explicit
exception; its presence here is itself a finding the security review is
expected to catch.
