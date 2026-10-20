from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# 1. Pure FastAPI Setup
app = FastAPI()

# 2. CORS Fix (Vercel Frontend Allow Kar Diya)
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

# 3. Data Format
class EvaluationRequest(BaseModel):
    topic: str
    answer: str

# 4. Tera Endpoint
@app.post("/api/evaluate")
async def evaluate_answer(request: EvaluationRequest):
    # (Yahan tera asli Gemini/AI logic aayega)
    user_topic = request.topic
    user_answer = request.answer
    
    return {
        "success": True,
        "evaluation": f"Mock evaluation for {user_topic}. Answer received successfully!",
        "score": 8
    }

# 5. Render ke liye Health Check Route (Zaroori hota hai)
@app.get("/")
def home():
    return {"message": "AI Backend is running smoothly on Render!"}