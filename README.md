# Smart Attendance System using Face Recognition

A compact minor-project implementation for contactless classroom attendance. It provides student registration, face-sample enrolment, local face-model training, live recognition, attendance logs, and CSV export.

## Features

- Register and manage students
- Capture face samples through the computer camera
- Train an OpenCV LBPH face recogniser locally
- Mark attendance only once per student per day
- View attendance history and download it as CSV
- Runs entirely on the local machine; no facial data is sent to a cloud service

## Setup

1. Install Python 3.10 or newer.
2. Open a terminal in this folder and run:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python app.py
   ```

3. Visit `http://127.0.0.1:5000`.

## How to demonstrate

1. Add a student in **Students**.
2. Open **Enrolment**, select the student, allow camera access, and capture 20–30 samples.
3. Open **Train Model** and train the recogniser.
4. Open **Live Attendance**, allow camera access, and place an enrolled face in the frame.
5. Check **Attendance** or export the CSV.

## Project structure

- `app.py` — Flask app, SQLite data layer, recognition and export APIs
- `templates/` — web interface pages
- `static/` — CSS and browser-camera JavaScript
- `data/` — generated automatically for database, face samples, and trained model

## Notes and limitations

LBPH is a lightweight offline recognition method appropriate for a classroom prototype. Accuracy improves with clear, varied face samples and good lighting. Obtain consent before collecting biometric samples, and use the system only for its stated educational purpose.
