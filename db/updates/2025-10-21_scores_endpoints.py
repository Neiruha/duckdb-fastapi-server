from __future__ import annotations

import os
import sys

import duckdb

DUCKDB_PATH = os.getenv("DUCKDB_PATH", "/srv/neiruha/lab/app/data/neiruha.duckdb")


def main() -> None:
    con = duckdb.connect(DUCKDB_PATH)
    try:
        con.execute("BEGIN")
        # No schema updates required for this release, keep as version marker.
        con.execute("COMMIT")
    except Exception as exc:  # pragma: no cover - migration guard
        con.execute("ROLLBACK")
        print(f"Migration failed: {exc}", file=sys.stderr)
        raise
    finally:
        con.close()


if __name__ == "__main__":
    main()
