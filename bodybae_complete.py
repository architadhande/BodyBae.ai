from flask import Flask, request, jsonify, session
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
import json
import numpy as np

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    from sentence_transformers import SentenceTransformer
    import chromadb
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️ AI dependencies not fully available, using fallback system")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Storage
users_db = {}
chat_history_db = {}

class LightweightHealthRAG:
    """Lightweight RAG system for health coaching using small models"""
    
    def __init__(self):
        self.model_pipeline = None
        self.embedding_model = None
        self.collection = None
        
        if DEPENDENCIES_AVAILABLE:
            try:
                # Use DialogGPT-medium for conversation (762M params, works on free tier)
                print("Loading conversational model...")
                self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
                self.model = AutoModelForCausalLM.from_pretrained(
                    "microsoft/DialoGPT-medium",
                    pad_token_id=self.tokenizer.eos_token_id
                )
                self.model_pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    max_length=500,
                    temperature=0.8,
                    do_sample=True
                )
                
                # Use MiniLM for embeddings (22M params, very lightweight)
                print("Loading embedding model...")
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Initialize ChromaDB
                print("Setting up knowledge base...")
                self.setup_knowledge_base()
                
                print("✅ All models loaded successfully!")
                
            except Exception as e:
                print(f"Error loading models: {e}")
                print("Using fallback response system")
    
    def setup_knowledge_base(self):
        """Set up a lightweight health knowledge base"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.Client()
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.create_collection(
                    name="health_knowledge",
                    metadata={"description": "Health and fitness knowledge base"}
                )
            except:
                self.collection = self.chroma_client.get_collection(name="health_knowledge")
            
            # Health knowledge documents
            health_knowledge = [
                {
                    "id": "weight_loss_1",
                    "text": "Weight loss occurs through a caloric deficit. Aim for 500-750 calorie deficit daily for 1-2 pounds loss per week. Combine cardio and strength training. Focus on whole foods, lean proteins, vegetables, and stay hydrated. Track your progress weekly."
                },
                {
                    "id": "muscle_gain_1", 
                    "text": "Muscle building requires progressive overload and adequate protein. Consume 0.7-1g protein per pound bodyweight. Train each muscle group 2-3x per week. Focus on compound movements: squats, deadlifts, bench press. Get 7-9 hours sleep for recovery."
                },
                {
                    "id": "nutrition_1",
                    "text": "Balanced nutrition includes all macronutrients. Protein repairs tissues, carbs provide energy, fats support hormones. Eat colorful vegetables for micronutrients. Stay hydrated with 8-10 glasses water daily. Time meals around workouts for better performance."
                },
                {
                    "id": "cardio_1",
                    "text": "Cardiovascular exercise improves heart health and endurance. Mix steady-state cardio with HIIT for best results. Start with 150 minutes moderate cardio weekly. Walking, running, cycling, swimming are excellent options. Monitor heart rate for optimal training zones."
                },
                {
                    "id": "motivation_1",
                    "text": "Stay motivated by setting SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound. Track small victories daily. Find workout partners for accountability. Celebrate progress, not perfection. Remember why you started when things get tough."
                },
                {
                    "id": "recovery_1",
                    "text": "Recovery is crucial for progress. Get 7-9 hours quality sleep. Include rest days in your program. Practice stretching and mobility work. Consider yoga or meditation for stress management. Proper recovery prevents injury and burnout."
                }
            ]
            
            # Add documents to collection
            documents = [doc["text"] for doc in health_knowledge]
            ids = [doc["id"] for doc in health_knowledge]
            
            if self.embedding_model:
                embeddings = self.embedding_model.encode(documents).tolist()
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    ids=ids
                )
            else:
                self.collection.add(
                    documents=documents,
                    ids=ids
                )
            
            print(f"✅ Added {len(documents)} documents to knowledge base")
            
        except Exception as e:
            print(f"Error setting up knowledge base: {e}")
    
    def retrieve_context(self, query: str, n_results: int = 2) -> str:
        """Retrieve relevant context from knowledge base"""
        if not self.collection or not self.embedding_model:
            return ""
        
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            context = "\n".join(results['documents'][0]) if results['documents'] else ""
            return context
            
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return ""
    
    def generate_response(self, message: str, user_profile: Dict = None, conversation_history: List = None) -> str:
        """Generate response using lightweight models or fallback"""
        
        # If models aren't available, use intelligent fallback
        if not DEPENDENCIES_AVAILABLE or not self.model_pipeline:
            return self.get_fallback_response(message, user_profile)
        
        try:
            # Retrieve relevant context
            context = self.retrieve_context(message)
            
            # Build prompt with user context
            prompt = self.build_prompt(message, user_profile, context)
            
            # Generate response
            response = self.model_pipeline(
                prompt,
                max_new_tokens=150,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Clean response (remove prompt from output)
            if prompt in generated_text:
                generated_text = generated_text.replace(prompt, "").strip()
            
            # Ensure response is relevant and not empty
            if len(generated_text) < 10:
                return self.get_fallback_response(message, user_profile)
            
            return generated_text
            
        except Exception as e:
            print(f"Generation error: {e}")
            return self.get_fallback_response(message, user_profile)
    
    def build_prompt(self, message: str, user_profile: Dict = None, context: str = "") -> str:
        """Build a focused prompt for the model"""
        
        # Base prompt
        prompt = "You are BodyBae, a helpful fitness coach. "
        
        # Add user profile context if available
        if user_profile:
            name = user_profile.get('name', 'there')
            goals = user_profile.get('goals', [])
            bmi = user_profile.get('bmi', '')
            
            prompt += f"The user {name} has these goals: {', '.join(goals)}. "
            if bmi:
                prompt += f"Their BMI is {bmi}. "
        
        # Add retrieved context if available
        if context:
            prompt += f"Relevant info: {context[:200]}... "
        
        # Add the user's message
        prompt += f"\nUser: {message}\nBodyBae:"
        
        return prompt
    
    def get_fallback_response(self, message: str, user_profile: Dict = None) -> str:
        """Intelligent fallback responses when AI is unavailable"""
        
        message_lower = message.lower()
        name = user_profile.get('name', 'there') if user_profile else 'there'
        goals = user_profile.get('goals', []) if user_profile else []
        
        # Weight loss responses
        if any(word in message_lower for word in ['weight', 'lose', 'fat', 'diet']):
            responses = [
                f"Hi {name}! For weight loss, focus on creating a sustainable caloric deficit of 500-750 calories daily. This leads to healthy weight loss of 1-2 pounds per week.",
                f"Great question, {name}! Combine cardio exercises with strength training for optimal fat loss while preserving muscle mass. Aim for 150 minutes of moderate cardio weekly.",
                f"Remember {name}, weight loss is 80% diet and 20% exercise. Focus on whole foods, lean proteins, and plenty of vegetables. Stay consistent!"
            ]
            base_response = responses[hash(message) % len(responses)]
            
            if 'Weight Loss' in goals:
                base_response += " I see weight loss is one of your goals - you're on the right track!"
            
            return base_response
        
        # Muscle building responses
        elif any(word in message_lower for word in ['muscle', 'gain', 'bulk', 'strength']):
            responses = [
                f"Hey {name}! For muscle building, progressive overload is key. Gradually increase weights or reps each week. Aim for 0.7-1g protein per pound of body weight.",
                f"Building muscle requires consistency, {name}! Train each muscle group 2-3 times per week with compound movements like squats, deadlifts, and bench press.",
                f"Great focus, {name}! Remember the three pillars of muscle growth: training stimulus, adequate protein, and sufficient recovery. Get 7-9 hours of sleep!"
            ]
            return responses[hash(message) % len(responses)]
        
        # Nutrition responses
        elif any(word in message_lower for word in ['eat', 'food', 'nutrition', 'meal', 'protein']):
            responses = [
                f"{name}, balanced nutrition is crucial! Include lean proteins, complex carbs, healthy fats, and plenty of vegetables in your meals.",
                f"Good question, {name}! For optimal nutrition, eat protein with every meal, stay hydrated with 8-10 glasses of water daily, and don't skip meals.",
                f"Nutrition tip for you, {name}: Prep meals in advance to stay on track. Focus on whole, unprocessed foods for 80% of your diet."
            ]
            return responses[hash(message) % len(responses)]
        
        # Exercise responses
        elif any(word in message_lower for word in ['workout', 'exercise', 'train', 'gym']):
            responses = [
                f"{name}, a balanced workout routine should include both cardio and strength training. Start with 3-4 days per week and gradually increase.",
                f"Great to see you interested in exercise, {name}! Mix up your workouts to prevent boredom: try weights, bodyweight exercises, yoga, or sports.",
                f"Exercise tip, {name}: Always warm up before workouts and cool down after. This prevents injury and improves recovery."
            ]
            return responses[hash(message) % len(responses)]
        
        # Motivation responses
        elif any(word in message_lower for word in ['motivat', 'help', 'stuck', 'difficult', 'hard']):
            return f"I hear you, {name}! Remember, every small step counts. Focus on progress, not perfection. You've got this! What specific challenge can I help you with?"
        
        # General response
        else:
            general_responses = [
                f"Hi {name}! I'm here to help with your fitness journey. What specific aspect would you like to focus on - nutrition, exercise, or goal planning?",
                f"Great to chat with you, {name}! Whether it's weight loss, muscle building, or general fitness, I'm here to guide you. What's on your mind?",
                f"Hey {name}! Your health journey is unique. Tell me more about what you'd like to achieve, and I'll provide personalized advice."
            ]
            
            response = general_responses[hash(message) % len(general_responses)]
            
            if goals:
                response += f" I see you're focused on {', '.join(goals[:2])} - let's work on that together!"
            
            return response

# Initialize RAG system
print("🔄 Initializing lightweight RAG system...")
rag_system = LightweightHealthRAG()
print("✅ RAG system ready!")

def calculate_bmi_and_metrics(user_data):
    """Calculate BMI and health metrics"""
    weight = user_data['weight']
    height = user_data['height'] / 100  # Convert to meters
    age = user_data['age']
    gender = user_data['gender']
    activity = user_data['activity']
    
    # BMI calculation
    bmi = weight / (height ** 2)
    
    # BMI category
    if bmi < 18.5:
        category = "Underweight"
        advice = "Consider focusing on healthy weight gain with nutrient-dense foods."
    elif bmi < 25:
        category = "Normal Weight"
        advice = "Great job maintaining a healthy weight! Focus on overall fitness."
    elif bmi < 30:
        category = "Overweight"
        advice = "Consider a moderate weight loss approach with balanced nutrition and exercise."
    else:
        category = "Obese"
        advice = "Consult with healthcare professionals for a comprehensive weight management plan."
    
    # BMR calculation (Mifflin-St Jeor)
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * (height * 100) - 5 * age - 161
    
    # TDEE calculation
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extremely_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity, 1.2)
    
    return {
        'bmi': round(bmi, 1),
        'bmi_category': category,
        'bmi_advice': advice,
        'bmr': round(bmr),
        'tdee': round(tdee),
        'protein_needs': round(weight * 1.6, 1),
        'water_needs': round(weight * 35)
    }

@app.route('/')
def index():
    """Serve the single-page application"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BodyBae.ai - Your AI Fitness Coach</title>
    <style>
        /* Reset and Base Styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        /* Container and Layout */
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }

        .page {
            display: none;
            min-height: 100vh;
        }

        .page.active {
            display: block;
        }

        /* Header Styles */
        header {
            text-align: center;
            margin-bottom: 40px;
        }

        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            color: #4a7c59;
            margin-bottom: 10px;
        }

        .tagline {
            color: #666;
            font-size: 1.1rem;
        }

        /* Profile Card */
        .profile-card {
            background: white;
            border-radius: 12px;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            max-width: 600px;
            margin: 0 auto;
        }

        .profile-card h2 {
            color: #333;
            margin-bottom: 30px;
            font-size: 1.8rem;
        }

        /* Form Styles */
        .form-group {
            margin-bottom: 20px;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        label {
            display: block;
            margin-bottom: 5px;
            color: #555;
            font-weight: 500;
        }

        input[type="text"],
        input[type="number"],
        select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }

        input:focus,
        select:focus {
            outline: none;
            border-color: #4a7c59;
        }

        /* Goals Grid */
        .goals-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 10px;
        }

        .goal-item {
            display: flex;
            align-items: center;
            padding: 12px;
            background: #f8f8f8;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }

        .goal-item:hover {
            background: #e8f5e9;
            border-color: #4a7c59;
        }

        .goal-item input[type="checkbox"] {
            margin-right: 8px;
        }

        .goal-item input[type="checkbox"]:checked + span {
            color: #4a7c59;
            font-weight: 600;
        }

        /* Buttons */
        .btn-primary {
            width: 100%;
            padding: 15px;
            background: #4a7c59;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 30px;
        }

        .btn-primary:hover {
            background: #3d6348;
        }

        /* Chat Page Styles */
        .chat-container {
            height: 100vh;
            display: flex;
            flex-direction: column;
            background: white;
        }

        .chat-header {
            background: #4a7c59;
            color: white;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header .logo {
            font-size: 1.8rem;
            margin: 0;
            color: white;
        }

        .user-info {
            display: flex;
            gap: 20px;
            align-items: center;
        }

        .user-name {
            font-weight: 600;
        }

        .user-bmi {
            background: rgba(255, 255, 255, 0.2);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
        }

        /* Chat Main Area */
        .chat-main {
            flex: 1;
            display: flex;
            overflow: hidden;
        }

        /* Metrics Panel */
        .metrics-panel {
            width: 250px;
            background: #f8f8f8;
            padding: 25px;
            border-right: 1px solid #e0e0e0;
        }

        .metrics-panel h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.2rem;
        }

        .metric {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }

        .metric-label {
            display: block;
            color: #666;
            font-size: 0.9rem;
            margin-bottom: 5px;
        }

        .metric-value {
            display: block;
            color: #333;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .goals-display {
            margin-top: 20px;
            color: #555;
            font-size: 0.95rem;
        }

        /* Chat Area */
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        .messages {
            flex: 1;
            padding: 30px;
            overflow-y: auto;
            background: white;
        }

        .message {
            margin-bottom: 20px;
            padding: 15px 20px;
            border-radius: 12px;
            max-width: 70%;
            animation: fadeIn 0.3s ease;
        }

        .message.user {
            background: #4a7c59;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            background: #f0f0f0;
            color: #333;
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }

        .message.typing {
            background: #f0f0f0;
            margin-right: auto;
            padding: 10px 15px;
        }

        /* Typing Animation */
        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dots span:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dots span:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Input Area */
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .quick-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            border: 1px solid #e0e0e0;
            border-radius: 20px;
            color: #555;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.3s;
        }

        .quick-btn:hover {
            background: #e8f5e9;
            color: #4a7c59;
            border-color: #4a7c59;
        }

        .chat-form {
            display: flex;
            gap: 10px;
        }

        #message-input {
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
        }

        .send-btn {
            padding: 12px 24px;
            background: #4a7c59;
            color: white;
            border: none;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }

        .send-btn:hover {
            background: #3d6348;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .goals-grid {
                grid-template-columns: 1fr;
            }
            
            .chat-main {
                flex-direction: column;
            }
            
            .metrics-panel {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e0e0e0;
                padding: 20px;
            }
            
            .message {
                max-width: 85%;
            }
            
            .quick-actions {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <!-- Profile Setup Page -->
    <div id="profile-page" class="page active">
        <div class="container">
            <header>
                <h1 class="logo">BodyBae.ai</h1>
                <p class="tagline">Your AI-powered fitness journey starts here</p>
            </header>

            <div class="profile-card">
                <h2>Let's get to know you</h2>
                <form id="profile-form">
                    <div class="form-group">
                        <label for="name">Name</label>
                        <input type="text" id="name" name="name" required placeholder="Your name">
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="age">Age</label>
                            <input type="number" id="age" name="age" min="13" max="100" required placeholder="25">
                        </div>
                        <div class="form-group">
                            <label for="gender">Gender</label>
                            <select id="gender" name="gender" required>
                                <option value="">Select</option>
                                <option value="male">Male</option>
                                <option value="female">Female</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="height">Height (cm)</label>
                            <input type="number" id="height" name="height" min="100" max="250" required placeholder="170">
                        </div>
                        <div class="form-group">
                            <label for="weight">Weight (kg)</label>
                            <input type="number" id="weight" name="weight" min="30" max="300" step="0.1" required placeholder="70">
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="activity">Activity Level</label>
                        <select id="activity" name="activity" required>
                            <option value="">Select your activity level</option>
                            <option value="sedentary">Sedentary (little to no exercise)</option>
                            <option value="lightly_active">Lightly Active (exercise 1-3 days/week)</option>
                            <option value="moderately_active">Moderately Active (exercise 3-5 days/week)</option>
                            <option value="very_active">Very Active (exercise 6-7 days/week)</option>
                            <option value="extremely_active">Extremely Active (physical job + exercise)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label>Fitness Goals (select all that apply)</label>
                        <div class="goals-grid">
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="Weight Loss">
                                <span>Weight Loss</span>
                            </label>
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="Muscle Building">
                                <span>Muscle Building</span>
                            </label>
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="Improve Endurance">
                                <span>Improve Endurance</span>
                            </label>
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="General Fitness">
                                <span>General Fitness</span>
                            </label>
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="Flexibility">
                                <span>Flexibility</span>
                            </label>
                            <label class="goal-item">
                                <input type="checkbox" name="goals" value="Stress Relief">
                                <span>Stress Relief</span>
                            </label>
                        </div>
                    </div>

                    <button type="submit" class="btn-primary">Start My Journey</button>
                </form>
            </div>
        </div>
    </div>

    <!-- Chat Page -->
    <div id="chat-page" class="page">
        <div class="chat-container">
            <header class="chat-header">
                <h1 class="logo">BodyBae.ai</h1>
                <div class="user-info" id="user-info"></div>
            </header>

            <div class="chat-main">
                <div class="metrics-panel" id="metrics-panel"></div>
                
                <div class="chat-area">
                    <div class="messages" id="messages"></div>
                    
                    <div class="input-area">
                        <div class="quick-actions">
                            <button class="quick-btn" onclick="askQuestion('What should I eat today?')">Nutrition</button>
                            <button class="quick-btn" onclick="askQuestion('Create a workout plan for me')">Workout</button>
                            <button class="quick-btn" onclick="askQuestion('How can I stay motivated?')">Motivation</button>
                            <button class="quick-btn" onclick="askQuestion('Tips for better recovery')">Recovery</button>
                        </div>
                        <form id="chat-form" class="chat-form">
                            <input type="text" id="message-input" placeholder="Ask me anything about fitness, nutrition, or wellness..." required>
                            <button type="submit" class="send-btn">Send</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // State management
        let userProfile = {};
        let chatHistory = [];

        // DOM elements
        const profilePage = document.getElementById('profile-page');
        const chatPage = document.getElementById('chat-page');
        const profileForm = document.getElementById('profile-form');
        const chatForm = document.getElementById('chat-form');
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');

        // Profile form submission
        profileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(profileForm);
            const goals = formData.getAll('goals');
            
            if (goals.length === 0) {
                alert('Please select at least one fitness goal');
                return;
            }

            const profileData = {
                name: formData.get('name'),
                age: formData.get('age'),
                gender: formData.get('gender'),
                height: formData.get('height'),
                weight: formData.get('weight'),
                activity: formData.get('activity'),
                goals: goals
            };

            try {
                const response = await fetch('/save_profile', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(profileData)
                });

                const result = await response.json();
                
                if (result.success) {
                    userProfile = result.profile;
                    showChatPage(result.metrics, result.welcome_message);
                } else {
                    alert('Error saving profile: ' + result.error);
                }
            } catch (error) {
                alert('Network error. Please try again.');
            }
        });

        // Show chat page
        function showChatPage(metrics, welcomeMessage) {
            profilePage.classList.remove('active');
            chatPage.classList.add('active');

            // Display user info
            document.getElementById('user-info').innerHTML = `
                <span class="user-name">${userProfile.name}</span>
                <span class="user-bmi">BMI: ${metrics.bmi}</span>
            `;

            // Display metrics
            document.getElementById('metrics-panel').innerHTML = `
                <h3>Your Health Metrics</h3>
                <div class="metric">
                    <span class="metric-label">BMI</span>
                    <span class="metric-value">${metrics.bmi} (${metrics.bmi_category})</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Daily Calories</span>
                    <span class="metric-value">${metrics.tdee} cal</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Protein Target</span>
                    <span class="metric-value">${metrics.protein_needs}g</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Water Intake</span>
                    <span class="metric-value">${Math.round(metrics.water_needs/1000)}L</span>
                </div>
                <div class="goals-display">
                    <strong>Goals:</strong><br>
                    ${userProfile.goals.join(', ')}
                </div>
            `;

            // Add welcome message
            addMessage('bot', welcomeMessage);
        }

        // Chat form submission
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage('user', message);
            messageInput.value = '';

            // Show typing indicator
            const typingDiv = addMessage('typing', '...');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });

                const result = await response.json();
                
                // Remove typing indicator
                typingDiv.remove();
                
                // Add bot response
                addMessage('bot', result.response);
                
            } catch (error) {
                typingDiv.remove();
                addMessage('bot', 'Sorry, I encountered an error. Please try again.');
            }
        });

        // Add message to chat
        function addMessage(type, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            if (type === 'typing') {
                messageDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
            } else {
                messageDiv.textContent = content;
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageDiv;
        }

        // Quick action buttons
        function askQuestion(question) {
            messageInput.value = question;
            chatForm.dispatchEvent(new Event('submit'));
        }
    </script>
</body>
</html>
'''

@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Save user profile and generate AI insights"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        user_data = {
            'name': data['name'],
            'age': int(data['age']),
            'height': float(data['height']),
            'weight': float(data['weight']),
            'gender': data['gender'],
            'activity': data['activity'],
            'goals': data['goals'],
            'created_at': datetime.now().isoformat()
        }
        
        # Calculate health metrics
        metrics = calculate_bmi_and_metrics(user_data)
        user_data.update(metrics)
        
        # Store user data
        users_db[user_id] = user_data
        session['user_id'] = user_id
        
        # Generate welcome message
        welcome_message = f"""Welcome {data['name']}! I've calculated your health metrics:

BMI: {metrics['bmi']} ({metrics['bmi_category']})
Daily Calorie Needs: {metrics['tdee']} calories
Protein Target: {metrics['protein_needs']}g daily

Your goals: {', '.join(data['goals'])}

{metrics['bmi_advice']}

I'm here to help you achieve your fitness goals with personalized advice. What would you like to know first?"""
        
        return jsonify({
            'success': True,
            'profile': user_data,
            'metrics': metrics,
            'welcome_message': welcome_message
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    data = request.json
    message = data.get('message', '')
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'})
    
    try:
        # Get user profile
        user_profile = {}
        if user_id and user_id in users_db:
            user_profile = users_db[user_id]
        
        # Get conversation history
        conversation_history = []
        if user_id and user_id in chat_history_db:
            conversation_history = chat_history_db[user_id][-10:]  # Last 10 messages
        
        # Generate response using RAG system
        response = rag_system.generate_response(
            message, 
            user_profile, 
            conversation_history
        )
        
        # Store conversation
        if user_id:
            if user_id not in chat_history_db:
                chat_history_db[user_id] = []
            chat_history_db[user_id].extend([
                {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
            ])
        
        return jsonify({
            'response': response,
            'success': True
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        fallback_response = "I'm here to help with your fitness journey! Could you tell me more about what specific guidance you're looking for?"
        return jsonify({
            'response': fallback_response,
            'success': True
        })

@app.route('/health_check')
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'BodyBae_v2.0',
        'rag_status': 'active' if rag_system else 'unavailable'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)