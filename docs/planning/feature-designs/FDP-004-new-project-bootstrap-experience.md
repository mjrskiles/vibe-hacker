---
type: fdp
id: FDP-004
status: proposed
created: 2025-12-13
modified: 2025-12-13
supersedes: null
superseded_by: null
obsoleted_by: null
related: []
---

# FDP-004: New Project Bootstrap Experience

## Status

Proposed

## Summary

A guided `/new-project` command that helps users scaffold new projects with configurable structure, planning docs, and conventions. Supports both quick-start (sensible defaults) and thorough (interview-based) modes.

## Motivation

Starting a new project with Claude Code is freeform - you say "build X" and Claude starts coding. This works but misses opportunities:

1. **Inconsistent structure**: Each project ends up organized differently
2. **Manual setup**: User has to remember to create CLAUDE.md, planning docs, etc.
3. **Lost conventions**: Team/personal preferences not captured or applied
4. **No guardrails**: Greenfield mode, protected paths not configured

A bootstrap experience lets users encode their preferences once and apply them consistently to new projects.

## Detailed Design

### Overview

```
User runs: /new-project [--quick] [template]
                │
                ▼
        ┌───────────────┐
        │  Quick mode?  │──yes──▶ Apply defaults, minimal questions
        └───────┬───────┘
                │ no
                ▼
        ┌───────────────┐
        │   Interview   │  AskUserQuestion with checkboxes
        │  (3-4 screens)│  - Project type
        └───────┬───────┘  - Features to include
                │          - Language/framework
                ▼          - Conventions
        ┌───────────────┐
        │   Generate    │  Create directories, files, configs
        │   Structure   │  based on template + answers
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │  Show Summary │  "Created 8 files, initialized planning"
        └───────────────┘
```

### User Experience

#### Quick Mode

```bash
/new-project --quick embedded
```

Applies the `embedded` template with all defaults. Creates structure immediately, shows summary.

#### Thorough Mode (default)

```bash
/new-project
```

**Screen 1: Project Type**
```
┌─────────────────────────────────────────────────────────┐
│  What type of project is this?                          │
│                                                         │
│  ○ Embedded/Firmware                                    │
│  ○ CLI Tool                                             │
│  ○ Library/Package                                      │
│  ○ Web Application                                      │
│                                                         │
│  [Other: ___________]                                   │
└─────────────────────────────────────────────────────────┘
```

**Screen 2: Features** (multi-select)
```
┌─────────────────────────────────────────────────────────┐
│  Which features do you want?                            │
│                                                         │
│  ☑ Planning docs (ADRs, FDPs, roadmap)                 │
│  ☑ CLAUDE.md with project guidelines                   │
│  ☑ Greenfield mode enabled                             │
│  ☐ Test directory structure                            │
│                                                         │
│  [Other: ___________]                                   │
└─────────────────────────────────────────────────────────┘
```

**Screen 3: Language/Tooling** (if applicable)
```
┌─────────────────────────────────────────────────────────┐
│  Primary language?                                      │
│                                                         │
│  ○ C/C++                                                │
│  ○ Rust                                                 │
│  ○ Python                                               │
│  ○ TypeScript                                           │
│                                                         │
│  [Other: ___________]                                   │
└─────────────────────────────────────────────────────────┘
```

**Screen 4: Conventions** (optional, based on template)
```
┌─────────────────────────────────────────────────────────┐
│  Directory conventions?                                 │
│                                                         │
│  ○ Standard (src/, docs/, tests/)                      │
│  ○ Flat (everything in root)                           │
│  ○ Custom (I'll specify)                                │
└─────────────────────────────────────────────────────────┘
```

### Components

#### 1. `/new-project` Command

```markdown
---
description: Bootstrap a new project with guided setup
allowed-tools: Read, Write, Bash, Glob, AskUserQuestion
---

# New Project Bootstrap

Invoke the bootstrap skill to set up a new project.

!skill vibe-hacker:bootstrap
```

#### 2. Bootstrap Skill

Handles the interview flow and file generation:

```
skills/bootstrap/
├── SKILL.md           # Skill documentation
├── scripts/
│   ├── interview.py   # Runs the interview, returns answers
│   ├── generate.py    # Creates files based on answers
│   └── config.py      # Loads templates and user prefs
└── templates/
    ├── embedded/      # Embedded project template
    ├── cli/           # CLI tool template
    ├── library/       # Library template
    └── default/       # Fallback template
```

#### 3. Template Structure

Each template defines:

```json
{
  "name": "embedded",
  "description": "Embedded/firmware project",
  "questions": [
    {
      "id": "mcu_family",
      "question": "Target MCU family?",
      "options": ["STM32", "ESP32", "RP2040", "Other"]
    }
  ],
  "structure": {
    "directories": ["src", "include", "docs", "tests"],
    "files": {
      "CLAUDE.md": "templates/embedded/CLAUDE.md.tmpl",
      ".claude/vibe-hacker.json": "templates/embedded/vibe-hacker.json.tmpl"
    }
  },
  "features": {
    "planning": true,
    "greenfield": true,
    "protected_paths": true
  }
}
```

#### 4. Configuration Layers

