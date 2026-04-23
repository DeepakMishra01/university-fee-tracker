import csv
import io
from datetime import datetime

from flask import Flask, jsonify, render_template, request

import seed
from db import get_conn

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/students")
def api_students():
    try:
        month = int(request.args.get("month", ""))
        year = int(request.args.get("year", ""))
    except ValueError:
        return jsonify({"error": "month and year must be integers"}), 400
    if not (1 <= month <= 12):
        return jsonify({"error": "month must be 1-12"}), 400

    sql = """
        SELECT s.student_id, s.name, s.roll_number, s.batch_name, s.semester,
               f.amount_paid, f.payment_date,
               CASE WHEN f.fee_id IS NULL THEN 'Unpaid' ELSE 'Paid' END AS status
        FROM students s
        LEFT JOIN fees f
          ON f.student_id = s.student_id
         AND f.month = %s AND f.year = %s
        ORDER BY s.batch_name, s.roll_number;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, (month, year))
        rows = cur.fetchall()

    for r in rows:
        if r["amount_paid"] is not None:
            r["amount_paid"] = float(r["amount_paid"])
        if r["payment_date"] is not None:
            r["payment_date"] = r["payment_date"].isoformat()
    return jsonify(rows)


@app.route("/api/batches")
def api_batches():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT batch_name FROM students ORDER BY batch_name;")
        batches = [r["batch_name"] for r in cur.fetchall()]
        cur.execute("SELECT DISTINCT semester FROM students ORDER BY semester;")
        semesters = [r["semester"] for r in cur.fetchall()]
    return jsonify({"batches": batches, "semesters": semesters})


@app.route("/api/upload-fees", methods=["POST"])
def api_upload_fees():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file uploaded (field name: file)"}), 400

    try:
        text = f.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({"error": "file must be UTF-8 encoded"}), 400

    reader = csv.DictReader(io.StringIO(text))
    required = {
        "roll_number", "name", "batch_name", "semester",
        "month", "year", "amount_paid", "payment_date",
    }
    if reader.fieldnames is None or not required.issubset({c.strip() for c in reader.fieldnames}):
        return jsonify({
            "error": f"CSV must have columns: {sorted(required)}",
            "found": reader.fieldnames,
        }), 400

    valid_rows = []
    errors = []
    for i, row in enumerate(reader, start=2):  # start=2 accounts for header
        try:
            roll = row["roll_number"].strip()
            name = row["name"].strip()
            batch_name = row["batch_name"].strip()
            semester = row["semester"].strip()
            month = int(row["month"])
            year = int(row["year"])
            amount = float(row["amount_paid"])
            payment_date = datetime.strptime(row["payment_date"].strip(), "%Y-%m-%d").date()
            if not (1 <= month <= 12):
                raise ValueError("month must be 1-12")
            if not roll or not name or not batch_name or not semester:
                raise ValueError("roll_number, name, batch_name, and semester must not be empty")
            valid_rows.append((roll, name, batch_name, semester, month, year, amount, payment_date))
        except (ValueError, KeyError, AttributeError) as e:
            errors.append({"line": i, "error": str(e), "row": row})

    if not valid_rows:
        return jsonify({
            "inserted": 0, "updated": 0, "new_students_created": 0,
            "parse_errors": errors,
        })

    # De-duplicate student rows by roll_number (last one wins for name/batch/semester)
    students_by_roll = {}
    for roll, name, batch_name, semester, *_ in valid_rows:
        students_by_roll[roll] = (name, roll, batch_name, semester)

    with get_conn() as conn, conn.cursor() as cur:
        # Bulk upsert students; RETURNING tells us which rolls were newly created.
        cur.executemany(
            """
            INSERT INTO students (name, roll_number, batch_name, semester)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (roll_number) DO NOTHING
            RETURNING roll_number;
            """,
            list(students_by_roll.values()),
            returning=True,
        )
        new_rolls = set()
        while True:
            row = cur.fetchone()
            if row is not None:
                new_rolls.add(row["roll_number"])
            if not cur.nextset():
                break
        new_students_created = len(new_rolls)

        # Load roll_number → student_id map for all rolls in this batch.
        rolls = list(students_by_roll.keys())
        cur.execute(
            "SELECT student_id, roll_number FROM students WHERE roll_number = ANY(%s);",
            (rolls,),
        )
        id_by_roll = {r["roll_number"]: r["student_id"] for r in cur.fetchall()}

        # Bulk upsert fees.
        fee_rows = [
            (id_by_roll[roll], month, year, amount, payment_date)
            for roll, _name, _batch, _sem, month, year, amount, payment_date in valid_rows
            if roll in id_by_roll
        ]
        cur.executemany(
            """
            INSERT INTO fees (student_id, month, year, amount_paid, payment_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (student_id, month, year)
            DO UPDATE SET amount_paid = EXCLUDED.amount_paid,
                          payment_date = EXCLUDED.payment_date
            RETURNING (xmax = 0) AS inserted;
            """,
            fee_rows,
            returning=True,
        )
        inserted = updated = 0
        while True:
            row = cur.fetchone()
            if row is not None:
                if row["inserted"]:
                    inserted += 1
                else:
                    updated += 1
            if not cur.nextset():
                break

    return jsonify({
        "inserted": inserted,
        "updated": updated,
        "new_students_created": new_students_created,
        "parse_errors": errors,
    })


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def api_delete_student(student_id):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM students WHERE student_id = %s RETURNING student_id;", (student_id,))
        row = cur.fetchone()
    if not row:
        return jsonify({"error": "student not found", "student_id": student_id}), 404
    return jsonify({"deleted": True, "student_id": student_id})


@app.route("/api/wipe-all", methods=["POST"])
def api_wipe_all():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE fees, students RESTART IDENTITY CASCADE;")
    seed.main()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS c FROM students;")
        students_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) AS c FROM fees;")
        fees_count = cur.fetchone()["c"]
    return jsonify({
        "wiped": True,
        "reseeded_students": students_count,
        "reseeded_fees": fees_count,
    })


if __name__ == "__main__":
    app.run(debug=True)
