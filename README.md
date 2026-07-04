# Exam Portal

Online exam portal with real-time webcam monitoring. Built with FastAPI and vanilla JavaScript — supports multiple choice exams, user authentication, face detection via MediaPipe to flag suspicious gaze patterns, and tab/window switch tracking. Generates a cheating report for each attempt.

## Features

- User registration and login
- Multiple choice exams
- Real-time face detection via webcam (MediaPipe)
- Tab switch and window focus loss detection
- Cheating report per exam attempt
- Exam history

## Tech Stack

- **Backend:** Python, FastAPI, uvicorn
- **Frontend:** HTML, CSS, vanilla JavaScript
- **Database:** SQLite
- **AI/CV:** MediaPipe FaceLandmarker, OpenCV

## Project Structure

```
exam-portal/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── detector.py
│   └── exams.json
├── frontend/
│   ├── index.html
│   ├── exam.html
│   ├── result.html
│   ├── style.css
│   ├── camera.js
│   └── exam.js
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

1. Clone the repository:
```bash
   git clone https://github.com/your-username/exam-portal.git
   cd exam-portal
```

2. Create and activate a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Run the server:
```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open your browser at `http://localhost:8000`

> The FaceLandmarker model (~30MB) will be downloaded automatically on first run.

## Usage

1. Register an account and sign in
2. Select an exam and click **Start exam**
3. Allow camera access when prompted
4. Answer all questions and click **Submit exam**
5. Review your score and the monitoring report
