from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
import random
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize LangChain components
openai_api_key = os.getenv('OPENAI_API_KEY')
embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
llm = ChatOpenAI(temperature=0.7, model_name="gpt-3.5-turbo", openai_api_key=openai_api_key)

# Global variable to store vector store
vector_store = None

# Simple in-memory storage (replace with database in production)
users = {}

# Knowledge base content from the PDF
KNOWLEDGE_BASE = [
    {
        "topic": "BMI Calculation",
        "content": "BMI (Body Mass Index) is calculated by dividing weight in kilograms by height in meters squared. BMI = weight(kg) / (height(m))². Categories: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30)."
    },
    {
        "topic": "Calorie Requirements",
        "content": "Daily calorie needs depend on age, sex, weight, height, and activity level. Calculate BMR using: Men: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) + 5. Women: (10 × weight in kg) + (6.25 × height in cm) - (5 × age) - 161. Multiply BMR by activity factor: Sedentary (1.4), Moderately Active (1.6), Highly Active (1.8)."
    },
    {
        "topic": "Protein Requirements",
        "content": "For muscle gain, consume approximately 1.6g of protein per kilogram of bodyweight per day. Protein has 4 calories per gram. Good sources include meat, fish, eggs, dairy, legumes, nuts, and seeds."
    },
    {
        "topic": "Fat Intake",
        "content": "Around 35% of your diet should come from fats. Focus on healthy fats like monounsaturated and polyunsaturated fats found in avocados, nuts, olive oil, and fatty fish. Avoid trans fats."
    },
    {
        "topic": "Carbohydrates",
        "content": "Remaining calories after protein and fat should come from carbohydrates. Choose complex carbs like whole grains, fruits, and vegetables. Carbohydrates provide 4 calories per gram."
    },
    {
        "topic": "HIIT Workouts",
        "content": "High-Intensity Interval Training (HIIT) involves short bursts of intense exercise followed by rest periods. Effective for fat burning and improving cardiovascular fitness. Example: 30 seconds sprint, 30 seconds rest, repeat 5-10 times."
    },
    {
        "topic": "Home Exercises",
        "content": "Effective bodyweight exercises include: Squats (builds glutes and legs), Push-ups (chest and arms), Planks (core strength), Burpees (full body), Lunges (legs and balance). Complete 5 circuits of 15 reps each with 60 seconds rest between circuits."
    },
    {
        "topic": "Weight Loss",
        "content": "To lose fat while maintaining muscle, subtract 500 calories from your TDEE (Total Daily Energy Expenditure). This creates a sustainable deficit for losing approximately 0.5kg per week. Combine with strength training to preserve muscle mass."
    },
    {
        "topic": "Muscle Building",
        "content": "To gain muscle, add 500 calories to your TDEE. Focus on progressive overload in training and adequate protein intake. Expect to gain 0.25-0.5kg per week with proper training and nutrition."
    },
    {
        "topic": "Pre-Workout Nutrition",
        "content": "Consume a balanced meal 2-3 hours before exercise or a small snack 30-60 minutes before. Include carbs for energy and some protein. Avoid high-fat or high-fiber foods immediately before training."
    },
    {
        "topic": "Post-Workout Recovery",
        "content": "After exercise, consume protein within 30-60 minutes to support muscle recovery. Aim for 20-30g of protein. Whey protein shakes are convenient, or whole food options like chicken, eggs, or Greek yogurt."
    },
    {
        "topic": "Hydration",
        "content": "Drink at least 8 glasses of water daily, more if exercising. Proper hydration supports metabolism, nutrient transport, and exercise performance. Drink water before, during, and after workouts."
    },
    {
        "topic": "Sleep and Recovery",
        "content": "Aim for 7-9 hours of quality sleep per night. Sleep is crucial for muscle recovery, hormone regulation, and overall health. Poor sleep can increase cortisol and hinder progress."
    },
    {
        "topic": "Supplements",
        "content": "Basic supplements to consider: Whey protein for convenient protein intake, Creatine for strength and muscle gains, Omega-3 for heart health, Multivitamin for nutritional gaps. Always prioritize whole foods first."
    },
    {
        "topic": "Progress Tracking",
        "content": "Track progress through: Progress photos (same time, lighting, clothes), Body measurements (waist, arms, thighs), Strength gains (personal records), How clothes fit. Don't rely solely on scale weight."
    }
]

# Daily tips
DAILY_TIPS = [
    "Stay hydrated! Aim for at least 8 glasses of water throughout the day.",
    "Focus on compound exercises like squats and deadlifts for maximum muscle engagement.",
    "Remember: consistency beats perfection. Small daily actions lead to big results!",
    "Prioritize sleep - aim for 7-9 hours for optimal recovery and muscle growth.",
    "Track your protein intake to ensure you're getting enough for your goals.",
    "Don't skip warm-ups! 5-10 minutes can prevent injuries and improve performance.",
    "Mix up your workouts to prevent plateaus and keep things interesting.",
    "Meal prep on Sundays to stay on track during busy weekdays.",
    "Listen to your body - rest days are just as important as training days.",
    "Celebrate small victories along your fitness journey!"
]

