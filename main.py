from flask import Flask, request, jsonify, render_template
from rag_system.rag_processor import RAGProcessor
import json
import os
from datetime import datetime

app = Flask(__name__)
app.static_folder = 'static'

# Initialize RAG system
rag_processor = RAGProcessor()

# In-memory database (replace with real DB in production)
users_db = {}
goals_db = {}
progress_db = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get('user_id', 'default')
    message = data.get('message', '')
    
    # Check if this is initial onboarding
    if not users_db.get(user_id):
        return handle_onboarding(user_id, message)
    
    # Process regular messages
    response = process_message(user_id, message)
    return jsonify(response)

def handle_onboarding(user_id, message):
    if not users_db.get(user_id):
        users_db[user_id] = {'step': 'name', 'data': {}}
        return jsonify({
            'response': "Welcome to BodyBae.ai! What's your name?",
            'user_id': user_id
        })
    
    user_data = users_db[user_id]
    current_step = user_data['step']
    
    # Multi-step onboarding flow
    if current_step == 'name':
        user_data['data']['name'] = message
        user_data['step'] = 'age'
        return jsonify({'response': f"Nice to meet you, {message}! How old are you?"})
    
    elif current_step == 'age':
        user_data['data']['age'] = int(message)
        user_data['step'] = 'height'
        return jsonify({'response': "Got it. What's your height in cm?"})
    
    elif current_step == 'height':
        user_data['data']['height'] = float(message)
        user_data['step'] = 'weight'
        return jsonify({'response': "What's your current weight in kg?"})
    
    elif current_step == 'weight':
        user_data['data']['weight'] = float(message)
        user_data['step'] = 'sex'
        return jsonify({
            'response': "What's your biological sex? (male/female/other)",
            'options': ["male", "female", "other"]
        })
    
    elif current_step == 'sex':
        user_data['data']['sex'] = message.lower()
        user_data['step'] = 'activity'
        return jsonify({
            'response': "How would you describe your activity level?",
            'options': ["sedentary", "lightly active", "moderately active", "very active"]
        })
    
    elif current_step == 'activity':
        user_data['data']['activity'] = message.lower()
        user_data['step'] = 'complete'
        users_db[user_id] = user_data
        
        # Calculate BMI
        height_m = user_data['data']['height'] / 100
        bmi = user_data['data']['weight'] / (height_m ** 2)
        user_data['data']['bmi'] = round(bmi, 1)
        
        return jsonify({
            'response': "Onboarding complete! What fitness goal would you like to work on?",
            'options': ["Lose Weight", "Gain Weight", "Gain Muscle", "Lose Fat", "Toning", "Maintain Weight"],
            'user_data': user_data['data'],
            'onboarding_complete': True
        })

def process_message(user_id, message):
    # Check for goal setting
    if message.lower() in ["lose weight", "gain weight", "gain muscle", "lose fat", "toning", "maintain weight"]:
        goals_db[user_id] = {
            'goal': message,
            'start_date': datetime.now().strftime("%Y-%m-%d"),
            'target_date': None,
            'progress': []
        }
        return {
            'response': f"Great goal! When would you like to achieve this? (e.g., '3 months')",
            'goal_set': True
        }
    
    # Handle goal deadline setting
    if goals_db.get(user_id) and not goals_db[user_id].get('target_date'):
        try:
            # Simple parsing of time duration
            if 'month' in message:
                months = int(message.split()[0])
                goals_db[user_id]['target_date'] = months
                return {
                    'response': generate_goal_plan(user_id, months),
                    'goal_plan': True
                }
        except:
            return {'response': "Please specify a valid timeframe (e.g., '3 months')"}
    
    # Handle progress logging
    if message.lower().startswith("log weight"):
        try:
            weight = float(message.split()[2])
            if user_id not in progress_db:
                progress_db[user_id] = []
            progress_db[user_id].append({
                'date': datetime.now().strftime("%Y-%m-%d"),
                'weight': weight
            })
            return {'response': f"Logged weight: {weight} kg"}
        except:
            return {'response': "Please use format: 'log weight 70.5'"}
    
    # Use RAG for health questions
    if is_health_question(message):
        response = rag_processor.process_query(message)
        return {'response': response}
    
    # Default response
    return {
        'response': "I'm here to help with your fitness goals! You can ask me health questions, set goals, or log progress."
    }

def is_health_question(message):
    health_keywords = ['exercise', 'diet', 'nutrition', 'workout', 'weight', 'muscle', 'fat', 'calories']
    return any(keyword in message.lower() for keyword in health_keywords)

def generate_goal_plan(user_id, months):
    user_data = users_db[user_id]['data']
    goal = goals_db[user_id]['goal']
    
    if goal == "Lose Weight":
        healthy_loss = 0.5 * 4 * months  # 0.5kg/week
        return (f"Based on your goal to {goal.lower()}, a healthy target would be about {healthy_loss:.1f} kg "
                f"in {months} months. Focus on a slight calorie deficit and regular exercise!")
    
    elif goal == "Gain Weight":
        healthy_gain = 0.5 * 4 * months  # 0.5kg/week
        return (f"For healthy weight gain, aim for about {healthy_gain:.1f} kg in {months} months. "
                "Increase calorie intake with nutritious foods and strength training!")
    
    return f"Great! I'll help you {goal.lower()} over the next {months} months. You've got this!"

if __name__ == '__main__':
    app.run(debug=True)