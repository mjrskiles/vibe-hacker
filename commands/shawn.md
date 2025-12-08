---
description: Invoke Shawn for educational review (onboarding|concepts|examples|depth|full)
allowed-tools: Read, Grep, Glob, Bash, Task
argument-hint: [review-type]
---

# Shawn Educational Review Request

Invoke the Shawn subagent to review this project as a learning resource.

**Review type requested**: $ARGUMENTS

If no review type specified, ask the user what aspect they'd like reviewed, or suggest a full review to understand the project's educational potential.

**Review types available:**
- `onboarding` - First five minutes experience, setup friction, initial success
- `concepts` - Concept clarity, learning progression, mental models
- `examples` - Example quality, progression, runnability
- `depth` - Challenge gradient, growth pathways, independence building
- `full` - Comprehensive educational review (all of the above)

**Current project context:**
!ls -la
!head -50 README.md 2>/dev/null || echo "No README found"
!ls -la docs/ 2>/dev/null || echo "No docs/ directory"
!ls -la examples/ 2>/dev/null || echo "No examples/ directory"

Spawn Shawn to perform the requested review. Shawn should:
1. Approach with a learner's mindset
2. Identify the learning journey through the project
3. Spot friction points and "aha!" moments
4. Suggest improvements that help learners grow

Remember: Shawn is warm, curious, and focused on sparking understanding. The goal is to make learners feel smart, not intimidated.
