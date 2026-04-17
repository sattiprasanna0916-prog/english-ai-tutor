const API_BASE = window.location.origin.includes("localhost")
  ? "http://127.0.0.1:8000"
  : "https://english-ai-tutor-1.onrender.com";
/* ---------------- STORAGE ---------------- */
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
let timerInterval;
let seconds = 0;
const $ = (id) => document.getElementById(id);
const uid = () => localStorage.getItem(LS.id);

/* ---------------- AUTH ---------------- */

function logout() {
  localStorage.clear();
  location.href = "index.html";
}

/* ---------------- INTERVIEW STATE ---------------- */

let interviewStarted = false;
let questionCount = 0;
let maxQuestions = 5;

let currentQuestion = "";
let lastAnswer = "";
let isRetry = false;
let mediaRecorder;
let audioBlob;

/* ---------------- UI HELPERS ---------------- */

function toggleResult(show) {
  const section = $("resultSection");
  if (!section) return;
  section.style.display = show ? "block" : "none";
}

/* ---------------- CHAT UI ---------------- */
function updateProgress() {
  $("progress").innerText = questionCount;

  const fill = $("progressFill");
  if (fill) {
    fill.style.width = (questionCount / 5) * 100 + "%";
  }
}

/* ---------------- INTERVIEW FLOW ---------------- */

async function startInterview() {
  interviewStarted = true;
  questionCount = 1;
  updateButtons("initial");
  const level = $("level").value;
  const role = $("role").value;
  const category = $("category").value;
$("retryBtn").style.display = "none";
  const res = await fetch(`${API_BASE}/question/generate`, {
    method: "POST",
    headers: {"Content-Type": "application/json",
       "Authorization": "Bearer " + localStorage.getItem("token"),
       ...getAuthHeaders()
    },
    body: JSON.stringify({ level, role, category })
  });

  const data = await res.json();

  currentQuestion = (data.question || "").trim();

  $("chatBox").innerHTML = "";
  addMessage("ai", currentQuestion);
  updateProgress();
  $("nextBtn").disabled = true;
  toggleResult(false); // hide AI panel initially
}

