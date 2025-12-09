# Vibe Hacker - Claude Code Guidelines

## Project Status: GREENFIELD / PROTOTYPE

This project is **unreleased** with **zero external users**. Development is rapid iteration and experimentation.

## Critical: No Backwards Compatibility

When refactoring or making changes:

- **DELETE old code entirely** - do not deprecate, comment out, or keep "for reference"
- **Do NOT add backwards-compatibility shims**, re-exports, renamed `_unused` variables, or migration helpers
- **Do NOT document "the old way"** in comments - there is no old way, there are no users to migrate
- **If something is unused after a change, remove it completely**
- **Prefer clean breaks over gentle transitions**
- **No deprecation comments** like `// deprecated`, `// legacy`, `// old:`, `// TODO: remove after migration`

## Why This Matters

In prototype/greenfield projects, "helpful" backwards-compatibility code creates confusion:
- Comments about "the old API" when there was no old API
- Migration guides for users who don't exist
- Cruft that obscures the actual current implementation

## When Making Big Changes

1. Delete the old implementation entirely
2. Write the new implementation fresh
3. Update any imports/references to use the new code
4. Do not leave traces of the old approach in comments or docs

## Notes

- This is a Claude Code plugin for hacking, development workflows, and greenfield projects
- Target audience: developers who want expert agents, context priming, and greenfield mode
- Stack: Shell scripts, markdown, JSON configuration
