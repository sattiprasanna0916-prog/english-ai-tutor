/* ================= CONFIG ================= */
const API_BASE = window.location.origin.includes("localhost")
  ? "http://127.0.0.1:8000"
  : "https://english-ai-tutor-1.onrender.com";

const idealAnswers = {
  "Software Engineer": "problem solving coding data structures algorithms system design",
  "Data Analyst": "data analysis visualization statistics sql python insights",
  "Machine Learning Engineer": "machine learning models training data evaluation algorithms",
  "Product Manager": "product strategy roadmap users business metrics",
  "Business Analyst": "requirements analysis stakeholders data insights business process"
};

const LS = {
  id: "user_id",
  email: "user_email",
  level: "user_level"
};

const $ = (id) => document.getElementById(id);

/* ================= GLOBAL STATE ================= */
let interviewStarted = false;
let questionCount = 0;
let maxQuestions = 5;

let currentQuestion = "";
let lastAnswer = "";
let isRetry = false;

let mediaRecorder;
let audioBlob;

let timerInterval;
let seconds = 0;

/* ================= AUTH ================= */

function getAuthHeaders() {
  const token = localStorage.getItem("token");

  if (!token) {
    alert("Session expired. Please login again.");
    window.location.href = "index.html";
    return {};
  }

  return { Authorization: "Bearer " + token };
}

function logout() {
  localStorage.clear();
  location.href = "index.html";
}

/* ================= UI HELPERS ================= */

function toggleResult(show) {
  const section = $("resultSection");
  if (section) section.style.display = show ? "block" : "none";
}

function updateProgress() {
  if ($("progress")) $("progress").innerText = questionCount;

  const fill = $("progressFill");
  if (fill) fill.style.width = (questionCount / maxQuestions) * 100 + "%";
}

function updateButtons(state) {
  $("startBtn").style.display = state === "idle" ? "block" : "none";
  $("stopBtn").style.display = state === "recording" ? "block" : "none";
  $("analyzeBtn").style.display = state === "recorded" ? "block" : "none";
  $("nextBtn").style.display = state === "analyzed" ? "block" : "none";
}

/* ================= INTERVIEW ================= */

async function startInterview() {
  interviewStarted = true;
  questionCount = 1;
  updateButtons("idle");

  $("retryBtn").style.display = "none";

  const res = await fetch(`${API_BASE}/question/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      level: $("level").value,
      role: $("role").value,
      category: $("category").value
    })
  });

  const data = await res.json();

  currentQuestion = (data.question || "").trim();

  $("chatBox").innerHTML = "";
  addMessage("ai", currentQuestion);

  updateProgress();
  $("nextBtn").disabled = true;
  toggleResult(false);
}

async function nextQuestion() {
  if (!interviewStarted) return alert("Start interview first");
  if (!lastAnswer) return alert("Answer current question first");
  if (questionCount >= maxQuestions) return alert("Interview completed");

  $("retryBtn").style.display = "none";
  questionCount++;

  const quality = analyzeAnswerQuality(lastAnswer);

  let followUpPrompt = "";
  if (quality === "short") {
    followUpPrompt = "Can you explain your answer in more detail?";
  } else if (quality === "medium") {
    followUpPrompt = "Can you give a specific example to support your answer?";
  } else {
    followUpPrompt = "Great. Let's move to the next question.";
  }

  const res = await fetch(`${API_BASE}/question/followup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      previous_question: currentQuestion,
      user_answer: lastAnswer,
      role: $("role").value,
      hint: followUpPrompt
    })
  });

  const data = await res.json();

  currentQuestion = (data.question || "").trim();
  addMessage("ai", currentQuestion);

  updateProgress();
  toggleResult(false);
}

function endInterview() {
  interviewStarted = false;
  questionCount = 0;
  currentQuestion = "";
  lastAnswer = "";

  $("chatBox").innerHTML = `<div class="chat-msg ai">Interview ended</div>`;
  $("progress").innerText = 0;

  toggleResult(false);
}

/* ================= RECORDING ================= */

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  mediaRecorder = new MediaRecorder(stream);
  let chunks = [];

  mediaRecorder.ondataavailable = (e) => chunks.push(e.data);

  mediaRecorder.onstop = () => {
    audioBlob = new Blob(chunks, { type: "audio/webm" });
    $("status").innerText = "Recording ready";
  };

  mediaRecorder.start();

  $("status").innerText = "Recording...";
  updateButtons("recording");

  seconds = 0;
  if ($("timer")) $("timer").innerText = "00:00";

  timerInterval = setInterval(() => {
    seconds++;
    const mins = String(Math.floor(seconds / 60)).padStart(2, "0");
    const secs = String(seconds % 60).padStart(2, "0");

    if ($("timer")) $("timer").innerText = `${mins}:${secs}`;
  }, 1000);

  $("micIndicator")?.classList.add("active");

  $("startBtn").disabled = true;
  $("stopBtn").disabled = false;
  $("analyzeBtn").disabled = true;
}