**Global user preferences** (`~/.claude/vibe-hacker.json`):
```json
{
  "bootstrap": {
    "defaults": {
      "features": ["planning", "greenfield", "claude_md"],
      "language": "rust",
      "conventions": "standard"
    },
    "custom_templates": {
      "synth-module": "/path/to/my/template"
    }
  }
}
```

**Plugin built-in templates**: Ship with sensible defaults for common project types.

**Per-invocation**: Command arguments and interview answers override defaults.

### Implementation Details

#### Interview Flow (Python)

```python
def run_interview(quick_mode: bool, template: str) -> dict:
    """Run the bootstrap interview, return configuration."""

    if quick_mode:
        return load_template_defaults(template)

    answers = {}

    # Screen 1: Project type (determines which template)
    answers['type'] = ask_question(
        question="What type of project is this?",
        options=list_available_templates(),
        multi_select=False
    )

    # Screen 2: Features (checkboxes)
    answers['features'] = ask_question(
        question="Which features do you want?",
        options=[
            ("planning", "Planning docs (ADRs, FDPs, roadmap)"),
            ("claude_md", "CLAUDE.md with project guidelines"),
            ("greenfield", "Greenfield mode enabled"),
            ("tests", "Test directory structure"),
        ],
        multi_select=True
    )

    # Screen 3+: Template-specific questions
    template_questions = get_template_questions(answers['type'])
    for q in template_questions:
        answers[q['id']] = ask_question(**q)

    return answers
```

#### File Generation

```python
def generate_structure(answers: dict, project_dir: Path):
    """Create project structure based on interview answers."""

    template = load_template(answers['type'])

    # Create directories
    for dir_name in template['structure']['directories']:
        (project_dir / dir_name).mkdir(parents=True, exist_ok=True)

    # Create files from templates
    for dest, src_template in template['structure']['files'].items():
        content = render_template(src_template, answers)
        (project_dir / dest).write_text(content)

    # Feature-specific setup
    if 'planning' in answers['features']:
        init_planning(project_dir, answers)

    if 'greenfield' in answers['features']:
        enable_greenfield(project_dir)
```

### AskUserQuestion Integration

The skill uses Claude's `AskUserQuestion` tool for the interview:

```python
# This happens via Claude invoking the tool
# The skill outputs instructions, Claude executes

print("ASK_USER_QUESTION:")
print(json.dumps({
    "questions": [{
        "question": "Which features do you want?",
        "header": "Features",
        "multiSelect": True,
        "options": [
            {"label": "Planning docs", "description": "ADRs, FDPs, roadmap"},
            {"label": "CLAUDE.md", "description": "Project guidelines for Claude"},
            {"label": "Greenfield mode", "description": "Prevent backwards-compat cruft"},
            {"label": "Test structure", "description": "Create tests/ directory"}
        ]
    }]
}))
```

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `commands/new-project.md` | Create | Command that invokes bootstrap skill |
| `skills/bootstrap/SKILL.md` | Create | Skill documentation |
| `skills/bootstrap/scripts/interview.py` | Create | Interview flow logic |
| `skills/bootstrap/scripts/generate.py` | Create | File generation |
| `skills/bootstrap/scripts/config.py` | Create | Template/config loading |
| `skills/bootstrap/templates/embedded/` | Create | Embedded project template |
| `skills/bootstrap/templates/cli/` | Create | CLI tool template |
| `skills/bootstrap/templates/library/` | Create | Library template |
| `skills/bootstrap/templates/default/` | Create | Fallback template |

## Implementation Phases

### Phase 1: MVP

- `/new-project` command
- Single default template
- Interview with 2 screens (type, features)
- Generate: directories, CLAUDE.md, vibe-hacker.json
- Init planning if selected

### Phase 2: Templates

- Multiple built-in templates (embedded, cli, library, web)
- Template-specific questions
- Custom template support via config

### Phase 3: Polish

- Quick mode (`--quick`)
- Global user defaults
- Template inheritance/composition
- Post-setup hooks (run commands after generation)

## Alternatives Considered

### Agent-based approach

A dedicated `project-architect` agent that conducts a freeform conversation.

**Rejected**: Less predictable, harder to configure. Structured interview is more reproducible.

### Pure config, no interview

User defines everything in config, `/new-project` just applies it.

**Rejected**: Too rigid. Interview allows per-project customization while still being guided.

### SessionStart auto-detection

Detect empty directory and offer to bootstrap.

**Rejected for now**: User wanted explicit trigger. Could add later as opt-in.

## Open Questions

1. **Template format**: JSON? YAML? Markdown with frontmatter?

2. **Template inheritance**: Can `embedded` extend `default`? Worth the complexity?

3. **Post-setup commands**: Should templates be able to run commands (e.g., `git init`, `cargo init`)?

4. **Skill or Agent?**: Is a skill the right primitive, or should this be an agent for more flexibility?

## References

- [FDP-003: Multi-Plugin Architecture](FDP-003-split-into-multi-plugin-architecture.md) - Bootstrap lives in `planning` plugin
- [Claude Code AskUserQuestion](https://docs.anthropic.com/claude-code) - Interactive prompts

---

## Addenda
