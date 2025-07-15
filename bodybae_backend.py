from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import json
import os
from datetime import datetime
import random
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# In-memory storage (for demo - use database in production)
users = {}
chat_sessions = {}

def calculate_goal_calories(tdee: int, goal: str) -> tuple:
    """Calculate daily calorie needs based on goal"""
    if goal in ['Lose Weight', 'Lose Fat']:
        # Moderate deficit for sustainable weight loss
        deficit = 500  # 0.5kg per week loss
        target_calories = tdee - deficit
        advice = f"To lose weight safely, aim for {target_calories} calories daily. This creates a 500-calorie deficit for ~0.5kg weekly loss."
    elif goal == 'Gain Weight':
        # Moderate surplus for healthy weight gain
        surplus = 300  # Gradual weight gain
        target_calories = tdee + surplus
        advice = f"To gain weight gradually, aim for {target_calories} calories daily. This creates a 300-calorie surplus."
    elif goal == 'Gain Muscle':
        # Small surplus for lean muscle gain
        surplus = 250  # Minimize fat gain while building muscle
        target_calories = tdee + surplus
        advice = f"For lean muscle gain, aim for {target_calories} calories daily. Focus on protein intake and progressive training."
    elif goal == 'Bulking':
        # Larger surplus for maximum muscle gain
        surplus = 500  # Aggressive muscle building
        target_calories = tdee + surplus
        advice = f"For bulking, aim for {target_calories} calories daily. Ensure adequate protein (1.6-2.2g/kg body weight)."
    elif goal == 'Toning':
        # Small deficit to reduce fat while maintaining muscle
        deficit = 250  # Gentle fat loss
        target_calories = tdee - deficit
        advice = f"For toning, aim for {target_calories} calories daily. Combine with strength training to preserve muscle."
    else:  # Maintain Weight
        target_calories = tdee
        advice = f"To maintain your weight, aim for {tdee} calories daily. Focus on balanced nutrition."
    
    return target_calories, advice

# BMI categories and advice
def calculate_bmi(weight: float, height: float) -> tuple:
    """Calculate BMI and return value, category, and advice"""
    # Ensure height is in meters for BMI calculation
    height_in_meters = height / 100
    bmi = weight / (height_in_meters ** 2)
    
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

