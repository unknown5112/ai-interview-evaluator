# 🎙️ AI Mock Interview & Speech Evaluator

A highly performant, cloud-native mock interview platform designed to evaluate spoken responses and presentations in real-time using Generative AI. 

## 🚀 Features
- **Real-Time AI Evaluation:** Leverages Google's Gemini 3.8 Flash model to provide instant, constructive feedback and scoring out of 10.
- **Serverless Architecture:** Backend powered by Modal and FastAPI, utilizing `min_containers=1` to bypass cold-starts and ensure zero-latency execution.
- **Persistent Database:** Integrated with Supabase (PostgreSQL) to maintain a robust, real-time log of interview transcripts, scores, and AI feedback.
- **Optimized UI:** Dark-mode, modern interface built with Tailwind CSS, featuring background server-warming ("Ninja Ping") for a seamless user experience.

## 💻 Tech Stack
- **Frontend:** HTML5, Tailwind CSS, JavaScript
- **Backend:** Python, FastAPI, Requests
- **Cloud Infrastructure:** Modal (Serverless Cloud Deployments)
- **Database:** Supabase (PostgreSQL)
- **AI Engine:** Google Gemini API (3.8 Flash)

## 🛠️ Installation & Deployment

### 1. Cloud Deployment (Backend)
Navigate to the `backend` directory and deploy the FastAPI backend to Modal's serverless infrastructure:
```bash
cd backend
modal deploy main.py