function stopRecording() {
  if (mediaRecorder) mediaRecorder.stop();

  $("micIndicator")?.classList.remove("active");
  clearInterval(timerInterval);

  updateButtons("recorded");

  $("startBtn").disabled = false;
  $("stopBtn").disabled = true;
  $("analyzeBtn").disabled = false;
}

/* ================= SUBMIT AUDIO ================= */

async function submitAudio() {
  $("analyzeBtn").disabled = true;

  const fileInput = $("audioUpload");
  const uploadedFile = fileInput?.files?.[0];

  if (!audioBlob && !uploadedFile) {
    $("status").innerText = "Please record or upload audio";
    return;
  }

  if (!currentQuestion) {
    $("status").innerText = "Start interview first";
    return;
  }

  const statusEl = $("status");
  statusEl.innerText = "Analyzing...";

  try {
    const form = new FormData();

    if (uploadedFile) {
      form.append("audio", uploadedFile);
    } else {
      form.append("audio", audioBlob, "recording.webm");
    }

    form.append("question", currentQuestion);
    form.append("level", $("level").value || "Beginner");

    const res = await fetch(`${API_BASE}/attempts/submit`, {
      method: "POST",
      headers: { ...getAuthHeaders() },
      body: form
    });

    const data = await res.json();

    if (data.error) {
      statusEl.innerText = data.error;
      return;
    }

    $("retryBtn").style.display = "block";
    updateButtons("analyzed");
    statusEl.innerText = "Analysis complete";

    $("feedbackList").innerHTML = "";

    lastAnswer = data.transcript || "";

    const role = $("role").value;
    const ideal = idealAnswers[role] || "";
    const similarity = calculateSimilarity(lastAnswer, ideal);

    const duration = data.audio_metrics?.audio_duration || seconds;
    const speechStats = analyzeSpeech(lastAnswer, duration);

    addMessage("user", lastAnswer);
    renderResult(data);

    // EXTRA FEEDBACK (kept original logic)
    if (speechStats) {
      const feedback = [];

      if (speechStats.fillerCount > 3) {
        feedback.push(`You used ${speechStats.fillerCount} filler words`);
      }

      feedback.push(`Speed: ${speechStats.wpm} WPM (${speechStats.pace})`);

      const list = $("feedbackList");

      feedback.forEach(f => {
        const li = document.createElement("li");
        li.innerText = f;
        list.appendChild(li);
      });
    }

    if (similarity) {
      const li = document.createElement("li");

      li.innerText = `Relevance Score: ${similarity}%`;

      if (similarity < 40) {
        li.innerText += " (Try to include more key concepts)";
      } else if (similarity > 75) {
        li.innerText += " (Excellent answer)";
      }

      $("feedbackList").appendChild(li);
    }

    toggleResult(true);

    audioBlob = null;
    if (fileInput) fileInput.value = "";

    $("analyzeBtn").disabled = false;
    $("nextBtn").disabled = false;

    isRetry = false;

  } catch (e) {
    console.error("ERROR:", e);
    statusEl.innerText = "Error occurred";
  }
}
/* ================= RESULT ================= */

function renderResult(d) {
  $("fluency").innerText = d.fluency ?? "-";
  $("grammar").innerText = d.grammar ?? "-";
  $("accuracy").innerText = d.accuracy ?? "-";
  $("final").innerText = d.final_score ?? "-";

  $("feedbackList").innerHTML =
    (d.feedback || "")
      .replace(/\*\*/g, "")
      .split("\n")
      .filter(line => line.trim() !== "")
      .filter(line => line.trim().length > 3)
      .map(line => `<li>👉 ${line.trim()}</li>`)
      .join("");

  $("improvedAnswer").innerHTML =
    (d.improved_answer || "No suggestion")
      .replace(/\.\s+/g, ".<br><br>");

  const impEl = $("improvement");

  if (d.improvement !== undefined) {
    if (d.improvement > 0) {
      impEl.innerText = "Improved 📈";
      impEl.style.color = "#22c55e";
    } else if (d.improvement < 0) {
      impEl.innerText = "Slight drop 📉";
      impEl.style.color = "#ef4444";
    } else {
      impEl.innerText = "No change";
      impEl.style.color = "#aaa";
    }
  } else {
    impEl.innerText = "-";
  }

  if (d.final_score < 6) {
    $("retryBtn").style.display = "inline-block";
  } else {
    $("retryBtn").style.display = "none";
  }
}

