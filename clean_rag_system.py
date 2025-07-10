import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Updated imports for compatibility
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.schema import Document
    from langchain.memory import ConversationBufferWindowMemory
    from sentence_transformers import SentenceTransformer
    import numpy as np
    
    DEPENDENCIES_AVAILABLE = True
    logger.info("✅ All RAG dependencies loaded successfully")
    
except ImportError as e:
    logger.warning(f"⚠️ RAG dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

class HealthRAGSystem:
    """Simple but effective RAG system for health and fitness advice"""
    
    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required dependencies not available")
            
        # Initialize embeddings model
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}  # Force CPU for compatibility
            )
            logger.info("✅ Embeddings model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load embeddings: {e}")
            raise
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Remember last 5 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        
        self.vectorstore = None
        self.setup_health_knowledge_base()
        
    def setup_health_knowledge_base(self):
        """Set up comprehensive health knowledge base"""
        
        # Comprehensive health knowledge
        health_knowledge = [
            {
                "topic": "Weight Loss Fundamentals",
                "content": """
                Weight loss occurs when you burn more calories than you consume (caloric deficit). 
                Safe weight loss: 0.5-1 kg per week through a 500-750 calorie daily deficit.
                Key strategies: Focus on whole foods, eat protein with every meal, stay hydrated,
                combine cardio and strength training, get 7-9 hours of sleep, manage stress.
                Avoid crash diets and extreme restrictions. Sustainable changes work best.
                """
            },
            {
                "topic": "Muscle Building and Strength",
                "content": """
                Building muscle requires progressive overload, adequate nutrition, and proper recovery.
                Protein needs: 1.6-2.2g per kg body weight daily. Eat protein every 3-4 hours.
                Training: Focus on compound movements (squats, deadlifts, bench press, rows).
                Train each muscle group 2-3 times per week. Progressive overload is essential.
                Recovery: 7-9 hours of sleep, 48-72 hours rest between training same muscles.
                Slight caloric surplus (200-500 calories) supports muscle growth.
                """
            },
            {
                "topic": "Cardiovascular Health",
                "content": """
                Cardio strengthens heart, improves circulation, reduces blood pressure and cholesterol.
                Guidelines: 150 minutes moderate or 75 minutes vigorous cardio weekly.
                Types: LISS (walking, easy cycling), MISS (jogging, brisk cycling), HIIT (intervals).
                Benefits: Improved insulin sensitivity, better mood, increased lung capacity.
                Heart rate zones: Zone 2 (60-70% max HR) for fat burning, Zone 4 (80-90%) for performance.
                Start gradually and build endurance over time.
                """
            },
            {
                "topic": "Nutrition Fundamentals",
                "content": """
                Balanced nutrition includes all macronutrients: proteins, carbohydrates, and fats.
                Protein: Essential for muscle repair and satiety. Include in every meal.
                Carbohydrates: Primary energy source. Choose complex carbs (oats, quinoa, vegetables).
                Fats: Important for hormone production. Include nuts, seeds, avocado, olive oil.
                Hydration: 35-40ml per kg body weight daily. More during exercise.
                Meal timing: Eat balanced meals, avoid late-night eating, fuel workouts properly.
                """
            },
            {
                "topic": "Sleep and Recovery",
                "content": """
                Sleep is crucial for muscle recovery, hormone regulation, and overall health.
                Adults need 7-9 hours of quality sleep nightly. Sleep affects appetite hormones.
                Sleep optimization: Consistent schedule, cool dark room, no screens before bed.
                Recovery strategies: Active recovery, stretching, foam rolling, stress management.
                Signs of overtraining: Persistent fatigue, frequent illness, mood changes.
                Quality sleep improves workout performance and supports weight management.
                """
            },
            {
                "topic": "Exercise Programming",
                "content": """
                Effective exercise programs include cardio, strength training, and flexibility work.
                Beginners: Start with 2-3 workouts per week, focus on form over intensity.
                Intermediate: 3-5 workouts weekly, mix different training styles.
                Advanced: 5-6 workouts, include periodization and specialization.
                Compound movements are most effective: squats, deadlifts, push-ups, rows.
                Progressive overload: Gradually increase weight, reps, or sets over time.
                """
            },
            {
                "topic": "Healthy Lifestyle Habits",
                "content": """
                Health extends beyond diet and exercise to include mental wellbeing and lifestyle.
                Stress management: Practice meditation, deep breathing, regular social connection.
                Hydration: Drink water throughout the day, monitor urine color for hydration status.
                Movement: Include daily movement, take stairs, walk meetings, stretch regularly.
                Social support: Exercise with friends, join fitness communities, seek accountability.
                Consistency: Small daily habits create lasting change. Focus on progress, not perfection.
                """
            },
            {
                "topic": "Goal Setting and Motivation",
                "content": """
                Effective goal setting uses SMART principles: Specific, Measurable, Achievable, Relevant, Time-bound.
                Break large goals into smaller milestones. Celebrate small wins along the way.
                Track progress through multiple metrics: how you feel, energy levels, strength gains.
                Motivation strategies: Find your 'why', create accountability, reward progress.
                Overcome plateaus: Change routines, reassess goals, focus on non-scale victories.
                Long-term success comes from building sustainable habits, not quick fixes.
                """
            }
        ]
        
        # Convert to documents
        documents = []
        for item in health_knowledge:
            doc = Document(
                page_content=item["content"],
                metadata={"topic": item["topic"], "source": "health_knowledge"}
            )
            documents.append(doc)
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len
        )
        
        split_docs = text_splitter.split_documents(documents)
        
        # Create vector store
        try:
            self.vectorstore = Chroma.from_documents(
                documents=split_docs,
                embedding=self.embeddings,
                persist_directory="./chroma_health_db"
            )
            logger.info(f"✅ Vector store created with {len(split_docs)} chunks")
        except Exception as e:
            logger.error(f"❌ Failed to create vector store: {e}")
            raise
    
    def get_health_response(self, question: str, user_profile: Dict = None) -> str:
        """Generate a health-focused response using RAG"""
        try:
            # Get relevant context from knowledge base
            relevant_docs = self.vectorstore.similarity_search(question, k=3)
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Build user context
            user_context = ""
            if user_profile:
                name = user_profile.get('name', 'there')
                bmi = user_profile.get('bmi', 'unknown')
                bmi_category = user_profile.get('bmi_category', 'unknown')
                age = user_profile.get('age', 'unknown')
                activity_level = user_profile.get('activity_level', 'unknown')
                
                user_context = f"""
                User: {name}, Age: {age}, BMI: {bmi} ({bmi_category}), Activity: {activity_level}
                """
            
            # Generate personalized response
            response = self.generate_personalized_response(question, context, user_context)
            
            # Store in memory
            self.memory.save_context({"input": question}, {"output": response})
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_fallback_response(question, user_profile)
    
    def generate_personalized_response(self, question: str, context: str, user_context: str) -> str:
        """Generate a personalized response based on context and user profile"""
        
        # Simple but effective response generation
        question_lower = question.lower()
        
        # Extract user info for personalization
        name = "there"
        if user_context and "User:" in user_context:
            try:
                name_part = user_context.split("User:")[1].split(",")[0].strip()
                if name_part and name_part != "unknown":
                    name = name_part
            except:
                pass
        
        # Generate contextual response based on question type and retrieved knowledge
        if any(word in question_lower for word in ['weight loss', 'lose weight', 'losing weight']):
            response = f"Hi {name}! Based on proven weight loss principles: "
            if "caloric deficit" in context:
                response += "Create a moderate caloric deficit of 500-750 calories daily for safe weight loss of 0.5-1 kg per week. "
            if "whole foods" in context:
                response += "Focus on whole foods like lean proteins, vegetables, fruits, and whole grains. "
            if "hydrated" in context:
                response += "Stay well-hydrated and drink water before meals. "
            response += "Combine cardio with strength training for best results. You've got this! 💪"
            
        elif any(word in question_lower for word in ['muscle', 'gain muscle', 'build muscle']):
            response = f"Great question, {name}! For effective muscle building: "
            if "protein" in context:
                response += "Aim for 1.6-2.2g of protein per kg body weight daily. "
            if "progressive overload" in context:
                response += "Focus on progressive overload - gradually increase weight, reps, or sets. "
            if "sleep" in context:
                response += "Get 7-9 hours of quality sleep for recovery. "
            if "compound" in context:
                response += "Prioritize compound movements like squats, deadlifts, and bench press. "
            response += "Consistency and patience are key! 🏋️‍♀️"
            
        elif any(word in question_lower for word in ['cardio', 'cardiovascular', 'heart health']):
            response = f"Excellent question, {name}! For cardiovascular health: "
            if "150 minutes" in context:
                response += "Aim for 150 minutes of moderate cardio or 75 minutes of vigorous cardio weekly. "
            if "heart rate" in context:
                response += "Train in different heart rate zones - Zone 2 (60-70% max HR) is great for fat burning. "
            if "circulation" in context:
                response += "Regular cardio strengthens your heart and improves circulation. "
            response += "Start gradually and build endurance over time! ❤️"
            
        elif any(word in question_lower for word in ['nutrition', 'diet', 'food', 'eat']):
            response = f"Nutrition is crucial, {name}! Here's what works: "
            if "balanced" in context:
                response += "Focus on balanced nutrition with proteins, complex carbs, and healthy fats. "
            if "hydration" in context:
                response += "Stay hydrated with 35-40ml of water per kg body weight daily. "
            if "meal timing" in context:
                response += "Eat balanced meals throughout the day and fuel your workouts properly. "
            response += "Small, sustainable changes lead to lasting results! 🥗"
            
        elif any(word in question_lower for word in ['sleep', 'recovery', 'rest']):
            response = f"Sleep and recovery are essential, {name}! "
            if "7-9 hours" in context:
                response += "Adults need 7-9 hours of quality sleep nightly for optimal recovery. "
            if "hormone" in context:
                response += "Good sleep regulates appetite hormones and supports muscle recovery. "
            if "stress" in context:
                response += "Manage stress through relaxation techniques and consistent sleep schedule. "
            response += "Quality rest is when your body gets stronger! 😴"
            
        elif any(word in question_lower for word in ['motivation', 'motivated', 'give up', 'struggling']):
            response = f"I believe in you, {name}! 🌟 "
            if "goal" in context:
                response += "Remember your goals and why you started this journey. "
            if "progress" in context:
                response += "Progress isn't always linear - focus on how you feel, not just the scale. "
            if "habits" in context:
                response += "Small daily habits create lasting change. "
            response += "You're stronger than you think and capable of amazing things! Every step counts! 💪"
            
        elif any(word in question_lower for word in ['workout', 'exercise', 'training']):
            response = f"Let's talk workouts, {name}! "
            if "compound" in context:
                response += "Focus on compound movements that work multiple muscle groups. "
            if "progressive" in context:
                response += "Use progressive overload to continuously challenge your body. "
            if "frequency" in context:
                response += "Start with 2-3 workouts per week and build from there. "
            response += "Consistency beats perfection every time! 🏃‍♀️"
            
        else:
            # General helpful response using context
            response = f"Hi {name}! Great question! "
            if context:
                # Extract key advice from context
                sentences = context.split('.')[:3]  # Get first 3 sentences
                for sentence in sentences:
                    if len(sentence.strip()) > 20:  # Only meaningful sentences
                        response += sentence.strip() + ". "
            response += " I'm here to help you on your health journey! What specific aspect would you like to explore further? 😊"
        
        return response.strip()
    
    def get_fallback_response(self, question: str, user_profile: Dict = None) -> str:
        """Simple fallback when RAG fails"""
        name = user_profile.get('name', 'there') if user_profile else 'there'
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['weight loss', 'lose weight']):
            return f"Hi {name}! For healthy weight loss, create a moderate caloric deficit through balanced nutrition and regular exercise. Focus on whole foods and stay consistent! 💪"
        
        elif any(word in question_lower for word in ['muscle', 'build muscle']):
            return f"Great question, {name}! To build muscle: eat adequate protein (1.6-2.2g per kg body weight), focus on progressive overload, and get plenty of sleep for recovery! 🏋️‍♀️"
        
        elif any(word in question_lower for word in ['workout', 'exercise']):
            return f"For effective workouts, {name}, combine strength training with cardio, focus on compound movements, and aim for consistency over perfection! 🌟"
        
        else:
            return f"Hi {name}! I'm here to help with your health and fitness journey. I can provide advice on nutrition, workouts, weight management, and motivation. What would you like to know more about? 😊"

# Test function
def test_rag_system():
    """Test the RAG system"""
    try:
        rag = HealthRAGSystem()
        
        test_questions = [
            "How do I lose weight safely?",
            "What's the best way to build muscle?",
            "How much sleep do I need?",
            "Give me workout advice"
        ]
        
        test_profile = {
            'name': 'Alex',
            'age': 30,
            'bmi': 24.5,
            'bmi_category': 'Normal Weight',
            'activity_level': 'moderately_active'
        }
        
        print("🧪 Testing RAG System:")
        print("=" * 50)
        
        for question in test_questions:
            print(f"\nQ: {question}")
            response = rag.get_health_response(question, test_profile)
            print(f"A: {response}")
            print("-" * 30)
            
        return True
        
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        return False

if __name__ == "__main__":
    if DEPENDENCIES_AVAILABLE:
        success = test_rag_system()
        if success:
            print("✅ RAG system test completed successfully!")
        else:
            print("❌ RAG system test failed!")
    else:
        print("❌ Dependencies not available for testing")