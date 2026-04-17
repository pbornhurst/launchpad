# /review — Analyze a Speaking Recording

Analyze a speaking practice recording and provide structured feedback using the 5-dimension rubric.

## Arguments: $ARGUMENTS

The user provides:
- A file path to an audio or video recording (required)
- Optionally a topic ID (e.g., "POS-001") or "freestyle"

If no file path is provided, ask for one.

## Instructions

1. **Get the recording file path** from $ARGUMENTS. Supported formats: .mp4, .mov, .m4a, .mp3, .wav, .webm

2. **Identify the topic:**
   - If a topic ID is given, read the matching topic file from `topics/` for context
   - If not specified, ask: "Which topic were you speaking on? Give me the ID or title, or say 'freestyle' if it was unstructured."
   - If "freestyle", skip topic-specific content evaluation and focus on delivery dimensions

3. **Load the rubric** from `rubric.md` for scoring calibration.

4. **Analyze the recording with Gemini:**
   Use `mcp__gemini__gemini-analyze-document` with the recording file path and this prompt:

   "You are a speaking coach analyzing a practice recording. The speaker is Phil, a Head of Account Management at a tech company, practicing speaking about restaurant technology topics. This is personal practice to improve speaking skills for meetings and presentations — NOT content for publication.

   Topic: [topic title and thesis if known, or 'freestyle/unstructured']
   Target duration: [X minutes if known]

   Analyze the recording across these five dimensions:

   1. CONTENT & STRUCTURE: Is there a clear thesis stated upfront? Logical flow with transitions? Supporting evidence or examples for every point? Strong conclusion that ties back?
   2. DELIVERY & PACE: Natural pace with intentional pauses? Speed variation for emphasis? Energy matching content? Any rushed sections or dead air?
   3. CLARITY & FILLER WORDS: Count all filler words (um, uh, like, you know, so, right, basically, literally). Note restarted or abandoned sentences. Rate articulation quality.
   4. PERSUASIVENESS & CONFIDENCE: Does he sound like an authority? Claims backed by evidence? Conviction without arrogance? Any hedging language (I think maybe, kind of, sort of)?
   5. ENGAGEMENT & RELATABILITY: Stories or analogies used? Concrete examples that make abstract concepts vivid? Any hook moments? Would an audience lean in?

   Also provide:
   - Approximate actual duration of the recording
   - A verbatim quote of the single strongest moment
   - A verbatim quote (or description) of the single weakest moment
   - Specific timestamps of notable moments if possible
   - Estimated filler word count

   Be direct, specific, and constructive. This is for self-improvement."

5. **Score using the rubric:**
   Based on the Gemini analysis and your own judgment, assign scores 1-5 for each dimension. If Gemini's analysis and your judgment disagree, use yours but note why.

6. **Check previous sessions** for comparison:
   - Look up the tracker spreadsheet ID from `README.md`
   - If it exists, read the last row from the Sessions sheet
   - Compare scores dimension-by-dimension

7. **Present the review:**

   ```
   ## Recording Review: [Topic Title or "Freestyle"]
   **Date:** [today] | **Duration:** [actual] / [target] min | **Topic:** [ID or freestyle]

   ### Scores
   | Dimension | Score | Notes |
   |-----------|-------|-------|
   | Content & Structure | X/5 | [one-line justification] |
   | Delivery & Pace | X/5 | [one-line justification] |
   | Clarity & Filler Words | X/5 | [one-line justification] |
   | Persuasiveness | X/5 | [one-line justification] |
   | Engagement | X/5 | [one-line justification] |
   | **Total** | **XX/25** | **[Band: Excellent/Strong/Developing/Early/Starting]** |

   ### Top Strength
   [What worked best — be specific with a quote or timestamp]

   ### Top Weakness
   [Single most impactful thing to fix — be specific]

   ### Strongest Moment
   > "[verbatim quote]"
   [Why this worked]

   ### Weakest Moment
   > "[verbatim quote or description]"
   [What to do instead]

   ### Three Things to Do Next Time
   1. [Specific, actionable improvement]
   2. [Specific, actionable improvement]
   3. [Specific, actionable improvement]

   ### vs. Last Session
   [Compare dimension-by-dimension if data exists, or: "First tracked session — baseline established."]
   ```

8. **Log to tracking sheet (with confirmation):**
   - If the Speaking Practice Tracker sheet doesn't exist yet, create it:
     - Use `mcp__google-workspace__create_spreadsheet` with title "Speaking Practice Tracker" and user_google_email "philip.bornhurst@doordash.com"
     - Write headers to row 1: Date, Topic ID, Topic Title, Duration Target, Actual Duration, Content, Delivery, Clarity, Persuasion, Engagement, Total, Band, Top Strength, Top Weakness, Key Takeaway, File Link
     - Store the new spreadsheet ID back in `README.md`
   - Prepare the session row with all scores and notes
   - **Show the row to Phil and ask for confirmation before writing**
   - Once confirmed, append the row using `mcp__google-workspace__modify_sheet_values`

9. **Offer next steps:**
   - "Use `/topic` to pick your next session"
   - "Use `/progress` to see your trends"

## Examples

```
/review ~/Desktop/recording.m4a
/review ~/Desktop/pos-talk.mp4 POS-001
/review ~/Desktop/freestyle.m4a freestyle
```
