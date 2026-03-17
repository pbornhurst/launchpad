# /mx-lookup — Merchant Lookup

Cross-reference a merchant across Master Hub, volume data, support history, and Snowflake.

## Instructions

1. Accept a merchant name, Store ID, or partial match as input.
2. Pull data from these sources in parallel:

   a. **Master Hub** — Use `mcp__google-workspace__read_sheet_values`
      - `spreadsheet_id: "1ndVs2lPhS5frpkEV0KzK7ec5aS18fmr9h1BQEu099E4"`
      - `user_google_email: "philip.bornhurst@doordash.com"`
      - On first use, read row 1 to discover column headers
      - Find the mx row. Extract: Store ID, Account Manager, Status, Tier, MSAT, notes link

   b. **Volume Drop Data** — Use `mcp__google-workspace__read_sheet_values`
      - `spreadsheet_id: "1bu0fWwKWQQeI8nrkhGKA68dTzKRtIh_MXAPeqze0NX0"`
      - `user_google_email: "philip.bornhurst@doordash.com"`
      - Find the mx row. Extract: current volume, previous volume, trend

   c. **Intercom** (primary support) — Use `mcp__intercom__search_conversations` with the mx name
      - Search for recent support conversations
      - If contact isn't clearly identifiable, use `mcp__intercom__get_contact` and cross-reference against Master Hub by business name, phone, or email
      - Note open/closed status and issue summaries

   d. **Slack** (escalations only) — Use `mcp__slack__slack_search_public_and_private` with the mx name
      - Search #pathfinder-support for recent escalations

   e. **Snowflake** (optional) — Use `mcp__ask-data-ai__ask_data_mx` or `mcp__ask-data-ai__ExecuteSnowflakeQuery`
      - Pull recent order metrics if Store ID is known

3. Compile into a unified mx profile:

```
## [Merchant Name] (Store ID: XXXXX)
**Tier:** ICP | **Status:** Live | **AM:** Phil Bornhurst
**Portal:** https://www.doordash.com/merchant/sales?store_id=XXXXX

### Volume
- Current: X orders/week | Previous: Y orders/week | Trend: up/down/flat

### MSAT
- Score: X/5 | Last surveyed: date

### Recent Support
- **Intercom:** [date] Issue summary (status: open/closed)
- **Slack escalation:** [date] Issue summary from #pathfinder-support

### Running Notes
- [Link to Google Doc if found in Master Hub]

### Snowflake Data
- GOV: $X | Orders: Y | Period: last 30 days
```

## Example usage

```
/mx-lookup Taco Bell Store 12345
/mx-lookup pizza palace
/mx-lookup 67890
```