/* ================= AUTH ================= */

async function loginUser(email) {
  try {
    const res = await fetch(`${API_BASE}/users/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user_id", data.user.user_id);
    localStorage.setItem("user_email", data.user.email);

    window.location.href = "home.html";

  } catch (err) {
    alert(err.message || "Login failed");
  }
}

async function registerUser(email, branch) {
  try {
    const res = await fetch(`${API_BASE}/users/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, branch })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }

    await loginUser(email);

  } catch (err) {
    alert(err.message || "Registration failed");
  }
}

/* ================= ANALYTICS ================= */

async function loadAnalytics() {
  const userId = localStorage.getItem("user_id");
  if (!userId) return;

  try {
    const res = await fetch(`${API_BASE}/progress/user/${userId}`);
    const data = await res.json();

    if ($("userLevel")) $("userLevel").innerText = data.current_level || "-";
    if ($("avgScore")) $("avgScore").innerText = data.avg_final ?? 0;
    if ($("weakSkill")) $("weakSkill").innerText = data.weakest_skill || "-";
    if ($("streak")) $("streak").innerText = (data.streak_days ?? 0) + " days";

    const flu = (data.avg_fluency || 0) * 10;
    const gra = (data.avg_grammar || 0) * 10;
    const acc = (data.avg_accuracy || 0) * 10;

    if ($("fluencyBar")) $("fluencyBar").style.width = flu + "%";
    if ($("grammarBar")) $("grammarBar").style.width = gra + "%";
    if ($("accuracyBar")) $("accuracyBar").style.width = acc + "%";

    highlightWeakSkill(data.weakest_skill);

  } catch (err) {
    console.error("Analytics error:", err);
  }
}

function highlightWeakSkill(skill) {
  ["fluencyBar", "grammarBar", "accuracyBar"].forEach(id => {
    $(id)?.parentElement.classList.remove("weak");
  });

  if (!skill) return;

  skill = skill.toLowerCase();

  if (skill === "fluency") $("fluencyBar")?.parentElement.classList.add("weak");
  if (skill === "grammar") $("grammarBar")?.parentElement.classList.add("weak");
  if (skill === "accuracy") $("accuracyBar")?.parentElement.classList.add("weak");
}

/* ================= RETRY ================= */

function retryAnswer() {
  if (!currentQuestion) return alert("No question to retry");

  lastAnswer = "";
  audioBlob = null;
  isRetry = true;

  $("status").innerText = "Try again";

  $("fluency").innerText = "-";
  $("grammar").innerText = "-";
  $("accuracy").innerText = "-";
  $("final").innerText = "-";
  $("improvement").innerText = "-";
  $("feedbackList").innerHTML = "";
  $("improvedAnswer").innerText = "Your improved answer will appear here";

  toggleResult(false);
}

/* ================= CHAT ================= */

function addMessage(type, text) {
  const chatBox = $("chatBox");

  const msg = document.createElement("div");
  msg.className = "chat-msg " + type;

  msg.innerText = text.replace(/([.?!])/g, "$1\n");

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/* ================= ANALYSIS ================= */

function analyzeAnswerQuality(answer) {
  if (!answer) return "empty";

  const words = answer.split(" ").length;

  if (words < 8) return "short";
  if (words < 20) return "medium";
  return "good";
}

function analyzeSpeech(transcript, durationSeconds) {
  if (!transcript) return null;

  const wordsArray = transcript.toLowerCase().split(/\s+/);
  const totalWords = wordsArray.length;

  const fillers = ["um", "uh", "like", "you know", "basically"];
  let fillerCount = 0;

  wordsArray.forEach(word => {
    if (fillers.includes(word)) fillerCount++;
  });

  const minutes = durationSeconds / 60;
  const wpm = minutes > 0 ? Math.round(totalWords / minutes) : 0;

  let pace = "Good";
  if (wpm < 90) pace = "Too slow";
  else if (wpm > 160) pace = "Too fast";

  return { fillerCount, wpm, pace, totalWords };
}

function calculateSimilarity(answer, ideal) {
  if (!answer || !ideal) return 0;

  const answerWords = answer.toLowerCase().split(/\s+/);
  const idealWords = ideal.toLowerCase().split(/\s+/);

  const matches = new Set(
    idealWords.filter(word => answerWords.includes(word))
  );

  return Math.round((matches.size / idealWords.length) * 100);
}

/* ================= INIT ================= */

window.addEventListener("DOMContentLoaded", () => {
  if ($("stopBtn")) $("stopBtn").disabled = true;
  if ($("resultSection")) $("resultSection").style.display = "none";
});