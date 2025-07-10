from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Enhanced AI imports
import openai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from dataclasses import dataclass
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# OpenAI API key (use environment variable)
openai.api_key = os.environ.get('OPENAI_API_KEY')

@dataclass
class HealthDocument:
    """Health knowledge document for RAG system"""
    content: str
    topic: str
    category: str
    keywords: List[str]
    embedding: Optional[np.ndarray] = None

class EnhancedHealthRAG:
    """Enhanced RAG system with better embeddings and health knowledge"""
    
    def __init__(self):
        """Initialize the enhanced RAG system"""
        # Use a better sentence transformer model
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.documents = []
        self.embeddings = None
        self.index = None
        
        # Initialize comprehensive health knowledge
        self._setup_health_knowledge()
        self._build_vector_index()
        
        logger.info(f"RAG system initialized with {len(self.documents)} health documents")
    
    def _setup_health_knowledge(self):
        """Setup comprehensive health and fitness knowledge base"""
        
        health_knowledge = [
            {
                "topic": "Weight Loss Science",
                "category": "weight_management",
                "content": """
                Weight loss fundamentally requires a caloric deficit - burning more calories than you consume. 
                A safe and sustainable deficit is 500-750 calories per day, leading to 0.5-1 kg weight loss weekly.
                
                Key principles:
                - Calculate TDEE (Total Daily Energy Expenditure) first
                - Create moderate deficit through diet and exercise
                - Prioritize protein (1.2-1.6g per kg body weight) to preserve muscle
                - Include strength training to maintain metabolism
                - Focus on whole foods: vegetables, lean proteins, complex carbs
                - Stay hydrated and get adequate sleep (7-9 hours)
                
                Avoid extreme deficits (<1200 calories for women, <1500 for men) as they can slow metabolism,
                cause muscle loss, and are unsustainable long-term.
                """,
                "keywords": ["weight loss", "caloric deficit", "TDEE", "sustainable", "protein", "metabolism"]
            },
            {
                "topic": "Muscle Building Optimization",
                "category": "muscle_building",
                "content": """
                Muscle building requires three key factors: progressive overload, adequate protein, and proper recovery.
                
                Training principles:
                - Progressive overload: gradually increase weight, reps, or sets
                - Compound movements: squats, deadlifts, bench press, rows
                - Train each muscle group 2-3 times per week
                - Rep ranges: 6-12 for hypertrophy, 1-5 for strength
                - Volume: 10-20 sets per muscle group per week
                
                Nutrition for muscle growth:
                - Protein: 1.6-2.2g per kg body weight daily
                - Slight caloric surplus: 200-500 calories above maintenance
                - Post-workout: 20-40g protein within 2 hours
                - Spread protein throughout the day (20-30g per meal)
                
                Recovery essentials:
                - Sleep 7-9 hours (growth hormone release during deep sleep)
                - Rest 48-72 hours between training same muscle groups
                - Manage stress (cortisol inhibits muscle growth)
                - Stay hydrated for optimal muscle function
                """,
                "keywords": ["muscle building", "progressive overload", "protein", "hypertrophy", "compound movements", "recovery"]
            },
            {
                "topic": "Cardiovascular Health and Endurance",
                "category": "cardio_endurance",
                "content": """
                Cardiovascular training improves heart health, endurance, and overall fitness.
                
                Types of cardio training:
                - LISS (Low Intensity Steady State): 65-75% max heart rate, fat burning zone
                - MISS (Moderate Intensity): 75-85% max heart rate, aerobic capacity
                - HIIT (High Intensity Interval): 85-95% max heart rate, improves VO2 max
                
                Training recommendations:
                - Beginners: 20-30 minutes LISS, 3-4 times per week
                - Intermediate: Mix LISS and MISS, 4-5 times per week
                - Advanced: Include HIIT 1-2 times per week
                
                Heart rate calculation:
                - Max HR = 220 - age (rough estimate)
                - Target zones: Fat burn 60-70%, Cardio 70-85%, Peak 85-95%
                
                Benefits:
                - Strengthens heart muscle and improves circulation
                - Reduces blood pressure and cholesterol
                - Improves insulin sensitivity and glucose metabolism
                - Enhances mood through endorphin release
                - Increases lung capacity and oxygen efficiency
                """,
                "keywords": ["cardio", "endurance", "heart rate", "HIIT", "LISS", "VO2 max", "aerobic"]
            },
            {
                "topic": "Nutrition Fundamentals",
                "category": "nutrition",
                "content": """
                Proper nutrition is the foundation of health, fitness, and performance.
                
                Macronutrient balance:
                - Protein: 10-35% of calories (tissue repair, satiety, metabolism)
                - Carbohydrates: 45-65% of calories (energy for brain and muscles)
                - Fats: 20-35% of calories (hormone production, nutrient absorption)
                
                Micronutrient priorities:
                - Vitamin D: immune function, bone health (sunlight, supplements)
                - Omega-3 fatty acids: inflammation, brain health (fish, walnuts, flax)
                - Iron: oxygen transport (red meat, spinach, legumes)
                - Calcium: bone health (dairy, leafy greens, fortified foods)
                - B-vitamins: energy metabolism (whole grains, meat, eggs)
                
                Meal timing strategies:
                - Eat protein with every meal for satiety and muscle preservation
                - Pre-workout: carbs 30-60 minutes before for energy
                - Post-workout: protein + carbs within 2 hours for recovery
                - Distribute calories evenly throughout the day
                
                Hydration guidelines:
                - 35-40ml per kg body weight daily
                - Additional 500-750ml per hour of exercise
                - Monitor urine color (pale yellow indicates good hydration)
                """,
                "keywords": ["nutrition", "macronutrients", "micronutrients", "meal timing", "hydration", "protein", "carbs"]
            },
            {
                "topic": "Sleep and Recovery Optimization",
                "category": "recovery",
                "content": """
                Recovery is when your body adapts to training and builds strength. Sleep is the most critical recovery tool.
                
                Sleep importance for fitness:
                - Muscle protein synthesis occurs during deep sleep
                - Growth hormone release peaks at night
                - Cognitive function and decision-making improve
                - Appetite hormones (leptin/ghrelin) regulate properly
                - Immune system strengthens and repairs
                
                Sleep optimization strategies:
                - Consistent schedule: same bedtime and wake time daily
                - Duration: 7-9 hours for adults
                - Environment: cool (65-68°F), dark, quiet room
                - Pre-sleep routine: no screens 1 hour before bed
                - Avoid: caffeine 6+ hours before bed, large meals 3 hours before
                
                Active recovery methods:
                - Light walking or swimming on rest days
                - Yoga or gentle stretching
                - Foam rolling and self-massage
                - Meditation and breathing exercises
                - Contrast showers (hot/cold therapy)
                
                Signs of poor recovery:
                - Persistent fatigue and decreased performance
                - Frequent illness or slow healing
                - Mood changes and irritability
                - Sleep disturbances
                - Loss of motivation or appetite
                """,
                "keywords": ["sleep", "recovery", "growth hormone", "rest days", "fatigue", "adaptation"]
            },
            {
                "topic": "Age-Specific Fitness Guidelines",
                "category": "age_fitness",
                "content": """
                Fitness needs and capabilities change throughout life. Training should adapt accordingly.
                
                Young Adults (18-30):
                - Build fitness foundation with variety
                - Focus on learning proper movement patterns
                - Higher intensity training is well-tolerated
                - Establish consistent exercise habits
                - Recovery is typically faster
                
                Middle Age (30-50):
                - Maintain muscle mass (begins declining after 30)
                - Include more flexibility and mobility work
                - Manage stress and prioritize sleep quality
                - Watch for overuse injuries
                - Balance family/work with fitness commitments
                
                Older Adults (50-65):
                - Focus on functional movement patterns
                - Emphasize strength training for bone density
                - Include balance and coordination exercises
                - Lower impact activities for joint health
                - May need longer recovery periods
                
                Seniors (65+):
                - Emphasize activities of daily living
                - Fall prevention through balance training
                - Social activities like group classes
                - Chair exercises if mobility is limited
                - Work closely with healthcare providers
                
                Universal principles regardless of age:
                - Start gradually and progress slowly
                - Listen to your body and adapt as needed
                - Consistency trumps intensity
                - Include strength, cardio, and flexibility
                """,
                "keywords": ["age", "seniors", "middle age", "young adults", "functional movement", "balance"]
            },
            {
                "topic": "Women's Health and Fitness",
                "category": "womens_health",
                "content": """
                Women have unique physiological considerations that affect training and nutrition.
                
                Menstrual cycle considerations:
                - Follicular phase (days 1-14): higher energy, good for intense training
                - Ovulation (around day 14): peak strength and power
                - Luteal phase (days 15-28): may need to reduce intensity
                - Menstruation: listen to body, gentle movement may help cramps
                
                Hormonal factors:
                - Estrogen: affects muscle recovery and fat metabolism
                - Progesterone: can increase appetite and water retention
                - Iron needs increase during menstruation (18mg daily)
                - Calcium crucial for bone health (1000-1200mg daily)
                
                Training adaptations:
                - Women typically recover faster between sets
                - Higher rep ranges often work well
                - Strength training won't cause "bulky" muscles
                - Focus on building bone density to prevent osteoporosis
                
                Pregnancy considerations:
                - Generally safe to continue exercise with modifications
                - Avoid contact sports and supine exercises after first trimester
                - Stay hydrated and avoid overheating
                - Consult healthcare provider for personalized guidance
                - Pelvic floor exercises are important
                
                Nutrition specifics:
                - Folate important for reproductive health
                - Adequate calories to support menstrual function
                - Iron-rich foods especially important
                """,
                "keywords": ["women", "menstrual cycle", "hormones", "pregnancy", "bone density", "iron"]
            },
            {
                "topic": "Men's Health and Fitness",
                "category": "mens_health",
                "content": """
                Men have specific health considerations and typically different fitness responses.
                
                Testosterone considerations:
                - Peaks in late teens/early twenties, gradually declines
                - Strength training helps maintain healthy levels
                - Adequate sleep crucial (7-9 hours) for production
                - Stress management important (cortisol suppresses testosterone)
                - Healthy body fat percentage (10-18%) supports hormone health
                
                Common health risks for men:
                - Cardiovascular disease: leading cause of death
                - Type 2 diabetes: higher risk with age and inactivity
                - Prostate health: regular exercise may reduce risk
                - Mental health: men less likely to seek help
                
                Training characteristics:
                - Typically build muscle faster than women
                - Higher risk of injury due to overconfidence
                - Often neglect flexibility and mobility work
                - May focus too much on upper body, neglect legs
                - Benefit from including cardio for heart health
                
                Nutrition focus:
                - Generally higher caloric needs than women
                - Adequate protein for muscle maintenance
                - Omega-3 fatty acids for heart and brain health
                - Limit processed foods and excessive alcohol
                - Stay hydrated, especially with physical jobs
                
                Preventive health:
                - Regular screenings: blood pressure, cholesterol, diabetes
                - Prostate exams after age 50 (45 if family history)
                - Skin cancer checks
                - Mental health awareness and support
                """,
                "keywords": ["men", "testosterone", "cardiovascular", "prostate", "mental health", "muscle building"]
            }
        ]
        
        # Convert to HealthDocument objects
        for item in health_knowledge:
            doc = HealthDocument(
                content=item["content"],
                topic=item["topic"],
                category=item["category"],
                keywords=item["keywords"]
            )
            self.documents.append(doc)
    
    def _build_vector_index(self):
        """Build FAISS vector index for fast similarity search"""
        # Generate embeddings for all documents
        document_texts = [doc.content for doc in self.documents]
        embeddings = self.encoder.encode(document_texts)
        
        # Store embeddings in documents
        for i, doc in enumerate(self.documents):
            doc.embedding = embeddings[i]
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings.astype('float32'))
        
        self.embeddings = embeddings
        
        logger.info(f"Built vector index with {len(embeddings)} documents")
    
    def search_relevant_docs(self, query: str, k: int = 3) -> List[HealthDocument]:
        """Search for relevant documents using semantic similarity"""
        # Encode query
        query_embedding = self.encoder.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search similar documents
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Return relevant documents
        relevant_docs = []
        for i, score in zip(indices[0], scores[0]):
            if score > 0.3:  # Similarity threshold
                relevant_docs.append(self.documents[i])
        
        return relevant_docs
    
    def generate_response(self, query: str, user_profile: Dict = None, conversation_history: List = None) -> str:
        """Generate AI response using RAG with OpenAI GPT"""
        
        # Search for relevant health documents
        relevant_docs = self.search_relevant_docs(query, k=3)
        
        # Build context from relevant documents
        context = "\n\n".join([
            f"Health Topic: {doc.topic}\n{doc.content}" 
            for doc in relevant_docs
        ])
        
        # Build user context
        user_context = ""
        if user_profile:
            user_context = f"""
User Profile:
- Name: {user_profile.get('name', 'User')}
- Age: {user_profile.get('age', 'Unknown')}
- Gender: {user_profile.get('gender', 'Unknown')}
- Weight: {user_profile.get('weight', 'Unknown')} kg
- Height: {user_profile.get('height', 'Unknown')} cm
- BMI: {user_profile.get('bmi', 'Unknown')}
- Activity Level: {user_profile.get('activity_level', 'Unknown')}
- Primary Goal: {user_profile.get('goal', 'Unknown')}
- TDEE: {user_profile.get('tdee', 'Unknown')} calories/day
"""
        
        # Build conversation context
        recent_history = ""
        if conversation_history and len(conversation_history) > 0:
            recent_exchanges = conversation_history[-4:]  # Last 2 exchanges
            recent_history = "\n".join([
                f"{'User' if msg.get('role') == 'user' else 'BodyBae'}: {msg.get('content', '')}"
                for msg in recent_exchanges
            ])
        
        # Create system prompt
        system_prompt = f"""You are BodyBae, an expert AI health and fitness coach. You're knowledgeable, supportive, motivational, and provide evidence-based advice.

PERSONALITY:
- Warm, encouraging, and enthusiastic
- Use emojis appropriately to make responses engaging
- Celebrate user's efforts and progress
- Provide specific, actionable advice
- Always prioritize safety and recommend medical consultation when appropriate

GUIDELINES:
- Use the provided health knowledge context to give accurate advice
- Personalize responses based on user profile when available
- Keep responses concise but comprehensive (150-250 words)
- Include practical tips and specific recommendations
- If unsure about medical issues, recommend consulting healthcare professionals
- Reference user's goals and current stats when relevant

{user_context}

Recent Conversation:
{recent_history}

Relevant Health Knowledge:
{context}

User Question: {query}

Provide a helpful, personalized response as BodyBae:"""

        try:
            # Use OpenAI GPT for response generation
            if openai.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",  # Use gpt-4 if available
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                # Fallback to rule-based response
                return self._generate_fallback_response(query, user_profile, relevant_docs)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_fallback_response(query, user_profile, relevant_docs)
    
    def _generate_fallback_response(self, query: str, user_profile: Dict, relevant_docs: List[HealthDocument]) -> str:
        """Generate fallback response when AI fails"""
        query_lower = query.lower()
        name = user_profile.get('name', 'there') if user_profile else 'there'
        
        # Use relevant docs to enhance response
        if relevant_docs:
            doc_content = relevant_docs[0].content[:200] + "..."
            base_response = f"Hi {name}! Based on current health science: {doc_content}"
        else:
            base_response = f"Hi {name}! I'm here to help with your health and fitness journey."
        
        # Add specific advice based on query
        if any(word in query_lower for word in ['weight loss', 'lose weight']):
            return f"{base_response}\n\nFor weight loss, focus on creating a moderate caloric deficit through nutrition and exercise. Aim for 0.5-1 kg per week for sustainable results! 💪"
        
        elif any(word in query_lower for word in ['muscle', 'strength', 'build']):
            return f"{base_response}\n\nFor muscle building, prioritize progressive overload, adequate protein (1.6-2.2g per kg), and proper recovery. Consistency is key! 🏋️"
        
        elif any(word in query_lower for word in ['cardio', 'endurance', 'running']):
            return f"{base_response}\n\nFor cardiovascular health, aim for 150 minutes of moderate cardio weekly. Mix steady-state with intervals for best results! 🏃"
        
        else:
            return f"{base_response}\n\nI can help with workout plans, nutrition advice, goal setting, and motivation. What specific aspect of your health would you like to focus on today? 😊"

# Initialize RAG system
rag_system = EnhancedHealthRAG()

# In-memory storage (replace with database in production)
users_db = {}
conversations_db = {}

class HealthCalculator:
    """Enhanced health calculations and recommendations"""
    
    @staticmethod
    def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if gender.lower() in ['male', 'man', 'm']:
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        return round(bmr)
    
    @staticmethod
    def calculate_tdee(bmr: float, activity_level: str) -> float:
        """Calculate Total Daily Energy Expenditure"""
        multipliers = {
            'sedentary': 1.2,
            'lightly_active': 1.375,
            'moderately_active': 1.55,
            'very_active': 1.725,
            'extremely_active': 1.9
        }
        return round(bmr * multipliers.get(activity_level, 1.2))
    
    @staticmethod
    def calculate_bmi_detailed(weight: float, height: float) -> Dict:
        """Calculate BMI with detailed analysis"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            category = "Underweight"
            advice = "Consider focusing on healthy weight gain with nutrient-dense foods and strength training."
            health_risk = "Low"
            color = "#FFA726"
        elif bmi < 25:
            category = "Normal Weight"
            advice = "Excellent! Maintain your healthy weight with balanced nutrition and regular exercise."
            health_risk = "Very Low"
            color = "#66BB6A"
        elif bmi < 30:
            category = "Overweight"
            advice = "Consider a moderate weight loss approach with balanced nutrition and increased physical activity."
            health_risk = "Moderate"
            color = "#FFA726"
        else:
            category = "Obese"
            advice = "Consult with healthcare professionals for a comprehensive weight management plan."
            health_risk = "High"
            color = "#EF5350"
        
        return {
            "bmi": round(bmi, 1),
            "category": category,
            "advice": advice,
            "health_risk": health_risk,
            "color": color,
            "ideal_weight_range": {
                "min": round(18.5 * height_m * height_m, 1),
                "max": round(24.9 * height_m * height_m, 1)
            }
        }
    
    @staticmethod
    def get_calorie_targets(tdee: float, goal: str) -> Dict:
        """Get calorie targets based on goal"""
        targets = {
            "lose_weight": {
                "calories": max(1200, tdee - 500),
                "deficit": 500,
                "description": "Moderate deficit for sustainable weight loss"
            },
            "gain_muscle": {
                "calories": tdee + 300,
                "surplus": 300,
                "description": "Slight surplus to support muscle growth"
            },
            "maintain_weight": {
                "calories": tdee,
                "deficit": 0,
                "description": "Maintenance calories to stay at current weight"
            },
            "improve_endurance": {
                "calories": tdee + 100,
                "surplus": 100,
                "description": "Slight surplus to fuel training"
            },
            "general_fitness": {
                "calories": tdee,
                "deficit": 0,
                "description": "Maintenance calories for general health"
            }
        }
        
        return targets.get(goal, targets["general_fitness"])

# Flask Routes
@app.route('/api/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with RAG integration"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        user_id = data.get('user_id') or session.get('user_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user profile and conversation history
        user_profile = users_db.get(user_id, {}) if user_id else {}
        conversation_history = conversations_db.get(user_id, []) if user_id else []
        
        # Generate AI response using RAG
        response = rag_system.generate_response(
            query=message,
            user_profile=user_profile,
            conversation_history=conversation_history
        )
        
        # Store conversation
        if user_id:
            if user_id not in conversations_db:
                conversations_db[user_id] = []
            
            conversations_db[user_id].extend([
                {
                    'role': 'user',
                    'content': message,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                }
            ])
            
            # Keep only last 20 messages to prevent memory issues
            if len(conversations_db[user_id]) > 20:
                conversations_db[user_id] = conversations_db[user_id][-20:]
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Error processing your message'}), 500

@app.route('/api/profile', methods=['POST'])
def save_profile():
    """Save or update user profile with enhanced calculations"""
    try:
        data = request.json
        user_id = str(uuid.uuid4())
        
        # Validate required fields
        required_fields = ['name', 'age', 'height', 'weight', 'gender', 'activity_level', 'goal']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Calculate health metrics
        bmr = HealthCalculator.calculate_bmr(
            data['weight'], data['height'], data['age'], data['gender']
        )
        tdee = HealthCalculator.calculate_tdee(bmr, data['activity_level'])
        bmi_info = HealthCalculator.calculate_bmi_detailed(data['weight'], data['height'])
        calorie_targets = HealthCalculator.get_calorie_targets(tdee, data['goal'])
        
        # Create user profile
        user_profile = {
            'user_id': user_id,
            'name': data['name'],
            'age': int(data['age']),
            'height': float(data['height']),
            'weight': float(data['weight']),
            'gender': data['gender'],
            'activity_level': data['activity_level'],
            'goal': data['goal'],
            'bmr': bmr,
            'tdee': tdee,
            'bmi_info': bmi_info,
            'calorie_targets': calorie_targets,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Store user profile
        users_db[user_id] = user_profile
        session['user_id'] = user_id
        
        # Initialize conversation
        if user_id not in conversations_db:
            conversations_db[user_id] = []
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'profile': user_profile,
            'message': f"Welcome {data['name']}! Your health profile has been created successfully."
        })
        
    except Exception as e:
        logger.error(f"Profile save error: {e}")
        return jsonify({'error': 'Error saving profile'}), 500

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """Get user profile"""
    try:
        profile = users_db.get(user_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        return jsonify({
            'success': True,
            'profile': profile
        })
        
    except Exception as e:
        logger.error(f"Profile get error: {e}")
        return jsonify({'error': 'Error retrieving profile'}), 500

@app.route('/api/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    """Get personalized recommendations based on user profile"""
    try:
        profile = users_db.get(user_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Generate personalized recommendations
        recommendations = generate_personalized_recommendations(profile)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
        
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify({'error': 'Error generating recommendations'}), 500

def generate_personalized_recommendations(profile: Dict) -> Dict:
    """Generate personalized health recommendations"""
    
    goal = profile.get('goal', 'general_fitness')
    age = profile.get('age', 25)
    bmi = profile.get('bmi_info', {}).get('bmi', 25)
    activity_level = profile.get('activity_level', 'moderately_active')
    
    recommendations = {
        'workout': [],
        'nutrition': [],
        'lifestyle': [],
        'daily_tips': []
    }
    
    # Workout recommendations based on goal
    if goal == 'lose_weight':
        recommendations['workout'] = [
            "🏃 Aim for 150 minutes of moderate cardio weekly",
            "🏋️ Include 2-3 strength training sessions to preserve muscle",
            "🔥 Try HIIT workouts 1-2 times per week for efficient fat burning",
            "🚶 Add daily walks to increase overall activity"
        ]
    elif goal == 'gain_muscle':
        recommendations['workout'] = [
            "🏋️ Focus on compound movements: squats, deadlifts, bench press",
            "📈 Progressive overload: gradually increase weight each week",
            "💪 Train each muscle group 2-3 times per week",
            "⏰ Rest 48-72 hours between training same muscle groups"
        ]
    elif goal == 'improve_endurance':
        recommendations['workout'] = [
            "🏃 Build aerobic base with 3-4 steady-state cardio sessions",
            "⚡ Add interval training 1-2 times per week",
            "🚴 Cross-train with different activities to prevent overuse",
            "📊 Track heart rate to train in optimal zones"
        ]
    
    # Nutrition recommendations
    calorie_target = profile.get('calorie_targets', {}).get('calories', 2000)
    protein_target = round(profile.get('weight', 70) * 1.6)
    
    recommendations['nutrition'] = [
        f"🎯 Target {calorie_target} calories daily for your {goal.replace('_', ' ')} goal",
        f"🥩 Aim for {protein_target}g protein daily (20-30g per meal)",
        "🥗 Fill half your plate with vegetables at each meal",
        "💧 Drink 8-10 glasses of water daily, more during exercise"
    ]
    
    # Age-specific recommendations
    if age > 50:
        recommendations['lifestyle'].extend([
            "🦴 Include weight-bearing exercises for bone health",
            "🧘 Add balance and flexibility training",
            "👥 Consider group fitness classes for social support"
        ])
    elif age < 25:
        recommendations['lifestyle'].extend([
            "🏃 Take advantage of higher recovery capacity",
            "📚 Learn proper form and technique early",
            "🎯 Focus on building lifelong healthy habits"
        ])
    
    # Activity level adjustments
    if 'sedentary' in activity_level:
        recommendations['lifestyle'].extend([
            "⏰ Start with 10-15 minute walks daily",
            "📱 Set hourly reminders to move",
            "🪑 Consider a standing desk if you work sitting"
        ])
    
    # Daily tips based on profile
    recommendations['daily_tips'] = [
        f"😴 Aim for 7-9 hours of sleep for optimal recovery",
        f"🍎 Plan your meals ahead to stay on track with nutrition",
        f"📊 Track your progress weekly, not daily",
        f"🎉 Celebrate small wins along your journey!"
    ]
    
    return recommendations

@app.route('/api/health-stats/<user_id>', methods=['GET'])
def get_health_stats(user_id):
    """Get comprehensive health statistics"""
    try:
        profile = users_db.get(user_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Calculate additional health metrics
        stats = {
            'basic_metrics': {
                'bmi': profile['bmi_info']['bmi'],
                'bmi_category': profile['bmi_info']['category'],
                'bmr': profile['bmr'],
                'tdee': profile['tdee']
            },
            'targets': profile['calorie_targets'],
            'ideal_weight_range': profile['bmi_info']['ideal_weight_range'],
            'health_risk': profile['bmi_info']['health_risk'],
            'progress_tracking': {
                'weight_goal': calculate_weight_goal(profile),
                'timeline': calculate_realistic_timeline(profile),
                'weekly_target': calculate_weekly_targets(profile)
            }
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Health stats error: {e}")
        return jsonify({'error': 'Error calculating health stats'}), 500

def calculate_weight_goal(profile: Dict) -> Dict:
    """Calculate weight goal based on user's objective"""
    current_weight = profile['weight']
    goal = profile['goal']
    bmi_info = profile['bmi_info']
    
    if goal == 'lose_weight':
        # Target weight for healthy BMI (around 22)
        height_m = profile['height'] / 100
        target_weight = 22 * height_m * height_m
        weight_to_lose = max(0, current_weight - target_weight)
        return {
            'target_weight': round(target_weight, 1),
            'weight_change': round(-weight_to_lose, 1),
            'description': f"Target healthy weight range"
        }
    elif goal == 'gain_muscle':
        # Modest weight gain for muscle building
        target_weight = current_weight + 3  # 3kg muscle gain goal
        return {
            'target_weight': round(target_weight, 1),
            'weight_change': 3,
            'description': "Muscle building target"
        }
    else:
        return {
            'target_weight': current_weight,
            'weight_change': 0,
            'description': "Maintain current weight"
        }

def calculate_realistic_timeline(profile: Dict) -> Dict:
    """Calculate realistic timeline for goals"""
    goal = profile['goal']
    
    timelines = {
        'lose_weight': {
            'weeks': 12,
            'description': "Healthy weight loss takes time - expect visible changes in 4-6 weeks"
        },
        'gain_muscle': {
            'weeks': 16,
            'description': "Muscle building is gradual - noticeable gains in 8-12 weeks"
        },
        'improve_endurance': {
            'weeks': 8,
            'description': "Cardiovascular improvements visible in 4-6 weeks"
        },
        'general_fitness': {
            'weeks': 12,
            'description': "Overall fitness improvements in 6-8 weeks"
        },
        'maintain_weight': {
            'weeks': 52,
            'description': "Focus on consistency and long-term habits"
        }
    }
    
    return timelines.get(goal, timelines['general_fitness'])

def calculate_weekly_targets(profile: Dict) -> Dict:
    """Calculate weekly targets"""
    goal = profile['goal']
    
    if goal == 'lose_weight':
        return {
            'weight_change': -0.5,
            'workouts': 4,
            'cardio_minutes': 150,
            'strength_sessions': 2
        }
    elif goal == 'gain_muscle':
        return {
            'weight_change': 0.25,
            'workouts': 4,
            'cardio_minutes': 75,
            'strength_sessions': 3
        }
    else:
        return {
            'weight_change': 0,
            'workouts': 3,
            'cardio_minutes': 150,
            'strength_sessions': 2
        }

@app.route('/api/health-check', methods=['GET'])
def health_check():
    """Application health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'services': {
            'rag_system': 'active',
            'embeddings_model': 'loaded',
            'vector_index': f'{len(rag_system.documents)} documents',
            'active_users': len(users_db)
        }
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting Enhanced BodyBae.ai...")
    print(f"🤖 RAG System: {len(rag_system.documents)} health documents loaded")
    print(f"🧠 AI Model: {'OpenAI GPT' if openai.api_key else 'Fallback responses'}")
    print(f"📡 Embeddings: {rag_system.encoder}")
    print(f"🌐 Running on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)