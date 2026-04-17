# /autoreason — Adversarial Multi-Agent Refinement

Refine any task through iterative adversarial critique, rewrite, synthesis, and blind judging. Produces the highest-quality output by pitting multiple agents against each other until convergence.

## Instructions

Dispatch the `autoreason` agent. Pass the user's full input as the task prompt.

The agent handles all iteration internally: Author → Strawman → B-rewrite → AB-synthesize → 3 Blind Judges → Borda count → convergence check. Loops until the incumbent wins twice (streak=2) or max rounds reached.

Optional modifiers the user can specify:
- **"max N rounds"** — set max_rounds cap (default 5)
- **"starting from: [text]"** — provide an initial draft to skip the Author A step and go straight into adversarial refinement

## Example usage

```
/autoreason Write a cold outreach email to a pizza chain about Pathfinder POS
/autoreason max 3 rounds: Draft a product requirements doc for kiosk ordering
/autoreason starting from: [paste existing draft] — Improve this executive summary
```
