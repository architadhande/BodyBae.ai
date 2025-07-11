from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
import json
import random
from datetime import datetime
from config import Config

class ChatbotService:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            openai_api_key=Config.OPENAI_API_KEY
        )
        
        self.memory = ConversationBufferMemory()
        
        # Load tips and motivation
        with open('data/tips_motivation.json', 'r') as f:
            self.tips_data = json.load(f)
        
        # Define conversation prompt
        self.prompt = PromptTemplate(
            input_variables=["history", "input"],
            template="""You are BodyBae, a friendly and knowledgeable fitness assistant. 
            You help users with their health and fitness journey.
            
            Previous conversation:
            {history}
            
            Human: {input}
            
            BodyBae: Let me help you with that!"""
        )
        
        self.conversation = ConversationChain(
            llm=self.llm,
            memory=self.memory,
            prompt=self.prompt,
            verbose=False
        )
    
    def process_message(self, message, user_id=None):
        """Process incoming message and determine response type"""
        
        # Check for onboarding flow
        if any(keyword in message.lower() for keyword in ['start', 'begin', 'hello', 'hi']):
            return self.start_onboarding()
        
        # Check for goal-related keywords
        if any(keyword in message.lower() for keyword in ['goal', 'target', 'achieve', 'want to']):
            return self.guide_goal_setting()
        
        # Check for progress-related keywords
        if any(keyword in message.lower() for keyword in ['progress', 'update', 'log', 'track']):
            return self.guide_progress_logging()
        
        # Default to conversational response
        try:
            response = self.conversation.predict(input=message)
            return {
                'type': 'chat',
                'message': response
            }
        except Exception as e:
            return {
                'type': 'error',
                'message': "I'm having trouble processing that. Could you rephrase your question?"
            }
    
    def start_onboarding(self):
        return {
            'type': 'onboarding',
            'step': 'welcome',
            'message': "Welcome to BodyBae! 🎯 I'm here to help you achieve your fitness goals. Let's start by getting to know you better. What's your name?"
        }
    
    def guide_goal_setting(self):
        return {
            'type': 'goal_setting',
            'message': "Great! Let's set up your fitness goals. What would you like to achieve? You can choose from: Lose Weight, Gain Weight, Gain Muscle, Lose Fat, Toning, or Bulking.",
            'options': ['Lose Weight', 'Gain Weight', 'Gain Muscle', 'Lose Fat', 'Toning', 'Bulking']
        }
    
    def guide_progress_logging(self):
        return {
            'type': 'progress_logging',
            'message': "Time to log your progress! What would you like to update today?",
            'options': ['Weight', 'Workout', 'Calories', 'All']
        }
    
    def get_daily_tip(self, user_id=None):
        """Get a daily tip based on user's goals or general fitness"""
        # For now, return a random tip
        category = random.choice(['nutrition', 'exercise', 'motivation', 'recovery'])
        tips = self.tips_data.get(category, [])
        
        if tips:
            return random.choice(tips)
        
        return "Stay consistent with your fitness journey! Every small step counts towards your goals. 💪"