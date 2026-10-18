import os
import json
import requests
import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

image = modal.Image.debian_slim().pip_install(
    "fastapi", "supabase", "requests", "pydantic"
)

# Naya app name taaki purana cache bilkul use na ho
app = modal.App("interview-coach-v2")

web_app = FastAPI(title="AI Interview Evaluator V2")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewRequest(BaseModel):
    topic: str
    transcript: str

@web_app.get("/")
def health_check():
    groq_key = os.environ.get("GROQ_API_KEY", "")
    return {
        "status": "online",
        "groq_key_loaded": bool(groq_key and groq_key.startswith("gsk_")),
        "key_prefix": groq_key[:7] + "..." if groq_key else "MISSING"
    }

def evaluate_with_groq(topic: str, transcript: str):
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise Exception("GROQ_API_KEY is missing in Modal Secret 'coach-secrets'")

    url = "https://api.groq.com/openai/v1/chat/completions"

    prompt = f"""
    You are an expert HR Interviewer and Communication Coach.
    Evaluate the following spoken response from a candidate.

    Topic/Question: {topic}
    Candidate's Transcript: {transcript}

    Provide a valid JSON response with this exact structure:
    {{
        "score": 8,
        "feedback": "A crisp 3-4 sentence constructive feedback highlighting strengths and areas for improvement."
    }}
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "You always respond in valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"}
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=20)
    if resp.status_code != 200:
        raise Exception(f"Groq API Error: {resp.text}")

    data = resp.json()
    return json.loads(data["choices"][0]["message"]["content"])

@web_app.post("/api/evaluate")
def evaluate_response(req: InterviewRequest):
    try:
        evaluation = evaluate_with_groq(req.topic, req.transcript)
        
        # Database logic inside nested try-except (failsafe)
        try:
            supabase_url = os.environ.get("SUPABASE_URL", "").strip()
            supabase_key = os.environ.get("SUPABASE_KEY", "").strip()
            if supabase_url and supabase_key:
                supabase: Client = create_client(supabase_url, supabase_key)
                supabase.table("mock_interviews").insert({
                    "topic": req.topic,
                    "transcript": req.transcript,
                    "score": evaluation.get("score", 0),
                    "feedback": evaluation.get("feedback", "")
                }).execute()
        except Exception as db_err:
            print(f"Supabase Failsafe: {str(db_err)}")

        return {
            "status": "success",
            "topic": req.topic,
            "evaluation": evaluation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.function(image=image, secrets=[modal.Secret.from_name("coach-secrets")], min_containers=1)
@modal.asgi_app()
def fastapi_app():
    return web_app