import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple knowledge base without heavy dependencies
class HealthRAGSystem:
    """Simple health knowledge system without heavy ML dependencies"""
    
    def __init__(self):
        logger.info("✅ Initializing simple health knowledge system")
        self.setup_health_knowledge_base()
        
    def setup_health_knowledge_base(self):
        """Set up comprehensive health knowledge base"""
        
        # Comprehensive health knowledge
        self.health_knowledge = {
            "weight_loss": {
                "keywords": ["weight loss", "lose weight", "losing weight", "diet", "calories"],
                "advice": """
                Safe weight loss: 0.5-1 kg per week through a 500-750 calorie daily deficit.
                Key strategies: Focus on whole foods, eat protein with every meal, stay hydrated,
                combine cardio and strength training, get 7-9 hours of sleep, manage stress.
                Avoid crash diets. Sustainable changes work best for long-term success.
                """
            },
            "muscle_building": {
                "keywords": ["muscle", "build muscle", "gain muscle", "strength", "protein"],
                "advice": """
                Building muscle requires progressive overload, adequate nutrition, and recovery.
                Protein needs: 1.6-2.2g per kg body weight daily. Eat protein every 3-4 hours.
                Training: Focus on compound movements (squats, deadlifts, bench press, rows).
                Train each muscle group 2-3 times per week. Get 7-9 hours of sleep for recovery.
                """
            },
            "cardio": {
                "keywords": ["cardio", "cardiovascular", "heart", "running", "endurance"],
                "advice": """
                Cardio strengthens heart, improves circulation, reduces blood pressure.
                Guidelines: 150 minutes moderate or 75 minutes vigorous cardio weekly.
                Types: Walking, jogging, cycling, swimming. Start gradually and build endurance.
                Heart rate zones: 60-70% max HR for fat burning, 80-90% for performance.
                """
            },
            "nutrition": {
                "keywords": ["nutrition", "diet", "food", "eat", "meal"],
                "advice": """
                Balanced nutrition includes proteins, carbohydrates, and healthy fats.
                Protein: Essential for muscle repair. Include in every meal.
                Carbs: Choose complex carbs (oats, quinoa, vegetables) for sustained energy.
                Fats: Include nuts, seeds, avocado, olive oil for hormone production.
                Hydration: 35-40ml per kg body weight daily. More during exercise.
                """
            },
            "sleep": {
                "keywords": ["sleep", "recovery", "rest", "tired", "energy"],
                "advice": """
                Adults need 7-9 hours of quality sleep for optimal health and recovery.
                Sleep affects appetite hormones, muscle recovery, and immune function.
                Tips: Consistent schedule, cool dark room, no screens before bed.
                Poor sleep impairs workout performance and weight management.
                """
            },
            "exercise": {
                "keywords": ["workout", "exercise", "training", "gym", "fitness"],
                "advice": """
                Effective programs include cardio, strength training, and flexibility.
                Beginners: Start 2-3 times per week, focus on form over intensity.
                Progressive overload: Gradually increase weight, reps, or sets.
                Compound movements are most effective for overall fitness.
                """
            },
            "motivation": {
                "keywords": ["motivation", "motivated", "give up", "struggling", "help"],
                "advice": """
                Set SMART goals: Specific, Measurable, Achievable, Relevant, Time-bound.
                Track progress through multiple metrics: energy, strength, how you feel.
                Find your 'why' and remember it during tough times.
                Small daily habits create lasting change. Progress isn't always linear.
                Celebrate small wins and focus on building sustainable habits.
                """
            }
        }
        
        logger.info("✅ Health knowledge base loaded with 7 categories")
    
    def get_health_response(self, question: str, user_profile: Dict = None) -> str:
        """Generate a health response using simple keyword matching"""
        try:
            question_lower = question.lower()
            name = user_profile.get('name', 'there') if user_profile else 'there'
            
            # Find matching knowledge category
            best_match = None
            best_score = 0
            
            for category, data in self.health_knowledge.items():
                score = sum(1 for keyword in data["keywords"] if keyword in question_lower)
                if score > best_score:
                    best_score = score
                    best_match = category
            
            if best_match and best_score > 0:
                advice = self.health_knowledge[best_match]["advice"].strip()
                
                # Personalize the response
                if best_match == "weight_loss" and user_profile:
                    bmi_category = user_profile.get('bmi_category', '')
                    if bmi_category in ['Overweight', 'Obese']:
                        response = f"Hi {name}! Based on your BMI category, weight loss could be beneficial. {advice}"
                    else:
                        response = f"Hi {name}! While your BMI is in a healthy range, here's evidence-based weight loss advice: {advice}"
                
                elif best_match == "muscle_building" and user_profile:
                    age = user_profile.get('age', 25)
                    if age > 40:
                        response = f"Hi {name}! At your age, recovery becomes even more important. {advice} Consider longer rest periods between sessions."
                    else:
                        response = f"Hi {name}! Perfect age to build muscle! {advice}"
                
                else:
                    response = f"Hi {name}! {advice}"
                
                # Add motivational ending
                response += " 💪 You've got this!"
                
                return response
            
            # Default response if no specific match
            return self.get_general_response(name, user_profile)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_fallback_response(question, user_profile)
    
    def get_general_response(self, name: str, user_profile: Dict = None) -> str:
        """General helpful response"""
        response = f"Hi {name}! I'm here to help with your health and fitness journey. I can provide guidance on:\n\n"
        response += "• Weight management and nutrition\n"
        response += "• Muscle building and strength training\n"
        response += "• Cardiovascular health and endurance\n"
        response += "• Sleep and recovery optimization\n"
        response += "• Workout planning and motivation\n\n"
        
        if user_profile and user_profile.get('bmi_category'):
            bmi_category = user_profile['bmi_category']
            response += f"Based on your BMI category ({bmi_category}), I can give you personalized advice. "
        
        response += "What specific aspect of your health would you like to focus on today? 😊"
        return response
    
    def get_fallback_response(self, question: str, user_profile: Dict = None) -> str:
        """Simple fallback when all else fails"""
        name = user_profile.get('name', 'there') if user_profile else 'there'
        return f"Hi {name}! I'm here to help with your health and fitness goals. Could you rephrase your question or ask about specific topics like nutrition, workouts, or weight management? 😊"

# Test function
def test_simple_system():
    """Test the simple system"""
    try:
        system = HealthRAGSystem()
        
        test_questions = [
            "How do I lose weight?",
            "Help me build muscle",
            "I need workout advice",
            "What should I eat?"
        ]
        
        test_profile = {
            'name': 'Alex',
            'age': 30,
            'bmi_category': 'Normal Weight'
        }
        
        print("🧪 Testing Simple Health System:")
        print("=" * 50)
        
        for question in test_questions:
            print(f"\nQ: {question}")
            response = system.get_health_response(question, test_profile)
            print(f"A: {response[:100]}...")
            print("-" * 30)
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_system()
    if success:
        print("✅ Simple health system test completed!")
    else:
        print("❌ Test failed!")