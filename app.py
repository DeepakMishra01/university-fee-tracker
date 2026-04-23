import csv
import io
from datetime import datetime

from flask import Flask, jsonify, render_template, request

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

    inserted = updated = new_students_created = 0

    with get_conn() as conn, conn.cursor() as cur:
        for roll, name, batch_name, semester, month, year, amount, payment_date in valid_rows:
            cur.execute("SELECT student_id FROM students WHERE roll_number = %s", (roll,))
            s = cur.fetchone()
            if s:
                student_id = s["student_id"]
            else:
                cur.execute(
                    """
                    INSERT INTO students (name, roll_number, batch_name, semester)
                    VALUES (%s, %s, %s, %s)
                    RETURNING student_id;
                    """,
                    (name, roll, batch_name, semester),
                )
                student_id = cur.fetchone()["student_id"]
                new_students_created += 1

            cur.execute(
                """
                INSERT INTO fees (student_id, month, year, amount_paid, payment_date)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (student_id, month, year)
                DO UPDATE SET amount_paid = EXCLUDED.amount_paid,
                              payment_date = EXCLUDED.payment_date
                RETURNING (xmax = 0) AS inserted;
                """,
                (student_id, month, year, amount, payment_date),
            )
            was_insert = cur.fetchone()["inserted"]
            if was_insert:
                inserted += 1
            else:
                updated += 1

    return jsonify({
        "inserted": inserted,
        "updated": updated,
        "new_students_created": new_students_created,
        "parse_errors": errors,
    })


if __name__ == "__main__":
    app.run(debug=True)
