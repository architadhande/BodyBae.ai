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
        "keywords": ["protein", "whey", "muscle", "supplement", "amino"],
        "responses": [
            "Based on research, you need approximately 1.6g of protein per kilogram of bodyweight per day for muscle gain. Protein is essential for rebuilding muscle and recovery.",
            "Great protein sources include meat, fish, eggs, legumes, nuts, and whey protein supplements. For muscle growth, combine adequate protein with consistent strength training.",
            "Whey protein is a convenient way to meet your protein needs. You can use it in shakes, pancakes, protein balls, or overnight oats for variety.",
            "For optimal muscle protein synthesis, aim to distribute protein intake throughout the day, with 20-30g per meal.",
            "Plant-based protein sources include lentils, chickpeas, quinoa, tofu, and tempeh. Combine different sources for complete amino acid profiles."
        ]
    },
    "calories": {
        "keywords": ["calories", "tdee", "bmr", "energy", "calorie", "deficit", "surplus"],
        "responses": [
            "Your Total Daily Energy Expenditure (TDEE) depends on your BMR and activity level. To lose fat, subtract 500kcal from your TDEE. To gain muscle, add 250-500kcal.",
            "Calculate your BMR using: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5 for men, or - 161 for women.",
            "Track your calories accurately for best results. Small inaccuracies can add up and affect your progress.",
            "A 500-calorie daily deficit typically results in 0.5kg weight loss per week - a safe and sustainable rate.",
            "For muscle gain, a 250-500 calorie surplus is recommended, combined with progressive strength training."
        ]
    },
    "workout": {
        "keywords": ["workout", "exercise", "hiit", "training", "gym", "cardio", "strength"],
        "responses": [
            "HIIT workouts are excellent for burning calories and improving fitness. Try circuits of burpees, jump squats, press-ups, and planks with 60-second rest between circuits.",
            "For home workouts, focus on compound movements like squats, lunges, push-ups, and planks. Do 5 circuits of 15 reps each exercise.",
            "Mix up your workouts to avoid plateaus. Combine strength training with cardio, and vary intensity and exercises weekly.",
            "Aim for at least 150 minutes of moderate aerobic activity or 75 minutes of vigorous activity per week, plus strength training twice weekly.",
            "Progressive overload is key for muscle growth - gradually increase weight, reps, or sets over time."
        ]
    },
    "diet": {
        "keywords": ["diet", "nutrition", "food", "meal", "eat", "macro", "carb", "fat"],
        "responses": [
            "A balanced diet should include 35% fats (focus on healthy fats like avocados and nuts), adequate protein (1.6g/kg body weight), and the rest from carbohydrates.",
            "Meal prep is key to success. Plan your meals ahead, include plenty of vegetables, and allow yourself occasional treats to stay on track.",
            "Stay hydrated, eat plenty of fiber to feel fuller longer, and avoid excessive alcohol which adds empty calories.",
            "Focus on whole foods: lean proteins, complex carbohydrates, healthy fats, and plenty of fruits and vegetables.",
            "Timing matters: eat protein within 2-3 hours post-workout for optimal recovery, and spread meals throughout the day."
        ]
    },
    "supplements": {
        "keywords": ["supplement", "vitamin", "pre-workout", "bcaa", "creatine", "omega"],
        "responses": [
            "Key supplements include: protein powder for muscle growth, omega-3 for heart health, and a good multivitamin for overall health.",
            "Pre-workout supplements with caffeine can boost performance. For recovery, consider whey protein or plant-based alternatives.",
            "Supplements aren't magic - they work best alongside a balanced diet and consistent training routine.",
            "Creatine monohydrate (3-5g daily) is one of the most researched supplements for strength and muscle gains.",
            "Vitamin D, especially in winter months, can support immune function and muscle recovery."
        ]
    },
    "weight_loss": {
        "keywords": ["weight loss", "lose weight", "fat loss", "cutting", "deficit", "burn"],
        "responses": [
            "For healthy weight loss, aim for a 500-calorie deficit daily. This leads to about 0.5kg loss per week - sustainable and healthy.",
            "Combine calorie deficit with strength training to preserve muscle mass while losing fat. Don't rush the process.",
            "Track progress through measurements and photos, not just the scale. Weight can fluctuate daily due to water retention.",
            "High-protein diets (1.6-2.2g/kg) help preserve muscle during weight loss and increase satiety.",
            "Include refeed days or diet breaks every 6-8 weeks to prevent metabolic adaptation."
        ]
    },
    "muscle_gain": {
        "keywords": ["muscle", "gain", "bulk", "strength", "mass", "build"],
        "responses": [
            "To gain muscle, eat in a 250-500 calorie surplus with adequate protein (1.6g/kg body weight) and progressive strength training.",
            "Focus on compound exercises like squats, deadlifts, and presses. Progressive overload is key - gradually increase weight or reps.",
            "Recovery is crucial for muscle growth. Aim for 7-9 hours of sleep and rest days between training the same muscle groups.",
            "Train each muscle group 2-3 times per week for optimal growth. Volume (sets x reps x weight) drives hypertrophy.",
            "Be patient - natural muscle gain is typically 0.25-0.5kg per month for beginners, less for experienced lifters."
        ]
    },
    "recovery": {
        "keywords": ["recovery", "rest", "sleep", "sore", "pain", "injury"],
        "responses": [
            "Sleep 7-9 hours nightly for optimal recovery. During sleep, growth hormone peaks and muscle repair occurs.",
            "Active recovery (light walking, swimming, yoga) can help reduce soreness and improve circulation.",
            "Proper nutrition post-workout is crucial: consume protein and carbs within 2-3 hours for optimal recovery.",
            "Listen to your body - persistent pain may indicate injury. Rest and seek professional advice if needed.",
            "Foam rolling and stretching can help reduce muscle tension and improve flexibility."
        ]
    },
    "motivation": {
        "keywords": ["motivation", "goal", "progress", "plateau", "stuck", "help"],
        "responses": [
            "Set SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound. Break big goals into smaller milestones.",
            "Track your progress with photos, measurements, and performance metrics - not just the scale.",
            "Find a workout buddy or join a fitness community for accountability and support.",
            "Celebrate small victories and focus on building sustainable habits rather than perfect adherence.",
            "Remember: progress isn't always linear. Plateaus are normal - stay consistent and trust the process."
        ]
    },
    "hydration": {
        "keywords": ["water", "hydration", "drink", "fluid", "thirsty"],
        "responses": [
            "Aim for at least 35ml of water per kg of body weight daily, more if you're active or in hot weather.",
            "Proper hydration supports metabolism, nutrient transport, and exercise performance.",
            "Check your urine color - pale yellow indicates good hydration, dark yellow suggests you need more fluids.",
            "Drink water before, during, and after exercise. For workouts over 60 minutes, consider electrolyte replacement.",
            "Foods like watermelon, cucumber, and oranges also contribute to hydration."
        ]
    },
    "cardio": {
        "keywords": ["cardio", "running", "aerobic", "endurance", "stamina"],
        "responses": [
            "For general health, aim for 150 minutes of moderate cardio or 75 minutes of vigorous cardio weekly.",
            "HIIT (High-Intensity Interval Training) can burn more calories in less time and improve cardiovascular fitness.",
            "Mix steady-state cardio with interval training for best results. Both have unique benefits.",
            "Cardio doesn't kill gains if programmed properly - keep volume moderate and fuel appropriately.",
            "Low-intensity cardio (walking, cycling) can aid recovery and won't interfere with strength training."
        ]
    },
    "flexibility": {
        "keywords": ["stretch", "flexibility", "yoga", "mobility", "warm"],
        "responses": [
            "Dynamic stretching before workouts prepares muscles for activity. Save static stretching for after.",
            "Aim to stretch major muscle groups 2-3 times per week, holding each stretch for 15-30 seconds.",
            "Yoga or dedicated mobility work can improve flexibility, reduce injury risk, and enhance performance.",
            "Foam rolling before stretching can help release muscle tension and improve range of motion.",
            "Good flexibility and mobility become increasingly important as we age - start early and stay consistent."
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
            response += f"📊 BMR: {bmr} calories (calories burned at rest)\n"
            response += f"📊 TDEE: {tdee} calories (total daily needs)\n"
            
            if goal and goal != 'Maintain Weight':
                target_calories, advice = calculate_goal_calories(tdee, goal)
                response += f"🎯 Goal: {goal}\n"
                response += f"🍽️ Target Calories: {target_calories} calories/day\n"
                response += f"\n💡 {advice}"
            else:
                response += f"🍽️ Maintenance Calories: {tdee} calories/day"
            
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
