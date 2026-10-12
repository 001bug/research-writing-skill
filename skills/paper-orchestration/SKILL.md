---
name: paper-orchestration
description: Use when a research-writing task spans multiple sections, medium-sized revisions, full-paper drafting, or repeated quality failures
---

## DSH 运行约定

仅在 DeepSeek Harness 中适用：先根据 `skill` 工具返回的 `resourceBase.path`
解析真实技能目录，再读取资源根目录的 `.dsh/RUNTIME.md`，按其中约定执行。
不要猜测仓库位置，也不要假定当前目录就是技能仓库。

```bash
# 将占位符替换为本次 skill 工具返回的 resourceBase.path（保留引号）。
SKILL_DIR="$(realpath '<resourceBase.path>')"
RESEARCH_WRITING_ROOT="$(dirname "$(dirname "$SKILL_DIR")")"
RESEARCH_WRITING_PYTHON="${DSH_HOME:-$HOME/.dsh}/research-writing/.venv/bin/python"
PAPER_ROOT="$(pwd -P)"
cat "$RESEARCH_WRITING_ROOT/.dsh/RUNTIME.md"
```

脚本与内置模板使用资源根目录的绝对路径；论文、用户模板和计划写入当前论文工作区。
以上变量只在当前 shell 调用有效，后续调用应重新设置或使用已经解析的绝对路径。

# Paper Orchestration

This skill controls the workflow around the writing skills. It prevents "one prompt writes the paper" behavior by forcing stage detection, task packets, review gates, and a capability-use audit.

## Hard Gate

For any medium task or full-paper task, do not write manuscript text until these exist or are created:

- `plan/project-overview.md`
- `plan/outline.md`
- `plan/progress.md`
- a task packet for the current section or deliverable
- for full-paper drafting or redrafting, `plan/chapter-architecture.md`

Medium task means any request that affects more than one paragraph, one subsection, one chapter, one figure/table set, or any claim tied to references or experiments.

## Full-Paper Redraft Gate

For a full-paper draft, the controller must first lock the chapter architecture. Do not inherit an old chapter split if the user, target venue, or paper type implies a different structure.

For computer science / engineering SCI papers, use this body structure unless the user or target template explicitly requires otherwise:

1. Introduction, with related work integrated into the motivation and research-gap argument.
2. Methodology.
3. Dataset and Experimental Setting, either standalone or integrated into Methodology/Results when short.
4. Experimental Results and Analysis.
5. Discussion.

Abstract, Conclusion, and References may be generated as supporting files, but they must not hide weak body chapters or inflate the chapter count. A standalone Related Work chapter is only allowed when the target outline explicitly demands it.

Create `plan/chapter-architecture.md` before drafting. It must list the exact required chapter files, target role, minimum body length, owner agent, and whether the chapter may use planning placeholders.

```markdown
## Required chapter files
- chapters/01_Introduction.md | role=introduction | min_chars=4500 | agent=required | placeholders=no
- chapters/02_Methodology.md | role=methodology | min_chars=4500 | agent=required | placeholders=no
```

If this file exists, the quality gate must treat extra or missing chapter files as failures.

## Chapter roles for the Python gate

Each entry in `plan/chapter-architecture.md` must declare `role=` independently of its filename.
Allowed roles: `abstract`, `introduction`, `related-work`, `methodology`, `body`,
`empirical-results`, `discussion`, `conclusion`, `references`, `acknowledgements`.
Use Chinese or English filenames, including spaces. Add `min_citations=` and
`min_paragraphs=` when the school's requirements differ from the gate defaults.
Existing plans without roles must be reviewed and updated explicitly; do not infer roles from numbering.
Citation-marker counts are structural checks, not proof that a source exists or supports a claim.

## DSH chapter delegation

