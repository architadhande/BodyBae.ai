from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import uuid

# Import the enhanced RAG system
try:
    from rag_system import create_enhanced_rag_system, integrate_enhanced_rag_with_flask_app
    RAG_AVAILABLE = True
except ImportError:
    print("RAG system not available - using fallback responses")
    RAG_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# In-memory storage (replace with database in production)
users_db = {}
progress_db = {}
goals_db = {}
chat_history_db = {}

# Initialize RAG system
rag_system = None
if RAG_AVAILABLE:
    try:
        rag_system = create_enhanced_rag_system()
        if rag_system:
            integrate_enhanced_rag_with_flask_app(app, rag_system)
            print("✅ Enhanced RAG system initialized successfully")
        else:
            print("⚠️ RAG system failed to initialize - using fallback")
    except Exception as e:
        print(f"⚠️ RAG system error: {e} - using fallback")
        rag_system = None

class BodyBaeAI:
    def __init__(self):
        self.fitness_goals = [
            "Lose Weight",
            "Gain Muscle", 
            "Improve Endurance",
            "Increase Strength",
            "Improve Flexibility",
            "General Fitness",
            "Maintain Weight"
        ]
        
        self.activity_levels = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }
        
        self.health_tips = {
            "Lose Weight": [
                "Create a moderate caloric deficit of 500-750 calories per day for healthy weight loss",
                "Focus on whole foods: lean proteins, vegetables, fruits, and whole grains",
                "Stay hydrated - drink water before meals to help with satiety",
                "Combine cardio and strength training for optimal fat loss while preserving muscle",
                "Get 7-9 hours of quality sleep - poor sleep affects hunger hormones",
                "Practice mindful eating and avoid distractions during meals"
            ],
            "Gain Muscle": [
                "Consume 1.6-2.2g of protein per kg of body weight daily",
                "Progressive overload is key - gradually increase weight, reps, or sets",
                "Get 7-9 hours of quality sleep for muscle recovery and growth hormone release",
                "Focus on compound movements like squats, deadlifts, bench press, and rows",
                "Stay in a slight caloric surplus (200-500 calories above maintenance)",
                "Train each muscle group 2-3 times per week for optimal growth"
            ],
            "Improve Endurance": [
                "Start with low-intensity steady-state cardio and gradually increase duration",
                "Include interval training 1-2 times per week for improved cardiovascular capacity",
                "Stay consistent - aim for at least 150 minutes of moderate cardio weekly",
                "Proper hydration is crucial - drink water before, during, and after exercise",
                "Fuel your workouts with adequate carbohydrates for energy",
                "Allow for rest days to prevent burnout and overtraining"
            ],
            "Increase Strength": [
                "Focus on compound movements with progressive overload",
                "Train in lower rep ranges (3-6 reps) with heavier weights",
                "Allow adequate rest between sets (2-5 minutes for strength training)",
                "Prioritize form over weight - proper technique prevents injuries",
                "Eat adequate protein and calories to support strength gains",
                "Track your lifts to ensure consistent progression"
            ],
            "Improve Flexibility": [
                "Incorporate daily stretching routines, holding each stretch for 15-30 seconds",
                "Try yoga or Pilates classes for structured flexibility training",
                "Warm up before stretching - dynamic stretches before workouts, static after",
                "Focus on major muscle groups and problem areas",
                "Be consistent - flexibility improvements take time and regular practice",
                "Listen to your body and never force a stretch to the point of pain"
            ],
            "General Fitness": [
                "Combine cardio, strength training, and flexibility work for balanced fitness",
                "Aim for 150 minutes of moderate cardio plus 2-3 strength sessions weekly",
                "Focus on functional movements that improve daily life activities",
                "Vary your workouts to prevent boredom and work different muscle groups",
                "Prioritize consistency over intensity - regular moderate exercise beats sporadic intense sessions",
                "Find activities you enjoy to make fitness sustainable long-term"
            ],
            "Maintain Weight": [
                "Focus on maintaining your current caloric intake at maintenance level",
                "Continue regular exercise to preserve muscle mass and cardiovascular health",
                "Eat balanced meals with adequate protein, carbs, and healthy fats",
                "Monitor your weight weekly, not daily - weight fluctuates naturally",
                "Focus on body composition rather than just the scale number",
                "Stay consistent with healthy habits you've already established"
            ]
        }
        
        self.motivational_messages = [
            "Every workout counts, no matter how small! 💪",
            "Progress isn't always linear - trust the process! 📈",
            "Your body can do it. It's your mind you need to convince. 🧠",
            "A healthy outside starts from the inside. ❤️",
            "The groundwork for all happiness is good health. 🌟",
            "You're stronger than you think and capable of amazing things! ⭐",
            "Small steps daily lead to big changes yearly. 🚀",
            "Your only competition is who you were yesterday. 🌱",
            "Consistency beats perfection every single time. ✨",
            "Believe in yourself - you've got this! 🔥"
        ]
    
    def calculate_bmr(self, weight: float, height: float, age: int, sex: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if sex.lower() in ['male', 'man', 'm']:
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:  # female or prefer not to say
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        return bmr
    
    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Calculate Total Daily Energy Expenditure"""
        return bmr * self.activity_levels.get(activity_level, 1.2)
    
    def calculate_bmi(self, weight: float, height: float) -> Dict:
        """Calculate BMI and return category with personalized recommendations"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            category = "Underweight"
            advice = "Consider focusing on healthy weight gain with nutrient-dense foods."
            recommended_goals = ["Gain Muscle", "Increase Strength", "General Fitness"]
        elif bmi < 25:
            category = "Normal Weight"
            advice = "Great job maintaining a healthy weight! Focus on overall fitness."
            recommended_goals = ["Gain Muscle", "Improve Endurance", "Increase Strength", "Improve Flexibility", "General Fitness", "Maintain Weight"]
        elif bmi < 30:
            category = "Overweight"
            advice = "Consider a moderate weight loss approach with balanced nutrition and exercise."
            recommended_goals = ["Lose Weight", "Improve Endurance", "General Fitness"]
        else:
            category = "Obese"
            advice = "Consult with healthcare professionals for a comprehensive weight management plan."
            recommended_goals = ["Lose Weight", "Improve Endurance", "General Fitness"]
        
        return {
            "bmi": round(bmi, 1),
            "category": category,
            "advice": advice,
            "recommended_goals": recommended_goals
        }
    
    def get_realistic_timeline(self, goal: str, current_weight: float, target_weight: float = None) -> Dict:
        """Provide realistic timeline for goals"""
        timelines = {
            "Lose Weight": {
                "rate": 0.5,  # kg per week
                "description": "Healthy weight loss is 0.5-1 kg per week",
                "min_weeks": 4,
                "max_weeks": 52
            },
            "Gain Muscle": {
                "rate": 0.25,  # kg per week
                "description": "Visible muscle gain typically takes 8-12 weeks with consistent training",
                "min_weeks": 8,
                "max_weeks": 24
            },
            "Improve Endurance": {
                "rate": None,
                "description": "Noticeable endurance improvements in 4-6 weeks with consistent training",
                "min_weeks": 4,
                "max_weeks": 12
            },
            "Increase Strength": {
                "rate": None,
                "description": "Strength gains are often seen within 2-4 weeks of consistent training",
                "min_weeks": 2,
                "max_weeks": 16
            },
            "Improve Flexibility": {
                "rate": None,
                "description": "Flexibility improvements visible in 3-4 weeks with daily practice",
                "min_weeks": 3,
                "max_weeks": 12
            },
            "General Fitness": {
                "rate": None,
                "description": "Overall fitness improvements noticeable in 4-8 weeks",
                "min_weeks": 4,
                "max_weeks": 16
            },
            "Maintain Weight": {
                "rate": 0,
                "description": "Focus on consistency and building healthy habits",
                "min_weeks": 4,
                "max_weeks": 52
            }
        }
        
        if goal in timelines:
            timeline_info = timelines[goal]
            if timeline_info["rate"] and target_weight:
                weight_diff = abs(target_weight - current_weight)
                weeks_needed = max(weight_diff / timeline_info["rate"], timeline_info["min_weeks"])
                weeks_needed = min(weeks_needed, timeline_info["max_weeks"])
                
                return {
                    "weeks": int(weeks_needed),
                    "description": timeline_info["description"],
                    "realistic": weeks_needed <= timeline_info["max_weeks"],
                    "rate_per_week": timeline_info["rate"]
                }
            else:
                return {
                    "weeks": timeline_info["min_weeks"],
                    "description": timeline_info["description"],
                    "realistic": True,
                    "rate_per_week": timeline_info["rate"]
                }
        
        return {
            "weeks": 12,
            "description": "Results typically visible in 8-12 weeks with consistency",
            "realistic": True,
            "rate_per_week": None
        }
    
    def get_daily_tip(self, goal: str) -> str:
        """Get a daily tip based on user's goal"""
        tips = self.health_tips.get(goal, self.health_tips["General Fitness"])
        import random
        return random.choice(tips)
    
    def get_motivation(self) -> str:
        """Get a motivational message"""
        import random
        return random.choice(self.motivational_messages)
    
    def analyze_activity_patterns(self, activity_log: List[Dict]) -> Dict:
        """Analyze user's activity patterns and provide insights"""
        if not activity_log:
            return {
                "message": "Start logging activities to get personalized insights!",
                "suggestions": ["Log your first workout!", "Track your meals!", "Record your weight!"]
            }
        
        # Categorize activities
        workouts = [a for a in activity_log if a.get('type') == 'workout']
        meals = [a for a in activity_log if a.get('type') == 'meal']
        weights = [a for a in activity_log if a.get('type') == 'weight']
        mood_logs = [a for a in activity_log if a.get('type') == 'mood']
        
        insights = []
        suggestions = []
        
        # Workout analysis
        if len(workouts) >= 3:
            avg_duration = sum(w.get('duration', 0) for w in workouts) / len(workouts)
            insights.append(f"You're doing great with {len(workouts)} workouts logged! Average duration: {avg_duration:.0f} minutes.")
            if avg_duration < 30:
                suggestions.append("Try gradually increasing workout duration to 30-45 minutes for better results.")
        elif len(workouts) > 0:
            insights.append("Good start with your workouts! Consistency is key.")
            suggestions.append("Aim for 3-4 workouts per week for optimal results.")
        else:
            suggestions.append("Start with 2-3 workouts per week - even 20 minutes counts!")
        
        # Weight tracking analysis
        if len(weights) >= 2:
            weight_trend = weights[-1].get('weight', 0) - weights[0].get('weight', 0)
            if abs(weight_trend) < 0.5:
                insights.append("Your weight is stable - great for maintenance goals!")
            elif weight_trend > 0:
                insights.append(f"Weight trend: +{weight_trend:.1f}kg - perfect if that's your goal!")
            else:
                insights.append(f"Weight trend: {weight_trend:.1f}kg - excellent progress!")
        
        # Mood/energy analysis
        if mood_logs:
            avg_energy = sum(m.get('energyLevel', 5) for m in mood_logs) / len(mood_logs)
            if avg_energy >= 7:
                insights.append(f"Your energy levels are great! Average: {avg_energy:.1f}/10")
            elif avg_energy < 5:
                insights.append(f"Your energy seems low (avg: {avg_energy:.1f}/10). Consider improving sleep and nutrition.")
                suggestions.append("Focus on getting 7-9 hours of sleep and eating balanced meals.")
        
        return {
            "total_activities": len(activity_log),
            "workout_count": len(workouts),
            "meal_count": len(meals),
            "weight_entries": len(weights),
            "insights": insights,
            "suggestions": suggestions,
            "message": " ".join(insights[:2]) if insights else "Keep tracking your progress!"
        }

# Initialize the AI assistant
bodybae = BodyBaeAI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/onboard', methods=['POST'])
def onboard_user():
    """Handle user onboarding with enhanced BMI calculation"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        # Store user data
        users_db[user_id] = {
            'name': data['name'],
            'age': int(data['age']),
            'height': float(data['height']),  # in cm
            'weight': float(data['weight']),  # in kg
            'sex': data['sex'],
            'activity_level': data['activity_level'],
            'created_at': datetime.now().isoformat()
        }
        
        # Calculate BMR, TDEE, and BMI
        user = users_db[user_id]
        bmr = bodybae.calculate_bmr(user['weight'], user['height'], user['age'], user['sex'])
        tdee = bodybae.calculate_tdee(bmr, user['activity_level'])
        bmi_info = bodybae.calculate_bmi(user['weight'], user['height'])
        
        user.update({
            'bmr': bmr,
            'tdee': tdee,
            'bmi': bmi_info['bmi'],
            'bmi_category': bmi_info['category'],
            'bmi_advice': bmi_info['advice']
        })
        
        # Store user_id in session
        session['user_id'] = user_id
        
        # Initialize chat history
        chat_history_db[user_id] = []
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'bmr': bmr,
            'tdee': tdee,
            'bmi_info': bmi_info,
            'message': f"Welcome {data['name']}! Your profile has been created successfully.",
            'personalized_tip': bodybae.get_daily_tip("General Fitness")
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/set_goal', methods=['POST'])
def set_goal():
    """Set user's fitness goal with enhanced timeline calculation"""
    data = request.json
    user_id = session.get('user_id')
    
    if not user_id or user_id not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        goal = data['goal']
        target_weight = data.get('target_weight')
        user_deadline = data.get('deadline_weeks', 12)
        
        current_weight = users_db[user_id]['weight']
        timeline = bodybae.get_realistic_timeline(goal, current_weight, target_weight)
        
        # Store goal with enhanced information
        goals_db[user_id] = {
            'goal': goal,
            'target_weight': target_weight,
            'current_weight': current_weight,
            'user_deadline': user_deadline,
            'realistic_timeline': timeline,
            'created_at': datetime.now().isoformat(),
            'milestones': [],
            'target_date': (datetime.now() + timedelta(weeks=timeline['weeks'])).isoformat()
        }
        
        # Create weekly milestones
        milestone_weeks = list(range(2, timeline['weeks'], 2))  # Every 2 weeks
        for week in milestone_weeks:
            if week <= timeline['weeks']:
                goals_db[user_id]['milestones'].append({
                    'week': week,
                    'target_date': (datetime.now() + timedelta(weeks=week)).isoformat(),
                    'completed': False,
                    'description': f"Week {week} checkpoint"
                })
        
        # Get personalized tips for the goal
        daily_tip = bodybae.get_daily_tip(goal)
        motivation = bodybae.get_motivation()
        
        return jsonify({
            'success': True,
            'goal': goal,
            'timeline': timeline,
            'daily_tip': daily_tip,
            'motivation': motivation,
            'message': f"Perfect! Your goal to {goal} has been set. {timeline['description']}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/log_progress', methods=['POST'])
def log_progress():
    """Enhanced progress logging with activity analysis"""
    data = request.json
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Initialize progress tracking for user
        if user_id not in progress_db:
            progress_db[user_id] = []
        
        # Create progress entry based on activity type
        progress_entry = {
            'type': data.get('type', 'general'),
            'date': datetime.now().isoformat(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Add type-specific data
        if data.get('type') == 'workout':
            progress_entry.update({
                'workoutType': data.get('workoutType'),
                'duration': int(data.get('duration', 0)),
                'calories': data.get('calories')
            })
        elif data.get('type') == 'meal':
            progress_entry.update({
                'mealType': data.get('mealType'),
                'calories': data.get('calories'),
                'description': data.get('description')
            })
        elif data.get('type') == 'weight':
            progress_entry.update({
                'weight': float(data.get('weight'))
            })
            # Update user's current weight
            if user_id in users_db:
                users_db[user_id]['weight'] = float(data.get('weight'))
                # Recalculate BMI
                bmi_info = bodybae.calculate_bmi(
                    users_db[user_id]['weight'],
                    users_db[user_id]['height']
                )
                users_db[user_id].update({
                    'bmi': bmi_info['bmi'],
                    'bmi_category': bmi_info['category']
                })
        elif data.get('type') == 'mood':
            progress_entry.update({
                'energyLevel': int(data.get('energyLevel', 5)),
                'notes': data.get('notes', '')
            })
        elif data.get('type') == 'water':
            progress_entry.update({
                'glasses': int(data.get('glasses', 0))
            })
        else:
            # General progress entry
            progress_entry.update({
                'weight': data.get('weight'),
                'workout_completed': data.get('workout_completed', False),
                'calories_consumed': data.get('calories_consumed'),
                'notes': data.get('notes', ''),
                'energy_level': data.get('energy_level', 5)
            })
        
        progress_db[user_id].append(progress_entry)
        
        # Analyze activity patterns
        analysis = bodybae.analyze_activity_patterns(progress_db[user_id])
        
        return jsonify({
            'success': True,
            'message': 'Progress logged successfully!',
            'total_entries': len(progress_db[user_id]),
            'analysis': analysis,
            'motivation': bodybae.get_motivation()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/get_progress')
def get_progress():
    """Get user's progress history with enhanced analytics"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        progress = progress_db.get(user_id, [])
        goal = goals_db.get(user_id, {})
        user_info = users_db.get(user_id, {})
        
        # Enhanced analytics
        analysis = bodybae.analyze_activity_patterns(progress)
        
        # Calculate streak
        recent_days = 7
        today = datetime.now()
        active_days = set()
        
        for entry in progress:
            entry_date = datetime.fromisoformat(entry['date']).date()
            if (today.date() - entry_date).days <= recent_days:
                active_days.add(entry_date)
        
        streak = len(active_days)
        
        return jsonify({
            'progress': progress,
            'goal': goal,
            'user_info': user_info,
            'total_entries': len(progress),
            'analysis': analysis,
            'streak_days': streak,
            'recent_activity': progress[-10:] if progress else []  # Last 10 activities
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/daily_tip')
def daily_tip():
    """Get daily tip and motivation with user context"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        goal = goals_db.get(user_id, {}).get('goal', 'General Fitness')
        user_info = users_db.get(user_id, {})
        
        tip = bodybae.get_daily_tip(goal)
        motivation = bodybae.get_motivation()
        
        # Get progress insights
        progress = progress_db.get(user_id, [])
        analysis = bodybae.analyze_activity_patterns(progress)
        
        return jsonify({
            'tip': tip,
            'motivation': motivation,
            'goal': goal,
            'progress_insight': analysis.get('message', ''),
            'suggestions': analysis.get('suggestions', [])[:2],  # Top 2 suggestions
            'bmi_category': user_info.get('bmi_category', 'Unknown')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat with RAG system integration"""
    data = request.json
    message = data.get('message', '')
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get user context
        user_profile = users_db.get(user_id, {}) if user_id else {}
        activity_log = progress_db.get(user_id, [])[-10:] if user_id else []  # Last 10 activities
        
        # Use enhanced RAG system if available
        if rag_system:
            try:
                response = rag_system.generate_health_response(
                    question=message,
                    user_profile=user_profile
                )
                
                # Get additional insights
                tips = rag_system.get_personalized_tips(user_profile) if user_profile else []
                progress_analysis = rag_system.analyze_progress(activity_log) if activity_log else {}
                
                # Store in chat history
                if user_id:
                    if user_id not in chat_history_db:
                        chat_history_db[user_id] = []
                    chat_history_db[user_id].extend([
                        {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                        {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
                    ])
                
                return jsonify({
                    'response': response,
                    'personalized_tips': tips[:2] if tips else [],
                    'progress_insight': progress_analysis.get('message', ''),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'enhanced_rag'
                })
                
            except Exception as rag_error:
                print(f"RAG system error: {rag_error}")
                # Fall through to simple responses
        
        # Fallback to simple rule-based responses
        response = get_simple_response(message, user_profile, activity_log)
        
        # Store in chat history
        if user_id:
            if user_id not in chat_history_db:
                chat_history_db[user_id] = []
            chat_history_db[user_id].extend([
                {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
            ])
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback'
        })
        
    except Exception as e:
        return jsonify({'error': 'Error processing chat message', 'details': str(e)}), 500

def get_simple_response(message: str, user_profile: Dict, activity_log: List[Dict]) -> str:
    """Fallback response system when RAG is not available"""
    message_lower = message.lower()
    name = user_profile.get('name', 'there') if user_profile else 'there'
    
    # Enhanced rule-based responses with user context
    if any(word in message_lower for word in ['weight loss', 'lose weight', 'losing weight']):
        bmi = user_profile.get('bmi', 0) if user_profile else 0
        if bmi > 25:
            return f"Hi {name}! For healthy weight loss, focus on creating a moderate caloric deficit of 500-750 calories daily. Your BMI suggests weight loss could be beneficial. Combine cardio with strength training, eat plenty of protein, and stay hydrated. Aim for 0.5-1 kg per week. You've got this! 💪"
        else:
            return f"Hi {name}! While your BMI is in a healthy range, if you want to lose weight, focus on body composition. Create a small deficit, prioritize protein, and include strength training to maintain muscle while losing fat. Remember, the scale doesn't tell the whole story! 📊"
    
    elif any(word in message_lower for word in ['muscle', 'gain muscle', 'build muscle']):
        age = user_profile.get('age', 25) if user_profile else 25
        activity_level = user_profile.get('activity_level', '') if user_profile else ''
        
        response = f"Great question, {name}! To build muscle, focus on progressive overload in your workouts and eat 1.6-2.2g protein per kg body weight daily. "
        
        if age > 40:
            response += "At your age, recovery becomes even more important - prioritize sleep and consider longer rest periods between sessions. "
        
        if 'sedentary' in activity_level:
            response += "Since you're starting from a more sedentary lifestyle, begin with 2-3 strength sessions per week. "
        
        response += "Compound exercises like squats and deadlifts are your best friends! Get 7-9 hours of sleep for recovery. 🏋️‍♀️"
        return response
    
    elif any(word in message_lower for word in ['calories', 'eat', 'nutrition', 'food']):
        if user_profile and 'tdee' in user_profile:
            tdee = user_profile['tdee']
            goal = goals_db.get(session.get('user_id', ''), {}).get('goal', 'General Fitness')
            
            if goal == 'Lose Weight':
                target_calories = int(tdee - 500)
                return f"Based on your profile, {name}, your maintenance calories are around {int(tdee)}. For weight loss, aim for about {target_calories} calories daily. Focus on whole foods: lean proteins, vegetables, fruits, and whole grains! 🥗"
            elif goal == 'Gain Muscle':
                target_calories = int(tdee + 300)
                return f"For muscle gain, {name}, aim for about {target_calories} calories daily (your maintenance is around {int(tdee)}). Include plenty of protein and complex carbs to fuel your workouts! 💪"
            else:
                return f"Your daily calorie needs are around {int(tdee)} calories, {name}. Focus on balanced meals with protein, healthy carbs, and good fats. Stay hydrated and eat mindfully! 💧"
        else:
            return f"Hi {name}! For nutrition guidance, focus on whole foods: lean proteins, vegetables, fruits, whole grains, and healthy fats. Eat balanced meals, stay hydrated, and listen to your hunger cues. The key is consistency! 🌟"
    
    elif any(word in message_lower for word in ['workout', 'exercise', 'training']):
        activity_level = user_profile.get('activity_level', '') if user_profile else ''
        
        if 'sedentary' in activity_level:
            return f"Perfect timing to start, {name}! Begin with 20-30 minutes of walking daily, then add 2-3 strength training sessions per week. Start small and build consistency - that's the key to long-term success! 🚶‍♀️"
        elif 'very_active' in activity_level:
            return f"You're already very active, {name}! Make sure you're including both cardio and strength training. Don't forget rest days - recovery is when your body actually gets stronger! 💪"
        else:
            return f"Hi {name}! Aim for 150 minutes of moderate cardio per week plus 2-3 strength training sessions. Mix it up to keep things interesting - your body loves variety! 🏃‍♀️"
    
    elif any(word in message_lower for word in ['motivation', 'motivated', 'give up', 'tired', 'struggling']):
        # Check activity log for context
        recent_workouts = [log for log in activity_log if log.get('type') == 'workout'] if activity_log else []
        
        if len(recent_workouts) >= 2:
            return f"I can see you've been putting in the work, {name}! 🌟 You've logged {len(recent_workouts)} workouts recently - that's amazing! Remember why you started this journey. Every small step counts, and you're already proving you can do this. Keep going! 🔥"
        else:
            return f"I believe in you, {name}! 🌟 It's totally normal to feel this way sometimes. Remember, progress isn't always linear, and setbacks are just setups for comebacks. Start with just 10 minutes today - sometimes that's all it takes to get back on track. You're stronger than you think! 💪"
    
    elif any(word in message_lower for word in ['bmi', 'healthy', 'health']):
        if user_profile and 'bmi' in user_profile:
            bmi = user_profile['bmi']
            category = user_profile.get('bmi_category', 'Unknown')
            return f"Your current BMI is {bmi}, which is in the '{category}' category, {name}. Remember, BMI is just one indicator of health. Focus on how you feel, your energy levels, and building healthy habits. Overall wellness includes physical fitness, mental health, good nutrition, and adequate sleep! 🌈"
        else:
            return f"Health is about so much more than just weight, {name}! Focus on building sustainable habits: regular movement, balanced nutrition, quality sleep, stress management, and staying hydrated. Small consistent changes lead to big transformations! ✨"
    
    elif any(word in message_lower for word in ['sleep', 'tired', 'energy', 'rest']):
        mood_logs = [log for log in activity_log if log.get('type') == 'mood'] if activity_log else []
        if mood_logs:
            avg_energy = sum(log.get('energyLevel', 5) for log in mood_logs) / len(mood_logs)
            if avg_energy < 6:
                return f"I notice your energy levels have been lower recently, {name}. Prioritize 7-9 hours of quality sleep, stay hydrated, and make sure you're eating balanced meals. Consider reducing screen time before bed and creating a relaxing bedtime routine. Your body needs rest to perform its best! 😴"
        
        return f"Sleep is so important for your health goals, {name}! Aim for 7-9 hours of quality sleep. It's when your body recovers, builds muscle, and regulates hormones. Create a consistent bedtime routine, keep your room cool and dark, and avoid screens before bed. Good sleep = better workouts and healthier choices! 🌙"
    
    elif any(word in message_lower for word in ['progress', 'results', 'how long', 'when will']):
        goal = goals_db.get(session.get('user_id', ''), {}).get('goal', 'Unknown')
        if goal != 'Unknown':
            return f"Great question, {name}! For your goal of '{goal}', you can typically expect to see initial changes in 2-4 weeks and more significant results in 6-12 weeks with consistency. Remember, progress isn't always visible on the scale - take photos, measurements, and note how you feel. Trust the process! 📈"
        else:
            return f"Results vary for everyone, {name}, but generally you can expect to feel better in 1-2 weeks and see visible changes in 4-8 weeks with consistent effort. The key is staying consistent with your nutrition and exercise. Progress takes time, but every day you're getting stronger! 💪"
    
    elif 'hello' in message_lower or 'hi' in message_lower:
        time_of_day = datetime.now().hour
        if time_of_day < 12:
            greeting = "Good morning"
        elif time_of_day < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        
        return f"{greeting}, {name}! 😊 I'm here to help you on your health and fitness journey. I can assist with workout advice, nutrition guidance, progress tracking, and motivation. What would you like to chat about today?"
    
    else:
        # Generic helpful response
        return f"Hi {name}! I'm here to help with your health and fitness journey. I can assist with:\n\n• Workout recommendations and form tips\n• Nutrition advice and meal planning\n• Progress tracking and goal setting\n• Motivation and mindset support\n• Sleep and recovery guidance\n\nWhat specific aspect of your health would you like to focus on today? 😊"

@app.route('/get_chat_history')
def get_chat_history():
    """Get user's chat history"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    history = chat_history_db.get(user_id, [])
    return jsonify({'chat_history': history})

@app.route('/faq')
def faq():
    """Get comprehensive FAQ responses"""
    faqs = {
        "How much water should I drink daily?": "Aim for 35-40ml per kg of body weight daily. If you weigh 70kg, that's about 2.5-2.8 liters. Drink more during exercise and hot weather!",
        
        "How many meals should I eat per day?": "3 main meals with 1-2 healthy snacks work well for most people. The key is eating when you're hungry and stopping when satisfied. Meal timing matters less than total daily nutrition.",
        
        "How long should I wait between workouts?": "Allow 24-48 hours rest between training the same muscle groups. You can do different muscle groups on consecutive days, but listen to your body and take complete rest days when needed.",
        
        "What's the best time to exercise?": "The best time is when you can be consistent! Some people have more energy in the morning, others prefer evening. Choose what fits your schedule and energy levels best.",
        
        "Should I eat before or after workouts?": "Light snack with carbs 30-60 minutes before (like a banana), and a balanced meal with protein and carbs within 2 hours after exercise for optimal recovery.",
        
        "How do I know if I'm making progress?": "Track multiple metrics: how you feel, energy levels, strength gains, body measurements, photos, and sleep quality. The scale is just one tool - your body composition matters more!",
        
        "What if I miss a workout?": "It's okay! Life happens. Don't let one missed workout derail your progress. Just get back to your routine the next day. Consistency over time matters more than perfection.",
        
        "How much protein do I really need?": "For general health: 0.8g per kg body weight. For muscle building: 1.6-2.2g per kg. For weight loss: higher protein (1.2-1.6g per kg) helps preserve muscle mass.",
        
        "Is it normal to feel sore after workouts?": "Mild muscle soreness 24-48 hours after exercise is normal, especially when starting or increasing intensity. Sharp pain or severe soreness isn't normal - listen to your body!",
        
        "How do I stay motivated long-term?": "Set small, achievable goals, track your progress, find activities you enjoy, celebrate wins, and remember your 'why'. Consider finding a workout buddy or community for support!"
    }
    
    return jsonify({'faqs': faqs})

@app.route('/health_check')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'services': {
                'database': 'ok',
                'rag_system': 'ok' if rag_system else 'fallback',
                'user_sessions': len(users_db)
            },
            'features': {
                'enhanced_rag': rag_system is not None,
                'chat_memory': True,
                'progress_analytics': True,
                'personalized_tips': True
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/user_stats')
def user_stats():
    """Get user statistics dashboard"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        user_info = users_db.get(user_id, {})
        progress = progress_db.get(user_id, [])
        goal_info = goals_db.get(user_id, {})
        
        # Calculate detailed stats
        workouts = [p for p in progress if p.get('type') == 'workout']
        meals = [p for p in progress if p.get('type') == 'meal']
        weights = [p for p in progress if p.get('type') == 'weight']
        
        # Workout stats
        total_workout_time = sum(w.get('duration', 0) for w in workouts)
        avg_workout_duration = total_workout_time / len(workouts) if workouts else 0
        
        # Weight progress
        weight_change = 0
        if len(weights) >= 2:
            weight_change = weights[-1].get('weight', 0) - weights[0].get('weight', 0)
        
        # Calculate days since start
        if user_info.get('created_at'):
            start_date = datetime.fromisoformat(user_info['created_at'])
            days_since_start = (datetime.now() - start_date).days
        else:
            days_since_start = 0
        
        stats = {
            'user_info': {
                'name': user_info.get('name', 'User'),
                'days_since_start': days_since_start,
                'current_bmi': user_info.get('bmi', 0),
                'bmi_category': user_info.get('bmi_category', 'Unknown')
            },
            'activity_stats': {
                'total_workouts': len(workouts),
                'total_workout_minutes': total_workout_time,
                'avg_workout_duration': round(avg_workout_duration, 1),
                'meals_logged': len(meals),
                'weight_entries': len(weights),
                'weight_change': round(weight_change, 1)
            },
            'goal_info': {
                'current_goal': goal_info.get('goal', 'Not set'),
                'target_weight': goal_info.get('target_weight'),
                'weeks_remaining': max(0, goal_info.get('realistic_timeline', {}).get('weeks', 0) - 
                                   ((datetime.now() - datetime.fromisoformat(goal_info.get('created_at', datetime.now().isoformat()))).days // 7)
                                   if goal_info.get('created_at') else 0)
            },
            'recent_activity': progress[-5:] if progress else []
        }
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting BodyBae.ai...")
    print(f"📊 RAG System: {'✅ Enhanced' if rag_system else '⚠️ Fallback'}")
    print(f"🌐 Running on port: {port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
