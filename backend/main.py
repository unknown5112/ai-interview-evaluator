from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
import json
from supabase import create_client, Client

app = FastAPI()

# 1. CORS Middleware Setup (Vercel frontend se connect karne ke liye)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production mein yahan apna Vercel URL daal dena
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Pydantic Request Models
class EvaluateRequest(BaseModel):
    topic: str
    transcript: str
    user_email: str = "anonymous@user.com"

# 3. POST Route: AI Evaluation
@app.post("/api/evaluate")
def evaluate_answer(request: EvaluateRequest):
    groq_api_key = os.environ.get("GROQ_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not all([groq_api_key, supabase_url, supabase_key]):
        raise HTTPException(status_code=500, detail="API keys missing in Render Environment.")

    supabase: Client = create_client(supabase_url, supabase_key)

    # Brutally objective system prompt
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

    # Custom Model Request
    data = {
        "model": "openai/gpt-oss-20b", 
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {request.topic}\nCandidate Answer: {request.transcript}"}
        ],
        "temperature": 0.2
    }

    try:
        response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        
        if not response.ok:
            raise Exception(f"Groq API Error: {response.text}")
            
        response.raise_for_status()
        
        response_json = response.json()
        ai_content = response_json["choices"][0]["message"]["content"]
        
        # Custom JSON Extractor
        start_index = ai_content.find('{')
        end_index = ai_content.rfind('}') + 1
        if start_index != -1 and end_index != 0:
            clean_json_str = ai_content[start_index:end_index]
        else:
            clean_json_str = ai_content

        parsed_result = json.loads(clean_json_str)
        final_score = float(parsed_result.get("score", 0.0))
        final_feedback = parsed_result.get("feedback", "No feedback provided.")

        # Database Insertion (int() fix to prevent 500 error)
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

# 4. GET Route: Fetch Past Scores for Logged-In User
@app.get("/api/scores/{user_email}")
def get_past_scores(user_email: str):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not all([supabase_url, supabase_key]):
        raise HTTPException(status_code=500, detail="API keys missing")
        
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Fetch data filtered by user_email and sorted by newest first
        response = supabase.table("mock_interviews").select("topic, score, feedback, created_at").eq("user_email", user_email).order("created_at", desc=True).execute()
        
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))