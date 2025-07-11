from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import json
import uuid
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import gc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Force CPU usage for free tier
torch.set_num_threads(1)
os.environ['OMP_NUM_THREADS'] = '1'

# Route to serve the frontend
@app.route('/')
def index():
    try:
        with open('bodybae_frontend.html', 'r') as f:
            return f.read()
    except:
        return "Frontend file not found.", 404

# In-memory storage
users_db = {}
conversations_db = {}

class LightweightLLMRAG:
    """Lightweight LLM + RAG system optimized for free tier"""
    
    def __init__(self):
        logger.info("Initializing lightweight LLM + RAG system...")
        
        # Use a small, efficient model for embeddings
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize small language model (using GPT-2 small for free tier)
        self.tokenizer = AutoTokenizer.from_pretrained('gpt2')
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Use text generation pipeline for efficiency
        self.generator = pipeline(
            'text-generation',
            model='gpt2',
            tokenizer=self.tokenizer,
            device=-1,  # Force CPU
            max_new_tokens=150,
            temperature=0.8,
            do_sample=True,
            top_p=0.9
        )
        
        # Initialize knowledge base
        self.documents = []
        self.document_embeddings = None
        self.index = None
        
        # Build knowledge base
        self._build_health_knowledge_base()
        self._create_embeddings()
        
        logger.info(f"RAG system initialized with {len(self.documents)} documents")
        
        # Clear memory
        gc.collect()
    
    def _build_health_knowledge_base(self):
        """Build comprehensive health knowledge base"""
        
        self.knowledge_base = [
            {
                "id": "weight_loss_basics",
                "title": "Weight Loss Fundamentals",
                "content": "Weight loss requires a caloric deficit. Safe weight loss is 0.5-1kg per week. Create a 500-750 calorie deficit daily through diet and exercise. Prioritize protein intake at 1.6g per kg body weight to preserve muscle. Include strength training 2-3 times per week. Stay hydrated with 35-40ml water per kg body weight. Get 7-9 hours of sleep for optimal hormone balance.",
                "keywords": ["weight loss", "caloric deficit", "diet", "fat loss"]
            },
            {
                "id": "muscle_building",
                "title": "Muscle Building Science",
                "content": "Muscle growth requires progressive overload, adequate protein, and recovery. Consume 1.8-2.2g protein per kg body weight. Create a slight caloric surplus of 200-500 calories. Train each muscle group 2-3 times per week with 10-20 sets total. Focus on compound movements: squats, deadlifts, bench press, rows. Allow 48-72 hours rest between training same muscles. Sleep 7-9 hours for growth hormone release.",
                "keywords": ["muscle", "gains", "hypertrophy", "strength", "protein"]
            },
            {
                "id": "nutrition_basics",
                "title": "Nutrition Guidelines",
                "content": "Balanced nutrition includes all macronutrients. Protein: 10-35% of calories for tissue repair. Carbohydrates: 45-65% for energy. Fats: 20-35% for hormones. Eat whole foods: vegetables, fruits, lean proteins, whole grains. Meal timing: protein every 3-4 hours, pre-workout carbs, post-workout protein plus carbs. Stay hydrated throughout the day.",
                "keywords": ["nutrition", "diet", "macros", "meal", "food"]
            },
            {
                "id": "cardio_training",
                "title": "Cardiovascular Training",
                "content": "Cardio improves heart health and endurance. For fat loss: 150-300 minutes moderate intensity weekly. For endurance: mix steady-state with intervals. LISS: 65-75% max heart rate for fat burning. HIIT: 85-95% max heart rate for fitness. Start gradually and progress slowly. Include variety: running, cycling, swimming, rowing.",
                "keywords": ["cardio", "running", "endurance", "HIIT", "aerobic"]
            },
            {
                "id": "workout_programming",
                "title": "Workout Programming",
                "content": "Effective workouts need structure. Beginners: full body 3x per week. Intermediate: upper/lower split 4x per week. Advanced: push/pull/legs 6x per week. Include compound movements first, then isolation. Rep ranges: 1-5 for strength, 6-12 for hypertrophy, 12+ for endurance. Progressive overload by increasing weight, reps, or sets weekly.",
                "keywords": ["workout", "training", "exercise", "program", "routine"]
            },
            {
                "id": "meal_planning",
                "title": "Meal Planning Strategies",
                "content": "Successful meal planning saves time and supports goals. Prep proteins in bulk: chicken, fish, tofu. Pre-cut vegetables for easy cooking. Cook grains in batches: rice, quinoa, oats. Portion meals based on calorie targets. Keep healthy snacks ready: Greek yogurt, nuts, fruits. Plan 3-4 days at a time for freshness.",
                "keywords": ["meal prep", "meal plan", "cooking", "recipes", "food prep"]
            },
            {
                "id": "recovery_sleep",
                "title": "Recovery and Sleep",
                "content": "Recovery is when adaptation occurs. Sleep 7-9 hours for muscle growth and fat loss. Maintain consistent sleep schedule. Create cool, dark environment. Avoid screens 1 hour before bed. Active recovery: light walking, yoga, swimming. Manage stress through meditation or breathing exercises. Proper recovery prevents overtraining and injury.",
                "keywords": ["sleep", "recovery", "rest", "fatigue", "stress"]
            },
            {
                "id": "supplements",
                "title": "Supplement Guidelines",
                "content": "Supplements support but don't replace good nutrition. Protein powder helps meet protein targets. Creatine monohydrate: 5g daily for strength and muscle. Vitamin D: 1000-2000 IU if deficient. Omega-3: 1-2g daily for inflammation. Caffeine: 100-400mg for performance. Always prioritize whole foods first.",
                "keywords": ["supplements", "protein powder", "creatine", "vitamins"]
            },
            {
                "id": "hydration",
                "title": "Hydration Science",
                "content": "Proper hydration is essential for performance. Drink 35-40ml per kg body weight daily. Add 500-750ml per hour of exercise. Monitor urine color: pale yellow indicates good hydration. Include electrolytes during intense exercise. Signs of dehydration: fatigue, headaches, dark urine. Hydration improves energy, performance, and recovery.",
                "keywords": ["water", "hydration", "drink", "fluid", "electrolytes"]
            },
            {
                "id": "motivation_mindset",
                "title": "Motivation and Mindset",
                "content": "Consistency beats perfection. Set SMART goals: specific, measurable, achievable, relevant, time-bound. Track progress beyond the scale: photos, measurements, performance. Celebrate small wins weekly. Find accountability partners. Focus on habits, not outcomes. Remember why you started. Progress isn't linear - expect ups and downs.",
                "keywords": ["motivation", "mindset", "goals", "consistency", "habits"]
            }
        ]
        
        # Convert to document format
        for item in self.knowledge_base:
            self.documents.append({
                'id': item['id'],
                'title': item['title'],
                'content': item['content'],
                'full_text': f"{item['title']}. {item['content']}"
            })
    
    def _create_embeddings(self):
        """Create embeddings for all documents"""
        # Extract texts
        texts = [doc['full_text'] for doc in self.documents]
        
        # Create embeddings
        logger.info("Creating document embeddings...")
        self.document_embeddings = self.encoder.encode(texts, convert_to_numpy=True)
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(self.document_embeddings, axis=1, keepdims=True)
        self.document_embeddings = self.document_embeddings / norms
        
        # Create FAISS index
        dimension = self.document_embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product = cosine similarity for normalized vectors
        self.index.add(self.document_embeddings.astype('float32'))
        
        logger.info(f"Created FAISS index with {len(self.documents)} documents")
    
    def search_documents(self, query: str, k: int = 3) -> List[Dict]:
        """Search for relevant documents using semantic similarity"""
        # Encode query
        query_embedding = self.encoder.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding.astype('float32'), k)
        
        # Get relevant documents
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if score > 0.3:  # Similarity threshold
                results.append({
                    'document': self.documents[idx],
                    'score': float(score)
                })
        
        return results
    
    def generate_response(self, query: str, user_profile: Optional[Dict] = None) -> str:
        """Generate response using RAG + LLM"""
        
        # Search for relevant documents
        relevant_docs = self.search_documents(query, k=3)
        
        # Build context from retrieved documents
        context_parts = []
        for result in relevant_docs:
            doc = result['document']
            context_parts.append(f"{doc['title']}: {doc['content']}")
        
        context = "\n\n".join(context_parts) if context_parts else "General fitness information."
        
        # Build user context
        user_context = ""
        if user_profile:
            user_context = f"""
User Profile:
- Name: {user_profile.get('name', 'User')}
- Goal: {user_profile.get('goal', 'general fitness').replace('_', ' ')}
- Weight: {user_profile.get('weight', 'unknown')}kg
- TDEE: {user_profile.get('tdee', 'unknown')} calories
"""
        
        # Create prompt for LLM
        prompt = f"""You are BodyBae, a friendly AI fitness coach. Answer based on this context:

{context}

{user_context}

User Question: {query}

Provide a helpful, personalized response (keep it concise):
BodyBae: """
        
        try:
            # Generate response with GPT-2
            response = self.generator(
                prompt,
                max_new_tokens=150,
                temperature=0.8,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract generated text
            generated = response[0]['generated_text']
            
            # Extract only the response part (after "BodyBae: ")
            if "BodyBae: " in generated:
                answer = generated.split("BodyBae: ")[-1].strip()
            else:
                answer = generated.split("\n")[-1].strip()
            
            # Clean up response
            answer = answer.replace("User Question:", "").strip()
            
            # Ensure response is not empty
            if not answer or len(answer) < 10:
                answer = self._get_fallback_response(query, relevant_docs, user_profile)
            
            return answer
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return self._get_fallback_response(query, relevant_docs, user_profile)
    
    def _get_fallback_response(self, query: str, relevant_docs: List[Dict], user_profile: Optional[Dict]) -> str:
        """Fallback response when LLM fails"""
        name = user_profile.get('name', 'there') if user_profile else 'there'
        
        if relevant_docs:
            doc = relevant_docs[0]['document']
            return f"Hi {name}! Based on your question about {query}, here's what I found: {doc['content'][:200]}..."
        
        return f"Hi {name}! I can help with workout plans, nutrition advice, and fitness questions. What specific aspect of your health journey would you like to discuss?"

# Initialize the LLM + RAG system
logger.info("Starting LLM + RAG initialization...")
llm_rag = LightweightLLMRAG()
logger.info("LLM + RAG system ready!")

class HealthCalculator:
    """Health calculations"""
    
    @staticmethod
    def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
        """Calculate Basal Metabolic Rate"""
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
    def calculate_bmi(weight: float, height: float) -> dict:
        """Calculate BMI"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal Weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"
        
        return {"bmi": round(bmi, 1), "category": category}

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint using LLM + RAG"""
    try:
        data = request.json
        message = data.get('message', '').strip()
        user_id = data.get('user_id') or session.get('user_id')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get user profile
        user_profile = users_db.get(user_id) if user_id else None
        
        # Generate response using LLM + RAG
        response = llm_rag.generate_response(message, user_profile)
        
        # Store conversation
        if user_id:
            if user_id not in conversations_db:
                conversations_db[user_id] = []
            
            conversations_db[user_id].extend([
                {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
            ])
            
            # Keep only last 10 messages (memory optimization)
            if len(conversations_db[user_id]) > 10:
                conversations_db[user_id] = conversations_db[user_id][-10:]
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({'error': 'Error processing message'}), 500

@app.route('/api/profile', methods=['POST'])
def save_profile():
    """Save user profile"""
    try:
        data = request.json
        user_id = str(uuid.uuid4())
        
        # Validate fields
        required = ['name', 'age', 'height', 'weight', 'gender', 'activity_level', 'goal']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Calculate metrics
        bmr = HealthCalculator.calculate_bmr(
            float(data['weight']), 
            float(data['height']), 
            int(data['age']), 
            data['gender']
        )
        tdee = HealthCalculator.calculate_tdee(bmr, data['activity_level'])
        bmi_info = HealthCalculator.calculate_bmi(float(data['weight']), float(data['height']))
        
        # Create profile
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
            'bmi': bmi_info['bmi'],
            'bmi_category': bmi_info['category'],
            'created_at': datetime.now().isoformat()
        }
        
        # Store profile
        users_db[user_id] = user_profile
        session['user_id'] = user_id
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'profile': user_profile,
            'message': f"Welcome {data['name']}! I'm BodyBae, your AI fitness coach. I'll use RAG to provide personalized advice for your {data['goal'].replace('_', ' ')} journey!"
        })
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({'error': 'Error saving profile'}), 500

@app.route('/api/health-check', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0',
        'features': {
            'llm': 'GPT-2 (lightweight)',
            'embeddings': 'all-MiniLM-L6-v2',
            'vector_search': 'FAISS',
            'documents': len(llm_rag.documents)
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("🌿 BodyBae.ai - LLM + RAG Backend")
    print("🤖 Language Model: GPT-2 (optimized for free tier)")
    print("🔍 RAG System: FAISS + Sentence Transformers")
    print(f"📚 Knowledge Base: {len(llm_rag.documents)} health documents")
    print(f"📡 Running on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=False)  # debug=False for production