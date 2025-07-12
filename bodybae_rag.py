import os
import json
from typing import Dict, Optional, List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.schema import Document
import PyPDF2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    def __init__(self):
        """Initialize the RAG system with PDF knowledge base"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. Using fallback responses.")
            self.use_fallback = True
        else:
            self.use_fallback = False
            self._initialize_rag()
    
    def _initialize_rag(self):
        """Initialize RAG components"""
        try:
            # Initialize embeddings and LLM
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            self.llm = ChatOpenAI(
                temperature=0.7,
                model_name="gpt-3.5-turbo",
                openai_api_key=self.api_key
            )
            
            # Load knowledge base
            self.knowledge_base = self._load_knowledge_base()
            
            # Create vector store
            self.vectorstore = self._create_vectorstore()
            
            # Initialize memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            # Create conversation chain
            self.conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(search_kwargs={"k": 3}),
                memory=self.memory,
                verbose=True
            )
            
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.use_fallback = True
    
    def _extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
                return content
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return ""
    
    def _load_knowledge_base(self) -> List[Document]:
        """Load knowledge base from PDF or fallback to built-in content"""
        documents = []
        
        # Try to load PDF if it exists
        pdf_path = "home_hiit_guide.pdf"
        if os.path.exists(pdf_path):
            logger.info(f"Loading knowledge from PDF: {pdf_path}")
            pdf_content = self._extract_pdf_content(pdf_path)
            if pdf_content:
                # Split PDF content into chunks
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200,
                    length_function=len
                )
                chunks = text_splitter.split_text(pdf_content)
                documents.extend([
                    Document(page_content=chunk, metadata={"source": "home_hiit_guide.pdf"})
                    for chunk in chunks
                ])
        
        # Add built-in health knowledge
        health_knowledge = [
            {
                "topic": "BMI Information",
                "content": "BMI (Body Mass Index) is calculated as weight(kg) / height(m)². Categories: Underweight (<18.5), Normal (18.5-24.9), Overweight (25-29.9), Obese (≥30). BMI is a screening tool but doesn't account for muscle mass or body composition."
            },
            {
                "topic": "Calorie Requirements",
                "content": "Daily calorie needs depend on age, sex, weight, height, and activity level. Basal Metabolic Rate (BMR) is calories burned at rest. Total Daily Energy Expenditure (TDEE) = BMR × activity factor (1.2 for sedentary to 1.725 for very active)."
            },
            {
                "topic": "Weight Loss Basics",
                "content": "Safe weight loss is 0.5-1 kg per week. Create a caloric deficit of 500-750 calories daily through diet and exercise. Focus on whole foods, adequate protein (0.8-1.2g per kg body weight), and regular physical activity."
            },
            {
                "topic": "Muscle Building",
                "content": "Building muscle requires progressive overload, adequate protein (1.6-2.2g per kg body weight), sufficient calories (slight surplus), and proper recovery. Visible results typically appear after 8-12 weeks of consistent training."
            },
            {
                "topic": "HIIT Training",
                "content": "High-Intensity Interval Training alternates between intense bursts and recovery periods. Benefits include improved cardiovascular fitness, increased metabolism, and time efficiency. Start with 2-3 sessions per week."
            },
            {
                "topic": "Nutrition Guidelines",
                "content": "Balanced diet: 45-65% carbohydrates, 20-35% fats, 10-35% protein. Eat variety of fruits, vegetables, whole grains, lean proteins, and healthy fats. Stay hydrated with 8-10 glasses of water daily."
            },
            {
                "topic": "Recovery and Sleep",
                "content": "Adequate sleep (7-9 hours) is crucial for muscle recovery, hormone regulation, and overall health. Include rest days in training schedule. Active recovery like walking or yoga can aid recovery."
            },
            {
                "topic": "Exercise Recommendations",
                "content": "Adults should aim for 150 minutes moderate-intensity or 75 minutes vigorous-intensity aerobic activity weekly, plus strength training 2+ days per week. Start gradually and progress slowly."
            }
        ]
        
        # Add built-in knowledge
        for item in health_knowledge:
            documents.append(
                Document(
                    page_content=f"{item['topic']}: {item['content']}",
                    metadata={"source": "built_in_knowledge", "topic": item['topic']}
                )
            )
        
        return documents
    
    def _create_vectorstore(self):
        """Create FAISS vector store from documents"""
        if not self.knowledge_base:
            raise ValueError("No knowledge base loaded")
        
        # Create vector store
        vectorstore = FAISS.from_documents(
            documents=self.knowledge_base,
            embedding=self.embeddings
        )
        
        logger.info(f"Created vector store with {len(self.knowledge_base)} documents")
        return vectorstore
    
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
