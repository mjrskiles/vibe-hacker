# Vibe Hacker - Claude Code Guidelines

## Project Status: GREENFIELD / PROTOTYPE

This project is **unreleased** with **zero external users**. Development is rapid iteration and experimentation.

## Replacing Code

Because there are no users to migrate, a change replaces code outright:

- Delete the old implementation and update imports and references to point at the new one.
- Leave out backwards-compatibility shims, re-exports, renamed `_unused` variables, migration helpers, deprecation comments, and migration docs.
- Remove anything that becomes unused as a result of the change.

Keeping the old approach around, even in comments, makes the current implementation harder to read.

## Notes

- This is a Claude Code plugin for hacking, development workflows, and greenfield projects
- Target audience: developers who want expert agents, context priming, and greenfield mode
- Stack: Shell scripts, markdown, JSON configuration
