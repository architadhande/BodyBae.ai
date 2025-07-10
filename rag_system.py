Previous conversation: {chat_history}

Current question: {question}

Provide a helpful, encouraging response as BodyBae:"""

        # Create retriever with enhanced search
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={
                "k": 4,  # Number of documents to retrieve
                "fetch_k": 8,  # Number of documents to fetch before MMR
                "lambda_mult": 0.7  # Diversity parameter
            }
        )
        
        # For now, we'll use a simple template-based approach
        # In production, you might want to fine-tune a model or use a more sophisticated approach
        self.retriever = retriever
        
        logger.info("Conversation chain setup complete")
    
    def generate_health_response(self, question: str, user_profile: Dict = None, context: str = "") -> str:
        """Generate a health-focused response using RAG"""
        try:
            # Retrieve relevant documents
            relevant_docs = self.retriever.get_relevant_documents(question)
            
            # Combine retrieved context
            retrieved_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Add user profile context if available
            profile_context = ""
            if user_profile:
                profile_context = f"""
                User Profile:
                - Name: {user_profile.get('name', 'User')}
                - Age: {user_profile.get('age', 'Unknown')}
                - Sex: {user_profile.get('sex', 'Unknown')}
                - Weight: {user_profile.get('weight', 'Unknown')} kg
                - Height: {user_profile.get('height', 'Unknown')} cm
                - BMI: {user_profile.get('bmi', 'Unknown')}
                - Activity Level: {user_profile.get('activity', 'Unknown')}
                """
            
            # Create comprehensive prompt
            full_prompt = f"""As BodyBae, a supportive AI health assistant, provide helpful advice based on this information:

{profile_context}

Relevant Health Information:
{retrieved_context}

User Question: {question}

Respond as BodyBae with:
1. A warm, encouraging greeting if this is the start of conversation
2. Specific, actionable advice based on the user's profile and question
3. Practical tips they can implement
4. Motivation and encouragement
5. If it's a medical concern, recommend consulting healthcare professionals

