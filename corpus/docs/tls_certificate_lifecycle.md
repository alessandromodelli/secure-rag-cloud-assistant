# TLS Certificate Lifecycle

This document describes how TLS certificates are issued, deployed, and renewed
for services and endpoints in the organization. It concerns the PKI plane and
does not cover identity, authorization, or user access.

## Issuance

Certificates are issued through the internal PKI or through the managed
certificate authority of the cloud provider, depending on where the endpoint
terminates. Public endpoints use publicly trusted certificates issued by the
managed authority; internal endpoints use certificates from the internal PKI
that chain to a private root. Both paths require the requester to prove
control over the target hostname before issuance proceeds.

## Deployment

For services running behind managed load balancers, certificate deployment is
handled by the load balancer itself: the operator selects the certificate at
configuration time and the load balancer serves it on the negotiated
handshake. For services that terminate TLS in-process, the certificate is
delivered through a sidecar that mounts the current material into the
container filesystem and reloads the server when the material changes.

## Renewal

Renewal is automated on a schedule tied to the certificate's remaining
validity. Managed certificates renew thirty days before expiry; certificates
issued from the internal PKI renew at half of their validity period, which is
shorter and therefore renews more often. Manual renewals are permitted only
for legacy endpoints scheduled for decommission.

## Expiry alerts

The certificate inventory tracks the expiry date of every issued certificate.
Alerts fire at thirty, fourteen, and three days before expiry so that a
missed automated renewal is caught before the certificate becomes invalid.
The three-day alert pages the owning team; earlier alerts are informational.

## Ownership

Every certificate has an owning team recorded at issuance. When ownership
changes — because a service is transferred, retired, or merged — the
inventory is updated so that renewal responsibility remains unambiguous.
