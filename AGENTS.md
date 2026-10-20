# Agent Instructions

This repository is the home of one Agent Skill, `build-a-skill`, which builds a new skill with
evals out of the conversation it is invoked in, plus the template that skill copies
(`skills/build-a-skill/assets/template/`).

Before starting any task, open [Workflow](docs/agents/workflow.md) and follow it.

When the user corrects wording, naming, scope, or policy, make that correction durable in the
relevant file under `docs/agents/`.

## More Detailed Instructions

- [Workflow](docs/agents/workflow.md)
- [Maintaining Agent Docs](docs/agents/maintaining-agent-docs.md)
- The template carries its own rules for the repositories it produces:
  [workflow](skills/build-a-skill/assets/template/docs/agents/workflow.md),
  [skill behavior](skills/build-a-skill/assets/template/docs/agents/skill-behavior.md),
  [evals](skills/build-a-skill/assets/template/docs/agents/evals.md).
