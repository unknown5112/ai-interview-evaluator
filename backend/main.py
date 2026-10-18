import modal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import requests
import json
from supabase import create_client, Client

app = modal.App("interview-coach-v2-fastapi-app")
image = modal.Image.debian_slim().pip_install("fastapi", "pydantic", "requests", "supabase")

web_app = FastAPI()

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EvaluateRequest(BaseModel):
    topic: str
    transcript: str
    user_email: Optional[str] = "guest" 

class EvaluationResponse(BaseModel):
    score: float  
    feedback: str

@web_app.post("/api/evaluate")
def evaluate_answer(request: EvaluateRequest):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not all([groq_api_key, supabase_url, supabase_key]):
        raise HTTPException(status_code=500, detail="API keys missing.")

    supabase: Client = create_client(supabase_url, supabase_key)

    # 🔥 NAYA STRICT SYSTEM PROMPT 🔥
    system_prompt = """
    You are a brutally honest and highly critical technical interviewer. 
    Evaluate the candidate's answer against the topic provided. 
    
    SCORING RUBRIC (0.0 to 10.0 in 0.5 increments):
    - 0.0 to 3.0: Completely wrong, irrelevant, or shows absolute lack of understanding.
    - 3.5 to 5.0: Poor. Missing core concepts, highly confused, or mostly incorrect.
    - 5.5 to 7.0: Average. Covers basics but lacks depth, examples, or technical precision.
    - 7.5 to 8.5: Good. Accurate and well-structured, but has minor flaws or missing details.
    - 9.0 to 10.0: Exceptional. Perfect technical depth, clear metrics, and zero mistakes.
    
    CRITICAL INSTRUCTION: Do NOT default to high scores. If the answer is wrong or vague, you MUST give a score between 1.0 and 4.0. Be extremely strict.
    
    Respond ONLY in valid JSON format: {"score": 4.5, "feedback": "..."}
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-oss-20b", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {request.topic}\nCandidate Answer: {request.transcript}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2 # Temperature kam ki taaki AI strict logic use kare
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        
        response_json = response.json()
        ai_content = response_json["choices"][0]["message"]["content"]
        
        parsed_result = json.loads(ai_content)
        final_score = float(parsed_result.get("score", 0.0))
        final_feedback = parsed_result.get("feedback", "No feedback provided.")

        db_data = {
            "topic": request.topic,
            "transcript": request.transcript,
            "score": final_score,
            "feedback": final_feedback,
            "user_email": request.user_email
        }
        supabase.table("mock_interviews").insert(db_data).execute()
        
        return {
            "evaluation": {
                "score": final_score,
                "feedback": final_feedback
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")

@app.function(image=image, secrets=[modal.Secret.from_name("coach-secrets")])
@modal.asgi_app()
def fastapi_app():
    return web_app