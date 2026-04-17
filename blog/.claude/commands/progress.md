# /progress — Speaking Practice Progress

Show progress trends and insights from speaking practice sessions.

## Arguments: $ARGUMENTS

Optional filters: "last 10", "this month", "this week", or a category like "POS"

## Instructions

1. **Read the tracking sheet:**
   - Look up the spreadsheet ID from `README.md`
   - Use `mcp__google-workspace__read_sheet_values` with user_google_email "philip.bornhurst@doordash.com"
   - If the sheet doesn't exist or has no data rows, respond:
     "No sessions tracked yet. Use `/topic` to pick a topic and `/review` after recording to start tracking."

2. **Compute summary stats:**
   - Total sessions completed
   - Average total score and per-dimension averages
   - Best session (highest total) and worst session (lowest total)
   - Most recent session date and score
   - Sessions this week / this month
   - Most practiced category (by topic ID prefix)
   - Least practiced category (with 0 sessions highlighted)

3. **Identify trends** (over last 5+ sessions):
   - Is the total score trending up, down, or flat?
   - Which dimension has improved most?
   - Which dimension is consistently the weakest?
   - Any dimension that regressed recently?

4. **Present the report:**

   ```
   ## Speaking Practice Progress
   **Sessions:** X total | **Since:** [first session date]
   **This week:** X | **This month:** X

   ### Score Trend (Last 5 Sessions)
   | Date | Topic | Total | Content | Delivery | Clarity | Persuasion | Engagement |
   |------|-------|-------|---------|----------|---------|------------|------------|
   | ... | ... | XX/25 | X | X | X | X | X |

   ### Dimension Averages
   | Dimension | Average | Trend |
   |-----------|---------|-------|
   | Content & Structure | X.X/5 | improving / declining / flat |
   | Delivery & Pace | X.X/5 | ... |
   | Clarity & Filler Words | X.X/5 | ... |
   | Persuasiveness | X.X/5 | ... |
   | Engagement | X.X/5 | ... |
   | **Overall** | **X.X/25** | **...** |

   ### Strongest Dimension: [Name] (avg X.X)
   [Brief note on what's working]

   ### Weakest Dimension: [Name] (avg X.X)
   [Brief note and suggestion for improvement]

   ### Topic Coverage
   | Category | Sessions | Avg Score |
   |----------|----------|-----------|
   | POS Fundamentals | X | XX |
   | Restaurant Ops | X | XX |
   | DoorDash Platform | X | XX |
   | Industry Trends | X | XX |
   | Pathfinder Deep Dives | X | XX |
   | Sales & Partnerships | X | XX |

   ### Recommendations
   1. [Data-driven suggestion — e.g., "Clarity scores are climbing but persuasion has plateaued. Focus on eliminating hedging language."]
   2. [Category suggestion — e.g., "You've done 5 POS topics but zero industry trends. Branch out."]
   3. [Duration suggestion — e.g., "Your 1-min scores are strong. Challenge yourself with a 5-min topic."]
   ```

5. **Offer next steps:**
   - "Use `/topic` to pick your next session"
   - "Use `/topic [weakest category]` to practice where you need it most"

## Examples

```
/progress
/progress last 10
/progress this month
/progress POS
```