async function nextQuestion() {
  if (!interviewStarted) {
    alert("Start interview first");
    return;
  }

  if (!lastAnswer) {
    alert("Answer current question first");
    return;
  }

  if (questionCount >= maxQuestions) {
    alert("Interview completed");
    return;
  }
 $("retryBtn").style.display = "none";
  questionCount++;

  const quality = analyzeAnswerQuality(lastAnswer);

  let followUpPrompt = "";

  if (quality === "short") {
    followUpPrompt = "Can you explain your answer in more detail?";
  } 
  else if (quality === "medium") {
    followUpPrompt = "Can you give a specific example to support your answer?";
  } 
  else {
    followUpPrompt = "Great. Let's move to the next question.";
  }

  const role = $("role").value;

  const res = await fetch(`${API_BASE}/question/followup`, {
    method: "POST",
    headers: {"Content-Type": "application/json",
      "Authorization": "Bearer " + localStorage.getItem("token"),
      ...getAuthHeaders()
    },
    body: JSON.stringify({
      previous_question: currentQuestion,
      user_answer: lastAnswer,
      role: role,
      hint: followUpPrompt   // 🔥 NEW
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

/* ---------------- RECORDING ---------------- */
async function startRecording() {
  console.log("START CLICKED");

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

  mediaRecorder = new MediaRecorder(stream);
  let chunks = [];

  mediaRecorder.ondataavailable = e => chunks.push(e.data);

  mediaRecorder.onstop = () => {
    audioBlob = new Blob(chunks, { type: "audio/webm" });
    $("status").innerText = "✅ Recording ready";
  };

  mediaRecorder.start();

  $("status").innerText = "🎤 Recording… speak now";
  updateButtons("recording");
  // TIMER START
  seconds = 0;
  if ($("timer")) $("timer").innerText = "00:00";

  timerInterval = setInterval(() => {
    seconds++;

    let mins = String(Math.floor(seconds / 60)).padStart(2, "0");
    let secs = String(seconds % 60).padStart(2, "0");

    if ($("timer")) {
      $("timer").innerText = `${mins}:${secs}`;
    }
  }, 1000);

  // MIC GLOW
  $("micIndicator")?.classList.add("active");

  // BUTTON STATES
  $("startBtn").disabled = true;
  $("stopBtn").disabled = false;
  $("analyzeBtn").disabled = true;
}
function stopRecording() {
  if (mediaRecorder) mediaRecorder.stop();
  $("micIndicator")?.classList.remove("active");
  clearInterval(timerInterval);
  updateButtons("recorded");
  // BUTTON STATES
  $("startBtn").disabled = false;
  $("stopBtn").disabled = true;
  $("analyzeBtn").disabled = false;
}

/* ---------------- SUBMIT AUDIO ---------------- */
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
      headers: {
  Authorization: "Bearer " + localStorage.getItem("token")
},
      body: form   // ✅ FIXED
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Request failed");
    }

    const data = await res.json();
    updateButtons("analyzed");
    statusEl.innerText = "Analysis complete";

    $("feedbackList").innerHTML = "";

    lastAnswer = (data.transcript || "").trim();

// 🚫 Ignore useless responses
if (lastAnswer.length < 5 || lastAnswer.toLowerCase() === "thank you") {
  $("status").innerText = "⚠️ No valid speech detected. Please try again.";
  return;
}
   const wordCount = lastAnswer.split(" ").length;

if (wordCount < 3) {
  $("status").innerText = "⚠️ Please speak a longer answer";
  return;
}
const isEnglish = /^[a-zA-Z0-9\s.,?!'"]+$/.test(lastAnswer);

if (!isEnglish) {
  $("status").innerText = "⚠️ Please speak in English";
  return;
}
    const role = $("role").value;
    const ideal = idealAnswers[role] || "";
    const similarity = calculateSimilarity(lastAnswer, ideal);

    const duration = data.audio_metrics?.audio_duration || seconds;
    const speechStats = analyzeSpeech(lastAnswer, duration);

    addMessage("user", lastAnswer);
    renderResult(data);

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
        li.innerText += " (Add more key concepts)";
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
    statusEl.innerText = e.message || "Error occurred";
  }
}

/* ---------------- RESULT ---------------- */

function renderResult(d) {
  $("fluency").innerText = d.fluency ?? "-";
  $("grammar").innerText = d.grammar ?? "-";
  $("accuracy").innerText = d.accuracy ?? "-";
  $("final").innerText = d.final_score ?? "-";

 $("feedbackList").innerHTML =
  (d.feedback || "")
    .replace(/\*\*/g, "")                 // remove **
    .split("\n")                        // split properly
    .filter(line => line.trim() !== "")  
    .filter(line => line.trim().length > 3) // remove empty lines
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

/* ---------------- LOGIN ---------------- */

async function loginUser(email) {
  try {
    const res = await fetch(`${API_BASE}/users/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
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
    console.error("Login error:", err);
    alert(err.message || "Login failed");
  }
}

/* ---------------- REGISTER ---------------- */

async function registerUser(email, branch) {
  try {
    const res = await fetch(`${API_BASE}/users/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, branch })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Registration failed");
    }

    // ✅ After register → login
    await loginUser(email);

  } catch (err) {
    console.error("Register error:", err);
    alert(err.message || "Registration failed");
  }
}
/* ---------------- INIT ---------------- */
/* ---------------- ANALYTICS ---------------- */

async function loadAnalytics() {
  const userId = localStorage.getItem("user_id");

  if (!userId) {
    console.log("No user found");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/progress/user/${userId}`);
    const data = await res.json();

    console.log("Analytics Data:", data);

    // Top cards
    const levelEl = $("userLevel");
const avgEl = $("avgScore");
const weakEl = $("weakSkill");
const streakEl = $("streak");

if (levelEl) levelEl.innerText = data.current_level || "-";
if (avgEl) avgEl.innerText = data.avg_final ?? 0;
if (weakEl) weakEl.innerText = data.weakest_skill || "-";
// highlight weakest skill tile
document.querySelectorAll(".tile").forEach(t => t.classList.remove("danger-tile"));

if (data.weakest_skill) {
  const skill = data.weakest_skill.toLowerCase();

  if (skill.includes("fluency")) document.getElementById("fluencyBar")?.closest(".tile")?.classList.add("danger-tile");
  if (skill.includes("grammar")) document.getElementById("grammarBar")?.closest(".tile")?.classList.add("danger-tile");
  if (skill.includes("accuracy")) document.getElementById("accuracyBar")?.closest(".tile")?.classList.add("danger-tile");
}
if (streakEl) streakEl.innerText = (data.streak_days ?? 0) + " days";
// streak warning (low streak)
const streakDays = data.streak_days ?? 0;

const streakTile = streakEl?.closest(".tile");

if (streakTile) {
  streakTile.classList.remove("streak-alert");

  if (streakDays < 3) {
    streakTile.classList.add("streak-alert");
  }
}
    // Bars (scale 0–10 → 0–100)
    const flu = (data.avg_fluency || 0) * 10;
    const gra = (data.avg_grammar || 0) * 10;
    const acc = (data.avg_accuracy || 0) * 10;

    setTimeout(() => {
  if ($("fluencyBar")) $("fluencyBar").style.width = flu + "%";
if ($("grammarBar")) $("grammarBar").style.width = gra + "%";
if ($("accuracyBar")) $("accuracyBar").style.width = acc + "%";
}, 200);
console.log("Weak skill:", data.weakest_skill);
    highlightWeakSkill(data.weakest_skill);
    // Chart
    const chartEl = document.getElementById("chart");

if (chartEl) {
  const ctx = chartEl.getContext("2d");

  const gradient = ctx.createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, "#60a5fa");
  gradient.addColorStop(1, "transparent");

  new Chart(ctx, {
  type: "line",
  data: {
    labels: data.history_labels,
    datasets: [{
      label: "Score",
      data: data.history_scores,
      borderColor: "#60a5fa",
      backgroundColor: gradient,
      fill: true,
      tension: 0.4
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false }
    },
    scales: {
      y: {
        min: 0,
        max: 10,
        beginAtZero: true,
        ticks: {
          stepSize: 1,
          callback: function(value) {
            return value;
          }
        }
      }
    }
  }
});
}

  } catch (err) {
    console.error("Analytics error:", err);
  }
}
function highlightWeakSkill(skill){
  // remove previous highlights
  ["fluencyBar","grammarBar","accuracyBar"].forEach(id=>{
  $(id)?.parentElement.classList.remove("weak");
});
  if(!skill) return;

  skill = skill.toLowerCase();

  if(skill === "fluency"){
    document.getElementById("fluencyBar").parentElement.classList.add("weak");
  }
  else if(skill === "grammar"){
    document.getElementById("grammarBar").parentElement.classList.add("weak");
  }
  else if(skill === "accuracy"){
    document.getElementById("accuracyBar").parentElement.classList.add("weak");
  }
}
function retryAnswer() {
  if (!currentQuestion) {
    alert("No question to retry");
    return;
  }

  // Clear previous answer
  lastAnswer = "";
  audioBlob = null;
  isRetry = true;
  $("status").innerText = "🔁 Try again";

  // Clear AI result
  $("fluency").innerText = "-";
  $("grammar").innerText = "-";
  $("accuracy").innerText = "-";
  $("final").innerText = "-";
  $("improvement").innerText = "-";
  $("feedbackList").innerHTML = "";
  $("improvedAnswer").innerText = "Your improved answer will appear here";

  toggleResult(false); // hide previous result
}
function addMessage(type, text) {
  const chatBox = $("chatBox");

  const msg = document.createElement("div");
  msg.className = "chat-msg " + type;

  // ✅ FIX spacing issue
  msg.innerText = text.replace(/([.?!])/g, "$1\n");
  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}
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

  // 🎯 FILLER WORDS
  const fillers = ["um", "uh", "like", "you know", "basically"];
  let fillerCount = 0;

  wordsArray.forEach(word => {
    if (fillers.includes(word)) fillerCount++;
  });

  // 🎯 WPM (words per minute)
  const minutes = durationSeconds / 60;
  const wpm = minutes > 0 ? Math.round(totalWords / minutes) : 0;

  // 🎯 SPEED CATEGORY
  let pace = "Good";
  if (wpm < 90) pace = "Too slow";
  else if (wpm > 160) pace = "Too fast";

  return {
    fillerCount,
    wpm,
    pace,
    totalWords
  };
}
function calculateSimilarity(answer, ideal) {
  if (!answer || !ideal) return 0;

  const answerWords = answer.toLowerCase().split(/\s+/);
  const idealWords = ideal.toLowerCase().split(/\s+/);

  const uniqueMatches = new Set(
    idealWords.filter(word => answerWords.includes(word))
  );

  const score = (uniqueMatches.size / idealWords.length) * 100;

  return Math.round(score);
}
function getAuthHeaders() {
  const token = localStorage.getItem("token");

  if (!token) {
    alert("Session expired. Please login again.");
    window.location.href = "index.html";
    return {};
  }

  return {
    "Authorization": "Bearer " + token
  };
}
function updateButtons(state) {

  const start = $("startBtn");
  const stop = $("stopBtn");
  const analyze = $("analyzeBtn");
  const next = $("nextBtn");
  const retry = $("retryBtn");

  // Hide all first
  [start, stop, analyze, next, retry].forEach(btn => {
    if (btn) btn.style.display = "none";
  });

  if (state === "initial") {
    start.style.display = "inline-block";
  }

  if (state === "recording") {
    stop.style.display = "inline-block";
  }

  if (state === "recorded") {
    analyze.style.display = "inline-block";
  }

  if (state === "analyzed") {
    next.style.display = "inline-block";
    retry.style.display = "inline-block";
  }
}
window.addEventListener("DOMContentLoaded", function () {

  updateButtons("initial");

  $("resultSection") && ($("resultSection").style.display = "none");

  $("status") && ($("status").innerText = "Idle");
  $("timer") && ($("timer").innerText = "00:00");

  $("micIndicator")?.classList.remove("active");
});