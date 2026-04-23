"""Seed sample students and a few fee payments for demo/testing."""
from datetime import date

from db import get_conn

STUDENTS = [
    # B.Tech CSE
    ("Aarav Sharma",   "CSE24001", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 1"),
    ("Priya Verma",    "CSE24002", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 1"),
    ("Rohan Iyer",     "CSE24003", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 2"),
    ("Isha Patel",     "CSE24004", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 2"),
    ("Kabir Singh",    "CSE24005", "2025 - Aug - B.Tech CSE", "B.Tech CSE - Sem 3"),
    # B.Tech ME
    ("Neha Gupta",     "ME24001",  "2025 - Aug - B.Tech ME",  "B.Tech ME - Sem 1"),
    ("Vikram Rao",     "ME24002",  "2025 - Aug - B.Tech ME",  "B.Tech ME - Sem 1"),
    ("Sneha Joshi",    "ME24003",  "2025 - Aug - B.Tech ME",  "B.Tech ME - Sem 2"),
    ("Arjun Mehta",    "ME24004",  "2025 - Aug - B.Tech ME",  "B.Tech ME - Sem 3"),
    # B.Tech CE
    ("Divya Nair",     "CE24001",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 1"),
    ("Rahul Desai",    "CE24002",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 1"),
    ("Meera Kapoor",   "CE24003",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 2"),
    ("Karan Bhatia",   "CE24004",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 2"),
    ("Anaya Reddy",    "CE24005",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 3"),
    ("Yash Malhotra",  "CE24006",  "2025 - Aug - B.Tech CE",  "B.Tech CE - Sem 3"),
]

# (roll, month, year, amount, payment_date)
FEES = [
    # Feb 2026 - mostly paid
    ("CSE24001", 2, 2026, 15000, date(2026, 2, 5)),
    ("CSE24002", 2, 2026, 15000, date(2026, 2, 6)),
    ("CSE24003", 2, 2026, 15000, date(2026, 2, 7)),
    ("ME24001",  2, 2026, 14000, date(2026, 2, 4)),
    ("ME24002",  2, 2026, 14000, date(2026, 2, 8)),
    ("CE24001",  2, 2026, 13500, date(2026, 2, 9)),
    ("CE24002",  2, 2026, 13500, date(2026, 2, 9)),

    # Mar 2026 - partial
    ("CSE24001", 3, 2026, 15000, date(2026, 3, 3)),
    ("CSE24004", 3, 2026, 15000, date(2026, 3, 4)),
    ("ME24003",  3, 2026, 14000, date(2026, 3, 6)),
    ("CE24003",  3, 2026, 13500, date(2026, 3, 10)),

    # Apr 2026 - only two paid so far
    ("CSE24001", 4, 2026, 15000, date(2026, 4, 2)),
    ("ME24001",  4, 2026, 14000, date(2026, 4, 3)),
]


def main():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE fees, students RESTART IDENTITY CASCADE;")
        cur.executemany(
            "INSERT INTO students (name, roll_number, batch_name, semester) VALUES (%s, %s, %s, %s);",
            STUDENTS,
        )
        for roll, month, year, amount, pay_date in FEES:
            cur.execute("SELECT student_id FROM students WHERE roll_number = %s;", (roll,))
            sid = cur.fetchone()["student_id"]
            cur.execute(
                """INSERT INTO fees (student_id, month, year, amount_paid, payment_date)
                   VALUES (%s, %s, %s, %s, %s);""",
                (sid, month, year, amount, pay_date),
            )
    print(f"Seeded {len(STUDENTS)} students and {len(FEES)} fee records.")


if __name__ == "__main__":
    main()
