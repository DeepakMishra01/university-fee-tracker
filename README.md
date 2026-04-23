# University Fee Tracker

Single-page Flask + PostgreSQL app to track monthly student fee payments.

## Prerequisites
- Python 3.10+
- PostgreSQL 14+ (install on macOS: `brew install postgresql@16 && brew services start postgresql@16`)

## Setup

```bash
cd "university-fee-tracker"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # edit DATABASE_URL if needed

createdb university_fees
psql university_fees -f schema.sql
python seed.py            # optional: loads 15 sample students + a few payments

flask --app app run --debug
```

Open http://localhost:5000

## CSV Format for Upload
```
roll_number,name,batch_name,semester,month,year,amount_paid,payment_date
CSE24001,Aarav Sharma,2025 - Aug - B.Tech CSE,B.Tech CSE - Sem 1,4,2026,15000,02/04/2026
NEW001,New Student,2025 - Aug - B.Tech ME,B.Tech ME - Sem 1,4,2026,14000,03/04/2026
```
- `payment_date` format: `DD/MM/YYYY` (also accepts `YYYY-MM-DD`)
- Re-uploading the same row updates the fee (idempotent via `ON CONFLICT`)
- Roll numbers not already in `students` are automatically created — one CSV handles both new and existing students

## API
- `GET  /api/students?month=<1-12>&year=<YYYY>` — all students + Paid/Unpaid for that month
- `GET  /api/batches` — distinct batches and semesters
- `POST /api/upload-fees` — multipart field `file` (CSV)

## Features
- Month/Year filter (top of page)
- Defaulter rows highlighted red
- Column filters (Name, Roll, Batch, Semester, Status) run client-side
- CSV upload + CSV export of currently visible rows
