import json, uuid, base64, cv2, numpy as np
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .database import init_db, create_user, get_user_by_credentials, create_session, get_user_by_token, save_exam_result, save_cheat_event, get_cheat_logs_by_result, get_results_by_user
from .detector import FaceDetector

app = FastAPI()

# Init DB
init_db()

# Init detector
detector = FaceDetector()

# Load exams
with open("backend/exams.json", "r", encoding="utf-8") as f:
    EXAMS = json.load(f)

# Serve frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def root():
    return FileResponse("frontend/index.html")


# AUTH
class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/register")
def register(data: AuthRequest):
    ok = create_user(data.username, data.password)
    if not ok:
        raise HTTPException(status_code=400, detail="User already exist")
    return {"ok": True}

@app.post("/api/login")
def login(data: AuthRequest):
    user = get_user_by_credentials(data.username, data. password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    token = str(uuid.uuid4())
    create_session(user["id"], token)
    return {"token": token, "username": user["username"]}


# EXAMS
@app.get("/api/exams")
def list_exams(token: str):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    return [{"id": e["id"], "title": e["title"], "description": e["description"]} for e in EXAMS]

@app.get("/api/exams/{exam_id}")
def get_exam(exam_id: str, token: str):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    exam = next((e for e in EXAMS if e["id"] == exam_id), None)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Return questions without correct answers
    questions = [
        {"id": q["id"], "text": q["text"], "options": q["options"]}
        for q in exam["questions"]
    ]

    return {"id": exam["id"], "title": exam["title"], "questions": questions}


# RESULTS
class SubmitRequest(BaseModel):
    token: str
    exam_id: str
    answers: dict
    started_at: str
    cheat_events: list

@app.post("/api/submit")
def submit_exam(data: SubmitRequest):
    user = get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    exam = next((e for e in EXAMS if e["id"] == data.exam_id), None)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Correct answers
    score = 0
    total = len(exam["questions"])
    corrections = []
    for q in exam["questions"]:
        qid = str(q["id"])
        user_answer = data.answers.get(qid)
        correct = q["correct"]
        is_correct = user_answer == correct
        if is_correct:
            score += 1
        corrections.append({
            "id": q["id"],
            "text": q["text"],
            "user_answer": user_answer,
            "correct_answer": correct,
            "is_correct": is_correct
        })

    finished_at = datetime.now().isoformat()

    # Save result
    result_id = save_exam_result(user["id"], data.exam_id, score, total, data.started_at, finished_at)

    # Save cheat events
    for event in data.cheat_events:
        save_cheat_event(result_id, event["type"], event.get("detail", ""))

    return {
        "result_id": result_id,
        "score": score,
        "total": total,
        "corrections": corrections,
        "finished_at": finished_at
    }

@app.get("/api/results/{result_id}/report")
def get_report(result_id: int, token: str):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    logs = get_cheat_logs_by_result(result_id)
    return {"result_id": result_id, "events": [dict(l) for l in logs]}

@app.get("/api/history")
def get_history(token: str):
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid session")
    results = get_results_by_user(user["id"])
    return [dict(r) for r in results]


# WebSocket (detection in real time)
@app.websocket("/ws/monitor/{token}")
async def monitor(websocket: WebSocket, token: str):
    user = get_user_by_token(token)
    if not user:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            frame_b64 = data.get("frame")
            if not frame_b64:
                continue

            # Decode frame
            img_bytes = base64.b64decode(frame_b64)
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            # Analyze frame
            result = detector.analyze(frame)
            await websocket.send_json(result)

    except WebSocketDisconnect:
        pass