import os
import json
from typing import Dict, Optional, List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from langchain.schema import Document
import PyPDF2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system with lightweight alternatives"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Using fallback responses.")
            self.use_fallback = True
        else:
            self.use_fallback = False
            self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialize RAG components with sentence-transformers"""
        try:
            # Use lightweight sentence-transformers instead of OpenAI embeddings
            self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')
            self.knowledge_base = self._load_knowledge_base()
            
            # Pre-compute document embeddings
            self.doc_embeddings = self._create_embeddings()
            
            logger.info("RAG system initialized with sentence-transformers")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.use_fallback = True

    def _create_embeddings(self):
        """Create embeddings for all documents"""
        texts = [doc.page_content for doc in self.knowledge_base]
        return self.embeddings.encode(texts, show_progress_bar=False)

    # Keep all other methods exactly the same until get_response()
    # [Previous _extract_pdf_content, _load_knowledge_base methods remain unchanged]

    def get_response(self, query: str, user_profile: Optional[Dict] = None) -> str:
        """Get response using similarity search with sentence-transformers"""
        if self.use_fallback:
            return self._get_fallback_response(query, user_profile)
        
        try:
            # Add user context to query if available
            context_query = query
            if user_profile:
                context = f"User profile: {user_profile.get('name', 'User')}, "
                context += f"Age: {user_profile.get('age', 'unknown')}, "
                context += f"BMI: {user_profile.get('bmi', 'unknown')}, "
                context += f"Goal: {user_profile.get('goal', 'general fitness')}. "
                context_query = context + query
            
            # Get most relevant document
            query_embedding = self.embeddings.encode([context_query])
            similarities = cosine_similarity(query_embedding, self.doc_embeddings)[0]
            most_similar_idx = np.argmax(similarities)
            
            if similarities[most_similar_idx] > 0.6:  # Similarity threshold
                return self.knowledge_base[most_similar_idx].page_content
            return self._get_fallback_response(query, user_profile)
            
        except Exception as e:
            logger.error(f"Error in RAG response: {e}")
            return self._get_fallback_response(query, user_profile)
    
    def get_response(self, query: str, user_profile: Optional[Dict] = None) -> str:
        """Get response to user query using RAG or fallback"""
        if self.use_fallback:
            return self._get_fallback_response(query, user_profile)
        
        try:
            # Add user context to query if available
            context_query = query
            if user_profile:
                context = f"User profile: {user_profile.get('name', 'User')}, "
                context += f"Age: {user_profile.get('age', 'unknown')}, "
                context += f"BMI: {user_profile.get('bmi', 'unknown')}, "
                context += f"Goal: {user_profile.get('goal', 'general fitness')}. "
                context_query = context + query
            
            # Get response from conversation chain
            result = self.conversation_chain({"question": context_query})
            return result['answer']
        
        except Exception as e:
            logger.error(f"Error getting RAG response: {e}")
            return self._get_fallback_response(query, user_profile)
    
    def _get_fallback_response(self, query: str, user_profile: Optional[Dict] = None) -> str:
        """Provide fallback responses when RAG is not available"""
        query_lower = query.lower()
        
        # Calorie-related queries
        if any(word in query_lower for word in ['calorie', 'calories', 'eat', 'food']):
            return "For weight loss, aim for a 500-750 calorie deficit. For muscle gain, eat in a slight surplus (200-500 calories). Your daily needs depend on your age, weight, height, and activity level. Focus on whole foods and adequate protein!"
        
        # Exercise queries
        elif any(word in query_lower for word in ['exercise', 'workout', 'hiit', 'training']):
            return "For general fitness, aim for 150 minutes of moderate cardio or 75 minutes of vigorous cardio weekly, plus 2-3 strength training sessions. HIIT is great for efficiency - try 20-30 minute sessions 2-3 times per week. Always warm up and cool down!"
        
        # Weight loss queries
        elif any(word in query_lower for word in ['weight loss', 'lose weight', 'fat loss']):
            return "Safe weight loss is 0.5-1 kg per week. Create a moderate caloric deficit through diet and exercise. Focus on whole foods, adequate protein (0.8-1.2g per kg body weight), and combine cardio with strength training. Be patient and consistent!"
        
        # Muscle building queries
        elif any(word in query_lower for word in ['muscle', 'gain muscle', 'build muscle', 'bulking']):
            return "To build muscle: eat adequate protein (1.6-2.2g per kg body weight), slight caloric surplus, progressive overload in training, and get 7-9 hours of sleep. Focus on compound exercises and be consistent. Results typically show after 8-12 weeks."
        
        # BMI queries
        elif any(word in query_lower for word in ['bmi', 'body mass index', 'weight category']):
            return "BMI = weight(kg) / height(m)². Categories: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30). Remember, BMI doesn't account for muscle mass, so it's just one health indicator among many."
        
        # Nutrition queries
        elif any(word in query_lower for word in ['nutrition', 'diet', 'protein', 'carbs', 'fats']):
            return "Aim for balanced nutrition: 45-65% carbs, 20-35% fats, 10-35% protein. Eat variety of fruits, vegetables, whole grains, lean proteins, and healthy fats. Stay hydrated with 8-10 glasses of water daily. Focus on whole foods over processed ones."
        
        # Recovery queries
        elif any(word in query_lower for word in ['recovery', 'rest', 'sleep', 'sore']):
            return "Recovery is crucial! Get 7-9 hours of quality sleep, include rest days in your routine, stay hydrated, and eat adequate protein. Light activity (walking, yoga) on rest days can help. Listen to your body - some soreness is normal, sharp pain is not."
        
        # Motivation queries
        elif any(word in query_lower for word in ['motivation', 'motivated', 'discipline', 'consistent']):
            return "Motivation gets you started, but discipline keeps you going! Set small, achievable goals. Track your progress. Find activities you enjoy. Remember why you started. Progress isn't always linear - trust the process and celebrate small wins!"
        
        # Default response
        else:
            return "I'm here to help with your fitness journey! Ask me about nutrition, exercise, weight management, muscle building, or any health-related topic. Remember, consistency is key to achieving your goals!"
    
    def clear_memory(self):
        """Clear conversation memory"""
        if hasattr(self, 'memory'):
            self.memory.clear()

# Test the RAG system
if __name__ == "__main__":
    rag = RAGSystem()
    
    test_queries = [
        "How many calories should I eat for weight loss?",
        "What's a good HIIT workout for beginners?",
        "How much protein do I need to build muscle?",
        "What does BMI of 25 mean?"
    ]
    
    print("Testing RAG System:")
    for query in test_queries:
        print(f"\nQ: {query}")
        response = rag.get_response(query)
        print(f"A: {response}")
