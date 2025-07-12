from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import uvicorn
from datetime import datetime
import os

# Import RAG system
from rag import RAGSystem

app = FastAPI(title="BodyBae.ai API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = RAGSystem()

# Pydantic models
class UserProfile(BaseModel):
    name: str
    age: int
    sex: str
    height: float  # in cm
    weight: float  # in kg
    activity_level: str  # sedentary, light, moderate, active

class GoalRequest(BaseModel):
    goal: str
    target_weeks: Optional[int] = 12

class ChatMessage(BaseModel):
    message: str
    user_profile: Optional[Dict] = None

class ProgressUpdate(BaseModel):
    weight: Optional[float] = None
    workout: Optional[str] = None

# In-memory user session (for MVP - not persistent)
user_sessions = {}

def calculate_bmi(weight: float, height: float) -> Dict:
    """Calculate BMI and return category with advice"""
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
        advice = "Consider focusing on healthy weight gain with nutrient-dense foods."
    elif bmi < 25:
        category = "Normal weight"
        advice = "Great job maintaining a healthy weight! Focus on overall fitness."
    elif bmi < 30:
        category = "Overweight"
        advice = "Consider a moderate weight loss approach with balanced nutrition and exercise."
    else:
        category = "Obese"
        advice = "Consult with healthcare professionals for a comprehensive weight management plan."
    
    return {
        "bmi": round(bmi, 1),
        "category": category,
        "advice": advice
    }

def calculate_bmr(weight: float, height: float, age: int, sex: str) -> float:
    """Calculate Basal Metabolic Rate"""
    if sex.lower() in ['male', 'man', 'm']:
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    return bmr

def get_activity_multiplier(activity_level: str) -> float:
    """Get activity multiplier for TDEE calculation"""
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725
    }
    return multipliers.get(activity_level.lower(), 1.2)

def get_realistic_timeline(goal: str, current_weight: float, bmi: float) -> Dict:
    """Provide realistic timeline based on goal and current status"""
    timelines = {
        "Lose Weight": {
            "rate": 0.5,  # kg per week
            "description": "Healthy weight loss is 0.5-1 kg per week",
            "min_weeks": 8,
            "max_weeks": 24
        },
        "Gain Weight": {
            "rate": 0.25,  # kg per week
            "description": "Healthy weight gain is 0.25-0.5 kg per week",
            "min_weeks": 8,
            "max_weeks": 24
        },
        "Gain Muscle": {
            "rate": 0.1,  # kg per week
            "description": "Visible muscle gain typically takes 8-12 weeks",
            "min_weeks": 8,
            "max_weeks": 16
        },
        "Lose Fat": {
            "rate": 0.4,  # kg per week
            "description": "Focused fat loss with muscle preservation",
            "min_weeks": 6,
            "max_weeks": 20
        },
        "Toning": {
            "rate": None,
            "description": "Body recomposition typically shows in 6-8 weeks",
            "min_weeks": 6,
            "max_weeks": 12
        },
        "Bulking": {
            "rate": 0.3,  # kg per week
            "description": "Controlled weight gain for muscle building",
            "min_weeks": 12,
            "max_weeks": 24
        },
        "Maintain Weight": {
            "rate": 0,
            "description": "Focus on consistency and healthy habits",
            "min_weeks": 4,
            "max_weeks": 52
        }
    }
    
    timeline = timelines.get(goal, timelines["Maintain Weight"])
    return timeline

def generate_milestones(weeks: int, goal: str) -> List[Dict]:
    """Generate milestone checkpoints"""
    milestones = []
    checkpoints = [2, 4, 6, 8, 12, 16, 20, 24]
    
    for week in checkpoints:
        if week <= weeks:
            milestones.append({
                "week": week,
                "description": f"Week {week} check-in",
                "target": f"Progress checkpoint for {goal.lower()}"
            })
    
    return milestones

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"message": "BodyBae.ai API is running!"}

