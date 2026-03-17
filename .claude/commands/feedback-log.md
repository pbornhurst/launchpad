# /feedback-log — Log Product Feedback

Log a product feedback entry to the Product Feedback Tracker spreadsheet.

## Instructions

1. **Gather feedback details** from the user:
   - **Merchant name** (required)
   - **Feature/Issue** (required) — what the mx is requesting or reporting
   - **Category** (if known) — e.g., Kiosk, OCL, Mobile App, 1p Online Ordering, Gift Cards, POS
   - **Priority** (if known) — Critical, High, Medium, Low
   - **Source** — call, email, Slack, Intercom (default: call)
   - **Additional context** — verbatim quote, screenshot ref, etc.

2. **Look up the mx** in Master Hub to get Store ID and Tier:
   - Use `mcp__google-workspace__read_sheet_values`:
     - `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
     - `user_google_email: "philip.bornhurst@doordash.com"`

3. **Check for duplicates** in the Product Feedback Tracker:
   - Use `mcp__google-workspace__read_sheet_values`:
     - `spreadsheet_id: "1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4"`
     - `range_name: "The Final Final Boss"`
     - `user_google_email: "philip.bornhurst@doordash.com"`
   - If similar feedback exists, note it and offer to add a "+1" or additional context instead

4. **Draft the row** and show for approval:

```
| Date | Merchant | Store ID | Tier | Category | Feedback | Priority | Source | AM |
|------|----------|----------|------|----------|----------|----------|--------|----|
| today | Name | ID | T1 | Kiosk | Description | High | call | Phil |
```

5. **Confirm before writing.** Only after user approves:
   - Use `mcp__google-workspace__modify_sheet_values`:
     - `spreadsheet_id: "1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4"`
     - `range_name: "The Final Final Boss!A[next row]:..."` (append to next empty row)
     - `user_google_email: "philip.bornhurst@doordash.com"`

6. **Confirm** the entry was logged with row number and link.

## Example usage

```
/feedback-log Pizza Palace wants kiosk customization for combo meals
/feedback-log Store 12345 requesting mobile app loyalty integration, high priority, from QBR call
/feedback-log
```