def initialize_vector_store():
    """Initialize the vector store with knowledge base content"""
    global vector_store
    
    # Create documents from knowledge base
    documents = []
    for item in KNOWLEDGE_BASE:
        doc = Document(
            page_content=f"{item['topic']}: {item['content']}",
            metadata={"topic": item["topic"]}
        )
        documents.append(doc)
    
    # Split documents if needed
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_docs = text_splitter.split_documents(documents)
    
    # Create vector store
    vector_store = FAISS.from_documents(split_docs, embeddings)

def get_rag_response(question):
    """Get response using RAG pipeline"""
    if vector_store is None:
        initialize_vector_store()
    
    # Create retrieval QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=False
    )
    
    # Get response
    try:
        response = qa_chain.run(question)
        return response
    except Exception as e:
        print(f"Error in RAG response: {e}")
        return "I'm having trouble accessing my knowledge base right now. Please try again later."

def calculate_bmi(weight, height):
    """Calculate BMI and return category"""
    height_m = height / 100  # Convert cm to m
    bmi = weight / (height_m ** 2)
    
    if bmi < 18.5:
        category = "Underweight"
        advice = "Consider increasing caloric intake with nutritious foods."
    elif 18.5 <= bmi < 25:
        category = "Normal weight"
        advice = "Great job! Maintain your current healthy lifestyle."
    elif 25 <= bmi < 30:
        category = "Overweight"
        advice = "Consider a balanced diet and regular exercise routine."
    else:
        category = "Obese"
        advice = "Consult with healthcare professionals for personalized guidance."
    
    return round(bmi, 1), category, advice

def calculate_calories(user_data):
    """Calculate BMR and TDEE"""
    weight = user_data['weight']
    height = user_data['height']
    age = user_data['age']
    sex = user_data['sex']
    activity = user_data['activity_level']
    
    # Calculate BMR
    if sex == 'male':
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
    
    # Activity multipliers
    activity_multipliers = {
        'sedentary': 1.4,
        'light': 1.6,
        'moderate': 1.7,
        'active': 1.8
    }
    
    tdee = bmr * activity_multipliers.get(activity, 1.6)
    
    return round(bmr), round(tdee)

@app.route('/api/onboard', methods=['POST'])
def onboard():
    """Handle user onboarding"""
    data = request.json
    
    # Calculate BMI
    bmi, category, advice = calculate_bmi(data['weight'], data['height'])
    
    # Calculate calories
    bmr, tdee = calculate_calories(data)
    
    # Store user data (in production, use a database)
    user_id = f"user_{len(users) + 1}"
    users[user_id] = {
        **data,
        'bmi': bmi,
        'bmi_category': category,
        'bmr': bmr,
        'tdee': tdee,
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({
        'user_id': user_id,
        'bmi': bmi,
        'bmi_category': category,
        'bmi_advice': advice,
        'bmr': bmr,
        'tdee': tdee,
        'message': f"Welcome {data['name']}! Your BMI is {bmi} ({category}). Your daily calorie needs are approximately {tdee} calories."
    })

@app.route('/api/set_goal', methods=['POST'])
def set_goal():
    """Set user fitness goal"""
    data = request.json
    goal = data['goal']
    target_weeks = data['target_weeks']
    
    # Provide realistic timeline feedback
    realistic_timelines = {
        'Lose Weight': (8, 16),
        'Gain Weight': (8, 16),
        'Gain Muscle': (12, 24),
        'Lose Fat': (8, 16),
        'Toning': (8, 12),
        'Bulking': (12, 20),
        'Maintain Weight': (4, 52)
    }
    
    min_weeks, max_weeks = realistic_timelines.get(goal, (8, 16))
    
    if target_weeks < min_weeks:
        advice = f"Your timeline might be too aggressive. Consider {min_weeks}-{max_weeks} weeks for sustainable results."
    elif target_weeks > max_weeks:
        advice = f"Great! A longer timeline allows for sustainable progress. Stay consistent!"
    else:
        advice = f"Perfect! {target_weeks} weeks is a realistic timeline for your {goal} goal."
    
    return jsonify({
        'goal': goal,
        'target_weeks': target_weeks,
        'advice': advice,
        'message': f"Goal set! Let's work together to {goal.lower()} over the next {target_weeks} weeks. {advice}"
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with RAG"""
    data = request.json
    message = data['message']
    user_profile = data.get('user_profile', {})
    
    # Use RAG to get response
    response = get_rag_response(message)
    
    # Personalize response if user profile is available
    if user_profile and 'name' in user_profile:
        response = f"{response}\n\nRemember {user_profile['name']}, consistency is key to reaching your goals!"
    
    return jsonify({
        'response': response
    })

@app.route('/api/daily_tip', methods=['GET'])
def daily_tip():
    """Get daily fitness tip"""
    tip = random.choice(DAILY_TIPS)
    return jsonify({
        'tip': tip
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    # Initialize vector store on startup
    initialize_vector_store()
    
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(host='0.0.0.0', port=port, debug=False)