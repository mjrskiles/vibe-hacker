# FDP-001: Firmware Project Setup Wizard

## Status

Proposed

## Summary

A project setup wizard/agent that generates opinionated firmware project scaffolding based on configurable templates. The wizard guides users through MCU selection, peripheral configuration, and project structure decisions, then generates a complete project with build system, HAL stubs, planning docs, and Claude Code integration pre-configured.

## Motivation

Starting a new firmware project involves significant boilerplate:

- Build system configuration (CMake with AVR/ARM/x86 targets)
- Hardware abstraction layer structure
- Test framework integration (Unity)
- Simulator scaffolding for hardware-free development
- Planning documentation structure (FDPs, ADRs, action plans)
- Claude Code integration (priming, greenfield mode, settings)

The gatekeeper project represents a well-refined approach to these concerns. Rather than copying and manually adapting that project each time, a wizard can:

1. Capture opinionated best practices in templates
2. Parameterize MCU-specific details
3. Generate consistent, ready-to-build projects
4. Reduce time from "idea" to "blinking LED" to minutes

## Detailed Design

### Overview

The system consists of three components:

1. **Template Library** - Parameterized project templates (files, directories, code stubs)
2. **Configuration Schema** - Defines available MCU families, peripherals, and project options
3. **Wizard Agent** - Interactive agent that gathers requirements and generates projects

```
┌─────────────────────────────────────────────────────────────┐
│                     Wizard Agent                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Gather     │→ │  Validate   │→ │  Generate Project   │  │
│  │  Config     │  │  Choices    │  │  from Templates     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         ↑                                      ↓
┌─────────────────┐                 ┌─────────────────────────┐
│ User Responses  │                 │  Generated Project      │
│ (AskUserQuestion)│                │  ├── CMakeLists.txt     │
└─────────────────┘                 │  ├── src/               │
                                    │  ├── test/              │
         ↑                          │  ├── sim/               │
┌─────────────────┐                 │  ├── docs/planning/     │
│ Config Schema   │                 │  └── .claude/           │
│ (mcu-families,  │                 └─────────────────────────┘
│  peripherals)   │
└─────────────────┘
```

### Template Library Structure

```
templates/
├── project/                    # Full project templates
│   ├── attiny/                 # ATtiny-specific template
│   │   ├── CMakeLists.txt.tmpl
│   │   ├── src/
│   │   │   ├── main.c.tmpl
│   │   │   └── hardware/
│   │   │       ├── hal.h.tmpl
│   │   │       └── hal.c.tmpl
│   │   ├── test/
│   │   │   ├── CMakeLists.txt.tmpl
│   │   │   └── unit/
│   │   │       └── mocks/
│   │   │           └── mock_hal.c.tmpl
│   │   └── sim/
│   │       └── sim_hal.c.tmpl
│   │
│   └── stm32/                  # STM32-specific template (future)
│
├── components/                 # Reusable component templates
│   ├── fsm/                    # State machine engine
│   ├── debounce/               # Input debouncing
│   ├── neopixel/               # WS2812B driver
│   └── eeprom/                 # EEPROM with wear leveling
│
├── docs/                       # Documentation templates
│   ├── README.md.tmpl
│   ├── ARCHITECTURE.md.tmpl
│   └── planning/
│       ├── feature-designs/
│       │   └── template.md
│       ├── action-plans/
│       │   └── template.md
│       └── decision-records/
│           └── template.md
│
└── claude/                     # Claude Code integration
    ├── CLAUDE.md.tmpl
    ├── firmware-hacker.json.tmpl
    ├── prime.json.tmpl
    └── settings.local.json.tmpl
```

### Configuration Schema

```json
{
  "project": {
    "name": "string",
    "description": "string",
    "author": "string"
  },
  "mcu": {
    "family": "attiny | stm32 | rp2040 | esp32",
    "model": "string (e.g., attiny85, stm32f103)",
    "clock_hz": "number",
    "flash_kb": "number",
    "sram_bytes": "number",
    "eeprom_bytes": "number (optional)"
  },
  "peripherals": {
    "gpio": ["list of pin definitions"],
    "timers": ["timer configurations"],
    "uart": "boolean",
    "spi": "boolean",
    "i2c": "boolean",
    "adc": ["channel list"],
    "pwm": ["channel list"]
  },
  "features": {
    "simulator": "boolean (default: true)",
    "unit_tests": "boolean (default: true)",
    "fsm_engine": "boolean",
    "neopixel": "boolean",
    "eeprom_wear_leveling": "boolean"
  },
  "project_type": "eurorack | standalone | library"
}
```