When running in DSH, inspect the currently exposed tools before delegation.
Use native `subagent` with `description` and a complete standalone `prompt`.
Include the absolute paper workspace, task packet path, required skill names,
exclusive chapter ownership, relevant sources and acceptance checks.
Omit provider/model to inherit the configured defaults; use `run_in_background: false`
when the next action depends on that chapter's result. For background runs, consume
DSH's completion notice and inspect the chapter before recording `status=ACCEPTED`.
A launch receipt is not a completed chapter. Use only the current tool schema.
If `subagent` is unavailable, ask whether the user accepts the original degraded
single-agent workflow and record that decision; never invent an agent provenance entry.

## Multi-Agent Chapter Gate

For any full-paper draft or redraft, the controller must not write all chapters itself. It must:

- create one task packet per major chapter;
- dispatch a separate fresh agent for each major chapter;
- give each agent only the relevant task packet, source excerpts, evidence map, experiment protocol, and hard rejection checks;
- assign disjoint write ownership so that two agents never edit the same chapter file;
- record the agent, prompt summary, inputs, output path, and review status in `plan/chapter-agent-provenance.md`;
- perform a controller review after agent output before claiming progress.

If subagents are not available, stop and ask the user whether to continue in degraded single-agent mode. Do not silently fall back to one-pass generation.

## Stage Detection

Classify the current work before acting:

| Stage | Trigger | Required next skill |
|---|---|---|
| S0 Scope | topic, target, structure unclear | `brainstorming-research` |
| S1 Evidence | references, Introduction, Related Work | `evidence-driven-writing` + `literature-review` |
| S2 Method | model, algorithm, system, method section | `writing-chapters` with method flow gate |
| S3 Experiments | setup, results, tables, charts | `experiment-results-planning` + `figures-python` |
| S4 Drafting | section text | `writing-chapters` |
| S5 Review | quality, consistency, submission risk | `peer-review` + `verification` |

Record the stage in `plan/progress.md`.

## Task Packet

Before dispatching a section task, create a persistent packet under `plan/task-packets/`. Conversation-only packets are not acceptable for medium or full-paper work because they cannot be audited later.

```markdown
## Task Packet
- Scope:
- Files to read:
- Files allowed to edit:
- Required skills:
- Evidence/data inputs:
- Required artifacts:
- Rejection checks:
- Validation commands:
```

Subagents must receive the task packet, not the entire vague project. If subagents are available, split independent work into literature mapping, method architecture, experiment planning, figure generation, and review. Do not let multiple agents edit the same file.

For chapter-writing packets, add:

- Target chapter file and exclusive owner.
- Required argument chain, in paragraph roles rather than bullet content.
- Minimum prose length.
- Required sources and data artifacts.
- Prohibited structure, especially bullet-like lists, process notes, and old chapter scaffolding.
- Required handoff format: status, file path changed, unresolved evidence/data gaps, and self-review.

## Review Gates

Every medium task needs two reviews before completion:

1. Spec compliance review: did the output match the task packet and required artifacts?
2. Quality review: are claims supported, section logic coherent, and manuscript pollution absent?

If either review fails, fix before moving to the next task.

## Capability-Use Audit

At the end of every medium task, write a short audit in `plan/progress.md`:

```markdown
### Capability-use audit
- Required skills:
- Skills actually used:
- Inputs consumed:
- Inputs not used and why:
- Artifacts produced:
- Verification run:
- Remaining risk:
```

The task is not complete without this audit.

## Common Failures

- Treating user instructions as manuscript content. Convert instructions into structure or edits; never paste them into the body.
- Claiming a section is "done" when it only has headings and placeholders.
- Running style checks while skipping evidence, data, and claim checks.
- Producing tables instead of prose to hide weak argumentation.
- Keeping an old chapter split after the user rejects it. Rebuild the chapter architecture first.
- Letting the controller write a full manuscript sequentially instead of using one independent agent per major chapter.
- Accepting short, enumerative prose because it passes keyword checks. Length, paragraph flow, evidence use, and agent provenance must all be reviewed.
