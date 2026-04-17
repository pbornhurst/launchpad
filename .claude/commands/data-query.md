# /data-query — Query DoorDash Data

Access the DoorDash data warehouse via ask-data-ai for metrics, tables, and dashboards.

## Instructions

1. Understand what the user wants — a metric, a table lookup, a dashboard, or a custom SQL query.
2. Route to the correct agent:
   - **Metrics / KPIs:** Use `mcp__ask-data-ai__ask_firefly` for standard metrics
   - **Table discovery:** Use `mcp__ask-data-ai__search_data_catalog` to find relevant tables
   - **Table schema:** Use `mcp__ask-data-ai__DescribeTable` for column details
   - **Custom SQL:** Use Bash: `python3 scripts/snowflake_query.py --json "SQL_HERE"` (direct Snowflake, no OAuth). Fallback: `mcp__ask-data-ai__ExecuteSnowflakeQuery`
   - **Dashboards:** Use `mcp__ask-data-ai__discover_sigma_dashboards` to find dashboards
   - **Finance data:** Use `mcp__ask-data-ai__ask_finance_ai` for P&L, revenue, cost questions
   - **Merchant data:** Use `mcp__ask-data-ai__ask_data_mx` for mx-specific metrics
   - **General fallback:** Use `mcp__ask-data-ai__ask_ai_network` if unsure which agent
3. Present results clearly:
   - Format numbers with commas and appropriate units
   - Include the time period covered
   - Always cite the source table or dashboard
   - For large result sets, summarize and offer to drill down

## Example usage

```
/data-query last week's GOV for Pathfinder
/data-query find tables related to dasher pay
/data-query CnG performance dashboard
/data-query what's our order volume trend this quarter
```