### Wizard Agent Workflow

The wizard agent (`agents/project-wizard.md`) follows this flow:

1. **Project Basics**
   - Project name, description, author
   - Project type (Eurorack module, standalone device, library)

2. **MCU Selection**
   - Family selection (ATtiny, STM32, RP2040, ESP32)
   - Specific model selection (filtered by family)
   - Validate memory constraints

3. **Peripheral Configuration**
   - Which peripherals are needed?
   - Pin assignments (with conflict detection)
   - Timer allocation

4. **Feature Selection**
   - Include simulator? (recommended)
   - Include unit tests? (recommended)
   - Optional components (FSM, debounce, NeoPixel, etc.)

5. **Generation**
   - Create project directory
   - Expand templates with configuration
   - Initialize git repository
   - Run initial build to validate

6. **Next Steps**
   - Summary of generated project
   - Suggested first action plan
   - How to invoke `/prime` in new project

### Template Syntax

Templates use a simple interpolation syntax:

```c
// {{project.name}} - {{project.description}}
// Author: {{project.author}}
// Target: {{mcu.family}} {{mcu.model}} @ {{mcu.clock_hz}}Hz

#include "hal.h"

int main(void) {
    hal_init();

    while (1) {
        // Main loop
    }
}
```

Conditional sections:

```c
{{#if features.fsm_engine}}
#include "fsm/fsm.h"
{{/if}}

{{#if peripherals.uart}}
#include "uart.h"
{{/if}}
```

### MCU Family Support

**Phase 1 (Initial):**
- ATtiny (85, 84, 1614, etc.) - Based on gatekeeper patterns

**Phase 2 (Future):**
- STM32 (F1, F4, L4 series)
- RP2040
- ESP32

Each family has:
- Toolchain configuration (avr-gcc, arm-none-eabi-gcc, etc.)
- HAL patterns specific to the architecture
- Memory layout and linker scripts
- Fuse/option byte configuration

### Error Handling

- Validate pin conflicts before generation
- Check memory constraints (will code fit?)
- Verify toolchain availability (warn if missing)
- Graceful fallback if optional tools missing

### Testing Strategy

1. **Template validation** - Ensure all templates expand without errors
2. **Generated project builds** - Integration test that generates and builds
3. **MCU-specific tests** - Validate each MCU family template

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `agents/project-wizard.md` | Create | Wizard agent definition |
| `commands/new-project.md` | Create | `/new-project` command |
| `templates/project/attiny/` | Create | ATtiny project template |
| `templates/components/` | Create | Reusable component templates |
| `templates/docs/` | Create | Documentation templates |
| `templates/claude/` | Create | Claude Code integration templates |
| `config/mcu-families.json` | Create | MCU configuration schema |
| `scripts/generate-project.sh` | Create | Template expansion script |

## Dependencies

- `jq` - JSON processing (already required)
- `envsubst` or similar - Template variable expansion
- MCU toolchains - For build validation (optional)

## Alternatives Considered

### Cookiecutter / Yeoman

Using existing scaffolding tools.

**Rejected:** Adds external dependencies, doesn't integrate with Claude agent workflow, less control over interactive flow.

### Simple file copy with sed

Copy gatekeeper and use sed to replace names.

**Rejected:** Too fragile, doesn't handle conditional sections, no validation.

### Prompt-only approach

Just use Claude to write files from scratch each time.

**Rejected:** Inconsistent output, doesn't capture best practices, slower.

## Open Questions

1. **Template engine choice** - Use shell/envsubst, or implement in Python/JS?
2. **Component dependencies** - How to handle components that require other components?
3. **Toolchain detection** - How aggressively to check for installed tools?
4. **Project location** - Generate in current dir, or ask for path?
5. **STM32 complexity** - STM32 has CubeMX integration; how much to replicate?

## Implementation Checklist

- [ ] Create template directory structure
- [ ] Port gatekeeper patterns to ATtiny template
- [ ] Implement project-wizard agent
- [ ] Create /new-project command
- [ ] Implement template expansion (scripts/generate-project.sh)
- [ ] Add MCU configuration schema
- [ ] Create documentation templates
- [ ] Create Claude Code integration templates
- [ ] Add component templates (FSM, debounce, neopixel)
- [ ] Integration test: generate and build ATtiny project
- [ ] Documentation: Update README with wizard usage
