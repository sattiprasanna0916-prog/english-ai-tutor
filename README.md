# 🎤 SpeakSmart – AI Interview Coach

An AI-powered web application that helps users practice interview questions with real-time feedback on fluency, grammar, and accuracy.

---

## 🚀 Features

- 🎯 AI-generated interview questions
- 🎤 Speech recording & analysis
- 📊 Performance scoring (Fluency, Grammar, Accuracy)
- 🤖 AI feedback & improved answers
- 📈 Analytics dashboard with progress tracking
- 🔁 Retry system for improvement

---

## 🧠 Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI (Python)
- AI Models:
  - Wav2Vec2 (speech analysis)
  - NLP-based scoring (grammar & accuracy)
   - 🤖 Groq API (LLM) – Dynamic interview question generation and AI feedback  
- 📊 Hugging Face Dataset – Used for training the fluency regression model  
---

## ⚙️ How to Run

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload