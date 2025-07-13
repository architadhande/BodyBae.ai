from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
import random
from typing import Dict, List, Optional
import re

app = Flask(__name__, static_folder='static')
CORS(app)

# In-memory storage (for demo - use database in production)
users = {}
chat_sessions = {}

# BMI categories and advice
def calculate_bmi(weight: float, height: float) -> tuple:
    """Calculate BMI and return value, category, and advice"""
    bmi = weight / ((height / 100) ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
        advice = "Focus on nutrient-dense foods and strength training"
    elif 18.5 <= bmi < 25:
        category = "Normal weight"
        advice = "Maintain your healthy lifestyle with balanced nutrition"
    elif 25 <= bmi < 30:
        category = "Overweight"
        advice = "Consider portion control and increasing physical activity"
    else:
        category = "Obese"
        advice = "Consult a healthcare provider for personalized guidance"
    
    return round(bmi, 1), category, advice

# Simple FAQ knowledge base extracted from the PDF
FAQ_KNOWLEDGE = {
    "protein": {
        "keywords": ["protein", "whey", "muscle", "supplement"],
        "responses": [
            "Based on research, you need approximately 1.6g of protein per kilogram of bodyweight per day for muscle gain. Protein is essential for rebuilding muscle and recovery.",
            "Great protein sources include meat, fish, eggs, legumes, nuts, and whey protein supplements. For muscle growth, combine adequate protein with consistent strength training.",
            "Whey protein is a convenient way to meet your protein needs. You can use it in shakes, pancakes, protein balls, or overnight oats for variety."
        ]
    },
    "calories": {
        "keywords": ["calories", "tdee", "bmr", "energy", "calorie"],
        "responses": [
            "Your Total Daily Energy Expenditure (TDEE) depends on your BMR and activity level. To lose fat, subtract 500kcal from your TDEE. To gain muscle, add 500kcal.",
            "Calculate your BMR using: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5 for men, or - 161 for women.",
            "Track your calories accurately for best results. Small inaccuracies can add up and affect your progress."
        ]
    },
    "workout": {
        "keywords": ["workout", "exercise", "hiit", "training", "gym"],
        "responses": [
            "HIIT workouts are excellent for burning calories and improving fitness. Try circuits of burpees, jump squats, press-ups, and planks with 60-second rest between circuits.",
            "For home workouts, focus on compound movements like squats, lunges, push-ups, and planks. Do 5 circuits of 15 reps each exercise.",
            "Mix up your workouts to avoid plateaus. Combine strength training with cardio, and vary intensity and exercises weekly."
        ]
    },
    "diet": {
        "keywords": ["diet", "nutrition", "food", "meal", "eat"],
        "responses": [
            "A balanced diet should include 35% fats (focus on healthy fats like avocados and nuts), adequate protein (1.6g/kg body weight), and the rest from carbohydrates.",
            "Meal prep is key to success. Plan your meals ahead, include plenty of vegetables, and allow yourself occasional treats to stay on track.",
            "Stay hydrated, eat plenty of fiber to feel fuller longer, and avoid excessive alcohol which adds empty calories."
        ]
    },
    "supplements": {
        "keywords": ["supplement", "vitamin", "pre-workout", "bcaa"],
        "responses": [
            "Key supplements include: protein powder for muscle growth, omega-3 for heart health, and a good multivitamin for overall health.",
            "Pre-workout supplements with caffeine can boost performance. For recovery, consider whey protein or plant-based alternatives.",
            "Supplements aren't magic - they work best alongside a balanced diet and consistent training routine."
        ]
    },
    "weight_loss": {
        "keywords": ["weight loss", "lose weight", "fat loss", "cutting"],
        "responses": [
            "For healthy weight loss, aim for a 500-calorie deficit daily. This leads to about 0.5kg loss per week - sustainable and healthy.",
            "Combine calorie deficit with strength training to preserve muscle mass while losing fat. Don't rush the process.",
            "Track progress through measurements and photos, not just the scale. Weight can fluctuate daily due to water retention."
        ]
    },
    "muscle_gain": {
        "keywords": ["muscle", "gain", "bulk", "strength"],
        "responses": [
            "To gain muscle, eat in a 500-calorie surplus with adequate protein (1.6g/kg body weight) and progressive strength training.",
            "Focus on compound exercises like squats, deadlifts, and presses. Progressive overload is key - gradually increase weight or reps.",
            "Recovery is crucial for muscle growth. Aim for 7-9 hours of sleep and rest days between training the same muscle groups."
        ]
    }
}

# Daily tips database
DAILY_TIPS = [
    "💧 Drink at least 8 glasses of water today to stay hydrated and support your metabolism.",
    "🥗 Add a serving of vegetables to every meal for extra nutrients and fiber.",
    "🚶 Take a 10-minute walk after meals to aid digestion and boost energy.",
    "😴 Aim for 7-9 hours of quality sleep tonight for better recovery and hormone balance.",
    "🧘 Start your day with 5 minutes of stretching to improve flexibility and reduce injury risk.",
    "🍎 Choose whole fruits over fruit juices to get more fiber and avoid sugar spikes.",
    "💪 Focus on form over weight - proper technique prevents injuries and maximizes results.",
    "📝 Keep a food journal this week to identify eating patterns and areas for improvement.",
    "🥜 Snack on a handful of nuts for healthy fats and sustained energy.",
    "🎯 Set small, achievable goals this week to build momentum toward your bigger objectives."
]

def find_best_response(message: str) -> str:
    """Find the most relevant response based on keywords"""
    message_lower = message.lower()
    best_match = None
    max_matches = 0
    
    for topic, data in FAQ_KNOWLEDGE.items():
        matches = sum(1 for keyword in data["keywords"] if keyword in message_lower)
        if matches > max_matches:
            max_matches = matches
            best_match = topic
    
    if best_match:
        return random.choice(FAQ_KNOWLEDGE[best_match]["responses"])
    
    # Default responses for common queries
    if any(word in message_lower for word in ["hello", "hi", "hey", "start"]):
        return "Hello! I'm BodyBae, your AI fitness companion. I can help you with nutrition advice, workout tips, and answer your fitness questions. What would you like to know about?"
    
    if any(word in message_lower for word in ["thank", "thanks", "bye", "goodbye"]):
        return "You're welcome! Keep up the great work on your fitness journey. Remember, consistency is key! 💪"
    
    return "I can help you with nutrition, workouts, supplements, and fitness goals. Try asking about protein requirements, calorie calculations, HIIT workouts, or healthy meal planning. What specific topic interests you?"

@app.route('/')
def serve_frontend():
    """Serve the frontend HTML"""
    return send_from_directory('.', 'bodybae_frontend.html')

@app.route('/api/onboard', methods=['POST'])
def onboard():
    """Handle user onboarding"""
    data = request.json
    
    # Calculate BMI
    bmi, category, advice = calculate_bmi(data['weight'], data['height'])
    
    # Calculate BMR and TDEE
    weight = data['weight']
    height = data['height']
    age = data['age']
    sex = data['sex']
    activity = data['activity_level']
    
    # Calculate BMR
    if sex == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # Calculate TDEE based on activity level
    activity_multipliers = {
        'sedentary': 1.4,
        'light': 1.6,
        'moderate': 1.8,
        'active': 2.0
    }
    tdee = int(bmr * activity_multipliers.get(activity, 1.6))
    
    # Store user data
    user_id = f"user_{len(users) + 1}"
    users[user_id] = {
        **data,
        'bmi': bmi,
        'bmi_category': category,
        'bmr': int(bmr),
        'tdee': tdee,
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'user_id': user_id,
        'bmi': bmi,
        'bmi_category': category,
        'bmi_advice': advice,
        'bmr': int(bmr),
        'tdee': tdee,
        'message': f"Great to meet you, {data['name']}! Your BMI is {bmi} ({category}). {advice} Your estimated daily calorie needs are {tdee} calories."
    })

