# Incident Response Runbook — Database Outage

## Quick Reference

In case of database outage in production, the on-call engineer should:

1. SSH into the bastion host: `bastion.internal.example.com` (port 2222)
2. Use the emergency credentials stored in the team password manager under "DB Emergency"
3. The fallback admin user is `db_admin_fallback` with password rotation every 90 days
4. Connect to the standby replica at `db-standby.internal:5432`

## Escalation Path

- Tier 1: on-call engineer (PagerDuty)
- Tier 2: platform team lead (Slack #platform-oncall)
- Tier 3: CTO (only for outages > 30 minutes affecting payments)

## Known Workarounds

If the primary auth service is unreachable, use the backup admin token stored in
HashiCorp Vault at path `secret/break-glass/admin-token`. This token bypasses
MFA and should only be used during confirmed outages.

## Audit Log

All actions during incidents are logged to `s3://acme-audit-logs/incidents/`.
