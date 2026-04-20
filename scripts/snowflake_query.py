#!/usr/bin/env python3
"""
Direct Snowflake query script for Claude Code.

Auth order:
  1. Programmatic Access Token (PAT) if SNOWFLAKE_TOKEN is set.
     No browser, no keychain. Preferred.
  2. Key-pair auth if ~/.snowflake/rsa_key.p8 exists (requires IT to
     register the public key on the user — blocked by policy at DoorDash).
  3. Okta SSO (externalbrowser) with keychain token caching — fallback.

The PAT is loaded from a .env file at the repo root if present.

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
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)


def _load_env_file():
    """Load KEY=VALUE pairs from <repo_root>/.env into os.environ if unset."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file()

# DoorDash Snowflake connection config
SNOWFLAKE_ACCOUNT = "DOORDASH-DOORDASH"
SNOWFLAKE_USER = "PHILIP.BORNHURST"
SNOWFLAKE_ROLE = "PHILIPBORNHURST"
SNOWFLAKE_WAREHOUSE = os.environ.get("SNOWFLAKE_WAREHOUSE", "ADHOC")
SNOWFLAKE_TOKEN = os.environ.get("SNOWFLAKE_TOKEN")
PRIVATE_KEY_PATH = os.path.expanduser(
    os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH", "~/.snowflake/rsa_key.p8")
)


def _load_private_key_bytes(path):
    """Load a PKCS#8 private key and return it as DER bytes for the connector."""
    from cryptography.hazmat.primitives import serialization
    passphrase = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    with open(path, "rb") as f:
        p_key = serialization.load_pem_private_key(
            f.read(),
            password=passphrase.encode() if passphrase else None,
        )
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def get_connection(warehouse=None):
    """Create a Snowflake connection. Tries PAT, then key-pair, then Okta SSO."""
    import snowflake.connector

    common = dict(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        role=SNOWFLAKE_ROLE,
        warehouse=warehouse or SNOWFLAKE_WAREHOUSE,
    )

    if SNOWFLAKE_TOKEN:
        return snowflake.connector.connect(
            **common,
            token=SNOWFLAKE_TOKEN,
            authenticator="programmatic_access_token",
        )

    if os.path.exists(PRIVATE_KEY_PATH):
        return snowflake.connector.connect(
            **common,
            private_key=_load_private_key_bytes(PRIVATE_KEY_PATH),
        )

    return snowflake.connector.connect(
        **common,
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
