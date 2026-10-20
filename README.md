# 🚀 AI Interview Coach (Full-Stack SaaS)

A production-ready AI Interview Evaluator built to analyze candidate responses with real-world strictness. It scores answers in granular 0.5 increments and provides constructive feedback based on technical depth.

## 🔗 Live Demo
https://ai-interview-evaluator-frontend.vercel.app/

## ✨ Features
*   **Granular AI Evaluation**: Uses strict system prompting to evaluate answers accurately (e.g., 7.5, 8.5) instead of generic whole numbers.
*   **Enterprise-Grade Auth**: Google OAuth and Email/Password authentication with email verification and password recovery, powered by Supabase.
*   **Secure Multi-Tenant Dashboard**: Users can track their own past interview scores securely without data leaks.
*   **Serverless Architecture**: FastAPI backend deployed seamlessly on Modal for high-performance AI inference via Groq.
*   **Modern UI/UX**: Fully responsive, dark-mode enabled interface built with Tailwind CSS.

## 🛠️ Tech Stack
*   **Frontend**: HTML5, Vanilla JavaScript, Tailwind CSS
*   **Backend**: Python, FastAPI, Render (Serverless Deployment)
*   **Database & Auth**: Supabase (PostgreSQL)
*   **AI Engine**: Groq API (gpt-oss-20b)

## 💡 What I Learned
As a 1st-year Computer Science (AI & ML) student, this project helped me transition from basic web development to building real-world architectures. Key learnings include:
1. Handling secure API keys in cloud environments.
2. Managing relational database operations (Inserts, Selects, Filtering).
3. Implementing row-level privacy logic for user-specific dashboards.
4. Structuring and deploying a decoupled Frontend (Vercel) + Backend (Render) system.
