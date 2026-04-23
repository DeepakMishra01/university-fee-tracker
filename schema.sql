-- University Fee Tracking System schema
DROP TABLE IF EXISTS fees;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    student_id   SERIAL PRIMARY KEY,
    name         TEXT NOT NULL,
    roll_number  TEXT NOT NULL UNIQUE,
    batch_name   TEXT NOT NULL,
    semester     TEXT NOT NULL
);

CREATE TABLE fees (
    fee_id       SERIAL PRIMARY KEY,
    student_id   INT NOT NULL REFERENCES students(student_id) ON DELETE CASCADE,
    month        SMALLINT NOT NULL CHECK (month BETWEEN 1 AND 12),
    year         SMALLINT NOT NULL,
    amount_paid  NUMERIC(10,2) NOT NULL,
    payment_date DATE NOT NULL,
    UNIQUE (student_id, month, year)
);

CREATE INDEX idx_fees_month_year ON fees(month, year);
CREATE INDEX idx_students_batch  ON students(batch_name);
