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
   - Use Bash: `gws sheets +read --spreadsheet 1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4 --range "B1:E800"`

3. **Check for duplicates** in the Product Feedback Tracker:
   - Use Bash: `gws sheets +read --spreadsheet 1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4 --range "The Final Final Boss"`
   - If similar feedback exists, note it and offer to add a "+1" or additional context instead

4. **Draft the row** and show for approval:

```
| Date | Merchant | Store ID | Tier | Category | Feedback | Priority | Source | AM |
|------|----------|----------|------|----------|----------|----------|--------|----|
| today | Name | ID | T1 | Kiosk | Description | High | call | Phil |
```

5. **Confirm before writing.** Only after user approves:
   - Use Bash: `gws sheets +append --spreadsheet 1-EylRCLxhpStfEoj-8ga9Ex_26dHBoWgxU6Yr_hT0Y4 --range "The Final Final Boss" --values '[["today","Name","ID","T1","Kiosk","Description","High","call","Phil"]]'` (appends to the next empty row)

6. **Confirm** the entry was logged with row number and link.

## Example usage

```
/feedback-log Pizza Palace wants kiosk customization for combo meals
/feedback-log Store 12345 requesting mobile app loyalty integration, high priority, from QBR call
/feedback-log
```