Keep your response conversational, helpful, and motivating (max 200 words):"""

            # Generate response using the health LLM
            response = self.health_llm.generate_response(full_prompt, max_length=200)
            
            # Post-process response to ensure it's helpful
            if not response or len(response.strip()) < 20:
                response = self.get_fallback_response(question, user_profile)
            
            # Store in memory
            self.memory.save_context({"input": question}, {"output": response})
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating health response: {e}")
            return self.get_fallback_response(question, user_profile)
    
    def get_fallback_response(self, question: str, user_profile: Dict = None) -> str:
        """Provide fallback responses when AI generation fails"""
        
        question_lower = question.lower()
        name = user_profile.get('name', 'there') if user_profile else 'there'
        
        # Rule-based fallback responses
        if any(word in question_lower for word in ['weight loss', 'lose weight', 'losing weight']):
            return f"Hi {name}! For healthy weight loss, focus on creating a moderate caloric deficit (500-750 calories daily), combine cardio and strength training, eat plenty of protein, and stay hydrated. Remember, sustainable weight loss is 0.5-1 kg per week. You've got this! 💪"
        
        elif any(word in question_lower for word in ['muscle', 'gain muscle', 'build muscle']):
            return f"Great question, {name}! To build muscle, focus on progressive overload in your workouts, eat 1.6-2.2g protein per kg body weight daily, get 7-9 hours of sleep, and be patient - muscle growth takes time. Compound exercises like squats and deadlifts are your best friends! 🏋️‍♀️"
        
        elif any(word in question_lower for word in ['workout', 'exercise', 'training']):
            return f"Hi {name}! For effective workouts, aim for 150 minutes of moderate cardio per week plus 2-3 strength training sessions. Start with what you can handle and gradually increase intensity. Consistency beats perfection every time! 🌟"
        
        elif any(word in question_lower for word in ['nutrition', 'diet', 'food', 'eat']):
            return f"Nutrition is so important, {name}! Focus on whole foods: lean proteins, vegetables, fruits, whole grains, and healthy fats. Eat balanced meals, stay hydrated, and don't forget that small, sustainable changes lead to big results over time! 🥗"
        
        elif any(word in question_lower for word in ['motivation', 'motivated', 'give up']):
            return f"I believe in you, {name}! 🌟 Remember why you started this journey. Every small step counts, progress isn't always linear, and setbacks are just setups for comebacks. You're stronger than you think and capable of amazing things!"
        
        else:
            return f"Hi {name}! I'm here to help with your health and fitness journey. I can assist with workout plans, nutrition advice, weight management, and motivation. What specific aspect of your health would you like to focus on today? 😊"
    
    def get_personalized_tips(self, user_profile: Dict) -> List[str]:
        """Generate personalized tips based on user profile"""
        
        tips = []
        
        if not user_profile:
            return ["Stay hydrated!", "Move your body daily!", "Eat colorful foods!", "Get enough sleep!"]
        
        bmi = user_profile.get('bmi', 0)
        age = user_profile.get('age', 25)
        sex = user_profile.get('sex', '')
        activity = user_profile.get('activity', '')
        
        # BMI-based tips
        if bmi < 18.5:
            tips.append("Focus on nutrient-dense, calorie-rich foods to support healthy weight gain.")
        elif bmi > 25:
            tips.append("Consider incorporating more vegetables and lean proteins while creating a modest caloric deficit.")
        else:
            tips.append("Great job maintaining a healthy weight! Focus on building strength and endurance.")
        
        # Age-based tips
        if age < 25:
            tips.append("Your metabolism is naturally higher - focus on building healthy habits that will last a lifetime!")
        elif age > 40:
            tips.append("Include flexibility and mobility work to maintain joint health as you age.")
        
        # Activity-based tips
        if 'sedentary' in activity.lower():
            tips.append("Start with just 10 minutes of walking daily - small steps lead to big changes!")
        elif 'very_active' in activity.lower():
            tips.append("Don't forget rest days! Recovery is when your body gets stronger.")
        
        # General tips
        tips.extend([
            "Aim for 7-9 hours of quality sleep each night.",
            "Stay hydrated - drink water throughout the day!",
            "Celebrate small wins along your journey! 🎉"
        ])
        
        return tips[:4]  # Return top 4 tips
    
    def analyze_progress(self, activity_log: List[Dict]) -> Dict:
        """Analyze user's activity log and provide insights"""
        
        if not activity_log:
            return {
                "message": "Start logging your activities to get personalized insights!",
                "recommendations": ["Log your first workout!", "Track your meals!", "Record your weight!"]
            }
        
        # Analyze different types of activities
        workouts = [log for log in activity_log if log.get('type') == 'workout']
        meals = [log for log in activity_log if log.get('type') == 'meal']
        weights = [log for log in activity_log if log.get('type') == 'weight']
        
        analysis = {
            "workout_frequency": len(workouts),
            "meal_tracking": len(meals),
            "weight_entries": len(weights),
            "total_activities": len(activity_log)
        }
        
        # Generate insights
        insights = []
        recommendations = []
        
        if len(workouts) >= 3:
            insights.append("Great job staying active! You're building a consistent exercise habit.")
        elif len(workouts) > 0:
            insights.append("You're off to a good start with exercise!")
            recommendations.append("Try to aim for 3-4 workouts per week for optimal results.")
        else:
            recommendations.append("Start with 2-3 workouts per week - consistency is key!")
        
        if len(weights) >= 2:
            # Calculate weight trend
            first_weight = weights[0].get('weight', 0)
            last_weight = weights[-1].get('weight', 0)
            change = last_weight - first_weight
            
            if abs(change) < 0.5:
                insights.append("Your weight is stable - great for maintenance goals!")
            elif change > 0:
                insights.append(f"You've gained {change:.1f}kg - perfect if that's your goal!")
            else:
                insights.append(f"You've lost {abs(change):.1f}kg - excellent progress!")
        
        analysis.update({
            "insights": insights,
            "recommendations": recommendations,
            "message": " ".join(insights) if insights else "Keep tracking your progress!"
        })
        
        return analysis

# Integration functions for Flask app
def create_enhanced_rag_system():
    """Create and return an enhanced RAG system instance"""
    try:
        # Use a good free model for health conversations
        # Options: microsoft/DialoGPT-medium, facebook/blenderbot-400M-distill, google/flan-t5-base
        rag_system = EnhancedHealthRAGSystem("microsoft/DialoGPT-medium")
        logger.info("Enhanced RAG system created successfully")
        return rag_system
    except Exception as e:
        logger.error(f"Error creating enhanced RAG system: {e}")
        return None