@app.post("/api/onboard")
async def onboard_user(profile: UserProfile):
    """Handle user onboarding and BMI calculation"""
    try:
        # Calculate BMI
        bmi_data = calculate_bmi(profile.weight, profile.height)
        
        # Calculate BMR and TDEE
        bmr = calculate_bmr(profile.weight, profile.height, profile.age, profile.sex)
        activity_multiplier = get_activity_multiplier(profile.activity_level)
        tdee = bmr * activity_multiplier
        
        # Create session
        session_id = f"{profile.name}_{datetime.now().timestamp()}"
        user_sessions[session_id] = {
            "profile": profile.dict(),
            "bmi_data": bmi_data,
            "bmr": round(bmr, 0),
            "tdee": round(tdee, 0)
        }
        
        return {
            "session_id": session_id,
            "bmi": bmi_data["bmi"],
            "bmi_category": bmi_data["category"],
            "bmi_advice": bmi_data["advice"],
            "bmr": round(bmr, 0),
            "tdee": round(tdee, 0),
            "message": f"Hi {profile.name}! Your BMI is {bmi_data['bmi']} ({bmi_data['category']}). {bmi_data['advice']}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/set_goal")
async def set_goal(request: GoalRequest):
    """Set user fitness goal and provide timeline"""
    try:
        # For MVP, we'll use the last created session
        if not user_sessions:
            raise HTTPException(status_code=404, detail="No user session found. Please onboard first.")
        
        session_id = list(user_sessions.keys())[-1]
        session = user_sessions[session_id]
        
        # Get realistic timeline
        timeline = get_realistic_timeline(
            request.goal, 
            session["profile"]["weight"],
            session["bmi_data"]["bmi"]
        )
        
        # Generate milestones
        target_weeks = min(request.target_weeks or timeline["max_weeks"], timeline["max_weeks"])
        milestones = generate_milestones(target_weeks, request.goal)
        
        # Update session
        session["goal"] = request.goal
        session["target_weeks"] = target_weeks
        session["milestones"] = milestones
        
        response_message = f"Great choice! {timeline['description']}. "
        if target_weeks < timeline["min_weeks"]:
            response_message += f"Note: {timeline['min_weeks']} weeks is recommended for sustainable results. "
        response_message += f"I've set {len(milestones)} milestones to track your progress!"
        
        return {
            "goal": request.goal,
            "target_weeks": target_weeks,
            "timeline_info": timeline,
            "milestones": milestones,
            "message": response_message
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Handle chat messages with RAG system"""
    try:
        # Get response from RAG system
        response = rag_system.get_response(
            message.message,
            user_profile=message.user_profile
        )
        
        return {
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/progress")
async def update_progress(update: ProgressUpdate):
    """Log progress update (conversational only for MVP)"""
    try:
        response = "Great job logging your progress! "
        
        if update.weight:
            response += f"Weight recorded: {update.weight}kg. "
        
        if update.workout:
            response += f"Workout completed: {update.workout}. "
        
        response += "Keep up the excellent work! 💪"
        
        return {
            "message": response,
            "logged_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/daily_tip")
async def get_daily_tip():
    """Get daily motivational tip"""
    tips = [
        "Remember: Progress, not perfection! Every small step counts.",
        "Stay hydrated! Aim for 8 glasses of water throughout the day.",
        "Focus on whole foods - they'll fuel your body better than processed ones.",
        "Rest days are growth days - your muscles need time to recover!",
        "Consistency beats perfection. Show up, even on tough days.",
        "Track your progress with photos and measurements, not just the scale.",
        "Sleep is crucial - aim for 7-9 hours for optimal recovery.",
        "Celebrate small wins - they add up to big changes!",
        "Mix up your workouts to prevent boredom and plateaus.",
        "Listen to your body - rest when needed, push when ready."
    ]
    
    import random
    tip = random.choice(tips)
    
    return {
        "tip": tip,
        "date": datetime.now().date().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "BodyBae.ai"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)