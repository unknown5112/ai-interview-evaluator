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
    score: int  
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
    - 0.0: If the answer is completely blank, gibberish, factually entirely wrong, or irrelevant to the topic.
    - 4.0 to 6.0: Moderate. Contains basic correct definitions but misses critical technical explanations.
    - 9.0 to 10.0: Flawless. Absolute technical mastery and complete comprehensive detail.
    
    Respond ONLY in valid JSON format exactly like this: {"score": 8.5, "feedback": "Your detailed feedback here."}
    Do not add any greetings or extra text.
    """

    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }

    # FIX 1: Naya fast model aur response_format hata diya taaki 400 error na aaye
    # Baki code upar ka same rahega...

    data = {
        "model": "openai/gpt-oss-20b",  # YAHAN EXACT LIST WALA NAAM DAALNA HAI
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {request.topic}\nCandidate Answer: {request.transcript}"}
        ],
        "temperature": 0.2
    }

    # Niche ka try...except block bhi same rahega

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        
        # FIX 2: Agar ab koi error aaya, toh hum exact reason screen par dikhayenge
        if not response.ok:
            raise Exception(f"Groq API Error: {response.text}")
            
        response.raise_for_status()
        
        response_json = response.json()
        ai_content = response_json["choices"][0]["message"]["content"]
        
        # FIX 3: Custom JSON Extractor (agar AI extra text de de toh crash na ho)
        start_index = ai_content.find('{')
        end_index = ai_content.rfind('}') + 1
        if start_index != -1 and end_index != 0:
            clean_json_str = ai_content[start_index:end_index]
        else:
            clean_json_str = ai_content

        parsed_result = json.loads(clean_json_str)
        final_score = int(parsed_result.get("score", 0.0))
        final_feedback = parsed_result.get("feedback", "No feedback provided.")

        db_data = {
            "topic": request.topic,
            "transcript": request.transcript,
            "score": int(final_score),
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "AI Interview Backend is running live on Render!", "status": "Active"}