def integrate_enhanced_rag_with_flask_app(app, rag_system):
    """Integrate enhanced RAG system with Flask app"""
    
    @app.route('/enhanced_chat', methods=['POST'])
    def enhanced_chat():
        """Enhanced chat endpoint with RAG and conversation memory"""
        data = request.json
        question = data.get('message', '')
        user_profile = data.get('userProfile', {})
        activity_log = data.get('activityLog', [])
        
        if not question:
            return jsonify({'error': 'Message is required'}), 400
        
        if not rag_system:
            return jsonify({'error': 'RAG system not available'}), 500
        
        try:
            # Generate personalized response
            response = rag_system.generate_health_response(
                question=question,
                user_profile=user_profile
            )
            
            # Get personalized tips
            tips = rag_system.get_personalized_tips(user_profile)
            
            # Analyze progress if activity log provided
            progress_analysis = rag_system.analyze_progress(activity_log)
            
            return jsonify({
                'response': response,
                'personalized_tips': tips,
                'progress_analysis': progress_analysis,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error in enhanced chat: {e}")
            return jsonify({'error': 'Error processing your message'}), 500
    
    @app.route('/get_tips', methods=['POST'])
    def get_personalized_tips():
        """Get personalized tips based on user profile"""
        data = request.json
        user_profile = data.get('userProfile', {})
        
        if not rag_system:
            return jsonify({'error': 'RAG system not available'}), 500
        
        try:
            tips = rag_system.get_personalized_tips(user_profile)
            return jsonify({'tips': tips})
        except Exception as e:
            logger.error(f"Error getting tips: {e}")
            return jsonify({'error': 'Error getting personalized tips'}), 500

# Example usage
if __name__ == "__main__":
    # Test the enhanced RAG system
    rag = create_enhanced_rag_system()
    if rag:
        test_profile = {
            'name': 'Alex',
            'age': 28,
            'sex': 'male',
            'weight': 75,
            'height': 175,
            'bmi': 24.5,
            'activity': 'moderately_active'
        }
        
        test_questions = [
            "How much protein do I need daily?",
            "What's the best workout routine for muscle building?",
            "I'm feeling unmotivated, can you help?",
            "How can I improve my sleep quality?"
        ]
        
        print("Testing Enhanced RAG System:")
        print("=" * 50)
        
        for question in test_questions:
            print(f"\nQ: {question}")
            response = rag.generate_health_response(question, test_profile)
            print(f"A: {response}")
            print("-" * 30)
        
        # Test personalized tips
        tips = rag.get_personalized_tips(test_profile)
        print(f"\nPersonalized Tips: {tips}")
    else:
        print("Failed to create RAG system")Previous conversation: {chat_history}                        input_ids,
                        max_length=input_ids.shape[-1] + max_length,
                        num_beams=3,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        no_repeat_ngram_size=2
                    )
                
                response = self.tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
                return response.strip()
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm having trouble generating a response right now. Please try rephrasing your question."

class EnhancedHealthRAGSystem:
    """Enhanced RAG system with Hugging Face models and better health knowledge"""
    
    def __init__(self, hf_model_name: str = "microsoft/DialoGPT-medium"):
        """Initialize the enhanced RAG system"""
        
        # Initialize embeddings (free Hugging Face model)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",  # Free, fast, good quality
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
        )
        
        # Initialize the health-focused LLM
        self.health_llm = HuggingFaceHealthLLM(hf_model_name)
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Remember last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        
        self.vectorstore = None
        self.conversation_chain = None
        
        # Enhanced health knowledge base
        self.setup_enhanced_knowledge_base()
        
    def setup_enhanced_knowledge_base(self):
        """Set up comprehensive health knowledge base"""
        
        # Expanded health knowledge with more detailed information
        health_knowledge = [
            {
                "topic": "Weight Loss Fundamentals",
                "content": """
                Weight loss occurs when you burn more calories than you consume (caloric deficit). Here are evidence-based principles:
                
                CALORIC DEFICIT:
                - Safe deficit: 500-750 calories per day for 0.5-1 kg weight loss per week
                - Calculate your TDEE (Total Daily Energy Expenditure) first
                - Track calories using apps like MyFitnessPal or Cronometer
                
                MACRONUTRIENT BALANCE:
                - Protein: 0.8-1.2g per kg body weight (helps preserve muscle)
                - Carbohydrates: 45-65% of total calories (choose complex carbs)
                - Fats: 20-35% of total calories (essential for hormone production)
                
                EFFECTIVE STRATEGIES:
                - Meal prep and portion control
                - Eat protein with every meal
                - Fill half your plate with vegetables
                - Drink water before meals
                - Get 7-9 hours of sleep
                - Manage stress (cortisol affects weight)
                - Be patient - healthy weight loss takes time
                
                EXERCISE COMBINATION:
                - Cardio: 150 minutes moderate or 75 minutes vigorous per week
                - Strength training: 2-3 times per week (prevents muscle loss)
                - HIIT: 1-2 times per week for efficiency
                """
            },
            {
                "topic": "Muscle Building and Strength",
                "content": """
                Building muscle requires progressive overload, adequate nutrition, and proper recovery.
                
                PROGRESSIVE OVERLOAD PRINCIPLES:
                - Gradually increase weight, reps, or sets over time
                - Track your workouts to ensure progression
                - Focus on compound movements: squats, deadlifts, bench press, rows
                - Train each muscle group 2-3 times per week
                
                NUTRITION FOR MUSCLE GROWTH:
                - Protein: 1.6-2.2g per kg body weight daily
                - Eat protein every 3-4 hours throughout the day
                - Post-workout: 20-40g protein within 2 hours
                - Slight caloric surplus: 200-500 calories above maintenance
                - Leucine-rich foods: eggs, chicken, fish, dairy, legumes
                
                OPTIMAL TRAINING PROGRAM:
                - 3-4 strength training sessions per week
                - 6-20 sets per muscle group per week
                - Rep ranges: 6-12 for hypertrophy, 1-5 for strength
                - Rest 48-72 hours between training same muscle groups
                
                RECOVERY ESSENTIALS:
                - Sleep: 7-9 hours for muscle protein synthesis
                - Hydration: 35-40ml per kg body weight daily
                - Stress management: chronic stress impairs muscle growth
                - Active recovery: light movement on rest days
                """
            },
            {
                "topic": "Cardiovascular Health and Endurance",
                "content": """
                Cardiovascular fitness is crucial for heart health, endurance, and overall wellbeing.
                
                CARDIO BENEFITS:
                - Strengthens heart and improves circulation
                - Reduces blood pressure and cholesterol
                - Improves insulin sensitivity
                - Enhances mood through endorphin release
                - Increases lung capacity and oxygen efficiency
                
                TYPES OF CARDIO:
                - LISS (Low Intensity Steady State): Walking, easy cycling, swimming
                - MISS (Moderate Intensity): Jogging, brisk cycling, dancing
                - HIIT (High Intensity Interval Training): Sprints, burpees, cycling intervals
                
                TRAINING RECOMMENDATIONS:
                - Beginners: Start with 20-30 minutes LISS, 3 times per week
                - Intermediate: Mix LISS and MISS, 4-5 times per week
                - Advanced: Include HIIT 1-2 times per week
                
                HEART RATE ZONES:
                - Zone 1 (50-60% max HR): Active recovery
                - Zone 2 (60-70% max HR): Fat burning
                - Zone 3 (70-80% max HR): Aerobic base
                - Zone 4 (80-90% max HR): Lactate threshold
                - Zone 5 (90-100% max HR): Neuromuscular power
                
                Max Heart Rate = 220 - Age (rough estimate)
                """
            },
            {
                "topic": "Nutrition and Meal Planning",
                "content": """
                Proper nutrition fuels your body and supports all fitness goals.
                
                FUNDAMENTAL PRINCIPLES:
                - Eat whole, minimally processed foods
                - Balance macronutrients at each meal
                - Stay hydrated throughout the day
                - Time nutrition around workouts
                - Listen to hunger and satiety cues
                
                MEAL TIMING:
                - Breakfast: Include protein to start metabolism
                - Pre-workout: Light carbs 30-60 minutes before
                - Post-workout: Protein + carbs within 2 hours
                - Evening: Lighter meals, avoid late-night eating
                
                HEALTHY FOOD CHOICES:
                Proteins: Lean meats, fish, eggs, dairy, legumes, tofu
                Carbohydrates: Oats, quinoa, brown rice, sweet potatoes, fruits
                Fats: Nuts, seeds, avocado, olive oil, fatty fish
                Vegetables: Aim for variety and color - 5-9 servings daily
                
                MEAL PREP STRATEGIES:
                - Plan meals weekly
                - Batch cook proteins and grains
                - Pre-cut vegetables
                - Use containers for portion control
                - Prepare healthy snacks in advance
                
                HYDRATION:
                - 35-40ml per kg body weight daily
                - More during exercise and hot weather
                - Monitor urine color (pale yellow is ideal)
                """
            },
            {
                "topic": "Sleep and Recovery",
                "content": """
                Recovery is when your body adapts to training and builds strength.
                
                SLEEP IMPORTANCE:
                - Muscle protein synthesis occurs during deep sleep
                - Growth hormone release peaks during sleep
                - Immune system recovery and strengthening
                - Mental recovery and memory consolidation
                - Appetite hormone regulation (leptin/ghrelin)
                
                SLEEP OPTIMIZATION:
                - 7-9 hours per night for adults
                - Consistent sleep schedule (same bedtime/wake time)
                - Cool, dark, quiet bedroom environment
                - No screens 1 hour before bed
                - Avoid caffeine 6 hours before bedtime
                - Create a relaxing bedtime routine
                
                ACTIVE RECOVERY:
                - Light walking or swimming
                - Yoga or gentle stretching
                - Foam rolling and self-massage
                - Meditation and breathing exercises
                
                STRESS MANAGEMENT:
                - Chronic stress elevates cortisol, hindering recovery
                - Practice mindfulness or meditation
                - Engage in hobbies and social activities
                - Consider professional help if needed
                
                SIGNS OF OVERTRAINING:
                - Persistent fatigue and decreased performance
                - Frequent illness or injury
                - Mood changes and irritability
                - Sleep disturbances
                - Loss of motivation
                """
            },
            {
                "topic": "Women's Health and Fitness",
                "content": """
                Women have unique physiological considerations for health and fitness.
                
                MENSTRUAL CYCLE AND TRAINING:
                - Follicular phase (days 1-14): Higher energy, good for intense training
                - Luteal phase (days 15-28): May need to reduce intensity
                - Listen to your body and adjust training accordingly
                - Track cycle to understand patterns
                
                HORMONAL CONSIDERATIONS:
                - Estrogen affects muscle recovery and fat metabolism
                - Progesterone can increase appetite and water retention
                - Iron needs increase during menstruation
                - Calcium and vitamin D crucial for bone health
                
                STRENGTH TRAINING BENEFITS:
                - Builds bone density (prevents osteoporosis)
                - Improves metabolic rate
                - Enhances functional strength
                - Myth-busting: Won't make you "bulky"
                
                NUTRITION SPECIFICS:
                - Iron: 18mg daily (more during menstruation)
                - Calcium: 1000-1200mg daily for bone health
                - Folate: Important for reproductive health
                - Adequate calories to support menstrual function
                
                PREGNANCY AND EXERCISE:
                - Generally safe to continue exercise during pregnancy
                - Avoid contact sports and exercises lying on back after first trimester
                - Stay hydrated and avoid overheating
                - Consult healthcare provider for personalized guidance
                """
            },
            {
                "topic": "Men's Health and Fitness",
                "content": """
                Men have specific health considerations and fitness needs.
                
                TESTOSTERONE AND TRAINING:
                - Peaks in late teens/early twenties, gradually declines
                - Strength training helps maintain healthy levels
                - Adequate sleep crucial for testosterone production
                - Stress management important (cortisol suppresses testosterone)
                
                COMMON HEALTH RISKS:
                - Cardiovascular disease: Leading cause of death in men
                - Type 2 diabetes: Higher risk with age and inactivity
                - Prostate health: Regular exercise may reduce risk
                - Mental health: Men less likely to seek help
                
                TRAINING CONSIDERATIONS:
                - Men typically build muscle faster than women
                - Higher risk of injury due to tendency to lift heavy too soon
                - Important to include flexibility and mobility work
                - Don't neglect cardio for heart health
                
                NUTRITION FOCUS:
                - Higher caloric needs than women on average
                - Adequate protein for muscle maintenance
                - Omega-3 fatty acids for heart and brain health
                - Limit processed foods and excessive alcohol
                - Stay hydrated, especially if physically active job
                
                PREVENTIVE HEALTH:
                - Regular health screenings (blood pressure, cholesterol)
                - Prostate exams after age 50 (or 45 if family history)
                - Skin cancer checks
                - Mental health awareness and support
                """
            },
            {
                "topic": "Age-Specific Fitness Guidelines",
                "content": """
                Fitness needs and capabilities change throughout life.
                
                TEENS (13-17 years):
                - Focus on movement patterns and skill development
                - Bodyweight exercises and light resistance training
                - Emphasize fun and variety to build lifelong habits
                - Adequate nutrition for growth and development
                - 60 minutes of physical activity daily
                
                YOUNG ADULTS (18-30 years):
                - Build fitness foundation with variety of activities
                - Progressive strength training
                - Establish consistent exercise routine
                - Learn proper form and technique
                - Recovery becomes more important
                
                MIDDLE AGE (30-50 years):
                - Maintain muscle mass (begins declining after 30)
                - Include more flexibility and mobility work
                - Manage stress and prioritize sleep
                - Watch for overuse injuries
                - Balance family/work commitments with fitness
                
                OLDER ADULTS (50+ years):
                - Focus on functional movement patterns
                - Balance and fall prevention exercises
                - Maintain bone density through weight-bearing exercise
                - Low-impact activities for joint health
                - Regular health screenings and medical clearance
                
                SENIORS (65+ years):
                - Emphasize activities of daily living
                - Chair exercises if mobility limited
                - Social activities like group classes
                - Gentle movement and stretching
                - Work with healthcare team for safe exercise plan
                """
            }
        ]
        
        # Convert to documents
        documents = []
        for item in health_knowledge:
            doc = Document(
                page_content=item["content"],
                metadata={"topic": item["topic"], "source": "health_knowledge_base"}
            )
            documents.append(doc)
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Smaller chunks for better retrieval
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        
        split_docs = text_splitter.split_documents(documents)
        
        # Create vector store
        persist_directory = "./chroma_health_db"
        self.vectorstore = Chroma.from_documents(
            documents=split_docs,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        
        logger.info(f"Created vector store with {len(split_docs)} document chunks")
        
        # Setup conversation chain
        self.setup_conversation_chain()
    
    def setup_conversation_chain(self):
        """Set up the conversational retrieval chain"""
        
        # Custom prompt template for health conversations
        system_prompt = """You are BodyBae, a knowledgeable and supportive AI fitness and health assistant. Your personality is encouraging, motivational, and scientifically accurate.

PERSONALITY TRAITS:
- Warm, friendly, and encouraging
- Enthusiastic about helping users achieve their health goals
- Evidence-based and scientifically accurate
- Supportive but not pushy
- Celebrates small wins and progress

GUIDELINES:
- Use the provided context to give accurate, helpful advice
- If asked about medical conditions or serious health issues, recommend consulting healthcare professionals
- Keep responses conversational and easy to understand
- Include practical, actionable tips
- Be motivational and positive
- If you don't know something, say so honestly

Context from knowledge base: {context}

Previous conversation: {chat_history}import os
from typing import List, Dict, Optional
import json
from datetime import datetime
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HuggingFaceHealthLLM:
    """Custom LLM wrapper for Hugging Face models optimized for health conversations"""
    
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        """
        Initialize with a free Hugging Face model
        Best free models for health conversations:
        - microsoft/DialoGPT-medium: Good for conversational AI
        - microsoft/DialoGPT-large: Better quality but slower
        - facebook/blenderbot-400M-distill: Good for chat
        - google/flan-t5-base: Instruction following
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            # For DialoGPT and similar conversational models
            if "DialoGPT" in model_name:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForCausalLM.from_pretrained(model_name)
                self.model.to(self.device)
                self.pipeline = None
            else:
                # For other models, use pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=model_name,
                    device=0 if torch.cuda.is_available() else -1,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                self.tokenizer = None
                self.model = None
                
            logger.info(f"Successfully loaded model: {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            # Fallback to a smaller model
            self.model_name = "microsoft/DialoGPT-small"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self.model.to(self.device)
            logger.info("Fallback to DialoGPT-small")

    def generate_response(self, prompt: str, max_length: int = 150) -> str:
        """Generate response using the loaded model"""
        try:
            if self.pipeline:
                # Use pipeline for text generation
                response = self.pipeline(
                    prompt,
                    max_length=max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.pipeline.tokenizer.eos_token_id
                )
                return response[0]['generated_text'].replace(prompt, '').strip()
            
            else:
                # Use DialoGPT style generation
                input_ids = self.tokenizer.encode(prompt + self.tokenizer.eos_token, return_tensors='pt').to(self.device)
                
                with torch.no_grad():
                    chat_history_ids = self.model.generate(
                        input_ids,
                        max_length=input_ids.shape[-1]