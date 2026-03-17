# /volume-alert — Volume Drop Monitor

Check for merchants with significant volume drops or going dark.

## Instructions

1. Read Volume Drop Data spreadsheet using `mcp__google-workspace__read_sheet_values`:
   - `spreadsheet_id: "1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0"`
   - `user_google_email: "philip.bornhurst@doordash.com"`
   - On first use, read row 1 to discover column headers
   - **CRITICAL — Gone Dark detection:** Google Sheets sorts blank/empty cells to the BOTTOM of the sheet, not the top. Stores that went dark will have a Previous Total value but a blank/empty Current Total, and they will appear in the LAST rows of the data. You MUST read the bottom of the sheet (last ~50 rows) in addition to the top to catch gone-dark mx. Do not assume the data is sorted with zeros/blanks first.
2. Identify three categories:
   - **Gone Dark** — Previous volume > 0, current = 0 or null (HIGHEST PRIORITY)
   - **Significant Drop** — Current volume < 50% of previous
   - **Declining Trend** — 3+ consecutive periods of decline
3. Cross-reference each flagged mx against Master Hub to get:
   - Tier, Account Manager, Status, Store ID
   - Use `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
4. Default to Phil's accounts. Filter to Mallory's if specified.
5. Present as:

```
## Volume Alerts

### Gone Dark (Critical)
| Merchant | Store ID | Tier | Last Active Volume | Weeks Dark | Portal |
|----------|----------|------|--------------------|------------|--------|

### Significant Drops (> 50%)
| Merchant | Store ID | Previous | Current | % Change | Portal |
|----------|----------|----------|---------|----------|--------|

### Declining Trend
| Merchant | Store ID | 3-Week Trend | Portal |
|----------|----------|--------------|--------|

## Recommended Actions
- [Prioritized by tier: reach out to gone-dark ICP mx first]
```

## Example usage

```
/volume-alert
/volume-alert Mallory's accounts
/volume-alert threshold 30%
```
