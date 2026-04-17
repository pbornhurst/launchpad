#!/usr/bin/env python3
"""
Direct Snowflake query script for Claude Code.
Uses Okta SSO (externalbrowser) with token caching — log in once via browser,
then tokens are cached in macOS keychain for subsequent runs.

Usage:
  python3 scripts/snowflake_query.py "SELECT 1 AS test"
  python3 scripts/snowflake_query.py --json "SELECT * FROM edw.pathfinder.agg_pathfinder_stores_daily LIMIT 5"
  python3 scripts/snowflake_query.py --warehouses          # list available warehouses
  python3 scripts/snowflake_query.py --warehouse SOME_WH "SELECT ..."
"""

import sys
import json
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

# DoorDash Snowflake connection config
SNOWFLAKE_ACCOUNT = "DOORDASH-DOORDASH"
SNOWFLAKE_USER = "PHILIP.BORNHURST"
SNOWFLAKE_ROLE = "PHILIPBORNHURST"
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "ADHOC")


def get_connection(warehouse=None):
    """Create a Snowflake connection with Okta SSO + token caching."""
    import snowflake.connector
    return snowflake.connector.connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        role=SNOWFLAKE_ROLE,
        warehouse=warehouse or SNOWFLAKE_WAREHOUSE,
        authenticator="externalbrowser",
        client_store_temporary_credential=True,
    )


def run_query(sql, warehouse=None):
    """Execute a SQL query and return columns + rows."""
    conn = get_connection(warehouse)
    try:
        cur = conn.cursor()
        cur.execute(sql)
        columns = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        return columns, rows
    finally:
        conn.close()


def print_table(columns, rows, max_rows=200):
    """Print results in a readable table format."""
    if not rows:
        print("(0 rows)")
        return

    widths = [len(c) for c in columns]
    for row in rows[:max_rows]:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], min(len(str(val)), 60))

    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    print(header)
    print("-+-".join("-" * w for w in widths))

    for row in rows[:max_rows]:
        line = " | ".join(str(v)[:60].ljust(widths[i]) for i, v in enumerate(row))
        print(line)

    total = len(rows)
    if total > max_rows:
        print(f"\n... ({total} total rows, showing first {max_rows})")
    else:
        print(f"\n({total} rows)")


def print_json(columns, rows):
    """Print results as JSON array of objects."""
    result = [dict(zip(columns, [str(v) if v is not None else None for v in row])) for row in rows]
    print(json.dumps(result, indent=2, default=str))


def main():
    args = sys.argv[1:]
    json_mode = False
    warehouse = None

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    # Parse flags
    while args:
        if args[0] == "--json":
            json_mode = True
            args = args[1:]
        elif args[0] == "--warehouse" and len(args) > 1:
            warehouse = args[1]
            args = args[2:]
        elif args[0] == "--warehouses":
            columns, rows = run_query("SHOW WAREHOUSES", warehouse)
            if json_mode:
                print_json(columns, rows)
            else:
                print_table(columns, rows)
            return
        else:
            break

    if not args:
        print("Error: No SQL query provided.", file=sys.stderr)
        sys.exit(1)

    sql = " ".join(args)
    columns, rows = run_query(sql, warehouse)

    if json_mode:
        print_json(columns, rows)
    else:
        print_table(columns, rows)


if __name__ == "__main__":
    main()
