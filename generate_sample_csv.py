"""Generate a 10,000-student sample CSV for stress-testing the fee tracker."""
import csv
import random
from calendar import monthrange
from datetime import date
from pathlib import Path

random.seed(42)

FIRST = [
    "Aarav", "Aanya", "Aditya", "Advait", "Akash", "Amit", "Ananya", "Arjun",
    "Aryan", "Bhavya", "Chirag", "Dev", "Diya", "Esha", "Farhan", "Gaurav",
    "Harsh", "Ishaan", "Ishita", "Jay", "Kabir", "Kavya", "Krish", "Laksh",
    "Manav", "Meera", "Neha", "Nikhil", "Nisha", "Om", "Parth", "Pooja",
    "Priya", "Rahul", "Raj", "Rakesh", "Riya", "Rohan", "Sakshi", "Sameer",
    "Sanya", "Shreya", "Siddharth", "Simran", "Suresh", "Tanvi", "Tarun",
    "Uday", "Varun", "Vikram", "Yash", "Zara",
]
LAST = [
    "Sharma", "Verma", "Iyer", "Patel", "Singh", "Gupta", "Rao", "Joshi",
    "Mehta", "Nair", "Desai", "Kapoor", "Bhatia", "Reddy", "Malhotra",
    "Agarwal", "Shah", "Chopra", "Saxena", "Tiwari", "Mishra", "Pandey",
    "Chauhan", "Yadav", "Das", "Kulkarni", "Roy", "Bose", "Pillai", "Menon",
]

BATCHES = {
    "2025 - Aug - B.Tech ME":  "B.Tech ME",
    "2025 - Aug - B.Tech CSE": "B.Tech CSE",
    "2025 - Aug - B.Tech CE":  "B.Tech CE",
}

OUTPUT = Path.home() / "Downloads" / "fees_10k_sample.csv"
N_STUDENTS = 10000
# Each student is in the CSV with ONE payment row in a random month/year.
# When viewing a specific month (e.g. April 2026), ~1/18 of students will
# show as Paid for that month — the rest show as Unpaid defaulters.

with OUTPUT.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow([
        "roll_number", "name", "batch_name", "semester",
        "month", "year", "amount_paid", "payment_date",
    ])
    for i in range(1, N_STUDENTS + 1):
        roll = f"STU{i:05d}"
        name = f"{random.choice(FIRST)} {random.choice(LAST)}"
        batch = random.choice(list(BATCHES.keys()))
        sem_n = random.randint(1, 6)
        semester = f"{BATCHES[batch]} - Sem {sem_n}"
        year = random.choice([2025, 2026])
        month = random.randint(1, 12)
        last_day = monthrange(year, month)[1]
        day = random.randint(1, last_day)
        amount = random.choice([13000, 13500, 14000, 14500, 15000, 15500, 16000])
        payment_date = date(year, month, day).strftime("%d/%m/%Y")
        w.writerow([roll, name, batch, semester, month, year, amount, payment_date])

print(f"Wrote {N_STUDENTS} rows to {OUTPUT} ({OUTPUT.stat().st_size/1024:.1f} KB)")
