# /churn-risk — Portfolio Health Score & Churn Risk Report

Run a churn risk analysis across the portfolio. Produces composite RED/YELLOW/GREEN health scores per mx by combining volume trends, support signals, and engagement data. Outputs a ranked Google Doc report with actionable recommendations.

## Instructions

Dispatch the `churn-risk` agent. Pass any filters from the user's input:
- Default: all Live mx
- "Phil's accounts" → scope to Phil Bornhurst
- "Mallory's accounts" → scope to Mallory Thornley
- "ICP only" → scope to ICP tier
- "Store 12345" or "[mx name]" → scope to specific mx

The agent runs 3 parallel sub-agents (volume, support, engagement), computes composite scores, and generates a Google Doc.

## Example usage

```
/churn-risk
/churn-risk ICP only
/churn-risk Mallory's accounts
/churn-risk Store 12345
/churn-risk Phil's Tier 1 accounts
```
