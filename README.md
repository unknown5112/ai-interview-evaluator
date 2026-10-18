# 🚀 AI Interview Coach

An AI-powered mock interview evaluator designed to help candidates practice their communication skills and technical answers. The application analyzes a user's transcript against a specific interview topic and provides an instant score (out of 10) along with crisp, constructive feedback.

## 🌟 Features
* **Instant AI Evaluation:** Get immediate grading and personalized feedback on your interview answers.
* **Serverless Architecture:** Backend powered by Modal for fast, scalable, and zero-idle-cost execution.
* **Real-time Database:** All interview transcripts, topics, and scores are automatically logged in Supabase.
* **Modern UI/UX:** Clean, responsive, and intuitive interface built with Tailwind CSS.

## 💻 Tech Stack
* **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript (Hosted on **Vercel**)
* **Backend:** Python, FastAPI (Serverless deployment via **Modal**)
* **AI Engine:** Groq API (`gpt-oss-20b` model) for lightning-fast inference
* **Database:** **Supabase** (PostgreSQL)

## 🏗️ Architecture Flow
1. User submits an interview topic and their answer transcript via the Vercel-hosted frontend.
2. An HTTP POST request is sent to the FastAPI endpoint hosted on Modal.
3. The backend securely retrieves the Groq API key and forwards the prompt to the AI model.
4. The AI evaluates the response, returning a structured JSON containing a score and feedback.
5. The backend asynchronously logs the evaluation data into the Supabase `mock_interviews` table.
6. The frontend displays the result to the user.

## 🚀 Local Setup & Deployment

### Prerequisites
* Python 3.9+
* Modal Account & CLI installed
* Supabase Account
* Groq API Key

### Backend Deployment
1. Install dependencies:
   ```bash
   pip install modal fastapi supabase requests pydantic
