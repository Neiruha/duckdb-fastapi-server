from __future__ import annotations

import os
import sys

import duckdb

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/srv/neiruha/lab/app/data/neiruha.duckdb")


def main() -> None:
    con = duckdb.connect(DUCKDB_PATH)
    try:
        con.execute("BEGIN")
        con.execute("DROP INDEX IF EXISTS ux_client_tokens_hash")
        con.execute("ALTER TABLE client_tokens DROP COLUMN IF EXISTS token_hash")
        con.execute('ALTER TABLE client_tokens DROP COLUMN IF EXISTS "role"')
        con.execute("ALTER TABLE client_tokens DROP COLUMN IF EXISTS last_used_at")
        con.execute("ALTER TABLE client_tokens ADD COLUMN IF NOT EXISTS payload_json JSON")
        con.execute("COMMIT")
    except Exception as exc:  # pragma: no cover - migration guard
        con.execute("ROLLBACK")
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
