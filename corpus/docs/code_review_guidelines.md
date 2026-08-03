# Code Review Guidelines

This document describes how code review is conducted in the engineering
organization. It covers what reviewers look for, how authors should prepare a
change for review, and the approval rules that gate merging.

## What review is for

Code review has three purposes. It catches defects before they reach the main
branch, it keeps the codebase readable by more than one person, and it spreads
knowledge across the team. It is not a substitute for automated testing and it
is not a debate club. The reviewer's job is to help the change land in good
shape, not to prove they could have written it differently.

## Preparing a change

Small changes get better reviews than large ones. A pull request that touches
more than roughly four hundred lines of non-generated code should be split
whenever the change can be decomposed without losing coherence. The
description should state what the change does, why it is needed, and what the
author considered and rejected. If the change is user-visible, screenshots or
a short recording help.

Every change carries automated checks: unit tests, linting, and where relevant
static analysis. Authors run these locally before requesting review; a red
build wastes the reviewer's attention.

## Approval rules

A change to application code requires one approval from a reviewer who is not
the author. Changes to shared libraries, build configuration, or anything
labelled infrastructure require two approvals, one of which must come from the
team that owns the affected area. The author is responsible for identifying
the right reviewers; the tooling suggests candidates based on file ownership.

## Style and tone

Comments are directed at the code, not at the person. Reviewers phrase
suggestions as questions when the intent is unclear and as concrete
suggestions when they have a specific alternative in mind. Authors are not
required to accept every suggestion, but a rejection needs a short reason so
the reviewer knows the point was considered.

## Turnaround

Reviews are answered within one working day. If a reviewer cannot look at a
change within that window, they reassign it rather than let it sit. Reviewers
do not block on stylistic preferences that a linter would catch; those get
addressed by the tool, not by discussion.
