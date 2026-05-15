# AWS IAM Best Practices (Summary)

## Principle of Least Privilege

Grant only the permissions required to perform a task. Start with a minimum set of
permissions and grant additional permissions as necessary.

## Avoid Wildcards

Avoid using `"Action": "*"` or `"Resource": "*"` in policies. Explicitly list the
actions and resources required.

## Use IAM Roles, Not Long-Term Keys

For EC2 instances, Lambda functions, and other AWS services, use IAM roles
instead of embedding long-term access keys.

## Enable MFA

Require multi-factor authentication for privileged users and for sensitive
operations such as deleting resources.

## Rotate Credentials Regularly

Access keys for IAM users should be rotated at least every 90 days. Unused
credentials should be removed.