@app.route('/api/set_goal', methods=['POST'])
def set_goal():
    """Set user fitness goal"""
    data = request.json
    goal = data['goal']
    target_weeks = data['target_weeks']
    
    # Provide realistic feedback based on goal
    goal_advice = {
        'Lose Weight': f"For healthy weight loss, aim for 0.5-1kg per week. In {target_weeks} weeks, you could realistically lose {target_weeks * 0.5}-{target_weeks * 1}kg.",
        'Gain Weight': f"For healthy weight gain, aim for 0.25-0.5kg per week. In {target_weeks} weeks, you could gain {target_weeks * 0.25}-{target_weeks * 0.5}kg.",
        'Gain Muscle': f"Muscle gain is gradual. With consistent training and nutrition, expect 0.25-0.5kg of muscle per month. Stay patient and consistent!",
        'Lose Fat': f"Fat loss requires a calorie deficit. Combine cardio with strength training for best results. Track measurements, not just weight.",
        'Maintain Weight': f"Focus on consistent habits and balanced nutrition. Your maintenance calories are key to stability.",
        'Toning': f"Toning means building lean muscle while reducing fat. Combine strength training with moderate cardio for best results.",
        'Bulking': f"For bulking, eat in a 300-500 calorie surplus with plenty of protein. Focus on progressive overload in your training."
    }
    
    message = goal_advice.get(goal, "Great goal! Stay consistent with your nutrition and training for best results.")
    
    return jsonify({
        'goal': goal,
        'target_weeks': target_weeks,
        'message': message
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    user_message = data['message']
    user_profile = data.get('user_profile', {})
    
    # Get relevant response
    response = find_best_response(user_message)
    
    # Personalize if user profile available
    if user_profile and 'name' in user_profile:
        response = response.replace("you", f"you, {user_profile['name']},")
    
    return jsonify({
        'response': response,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/daily_tip', methods=['GET'])
def daily_tip():
    """Get daily fitness tip"""
    # In production, this would check the date and serve one tip per day
    tip = random.choice(DAILY_TIPS)
    return jsonify({
        'tip': tip,
        'date': datetime.now().strftime('%Y-%m-%d')
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Use PORT environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)