# Comprehensive FAQ knowledge base extracted from the PDF and expanded
FAQ_KNOWLEDGE = {
    "protein": {
        "keywords": ["protein", "whey", "muscle", "supplement", "amino", "casein", "plant protein", "pea protein", "best protein powder", "how much protein", "high protein foods"],
        "responses": [
            "You need about 1.6–2.2g protein/kg body weight daily for muscle gain and fat loss support.",
            "Best high-protein foods: chicken, eggs, fish, Greek yogurt, lentils, tofu, and whey protein.",
            "Whey is fast-absorbing — great post-workout. Casein digests slowly — ideal before bed.",
            "Vegan? Combine legumes, grains, nuts, and seeds for a complete amino acid profile.",
            "Distribute protein intake evenly throughout the day for optimal muscle protein synthesis.",
            "You can safely consume up to 2.2g/kg body weight if training intensely — more isn’t proven beneficial.",
            "Post-workout meals should include 20–30g protein to optimize muscle repair and recovery.",
            "Protein shakes aren't mandatory — real food like eggs, chicken, and tofu work just as well.",
            "High-protein breakfast ideas: protein oats, cottage cheese, egg wraps, Greek yogurt bowls.",
            "Protein timing matters less than total daily intake — just hit your daily goal."

        ]
    },
    "calories": {
        "keywords": ["calories", "tdee", "bmr", "energy", "deficit", "surplus", "maintenance", "macros", "cutting", "bulk calories", "how many calories", "calorie calculator"],
        "responses": [
            "TDEE = BMR + activity. A deficit of 500kcal/day loses about 0.5kg/week.",
            "Bulk: 250–500 extra calories/day. Cut: 500 calorie deficit/day for steady fat loss.",
            "Use a TDEE calculator to find your maintenance, then adjust based on your goal.",
            "Calories matter — even if eating 'clean,' overconsumption causes weight gain.",
            "Macronutrient breakdown suggestion: 35% protein, 40% carbs, 25% healthy fats.",
            "A calorie is a calorie for weight balance, but food quality affects hunger, energy, and health.",
            "Calorie calculators give estimates — track your weight weekly to adjust as needed.",
            "Eating too few calories can slow metabolism and increase muscle loss.",
            "If fat loss stalls, try reducing calories by 100–200/day or increasing daily steps.",
            "Use a food scale for accurate calorie tracking — eyeballing often underestimates intake."

        ]
    },
    "workout": {
        "keywords": ["workout", "exercise", "hiit", "training", "gym", "cardio", "strength", "home workout", "mobility", "best exercises", "fat burning workouts", "training split"],
        "responses": [
            "Best exercises for muscle gain: squats, deadlifts, bench press, overhead press, pull-ups.",
            "Fat loss? Focus on HIIT, strength training, and staying active throughout the day.",
            "A balanced split: 2 upper, 2 lower, and 1 full-body or cardio day weekly.",
            "Home workout? Use bodyweight circuits: push-ups, lunges, squats, planks.",
            "Switch up your workout plan every 4–6 weeks to prevent plateaus and boredom.",
            "Even 20–30 minutes of daily movement boosts mood, heart health, and metabolism.",
            "Focus on form before increasing weight to prevent injuries.",
            "Training consistently (3–5x/week) matters more than having a 'perfect' workout split.",
            "Don’t skip warm-ups — dynamic mobility drills prep your joints and muscles.",
            "Use progressive overload: gradually increase reps, sets, or weight weekly."
        ]
    },
    "diet": {
        "keywords": ["diet", "nutrition", "food", "meal", "eat", "macro", "carb", "fat", "fiber", "clean eating", "healthy snacks", "meal plan", "low carb", "keto", "intermittent fasting"],
        "responses": [
            "A balanced diet = lean proteins, complex carbs, healthy fats, fiber, and hydration.",
            "Healthy snack ideas: Greek yogurt, boiled eggs, protein smoothies, and nuts.",
            "Low-carb diets can aid fat loss but aren't essential — calorie balance matters most.",
            "Intermittent fasting works for some as an appetite control strategy, not magic.",
            "Ensure at least 25–30g fiber/day for digestion, blood sugar control, and satiety.",
            "80/20 rule: eat nutritious whole foods 80% of the time, enjoy treats 20%.",
            "Whole grains, fruits, and veggies keep you fuller, aid digestion, and stabilize energy.",
            "Avoid ultra-restrictive diets — sustainable habits yield long-term success.",
            "Balance each plate: half veggies, 1/4 lean protein, 1/4 carbs.",
            "Track your fiber — aim for at least 25–30g daily for digestion and satiety."

        ]
    },
    "supplements": {
        "keywords": ["supplement", "vitamin", "pre-workout", "bcaa", "creatine", "omega", "multivitamin", "magnesium", "electrolyte", "greens powder", "what supplements should I take", "best supplements for muscle"],
        "responses": [
            "Top evidence-based supplements: whey protein, creatine, omega-3, and vitamin D.",
            "Pre-workouts with caffeine improve focus and energy — use them responsibly.",
            "BCAAs help muscle recovery in fasted states, but whole protein is better overall.",
            "Daily creatine (3–5g) is safe and improves strength, power, and muscle volume.",
            "Magnesium aids sleep, muscle recovery, and stress management — many are deficient.",
            "Supplements fill gaps — prioritize whole foods first.",
            "Greens powders offer vitamins but shouldn’t replace vegetables.",
            "Zinc and vitamin C can support immune health, especially in winter.",
            "Electrolyte tablets help during long or sweaty workouts.",
            "Read labels — avoid underdosed or filler-heavy supplements."

        ]
    },
    "hydration": {
        "keywords": ["water", "hydration", "drink", "fluid", "thirsty", "electrolyte", "dehydration", "sports drink", "how much water", "best drink after workout"],
        "responses": [
            "Aim for 35–40ml water per kg of body weight daily, more with exercise or heat.",
            "Pale yellow urine = hydrated. Dark = drink more water.",
            "Best post-workout drink: water + electrolytes for sessions over 60 mins.",
            "Sugary sports drinks are unnecessary unless training intensely for 60+ minutes.",
            "Coconut water naturally restores electrolytes, great for mild hydration.",
            "Start your day with a glass of water — dehydration affects energy and focus.",
            "Drink more if you’re sweating heavily or in hot climates.",
            "Flavored water or herbal teas count towards your fluid goal.",
            "Avoid excess caffeine and alcohol as they dehydrate you.",
            "Water-rich foods like cucumber and watermelon also boost hydration."

        ]
    },
    "motivation": {
        "keywords": ["motivation", "goal", "progress", "plateau", "stuck", "help", "discipline", "routine", "consistency", "visualize", "why am I not losing weight"],
        "responses": [
            "Set SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound.",
            "Plateaus are normal — adjust calories, training intensity, or take a rest week.",
            "Track non-scale victories: strength gains, measurements, energy, sleep quality.",
            "Focus on discipline, not motivation — habits built daily make lasting change.",
            "Visualize your goal daily — it reinforces commitment and purpose.",
            "Motivation fades — discipline and routine keep you going.",
            "Set weekly action goals: 'work out 4x' or 'cook 3 healthy meals.'",
            "Celebrate non-scale wins like better sleep or improved strength.",
            "Write down why you started to stay anchored to your goal.",
            "Small steps daily beat occasional big efforts."

        ]
    },
    "weight_loss": {
        "keywords": ["weight loss", "lose weight", "fat loss", "cutting", "deficit", "burn", "how to lose belly fat", "fat burning foods"],
        "responses": [
            "Target fat loss, not spot reduction — you can’t choose where fat comes off first.",
            "Best fat-loss foods: lean protein, leafy greens, berries, oats, avocado, green tea.",
            "Sleep affects fat loss — aim for 7–9 hours to regulate hunger hormones.",
            "Lifting weights while cutting preserves muscle and keeps metabolism higher.",
            "Monitor weight via weekly averages to offset daily water fluctuation noise.",
            "Prioritize protein while cutting to preserve muscle mass.",
            "Drink water before meals to reduce hunger.",
            "Manage stress — high cortisol can hinder fat loss.",
            "Avoid crash diets — they damage metabolism and lead to regain.",
            "Track inches, not just weight. Progress shows in photos and how clothes fit."

        ]
    },
    "muscle_gain": {
        "keywords": ["muscle", "gain", "bulk", "strength", "mass", "build", "how to gain muscle fast", "best foods for muscle"],
        "responses": [
            "Fastest muscle gain: calorie surplus + progressive strength training + good sleep.",
            "Best foods for muscle: chicken, salmon, rice, oats, quinoa, eggs, Greek yogurt.",
            "Don't skip recovery days — muscles grow while you rest, not in the gym.",
            "Track lifts and aim to increase weight/reps weekly to stimulate new muscle growth.",
            "Compound lifts (squats, bench, deadlift) deliver the biggest hypertrophy stimulus.",
            "Eating slightly above maintenance ensures muscle gain without excessive fat.",
            "Strength training 3–5x/week works best for hypertrophy.",
            "Sleep impacts muscle recovery and testosterone production.",
            "Creatine is one of the safest, most effective muscle-building supplements.",
            "Take progress pics monthly — the mirror shows what the scale can't."

        ]
    },
    "recovery": {
        "keywords": ["recovery", "rest", "sleep", "sore", "pain", "injury", "deload", "muscle recovery", "post workout recovery"],
        "responses": [
            "Sleep is non-negotiable for recovery — aim for 7–9 hours, especially after tough sessions.",
            "Use foam rolling, stretching, and light walks to improve recovery and reduce soreness.",
            "Protein and carbs within 1–2 hours post-workout speed up muscle repair.",
            "If soreness persists >3 days, reduce training intensity or volume.",
            "Schedule deload weeks every 6–8 weeks to manage fatigue and prevent injury.",
            "A post-workout cooldown lowers heart rate and improves recovery.",
            "Active recovery days speed up muscle healing.",
            "Listen to your body — persistent soreness may mean overtraining.",
            "Epsom salt baths can ease muscle tightness and reduce inflammation.",
            "Keep protein and sleep consistent even on rest days."

        ]
    },
    "cardio": {
        "keywords": ["cardio", "running", "aerobic", "endurance", "stamina", "best cardio for fat loss", "how much cardio"],
        "responses": [
            "150 min moderate or 75 min vigorous cardio per week improves heart and lung health.",
            "HIIT burns more calories quickly and boosts metabolic rate for hours after.",
            "Best cardio for fat loss: rowing, incline walking, cycling, or jump rope.",
            "Include low-intensity steady state (LISS) cardio on recovery days to aid blood flow.",
            "Don’t overdo cardio while bulking — it can hinder muscle growth.",
            "HIIT burns calories fast and improves endurance in short sessions.",
            "Walking 8–10k steps daily improves health and supports fat loss.",
            "Swimming is a joint-friendly, full-body cardio workout.",
            "Track heart rate to stay in your target cardio zone.",
            "Do cardio you enjoy — consistency beats perfection."

        ]
    },
    "flexibility": {
        "keywords": ["stretch", "flexibility", "yoga", "mobility", "warm", "how to improve flexibility"],
        "responses": [
            "Dynamic stretching pre-workout improves performance and reduces injury risk.",
            "Stretch each major muscle group 2–3 times per week, holding 20–30 seconds.",
            "Foam rolling before and after workouts boosts mobility and eases soreness.",
            "Yoga enhances flexibility, breathing control, and mental focus.",
            "Mobility drills keep joints healthy and improve lifting form.",
            "Stretch post-workout when muscles are warm.",
            "Focus extra mobility on tight areas like hips and shoulders.",
            "Regular stretching reduces injury risk and boosts workout performance.",
            "Yoga improves mental calmness along with flexibility.",
            "Consistency matters — flexibility improves slowly over time."

        ]
    },
    "general_health": {
        "keywords": ["health", "wellbeing", "stress", "sleep", "mental health", "lifestyle", "energy", "longevity", "immune", "best daily habits"],
        "responses": [
            "Daily habits for health: hydration, 7–9 hours sleep, 7,000+ steps, balanced diet.",
            "Manage stress via breathing exercises, journaling, and nature walks.",
            "Low vitamin D affects mood and immunity — aim for 10–20 mins sun or supplement.",
            "Omega-3 supports heart, joint, and brain health — consider fish or algae oil.",
            "Stay consistent — small daily habits compound into long-term wellbeing.",
            "Aim for 7–8k+ daily steps for longevity and metabolic health.",
            "Sun exposure boosts mood and regulates circadian rhythms.",
            "Deep breathing exercises reduce anxiety and improve focus.",
            "Strength training twice a week prevents muscle loss with aging.",
            "Stay consistent — your future health depends on habits you build today."

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

def find_best_response(message: str, user_profile: dict = None) -> str:
    """Find the most relevant response based on keywords, with user context"""
    message_lower = message.lower()
    best_match = None
    max_matches = 0
    
    # Check if asking about personal calories/nutrition
    if user_profile and any(word in message_lower for word in ["my calories", "how many calories", "my macros", "my tdee", "my bmr"]):
        if 'tdee' in user_profile:
            tdee = user_profile['tdee']
            bmr = user_profile.get('bmr', 'not calculated')
            goal = user_profile.get('goal', 'Maintain Weight')
            target_calories = user_profile.get('target_calories', tdee)
            
            response = f"Based on your profile:\n"
            response += f"📊 BMR: {bmr} calories (calories burned at rest)\n\n"
            response += f"📊 TDEE: {tdee} calories (total daily needs)\n\n"
            
            if goal and goal != 'Maintain Weight':
                target_calories, advice = calculate_goal_calories(tdee, goal)
                response += f"🎯 Goal: {goal}\n\n"
                response += f"🍽️ Target Calories: {target_calories} calories/day\n\n"
                response += f"\n💡 {advice}\n"
            else:
                response += f"🍽️ Maintenance Calories: {tdee} calories/day\n"
            
            return response
    
    # Regular keyword matching for general questions
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
    # Read the HTML file and serve it
    try:
        with open('bodybae_frontend.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Fix API URL to work properly on Render
        # Replace the API_URL line to ensure proper routing
        import re
        html_content = re.sub(
            r"const API_URL = .*?;",
            "const API_URL = '';",
            html_content
        )
        
        return html_content
    except FileNotFoundError:
        logger.error("Frontend HTML file not found")
        return jsonify({'error': 'Frontend not found'}), 404

@app.route('/api/onboard', methods=['POST'])
def onboard():
    """Handle user onboarding"""
    try:
        data = request.json
        logger.info(f"Onboarding request received: {data}")
        
        # Validate required fields
        required_fields = ['name', 'age', 'sex', 'height', 'weight', 'activity_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Calculate BMI
        weight = float(data['weight'])
        height = float(data['height'])
        bmi, category, advice = calculate_bmi(weight, height)
        
        # Calculate BMR and TDEE
        age = int(data['age'])
        sex = data['sex']
        activity = data['activity_level']
        
        # Calculate BMR using Mifflin-St Jeor equation
        if sex == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Calculate TDEE based on activity level (using standard multipliers)
        activity_multipliers = {
            'sedentary': 1.2,      # Little to no exercise
            'light': 1.375,        # Light exercise 1-3 days/week
            'moderate': 1.55,      # Moderate exercise 3-5 days/week
            'active': 1.725,       # Hard exercise 6-7 days/week
            'very_active': 1.9     # Very hard exercise, physical job
        }
        tdee = int(bmr * activity_multipliers.get(activity, 1.55))
        
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
        
        response_data = {
            'user_id': user_id,
            'bmi': bmi,
            'bmi_category': category,
            'bmi_advice': advice,
            'bmr': int(bmr),
            'tdee': tdee,
            'message': f"Great to meet you, {data['name']}! Your BMI is {bmi} ({category}). {advice} Your estimated daily calorie needs are {tdee} calories."
        }
        
        logger.info(f"Onboarding successful: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in onboarding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/set_goal', methods=['POST'])
def set_goal():
    """Set user fitness goal with personalized calorie recommendations"""
    try:
        data = request.json
        goal = data.get('goal')
        target_weeks = int(data.get('target_weeks', 12))
        user_id = data.get('user_id')
        
        # Get user's TDEE if available
        user_tdee = None
        if user_id and user_id in users:
            user_tdee = users[user_id].get('tdee')
        
        # Provide realistic feedback based on goal
        goal_advice = {
            'Lose Weight': f"For healthy weight loss, aim for 0.5-1kg per week. In {target_weeks} weeks, you could realistically lose {int(target_weeks * 0.5)}-{target_weeks}kg.",
            'Gain Weight': f"For healthy weight gain, aim for 0.25-0.5kg per week. In {target_weeks} weeks, you could gain {int(target_weeks * 0.25)}-{int(target_weeks * 0.5)}kg.",
            'Gain Muscle': f"Muscle gain is gradual. With consistent training and nutrition, expect 0.25-0.5kg of muscle per month. Stay patient and consistent!",
            'Lose Fat': f"Fat loss requires a calorie deficit. Combine cardio with strength training for best results. Track measurements, not just weight.",
            'Maintain Weight': f"Focus on consistent habits and balanced nutrition. Your maintenance calories are key to stability.",
            'Toning': f"Toning means building lean muscle while reducing fat. Combine strength training with moderate cardio for best results.",
            'Bulking': f"For bulking, eat in a 300-500 calorie surplus with plenty of protein. Focus on progressive overload in your training."
        }
        
        message = goal_advice.get(goal, "Great goal! Stay consistent with your nutrition and training for best results.")
        
        # Add personalized calorie recommendation if TDEE is available
        calorie_info = ""
        if user_tdee:
            target_calories, calorie_advice = calculate_goal_calories(user_tdee, goal)
            calorie_info = f"\n\n📊 {calorie_advice}"
            
            # Store goal and target calories for the user
            if user_id in users:
                users[user_id]['goal'] = goal
                users[user_id]['target_calories'] = target_calories
        
        return jsonify({
            'goal': goal,
            'target_weeks': target_weeks,
            'message': message + calorie_info,
            'target_calories': target_calories if user_tdee else None
        })
        
    except Exception as e:
        logger.error(f"Error in set_goal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        data = request.json
        user_message = data.get('message', '')
        user_profile = data.get('user_profile', {})
        
        logger.info(f"Chat request: {user_message}")
        
        # Get relevant response with user context
        response = find_best_response(user_message, user_profile)
        
        # Personalize if user profile available and not already personalized
        if user_profile and 'name' in user_profile and "Based on your profile:" not in response:
            # Only add name if it makes grammatical sense
            if "Hello!" in response:
                response = response.replace("Hello!", f"Hello {user_profile['name']}!")
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/daily_tip', methods=['GET'])
def daily_tip():
    """Get daily fitness tip"""
    try:
        # In production, this would check the date and serve one tip per day
        tip = random.choice(DAILY_TIPS)
        return jsonify({
            'tip': tip,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
    except Exception as e:
        logger.error(f"Error in daily_tip: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/nutrition_plan', methods=['POST'])
def nutrition_plan():
    """Get detailed nutrition plan based on user data and goals"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id or user_id not in users:
            return jsonify({'error': 'User not found'}), 404
        
        user = users[user_id]
        tdee = user['tdee']
        weight = user['weight']
        goal = user.get('goal', 'Maintain Weight')
        
        # Calculate target calories based on goal
        target_calories, calorie_advice = calculate_goal_calories(tdee, goal)
        
        # Calculate macronutrients
        # Protein: 1.6-2.2g per kg for muscle goals, 1.2-1.6g for weight loss
        if goal in ['Gain Muscle', 'Bulking']:
            protein_per_kg = 2.0
        elif goal in ['Lose Weight', 'Lose Fat', 'Toning']:
            protein_per_kg = 1.8
        else:
            protein_per_kg = 1.6
        
        protein_grams = int(weight * protein_per_kg)
        protein_calories = protein_grams * 4
        
        # Fat: 25-35% of total calories
        fat_percentage = 0.30
        fat_calories = int(target_calories * fat_percentage)
        fat_grams = int(fat_calories / 9)
        
        # Carbohydrates: Remainder
        carb_calories = target_calories - protein_calories - fat_calories
        carb_grams = int(carb_calories / 4)
        
        # Create meal timing suggestions
        meals_per_day = 4  # Breakfast, Lunch, Dinner, Snack
        calories_per_meal = target_calories // meals_per_day
        
        nutrition_data = {
            'tdee': tdee,
            'target_calories': target_calories,
            'calorie_advice': calorie_advice,
            'macros': {
                'protein': {
                    'grams': protein_grams,
                    'calories': protein_calories,
                    'percentage': round((protein_calories / target_calories) * 100)
                },
                'carbohydrates': {
                    'grams': carb_grams,
                    'calories': carb_calories,
                    'percentage': round((carb_calories / target_calories) * 100)
                },
                'fat': {
                    'grams': fat_grams,
                    'calories': fat_calories,
                    'percentage': round((fat_calories / target_calories) * 100)
                }
            },
            'meal_plan': {
                'meals_per_day': meals_per_day,
                'calories_per_meal': calories_per_meal,
                'sample_day': {
                    'breakfast': f"{calories_per_meal} cal (Protein: {protein_grams//4}g)",
                    'lunch': f"{calories_per_meal} cal (Protein: {protein_grams//4}g)",
                    'dinner': f"{calories_per_meal} cal (Protein: {protein_grams//4}g)",
                    'snack': f"{calories_per_meal} cal (Protein: {protein_grams//4}g)"
                }
            },
            'tips': [
                f"Aim for {protein_grams}g of protein daily, distributed across all meals",
                "Drink at least 35ml of water per kg of body weight daily",
                "Time carbohydrates around your workouts for better performance",
                "Include vegetables with every meal for fiber and micronutrients"
            ]
        }
        
        return jsonify(nutrition_data)
        
    except Exception as e:
        logger.error(f"Error in nutrition_plan: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Use PORT environment variable for Render deployment
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting BodyBae server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
