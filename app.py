from __future__ import annotations

import base64
import csv
import io
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, Response, flash, jsonify, redirect, render_template, request, send_file, url_for

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
FACES = DATA / "faces"
MODEL = DATA / "trainer.yml"
DB = DATA / "attendance.db"
for folder in (DATA, FACES):
    folder.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("ATTENDANCE_SECRET", "change-this-before-deployment")

CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def connection():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connection() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS students (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          roll_no TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL,
          course TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS attendance (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id INTEGER NOT NULL REFERENCES students(id),
          attendance_date TEXT NOT NULL,
          marked_at TEXT NOT NULL,
          confidence REAL,
          UNIQUE(student_id, attendance_date)
        );
        """)


def decode_image(payload: str) -> np.ndarray | None:
    try:
        raw = payload.split(",", 1)[1] if "," in payload else payload
        image = cv2.imdecode(np.frombuffer(base64.b64decode(raw), np.uint8), cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None


def detect_face(image: np.ndarray):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = CASCADE.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(100, 100))
    if len(faces) == 0:
        return None
    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])
    return cv2.resize(gray[y:y + h, x:x + w], (200, 200))


@app.route("/")
def dashboard():
    with connection() as con:
        students = con.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        today = con.execute("SELECT COUNT(*) FROM attendance WHERE attendance_date = ?", (datetime.now().date().isoformat(),)).fetchone()[0]
        recent = con.execute("""SELECT s.name, s.roll_no, a.marked_at FROM attendance a
                              JOIN students s ON s.id=a.student_id ORDER BY a.marked_at DESC LIMIT 6""").fetchall()
    return render_template("dashboard.html", students=students, today=today, recent=recent, model_ready=MODEL.exists())


@app.route("/students", methods=["GET", "POST"])
def students():
    if request.method == "POST":
        roll_no, name, course = (request.form.get(k, "").strip() for k in ("roll_no", "name", "course"))
        if not all((roll_no, name, course)):
            flash("Please complete all student details.", "error")
        else:
            try:
                with connection() as con:
                    con.execute("INSERT INTO students (roll_no, name, course) VALUES (?, ?, ?)", (roll_no, name, course))
                flash("Student registered successfully.", "success")
            except sqlite3.IntegrityError:
                flash("That roll number is already registered.", "error")
        return redirect(url_for("students"))
    with connection() as con:
        rows = con.execute("SELECT * FROM students ORDER BY name").fetchall()
    return render_template("students.html", students=rows)


@app.post("/students/<int:student_id>/delete")
def delete_student(student_id):
    with connection() as con:
        con.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        con.execute("DELETE FROM students WHERE id=?", (student_id,))
    sample_dir = FACES / str(student_id)
    if sample_dir.exists():
        for file in sample_dir.glob("*.jpg"):
            file.unlink()
        sample_dir.rmdir()
    flash("Student and related attendance records removed.", "success")
    return redirect(url_for("students"))


@app.route("/enrolment")
def enrolment():
    with connection() as con:
        rows = con.execute("SELECT * FROM students ORDER BY name").fetchall()
    return render_template("enrolment.html", students=rows)


@app.post("/api/enrol")
def enrol():
    student_id = request.form.get("student_id", type=int)
    image = decode_image(request.form.get("image", ""))
    if not student_id or image is None:
        return jsonify(ok=False, message="Invalid student or camera image."), 400
    face = detect_face(image)
    if face is None:
        return jsonify(ok=False, message="No face detected. Face the camera in brighter light."), 422
    with connection() as con:
        exists = con.execute("SELECT 1 FROM students WHERE id=?", (student_id,)).fetchone()
    if not exists:
        return jsonify(ok=False, message="Student not found."), 404
    directory = FACES / str(student_id)
    directory.mkdir(exist_ok=True)
    number = len(list(directory.glob("*.jpg"))) + 1
    cv2.imwrite(str(directory / f"sample_{number:03d}.jpg"), face)
    return jsonify(ok=True, count=number, message=f"Sample {number} captured")


@app.route("/train", methods=["GET", "POST"])
def train():
    if request.method == "POST":
        images, labels = [], []
        for folder in FACES.iterdir():
            if not folder.is_dir() or not folder.name.isdigit():
                continue
            for file in folder.glob("*.jpg"):
                face = cv2.imread(str(file), cv2.IMREAD_GRAYSCALE)
                if face is not None:
                    images.append(face)
                    labels.append(int(folder.name))
        if not images:
            flash("Capture face samples before training the model.", "error")
        else:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(images, np.array(labels))
            recognizer.write(str(MODEL))
            flash(f"Model trained with {len(images)} samples for {len(set(labels))} students.", "success")
        return redirect(url_for("train"))
    sample_count = sum(1 for _ in FACES.rglob("*.jpg"))
    return render_template("train.html", sample_count=sample_count, model_ready=MODEL.exists())


@app.route("/live")
def live():
    return render_template("live.html", model_ready=MODEL.exists())


@app.post("/api/recognize")
def recognize():
    if not MODEL.exists():
        return jsonify(ok=False, message="Train the model before starting live attendance."), 400
    image = decode_image(request.form.get("image", ""))
    if image is None:
        return jsonify(ok=False, message="Invalid camera image."), 400
    face = detect_face(image)
    if face is None:
        return jsonify(ok=True, matched=False, message="No face detected.")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(MODEL))
    student_id, distance = recognizer.predict(face)
    # Lower LBPH distance is a closer match; reject uncertain recognition.
    if distance > 62:
        return jsonify(ok=True, matched=False, confidence=round(float(distance), 1), message="Face not recognised. Try better lighting.")
    with connection() as con:
        student = con.execute("SELECT * FROM students WHERE id=?", (int(student_id),)).fetchone()
        if not student:
            return jsonify(ok=True, matched=False, message="Face record no longer belongs to a registered student.")
        date = datetime.now().date().isoformat()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            con.execute("INSERT INTO attendance (student_id, attendance_date, marked_at, confidence) VALUES (?, ?, ?, ?)", (student_id, date, now, float(distance)))
            status = "Attendance marked"
        except sqlite3.IntegrityError:
            status = "Already marked today"
    return jsonify(ok=True, matched=True, status=status, student=dict(student), confidence=round(float(distance), 1))


@app.route("/attendance")
def attendance():
    selected = request.args.get("date", datetime.now().date().isoformat())
    with connection() as con:
        rows = con.execute("""SELECT s.name, s.roll_no, s.course, a.attendance_date, a.marked_at, a.confidence
                              FROM attendance a JOIN students s ON s.id=a.student_id
                              WHERE a.attendance_date=? ORDER BY a.marked_at DESC""", (selected,)).fetchall()
    return render_template("attendance.html", rows=rows, selected=selected)


@app.route("/attendance/export")
def export_attendance():
    with connection() as con:
        rows = con.execute("""SELECT s.roll_no, s.name, s.course, a.attendance_date, a.marked_at, a.confidence
                              FROM attendance a JOIN students s ON s.id=a.student_id ORDER BY a.marked_at DESC""").fetchall()
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Roll Number", "Student Name", "Course", "Date", "Marked At", "LBPH Distance"])
    writer.writerows([tuple(row) for row in rows])
    return send_file(io.BytesIO(stream.getvalue().encode()), mimetype="text/csv", as_attachment=True, download_name="attendance_report.csv")


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
else:
    init_db()
