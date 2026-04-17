#!/usr/bin/env python3
"""
Trino/Starburst query script for Claude Code.
Connects to DoorDash's Starburst Trino gateway and runs read-only queries.

Usage:
  python3 scripts/trino_query.py "SELECT * FROM pinot.default.some_table LIMIT 10"
  python3 scripts/trino_query.py --catalogs          # list available catalogs
  python3 scripts/trino_query.py --schemas pinot      # list schemas in a catalog
  python3 scripts/trino_query.py --tables pinot.default  # list tables in a schema
"""

import sys
import json
import os
from trino.dbapi import connect
from trino.auth import OAuth2Authentication

# DoorDash Starburst/Trino connection config
TRINO_HOST = os.environ.get("TRINO_HOST", "trino-gateway.doordash.com")
TRINO_PORT = int(os.environ.get("TRINO_PORT", "443"))
TRINO_USER = os.environ.get("TRINO_USER", "philip.bornhurst")
TRINO_CATALOG = os.environ.get("TRINO_CATALOG", "pinot")
TRINO_SCHEMA = os.environ.get("TRINO_SCHEMA", "default")


def get_connection():
    """Create a Trino connection with OAuth2 auth (Okta SSO)."""
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=TRINO_CATALOG,
        schema=TRINO_SCHEMA,
        http_scheme="https",
        auth=OAuth2Authentication(),
    )


def get_connection_basic():
    """Fallback: basic auth (no password, just username header)."""
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog=TRINO_CATALOG,
        schema=TRINO_SCHEMA,
        http_scheme="https",
    )


def run_query(sql, conn=None):
    """Execute a SQL query and return results as a list of dicts."""
    if conn is None:
        try:
            conn = get_connection()
        except Exception:
            print("OAuth2 auth failed, trying basic auth...", file=sys.stderr)
            conn = get_connection_basic()

    cur = conn.cursor()
    cur.execute(sql)
    columns = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    return columns, rows


def print_results(columns, rows, max_rows=100):
    """Print results in a readable format."""
    if not rows:
        print("(0 rows)")
        return

    # Calculate column widths
    widths = [len(c) for c in columns]
    for row in rows[:max_rows]:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)[:80]))

    # Header
    header = " | ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    print(header)
    print("-+-".join("-" * w for w in widths))

    # Rows
    for row in rows[:max_rows]:
        line = " | ".join(str(v)[:80].ljust(widths[i]) for i, v in enumerate(row))
        print(line)

    if len(rows) > max_rows:
        print(f"\n... ({len(rows)} total rows, showing first {max_rows})")
    else:
        print(f"\n({len(rows)} rows)")


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if args[0] == "--catalogs":
        sql = "SHOW CATALOGS"
    elif args[0] == "--schemas" and len(args) > 1:
        sql = f"SHOW SCHEMAS IN {args[1]}"
    elif args[0] == "--tables" and len(args) > 1:
        sql = f"SHOW TABLES IN {args[1]}"
    elif args[0] == "--describe" and len(args) > 1:
        sql = f"DESCRIBE {args[1]}"
    elif args[0] == "--json":
        # JSON output mode for piping
        sql = " ".join(args[1:])
        columns, rows = run_query(sql)
        result = [dict(zip(columns, row)) for row in rows]
        print(json.dumps(result, indent=2, default=str))
        return
    else:
        sql = " ".join(args)

    columns, rows = run_query(sql)
    print_results(columns, rows)


if __name__ == "__main__":
    main()
