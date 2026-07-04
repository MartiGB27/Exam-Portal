const params = new URLSearchParams(window.location.search);
const examId = params.get("exam_id");
const token = params.get("token");

let exam = null;
let startedAt = null;
let timerInterval = null;
let elapsedSeconds = 0;
let monitor = null;

if(!token || !examId){
    window.location.href = "/";
} else{
    init();
}

async function init(){
    startedAt = new Date().toISOString();
    monitor = new CameraMonitor();

    startTimer();

    await Promise.all([
        monitor.start(),
        loadExam()
    ]);
}

async function loadExam(){
    const res = await fetch(`/api/exams/${examId}?token=${token}`);
    if(!res.ok){
        document.getElementById("exam-content").innerHTML = "<p class='error'>Could not load this exam. Please go back and try again.</p>";
        return;
    }
    exam = await res.json();
    renderExam();
}

function renderExam(){
    const content = document.getElementById("exam-content");
    content.innerHTML = `
        <h2>${exam.title}</h2>
        ${exam.questions.map((q, i) => `
            <div class="card question-card">
                <p class="question-text"><strong>Q${i + 1}.</strong> ${q.text}</p>
                <div class="options">
                    ${q.options.map(opt => `
                        <label class="option">
                            <input type="radio" name="q-${q.id}" value="${opt}" />
                            <span>${opt}</span>
                        </label>
                    `).join("")}
                </div>
            </div>
        `).join("")}
        <div class="submit-bar">
            <button class="btn-primary" onclick="submitExam()">Submit exam</button>
        </div>
    `;
}

function startTimer(){
    const timerEl = document.getElementById("timer");
    timerInterval = setInterval(() => {
        elapsedSeconds++;
        const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
        const seconds = String(elapsedSeconds % 60).padStart(2, "0");
        timerEl.textContent = `${minutes}:${seconds}`;
    }, 1000);
}

function collectAnswers(){
    const answers = {};
    exam.questions.forEach(q => {
        const selected = document.querySelector(`input[name="q-${q.id}"]:checked`);
        if(selected){
            answers[String(q.id)] = selected.value;
        }
    });
    return answers;
}

async function submitExam(){
    const confirmed = confirm("Are yoy sure you want to submit the exam? This cannot be undone!");
    if(!confirmed) return;

    clearInterval(timerInterval);

    const answers = collectAnswers();
    const cheatEvents = monitor.getCheatEvents();
    monitor.stop();

    const res = await fetch(`/api/submit`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            token,
            exam_id: examId,
            answers,
            started_at: startedAt,
            cheat_events: cheatEvents
        })
    });

    if(!res.ok){
        alert("There was an error submitting your exam. Please try again.");
        return;
    }

    const data = await res.json();
    sessionStorage.setItem("last_result", JSON.stringify(data));
    window.location.href = `/static/result.html?result_id=${data.result_id}&token=${token}`;
}