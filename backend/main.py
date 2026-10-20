# Yeh tera naya route hai past scores fetch karne ke liye
@app.get("/api/scores/{user_email}")
def get_past_scores(user_email: str):
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not all([supabase_url, supabase_key]):
        raise HTTPException(status_code=500, detail="API keys missing")
        
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        # Database se sirf is user_email ka data nikalenge
        response = supabase.table("mock_interviews").select("topic, score, feedback, created_at").eq("user_email", user_email).order("created_at", desc=True).execute()
        
        return {"status": "success", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))