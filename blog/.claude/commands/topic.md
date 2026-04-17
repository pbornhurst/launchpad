# /topic — Speaking Practice Topic

Pick or generate a restaurant tech speaking topic with prep notes.

## Arguments: $ARGUMENTS

The user may specify:
- A topic ID (e.g., "POS-001") — look it up directly
- A category (e.g., "POS", "OPS", "DD", "IND", "PF", "SAL") — filter to that category
- A difficulty (e.g., "beginner", "intermediate", "advanced") — filter to that level
- A duration (e.g., "1 min", "3 min", "5 min") — note the target
- "freestyle" — skip the library and generate a brand-new topic on the spot
- Nothing — pick a random topic

## Instructions

1. **Load the topic library:**
   - Read all files matching `topics/*.md`
   - Parse each topic entry (delimited by `### [TOPIC-ID]` headers)
   - Apply any filters from $ARGUMENTS

2. **Check for prior attempts** (if the Speaking Practice Tracker sheet exists):
   - Look up the spreadsheet ID from `README.md`
   - If it exists, read the Sessions sheet via `mcp__google-workspace__read_sheet_values` (user_google_email: "philip.bornhurst@doordash.com")
   - Prefer topics Phil hasn't attempted, or topics where he scored below 16
   - Note any previous scores for the selected topic

3. **Select a topic:**
   - If a specific topic ID was given, use that one
   - If filters were given, pick randomly from matching topics
   - If no filters, pick randomly — weighted toward untried topics and low-scoring topics
   - If "freestyle", generate a new topic in the same format drawing from Phil's restaurant tech expertise

4. **Present the topic:**

   Format the output as:

   ```
   ## Speaking Topic: [Title]
   **ID:** [TOPIC-ID] | **Difficulty:** [level] | **Target:** [duration] min

   ### Your Thesis
   [Core thesis — the one sentence you're arguing]

   ### Talking Points
   1. [Point 1] — [brief expansion]
   2. [Point 2] — [brief expansion]
   3. [Point 3] — [brief expansion]

   ### Real-World Examples You Can Use
   - [Example from Pathfinder/DoorDash/industry]
   - [Example 2]

   ### Prep Tips
   - **Opening hook:** [Suggested opening line or question to grab attention]
   - **Watch out for:** [The landmine to avoid]
   - **Strong close:** [Suggested closing line or callback to the thesis]

   ### Previous Attempts
   [Score from last time, or "First attempt — no pressure, just speak."]
   ```

5. **Offer options:**
   - "Say **another** for a different topic"
   - "Say **harder** or **easier** to adjust difficulty"
   - "When you're done recording, use `/review` to get feedback"

## Examples

```
/topic
/topic POS
/topic advanced 5 min
/topic POS-003
/topic something I haven't done
/topic freestyle
```
