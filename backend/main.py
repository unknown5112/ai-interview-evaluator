from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import requests
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Loads environment variables for local testing; Render uses its dashboard settings.
load_dotenv()

app = FastAPI()

# Vercel frontend URL allowed here to prevent CORS 'Failed to fetch' errors
origins = [
    "http://localhost:5173", 
    "https://ai-interview-evaluator-frontend.vercel.app" 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EvaluateRequest(BaseModel):
    topic: str
    transcript: str  # Matches the frontend body EXACTLY
    user_email: Optional[str] = "guest" 

class EvaluationResponse(BaseModel):
    score: float  
    feedback: str

@app.post("/api/evaluate")
def evaluate_answer(request: EvaluateRequest):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not all([groq_api_key, supabase_url, supabase_key]):
        raise HTTPException(status_code=500, detail="API keys missing in Render Environment.")

    supabase: Client = create_client(supabase_url, supabase_key)

    system_prompt = """
    You are an uncompromising, mathematically precise, and brutally objective technical evaluator. Your job is to grade candidates strictly based on factual accuracy, depth, and completeness using the absolute 0.0 to 10.0 scale.

    ABSOLUTE SCORING RULES:
    - 0.0: If the answer is completely blank, gibberish, factually entirely wrong, or irrelevant to the topic, you MUST give 0.0. No sympathy marks.
    - 1.0 to 3.0: Severely flawed, major misconceptions, or barely touching the right direction with mostly incorrect details.
    - 4.0 to 6.0: Moderate. Contains basic correct definitions but misses critical technical explanations, examples, or depth.
    - 7.0 to 8.9: Strong. Highly accurate, good examples, minor gaps or missing advanced edge cases.
    - 9.0 to 10.0: Flawless. Absolute technical mastery, perfect architecture, exact metrics, and complete comprehensive detail.

    Do not cluster scores around 7 or 8. If an answer is terrible, give 0 or 1. If it's a masterpiece, give 10. Be completely fearless in your grading.
    
    Respond ONLY in valid JSON format: {"score": 0.0, "feedback": "..."}
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "llama3-8b-8192", # Valid, fast model for Groq
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {request.topic}\nCandidate Answer: {request.transcript}"}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2
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

@app.get("/")
def home():
    return {"message": "AI Interview Backend is running live on Render!", "status": "Active"}