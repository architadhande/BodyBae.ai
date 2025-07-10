import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
from typing import List, Dict, Tuple
import re

class RAGSystem:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the RAG system with a lightweight model suitable for free tier."""
        # Use CPU for free tier compatibility
        self.device = torch.device("cpu")
        
        # Load tokenizer and model
        print("Loading model and tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        
        # Initialize knowledge base
        self.knowledge_base = self._load_knowledge_base()
        self.embeddings_cache = {}
        
        # Precompute embeddings for knowledge base
        self._precompute_embeddings()
    
    def _load_knowledge_base(self) -> Dict[str, List[Dict]]:
        """Load the health and fitness knowledge base."""
        knowledge_base = {
            "nutrition": [
                {
                    "topic": "balanced diet",
                    "content": "A balanced diet includes proteins, carbohydrates, healthy fats, vitamins, and minerals. Aim for variety in your meals with plenty of fruits and vegetables, whole grains, lean proteins, and healthy fats like omega-3s.",
                    "keywords": ["diet", "nutrition", "balanced", "healthy eating", "food"]
                },
                {
                    "topic": "protein intake",
                    "content": "For muscle building and maintenance, aim for 0.8-1.2g of protein per kg of body weight. Good sources include lean meats, fish, eggs, legumes, nuts, and dairy products.",
                    "keywords": ["protein", "muscle", "intake", "nutrition"]
                },
                {
                    "topic": "hydration",
                    "content": "Proper hydration is crucial. Aim for 8-10 glasses of water daily, more if you're active. Signs of good hydration include pale yellow urine and feeling energetic.",
                    "keywords": ["water", "hydration", "drink", "fluid"]
                },
                {
                    "topic": "weight loss nutrition",
                    "content": "For healthy weight loss, create a moderate caloric deficit of 300-500 calories daily. Focus on whole foods, increase protein intake, and avoid crash diets. Sustainable weight loss is 0.5-1kg per week.",
                    "keywords": ["weight loss", "calories", "deficit", "diet"]
                }
            ],
            "exercise": [
                {
                    "topic": "cardio exercise",
                    "content": "Cardiovascular exercise strengthens your heart and lungs. Aim for 150 minutes of moderate-intensity or 75 minutes of vigorous-intensity cardio weekly. Activities include running, cycling, swimming, and dancing.",
                    "keywords": ["cardio", "aerobic", "running", "heart", "endurance"]
                },
                {
                    "topic": "strength training",
                    "content": "Strength training builds muscle and bone density. Train major muscle groups 2-3 times per week with at least one rest day between sessions. Start with bodyweight exercises or light weights.",
                    "keywords": ["strength", "muscle", "weights", "resistance", "training"]
                },
                {
                    "topic": "flexibility",
                    "content": "Flexibility training improves range of motion and reduces injury risk. Include stretching or yoga 2-3 times per week. Hold stretches for 15-30 seconds without bouncing.",
                    "keywords": ["flexibility", "stretching", "yoga", "mobility"]
                },
                {
                    "topic": "rest and recovery",
                    "content": "Rest is crucial for muscle repair and growth. Aim for 7-9 hours of sleep nightly. Include rest days in your workout routine and listen to your body to prevent overtraining.",
                    "keywords": ["rest", "recovery", "sleep", "overtraining"]
                }
            ],
            "health": [
                {
                    "topic": "BMI interpretation",
                    "content": "BMI (Body Mass Index) is a screening tool. Underweight: <18.5, Normal: 18.5-24.9, Overweight: 25-29.9, Obese: ≥30. Remember, BMI doesn't account for muscle mass or body composition.",
                    "keywords": ["BMI", "body mass index", "weight", "height", "obesity"]
                },
                {
                    "topic": "mental health",
                    "content": "Mental health is as important as physical health. Regular exercise, adequate sleep, social connections, and stress management techniques like meditation can improve mental well-being.",
                    "keywords": ["mental health", "stress", "anxiety", "depression", "wellness"]
                },
                {
                    "topic": "sleep hygiene",
                    "content": "Good sleep hygiene includes: consistent sleep schedule, dark and cool room, avoiding screens before bed, limiting caffeine after 2 PM, and creating a relaxing bedtime routine.",
                    "keywords": ["sleep", "insomnia", "rest", "bedtime", "hygiene"]
                },
                {
                    "topic": "preventive health",
                    "content": "Regular health check-ups, vaccinations, and screenings are important. Monitor blood pressure, cholesterol, and blood sugar. Don't ignore persistent symptoms - consult healthcare providers.",
                    "keywords": ["prevention", "check-up", "screening", "health", "doctor"]
                }
            ],
            "lifestyle": [
                {
                    "topic": "habit formation",
                    "content": "Building healthy habits takes 21-66 days. Start small, be consistent, track progress, and reward yourself. Stack new habits with existing ones for better success.",
                    "keywords": ["habits", "routine", "consistency", "lifestyle"]
                },
                {
                    "topic": "stress management",
                    "content": "Manage stress through regular exercise, meditation, deep breathing, adequate sleep, and social support. Chronic stress can impact physical and mental health negatively.",
                    "keywords": ["stress", "relaxation", "meditation", "breathing", "mindfulness"]
                },
                {
                    "topic": "work-life balance",
                    "content": "Maintain boundaries between work and personal life. Schedule regular breaks, pursue hobbies, spend time with loved ones, and practice saying no to excessive commitments.",
                    "keywords": ["balance", "work", "life", "boundaries", "wellness"]
                }
            ]
        }
        return knowledge_base
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a given text."""
        # Check cache first
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Tokenize and get embeddings
        inputs = self.tokenizer(text, return_tensors="pt", 
                               truncation=True, max_length=512, 
                               padding=True).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
            embeddings = embeddings.cpu().numpy()
        
        # Cache the embedding
        self.embeddings_cache[text] = embeddings
        
        return embeddings
    
    def _precompute_embeddings(self):
        """Precompute embeddings for all knowledge base entries."""
        print("Precomputing embeddings for knowledge base...")
        for category, items in self.knowledge_base.items():
            for item in items:
                # Combine topic, content, and keywords for embedding
                full_text = f"{item['topic']} {item['content']} {' '.join(item['keywords'])}"
                self._get_embedding(full_text)
    
    def find_relevant_knowledge(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find the most relevant knowledge base entries for a query."""
        query_embedding = self._get_embedding(query.lower())
        
        relevant_items = []
        
        for category, items in self.knowledge_base.items():
            for item in items:
                # Create combined text for similarity matching
                full_text = f"{item['topic']} {item['content']} {' '.join(item['keywords'])}"
                item_embedding = self._get_embedding(full_text)
                
                # Calculate cosine similarity
                similarity = cosine_similarity(query_embedding, item_embedding)[0][0]
                
                relevant_items.append({
                    'category': category,
                    'topic': item['topic'],
                    'content': item['content'],
                    'similarity': similarity
                })
        
        # Sort by similarity and return top k
        relevant_items.sort(key=lambda x: x['similarity'], reverse=True)
        return relevant_items[:top_k]
    
    def get_response(self, query: str, context: str = "") -> str:
        """Generate a response based on the query and context."""
        # Find relevant knowledge
        relevant_knowledge = self.find_relevant_knowledge(query)
        
        # Build response based on query intent
        query_lower = query.lower()
        
        # Check for specific query types
        if any(word in query_lower for word in ['bmi', 'body mass', 'weight', 'overweight', 'underweight']):
            response = self._handle_bmi_query(query, context, relevant_knowledge)
        elif any(word in query_lower for word in ['exercise', 'workout', 'training', 'gym']):
            response = self._handle_exercise_query(query, context, relevant_knowledge)
        elif any(word in query_lower for word in ['diet', 'nutrition', 'food', 'eat', 'meal']):
            response = self._handle_nutrition_query(query, context, relevant_knowledge)
        elif any(word in query_lower for word in ['goal', 'target', 'achieve', 'plan']):
            response = self._handle_goal_query(query, context, relevant_knowledge)
        else:
            response = self._handle_general_query(query, context, relevant_knowledge)
        
        return response
    
    def _handle_bmi_query(self, query: str, context: str, knowledge: List[Dict]) -> str:
        """Handle BMI-related queries."""
        response = ""
        
        # Extract BMI from context if available
        bmi_match = re.search(r'BMI: ([\d.]+)', context)
        if bmi_match:
            bmi = float(bmi_match.group(1))
            category_match = re.search(r'BMI: [\d.]+ \(([^)]+)\)', context)
            category = category_match.group(1) if category_match else ""
            
            response = f"Based on your BMI of {bmi:.1f}, you're in the {category} category. "
            
            if bmi < 18.5:
                response += "To reach a healthy weight, focus on nutrient-dense foods and strength training. "
            elif 18.5 <= bmi < 25:
                response += "Great job maintaining a healthy weight! Continue with balanced nutrition and regular exercise. "
            elif 25 <= bmi < 30:
                response += "Consider creating a moderate caloric deficit through diet and increasing physical activity. "
            else:
                response += "I recommend consulting with healthcare providers for a personalized weight management plan. "
        
        # Add relevant knowledge
        for item in knowledge:
            if item['similarity'] > 0.5:
                response += f"\n\n{item['content']}"
                break
        
        return response or "I can help you understand BMI and healthy weight management. Could you provide more specific information about what you'd like to know?"
    
    def _handle_exercise_query(self, query: str, context: str, knowledge: List[Dict]) -> str:
        """Handle exercise-related queries."""
        response = "Here's some guidance on exercise and fitness:\n\n"
        
        # Add personalized advice if context available
        if "beginner" in query.lower() or "start" in query.lower():
            response += "As a beginner, start slowly and gradually increase intensity. "
        
        # Add relevant knowledge
        added_content = False
        for item in knowledge:
            if item['similarity'] > 0.4 and item['category'] == 'exercise':
                response += item['content'] + "\n\n"
                added_content = True
                break
        
        if not added_content and knowledge:
            response += knowledge[0]['content']
        
        # Add personalized touch if user profile exists
        if context and "goals" in context:
            response += "\n\nRemember to align your exercise routine with your personal goals!"
        
        return response
    
    def _handle_nutrition_query(self, query: str, context: str, knowledge: List[Dict]) -> str:
        """Handle nutrition-related queries."""
        response = "Let me help you with nutrition advice:\n\n"
        
        # Add relevant knowledge
        nutrition_items = [k for k in knowledge if k['category'] == 'nutrition']
        if nutrition_items:
            response += nutrition_items[0]['content']
        else:
            response += knowledge[0]['content'] if knowledge else ""
        
        # Add personalized advice based on context
        if "weight loss" in context.lower():
            response += "\n\nSince you have weight loss goals, remember to maintain a moderate caloric deficit while ensuring adequate nutrition."
        elif "muscle" in query.lower() or "protein" in query.lower():
            weight_match = re.search(r'Weight: ([\d.]+)kg', context)
            if weight_match:
                weight = float(weight_match.group(1))
                protein_min = weight * 0.8
                protein_max = weight * 1.2
                response += f"\n\nBased on your weight of {weight}kg, aim for {protein_min:.0f}-{protein_max:.0f}g of protein daily."
        
        return response
    
    def _handle_goal_query(self, query: str, context: str, knowledge: List[Dict]) -> str:
        """Handle goal-related queries."""
        response = "Setting and achieving health goals is important! "
        
        # Check for existing goals in context
        if "goals:" in context.lower():
            response += "I see you have some goals already. Here's how to work towards them:\n\n"
            response += "1. Break down large goals into smaller, manageable steps\n"
            response += "2. Track your progress regularly\n"
            response += "3. Celebrate small victories\n"
            response += "4. Adjust your approach based on what works\n\n"
        else:
            response += "Here are some tips for setting effective health goals:\n\n"
            response += "• Make them SMART (Specific, Measurable, Achievable, Relevant, Time-bound)\n"
            response += "• Start with one or two goals at a time\n"
            response += "• Write them down and review regularly\n"
            response += "• Find an accountability partner\n\n"
        
        # Add relevant knowledge
        if knowledge and knowledge[0]['similarity'] > 0.3:
            response += knowledge[0]['content']
        
        return response
    
    def _handle_general_query(self, query: str, context: str, knowledge: List[Dict]) -> str:
        """Handle general health queries."""
        response = ""
        
        # Use the most relevant knowledge
        if knowledge and knowledge[0]['similarity'] > 0.3:
            response = knowledge[0]['content']
            
            # Add additional relevant information
            if len(knowledge) > 1 and knowledge[1]['similarity'] > 0.4:
                response += f"\n\nAdditionally, {knowledge[1]['content']}"
        else:
            # Provide a general helpful response
            response = "I'm here to help with your health and fitness journey! "
            response += "I can assist with questions about nutrition, exercise, BMI, goal setting, and general wellness. "
            response += "What specific aspect would you like to know more about?"
        
        # Add personalized touch if context available
        if context and any(word in context for word in ['BMI', 'goals', 'Weight']):
            response += "\n\nBased on your profile, I can provide personalized recommendations. Feel free to ask!"
        
        return response
