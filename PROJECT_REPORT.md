# Smart Attendance System using Face Recognition

## Abstract

The Smart Attendance System is a contactless classroom attendance application that identifies enrolled students from a webcam image and records their daily attendance. The system uses OpenCV face detection and the Local Binary Patterns Histograms (LBPH) face-recognition algorithm. It replaces manual roll calls with a faster, local, and exportable attendance workflow.

## Objective

To develop a simple, low-cost attendance solution that recognises registered students through facial features and automatically stores attendance in a database.

## Scope

The project is designed as an educational prototype for a small classroom or laboratory. It supports student registration, face-sample collection, model training, real-time recognition, daily attendance marking, and CSV report download.

## Technology stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Web framework | Flask |
| Face detection | OpenCV Haar Cascade |
| Face recognition | OpenCV LBPH recogniser |
| Database | SQLite |
| User interface | HTML, CSS, JavaScript |

## Working methodology

1. The operator registers a student with roll number, name, and course.
2. The browser camera captures 20–30 face samples for that student.
3. The server detects the largest face, converts it to grayscale, and stores a normalised 200 × 200 image locally.
4. The LBPH recogniser trains on all captured samples and creates a local model file.
5. During live attendance, the browser periodically sends a camera frame to the server.
6. The model predicts a student ID and a distance score. A prediction is accepted only when its score is below the configured threshold.
7. A unique database constraint ensures that a recognised student is marked only once per date.

## Database design

### Students

`id`, `roll_no`, `name`, `course`, `created_at`

### Attendance

`id`, `student_id`, `attendance_date`, `marked_at`, `confidence`

The `student_id + attendance_date` pair is unique to prevent duplicate attendance.

## Functional requirements

- Add and remove students
- Capture biometric training samples
- Train a face-recognition model
- Recognise an enrolled face through a webcam
- Mark daily attendance once per student
- View attendance by date
- Export all attendance records as CSV

## Limitations and future scope

The current prototype works best in controlled indoor lighting and assumes one primary face in view. Future improvements can include anti-spoofing/liveness detection, teacher login, course-wise sessions, a stronger deep-learning embedding model, cloud backup, and SMS/email notifications. Face samples should be collected with informed consent and retained only for the required academic purpose.

## Conclusion

The project demonstrates a practical biometric attendance workflow using free, local tools. It reduces manual effort, maintains a searchable attendance record, and provides an appropriate foundation for further development into a full institutional system.
