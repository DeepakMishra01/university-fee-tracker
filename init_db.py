"""One-shot DB init for deploys: creates tables if missing, seeds if empty.

Safe to run on every deploy — schema is idempotent (checks for table existence)
and seeding only runs when the students table is empty.
"""
from pathlib import Path

from db import get_conn
import seed


def table_exists(cur, name: str) -> bool:
    cur.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = %s;",
        (name,),
    )
    return cur.fetchone() is not None


def main():
    schema_sql = Path(__file__).with_name("schema.sql").read_text()

    with get_conn() as conn, conn.cursor() as cur:
        if not table_exists(cur, "students") or not table_exists(cur, "fees"):
            print("Creating schema…")
            cur.execute(schema_sql)
        else:
            print("Schema already present, skipping create.")

        cur.execute("SELECT COUNT(*) AS c FROM students;")
        count = cur.fetchone()["c"]

    if count == 0:
        print("No students found — seeding sample data…")
        seed.main()
    else:
        print(f"Students table has {count} rows — skipping seed.")


if __name__ == "__main__":
    main()
