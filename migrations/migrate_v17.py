import sqlite3


def migrate(conn: sqlite3.Connection) -> None:
    """Apply migration version 17: Assessment Locking & Concurrent Edit
    Protection (#1467).

    Adds optimistic-concurrency support to the `assessments` table:

    - `revision`: starts at 1 for every row, incremented by exactly 1 on
      every successful update/finalize/reopen. Callers must pass back the
      revision they last read; if it no longer matches, the write is
      rejected as a conflict instead of silently overwriting newer data.
    - `is_finalized`: 0/1 flag. Once set, `update_assessment()` refuses
      ordinary edits - the row can only be changed again through the
      explicit `reopen_finalized_assessment()` workflow.
    """
    for column_sql in (
        "ADD COLUMN revision INTEGER NOT NULL DEFAULT 1",
        "ADD COLUMN is_finalized INTEGER NOT NULL DEFAULT 0",
    ):
        try:
            conn.execute(f"ALTER TABLE assessments {column_sql}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

    conn.commit()