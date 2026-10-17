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

app = modal.App("ai-interview-evaluator")

web_app = FastAPI(title="AI Interview Evaluator API")
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InterviewRequest(BaseModel):
    topic: str
    transcript: str

def evaluate_with_gemini(topic: str, transcript: str):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise Exception("Gemini API Key missing in environment")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}"

    prompt = f"""
    You are an expert HR Interviewer and Communication Coach.
    Evaluate the following spoken response from a candidate.

    Topic/Question: {topic}
    Candidate's Transcript: {transcript}

    Provide a valid JSON response with this exact structure:
    {{
        "score": <An integer out of 10 based on clarity, structure, relevance, and confidence>,
        "feedback": "A crisp 3-4 sentence constructive feedback highlighting strengths and areas for improvement."
    }}
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4}
    }

    print("--> Ping sent to Google Gemini...")
    # 🔥 FIX: Added a 20-second strict timeout to prevent indefinite hanging
    resp = requests.post(url, json=payload, timeout=20) 
    print(f"--> Google responded with status code: {resp.status_code}")

    if resp.status_code != 200:
        raise Exception(f"Gemini API Error: {resp.text}")

    data = resp.json()
    answer = data['candidates'][0]['content']['parts'][0]['text']
    answer = answer.replace("```json", "").replace("```", "").strip()

    return json.loads(answer)

@web_app.post("/api/evaluate")
def evaluate_response(req: InterviewRequest):
    print(f"\n🚀 New Request! Topic: {req.topic}")
    try:
        print("⏳ Step 1: Starting AI Evaluation...")
        evaluation = evaluate_with_gemini(req.topic, req.transcript)
        print("✅ Step 1 Success! AI Score:", evaluation.get("score"))

        print("⏳ Step 2: Connecting to Supabase Database...")
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")

        if supabase_url and supabase_key:
            supabase: Client = create_client(supabase_url, supabase_key)
            supabase.table("mock_interviews").insert({
                "topic": req.topic,
                "transcript": req.transcript,
                "score": evaluation["score"],
                "feedback": evaluation["feedback"]
            }).execute()
            print("✅ Step 2 Success! Data saved to Supabase.")
        else:
            print("⚠️ Supabase keys not found in environment. Skipping database step.")

        return {
            "status": "success",
            "topic": req.topic,
            "evaluation": evaluation
        }
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.function(image=image, secrets=[modal.Secret.from_dotenv()], min_containers=1)
@modal.asgi_app()
def fastapi_app():
    return web_app