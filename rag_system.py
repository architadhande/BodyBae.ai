import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    from sentence_transformers import SentenceTransformer
    import chromadb
    import torch
    
    DEPENDENCIES_AVAILABLE = True
    logger.info("✅ All AI dependencies loaded successfully")
    
except ImportError as e:
    logger.warning(f"⚠️ AI dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False

class SmolLMHealthRAG:
    """Advanced RAG system using SmolLM3-3B for health coaching"""
    
    def __init__(self):
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError("Required AI dependencies not available")
        
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🔧 Using device: {self.device}")
        
        # Initialize embedding model
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            raise
        
        # Initialize SmolLM3-3B model
        try:
            model_name = "HuggingFaceTB/SmolLM3-3B"
            logger.info(f"🔄 Loading {model_name}...")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            
            logger.info("✅ SmolLM3-3B model loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to load SmolLM3 model: {e}")
            raise
        
        # Initialize vector database
        try:
            self.chroma_client = chromadb.Client()
            self.collection = None
            self.setup_health_knowledge_base()
            logger.info("✅ Vector database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector database: {e}")
            raise
    
    def setup_health_knowledge_base(self):
        """Set up comprehensive health knowledge base"""
        
        # Comprehensive health knowledge for RAG
        health_knowledge = [
            {
                "topic": "Weight Loss Science",
                "content": """Weight loss occurs through creating a caloric deficit where energy expenditure exceeds energy intake. 
                Safe weight loss: 0.5-1kg per week through 500-750 calorie daily deficit. Key mechanisms include:
                
                Metabolic factors: BMR accounts for 60-70% of daily energy expenditure. Thermic effect of food (TEF) 
                contributes 8-10%. Physical activity and NEAT account for remaining expenditure.
                
                Hormonal regulation: Leptin decreases with fat loss, increasing hunger. Ghrelin increases appetite. 
                Insulin sensitivity improves with weight loss. Cortisol elevation can impair fat loss.
                
                Effective strategies: High protein intake (1.2-1.6g/kg) preserves muscle mass. Resistance training 
                maintains metabolic rate. Adequate sleep (7-9 hours) regulates appetite hormones. Stress management 
                prevents cortisol-driven fat storage.
                
                Sustainable approach: Gradual calorie reduction, flexible dieting approach, regular refeed days, 
                behavior modification, social support systems."""
            },
            {
                "topic": "Muscle Building Science",
                "content": """Muscle hypertrophy occurs through mechanical tension, metabolic stress, and muscle damage. 
                Protein synthesis must exceed protein breakdown for net muscle growth.
                
                Progressive overload: Systematic increase in training volume, intensity, or density. Rep ranges 
                6-20 effective for hypertrophy with higher volumes. Frequency: 2-3x per week per muscle group optimal.
                
                Protein requirements: 1.6-2.2g/kg bodyweight daily for trained individuals. Leucine threshold 
                ~2.5g per meal triggers muscle protein synthesis. Timing: protein every 3-4 hours optimizes synthesis.
                
                Training variables: Volume 10-20 sets per muscle per week. Intensity 65-85% 1RM. Rest periods 
                2-3 minutes for compound movements, 1-2 minutes for isolation. Eccentric emphasis enhances hypertrophy.
                
                Recovery factors: Sleep 7-9 hours for growth hormone release. Stress management prevents cortisol 
                interference. Hydration supports protein synthesis. Micronutrients: zinc, magnesium, vitamin D critical.
                
                Periodization: Block periodization, daily undulating periodization, or linear progression based on 
                training age and goals."""
            },
            {
                "topic": "Cardiovascular Health",
                "content": """Cardiovascular exercise strengthens heart muscle, improves circulation, reduces blood pressure, 
                and enhances oxygen delivery. Multiple training zones optimize different adaptations.
                
                Heart rate zones: Zone 1 (50-60% max HR) active recovery and fat oxidation. Zone 2 (60-70% max HR) 
                aerobic base building. Zone 3 (70-80% max HR) tempo training. Zone 4 (80-90% max HR) lactate threshold. 
                Zone 5 (90-100% max HR) neuromuscular power.
                
                Training methods: LISS (Low Intensity Steady State) improves mitochondrial density and fat oxidation. 
                HIIT (High Intensity Interval Training) enhances VO2 max and metabolic flexibility. Fartlek training 
                combines benefits of both.
                
                Adaptations: Increased stroke volume, lower resting heart rate, improved capillary density, 
                enhanced oxygen extraction, better blood lipid profiles, reduced inflammation markers.
                
                Programming: 150 minutes moderate or 75 minutes vigorous weekly minimum. Polarized training 
                80% low intensity, 20% high intensity. Recovery between HIIT sessions 48-72 hours.
                
                Health benefits: Reduced cardiovascular disease risk, improved insulin sensitivity, enhanced 
                cognitive function, better mood regulation, increased longevity."""
            },
            {
                "topic": "Nutrition Science",
                "content": """Optimal nutrition supports energy production, tissue repair, immune function, and hormonal balance. 
                Macronutrient and micronutrient timing affects metabolic outcomes.
                
                Macronutrient functions: Carbohydrates provide immediate energy and glycogen storage. Proteins supply 
                amino acids for tissue synthesis and repair. Fats support hormone production and vitamin absorption.
                
                Nutrient timing: Pre-workout carbohydrates enhance performance. Post-workout protein and carbs optimize 
                recovery. Evening protein supports overnight muscle protein synthesis. Morning protein aids satiety.
                
                Micronutrient cofactors: B vitamins for energy metabolism. Vitamin D for immune and bone health. 
                Magnesium for muscle function. Zinc for protein synthesis. Iron for oxygen transport.
                
                Hydration science: 35-40ml per kg bodyweight daily baseline. Additional 500-750ml per hour of exercise. 
                Electrolyte balance crucial for performance and recovery. Hyponatremia risk with excessive water intake.
                
                Dietary strategies: Mediterranean diet reduces inflammation. Intermittent fasting may improve insulin 
                sensitivity. Plant-based diets support cardiovascular health. Ketogenic diets may benefit metabolic disorders.
                
                Individual variation: Genetic polymorphisms affect nutrient metabolism. Food intolerances require 
                personalized approaches. Metabolic flexibility varies between individuals."""
            },
            {
                "topic": "Sleep and Recovery",
                "content": """Sleep facilitates physical recovery, memory consolidation, hormonal regulation, and immune function. 
                Sleep architecture includes multiple stages with distinct functions.
                
                Sleep stages: Stage 1-2 light sleep for transition. Stage 3-4 deep sleep for physical recovery and 
                growth hormone release. REM sleep for cognitive recovery and memory consolidation.
                
                Recovery mechanisms: Muscle protein synthesis peaks during deep sleep. Growth hormone release occurs 
                primarily in first half of night. Inflammatory markers decrease with adequate sleep. Glycogen 
                replenishment occurs during rest.
                
                Sleep optimization: Consistent sleep-wake times regulate circadian rhythm. Dark, cool environment 
                (65-68°F) promotes deep sleep. Blue light exposure reduction 2 hours before bed. Caffeine clearance 
                requires 6-8 hours.
                
                Recovery modalities: Active recovery promotes blood flow without stress. Massage reduces muscle tension 
                and inflammation. Cold therapy may enhance recovery and adaptation. Heat therapy improves circulation.
                
                Stress management: Chronic stress elevates cortisol, impairing recovery. Meditation reduces stress 
                hormones. Progressive muscle relaxation improves sleep quality. Social support buffers stress impact.
                
                Monitoring recovery: Heart rate variability indicates autonomic recovery. Subjective wellness 
                questionnaires track fatigue. Performance metrics reveal adaptation status."""
            },
            {
                "topic": "Exercise Programming",
                "content": """Effective exercise programming applies specificity, progressive overload, recovery, and variation 
                principles. Program design depends on goals, training age, and individual factors.
                
                Training principles: Specificity - adaptations match training demands. Progressive overload - gradual 
                increase in training stress. Recovery - adaptation occurs during rest. Individual differences - programs 
                must be personalized.
                
                Periodization models: Linear periodization progresses from high volume to high intensity. Block 
                periodization focuses on specific qualities sequentially. Daily undulating periodization varies 
                intensity and volume frequently.
                
                Exercise selection: Compound movements recruit multiple muscle groups efficiently. Isolation exercises 
                target specific muscles. Movement patterns include squat, hinge, push, pull, carry, rotate.
                
                Load management: Training load = volume × intensity. Acute:chronic workload ratio predicts injury risk. 
                Deload weeks prevent overreaching. Autoregulation adjusts training based on readiness.
                
                Program variables: Frequency (sessions per week), Volume (sets × reps), Intensity (% 1RM or RPE), 
                Density (work:rest ratio), Duration (session length).
                
                Adaptation timeline: Neural adaptations occur within 2-4 weeks. Structural adaptations require 
                6-12 weeks. Detaining occurs within 2-3 weeks of cessation."""
            },
            {
                "topic": "Behavioral Psychology",
                "content": """Behavior change requires understanding motivation, habit formation, and psychological factors. 
                Sustainable health behaviors develop through systematic approaches.
                
                Motivation theory: Intrinsic motivation (autonomy, mastery, purpose) sustains long-term adherence. 
                Extrinsic motivation provides short-term compliance. Self-determination theory explains motivation sources.
                
                Habit formation: Habits form through cue-routine-reward loops. Implementation intentions link 
                behaviors to environmental cues. Habit stacking builds new behaviors onto existing ones.
                
                Goal setting: SMART goals (Specific, Measurable, Achievable, Relevant, Time-bound) improve success. 
                Process goals focus on behaviors. Outcome goals focus on results. Approach goals outperform avoidance goals.
                
                Cognitive strategies: Self-monitoring increases awareness. Cognitive restructuring addresses negative 
                thoughts. Visualization improves performance and adherence. Mindfulness reduces emotional eating.
                
                Social factors: Social support improves adherence. Accountability partners increase compliance. 
                Group dynamics enhance motivation. Environmental design shapes behavior choices.
                
                Behavior change techniques: Gradual progression prevents overwhelm. Relapse prevention plans maintain 
                progress. Reward systems reinforce positive behaviors. Barrier identification enables problem-solving."""
            }
        ]
        
        # Create collection and add documents
        try:
            self.collection = self.chroma_client.create_collection(
                name="health_knowledge",
                metadata={"description": "Comprehensive health and fitness knowledge base"}
            )
            
            documents = []
            metadatas = []
            ids = []
            
            for i, item in enumerate(health_knowledge):
                documents.append(item["content"])
                metadatas.append({"topic": item["topic"], "source": "health_kb"})
                ids.append(f"doc_{i}")
            
            # Generate embeddings and add to collection
            embeddings = self.embedding_model.encode(documents).tolist()
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Added {len(documents)} documents to knowledge base")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup knowledge base: {e}")
            raise
    
    def retrieve_relevant_context(self, query: str, n_results: int = 3) -> str:
        """Retrieve relevant context from knowledge base"""
        try:
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results
            )
            
            # Combine retrieved documents
            context = "\n\n".join(results['documents'][0])
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return ""
    
    def generate_health_response(self, user_message: str, user_profile: Dict = None, conversation_history: List = None) -> str:
        """Generate intelligent health response using SmolLM3-3B with RAG"""
        try:
            # Retrieve relevant context
            relevant_context = self.retrieve_relevant_context(user_message)
            
            # Build comprehensive prompt
            system_prompt = """You are BodyBae, an expert AI health and fitness coach. You provide evidence-based, personalized advice using scientific knowledge. Your responses are helpful, encouraging, and actionable.

Guidelines:
- Use the provided knowledge context to give accurate advice
- Consider the user's profile for personalized recommendations
- Be supportive and motivational
- Provide specific, actionable steps
- Include relevant scientific explanations when helpful
- If medical concerns arise, recommend consulting healthcare professionals

"""
            
            # Add user profile context
            profile_context = ""
            if user_profile:
                profile_context = f"""
User Profile:
- Name: {user_profile.get('name', 'User')}
- Age: {user_profile.get('age', 'N/A')}
- Gender: {user_profile.get('gender', 'N/A')}
- Height: {user_profile.get('height', 'N/A')}cm
- Weight: {user_profile.get('weight', 'N/A')}kg
- Activity Level: {user_profile.get('activity', 'N/A')}
- Goals: {', '.join(user_profile.get('goals', []))}
- BMI: {user_profile.get('bmi', 'N/A')}

"""
            
            # Build conversation context
            conversation_context = ""
            if conversation_history:
                recent_history = conversation_history[-4:]  # Last 2 exchanges
                conversation_context = "Recent conversation:\n"
                for msg in recent_history:
                    role = "User" if msg['role'] == 'user' else "BodyBae"
                    conversation_context += f"{role}: {msg['content']}\n"
                conversation_context += "\n"
            
            # Create full prompt
            full_prompt = f"""{system_prompt}

{profile_context}

Relevant Knowledge:
{relevant_context}

{conversation_context}

User Question: {user_message}

BodyBae Response:"""
            
            # Generate response using SmolLM3
            response = self.generator(
                full_prompt,
                max_new_tokens=300,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1
            )
            
            # Extract generated text
            generated_text = response[0]['generated_text']
            
            # Extract only the response part
            response_start = generated_text.find("BodyBae Response:") + len("BodyBae Response:")
            ai_response = generated_text[response_start:].strip()
            
            # Clean up response
            ai_response = self.clean_response(ai_response)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_fallback_response(user_message, user_profile)
    
    def clean_response(self, response: str) -> str:
        """Clean and format the AI response"""
        # Remove any remaining prompt artifacts
        lines = response.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip empty lines and prompt artifacts
            if line and not line.startswith('User:') and not line.startswith('BodyBae:'):
                cleaned_lines.append(line)
        
        # Join lines and limit length
        cleaned_response = '\n'.join(cleaned_lines)
        
        # Limit response length
        if len(cleaned_response) > 1000:
            cleaned_response = cleaned_response[:1000] + "..."
        
        return cleaned_response
    
    def get_fallback_response(self, user_message: str, user_profile: Dict = None) -> str:
        """Fallback response when AI generation fails"""
        name = user_profile.get('name', 'there') if user_profile else 'there'
        
        return f"Hi {name}! I'm experiencing some technical difficulties, but I'm here to help with your health and fitness journey. Could you please rephrase your question? I can assist with workout plans, nutrition advice, goal setting, and motivation!"

# Test function
def test_smol_lm_rag():
    """Test the SmolLM RAG system"""
    try:
        rag = SmolLMHealthRAG()
        
        test_profile = {
            'name': 'Alex',
            'age': 28,
            'gender': 'male',
            'height': 175,
            'weight': 70,
            'activity': 'moderately_active',
            'goals': ['Weight Loss', 'Muscle Building'],
            'bmi': 22.9
        }
        
        test_questions = [
            "How should I structure my workout routine?",
            "What's the best way to lose fat while building muscle?",
            "How much protein do I need daily?",
            "I'm feeling unmotivated, can you help?"
        ]
        
        print("🧪 Testing SmolLM3 Health RAG System:")
        print("=" * 60)
        
        for question in test_questions:
            print(f"\nQ: {question}")
            response = rag.generate_health_response(question, test_profile)
            print(f"A: {response}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    if DEPENDENCIES_AVAILABLE:
        success = test_smol_lm_rag()
        if success:
            print("✅ SmolLM3 Health RAG system test completed!")
        else:
            print("❌ Test failed!")
    else:
        print("❌ Dependencies not available for testing")