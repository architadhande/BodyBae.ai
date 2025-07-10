from flask import Flask, render_template_string, request, jsonify, session
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
import uuid

# Import the RAG system
try:
    from rag_system import HealthRAGSystem
    RAG_AVAILABLE = True
    print("✅ RAG system imported successfully")
except ImportError as e:
    print(f"⚠️ RAG system not available: {e}")
    RAG_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# In-memory storage (replace with database in production)
users_db = {}
progress_db = {}
goals_db = {}
chat_history_db = {}

# Initialize RAG system
rag_system = None
if RAG_AVAILABLE:
    try:
        rag_system = HealthRAGSystem()
        print("✅ Health RAG system initialized successfully")
    except Exception as e:
        print(f"⚠️ RAG system error: {e} - using fallback")
        rag_system = None

class BodyBaeAI:
    def __init__(self):
        self.health_tips = {
            "Lose Weight": [
                "Create a moderate caloric deficit of 500-750 calories per day for healthy weight loss",
                "Focus on whole foods: lean proteins, vegetables, fruits, and whole grains",
                "Stay hydrated - drink water before meals to help with satiety",
                "Combine cardio and strength training for optimal fat loss while preserving muscle"
            ],
            "Gain Muscle": [
                "Consume 1.6-2.2g of protein per kg of body weight daily",
                "Progressive overload is key - gradually increase weight, reps, or sets",
                "Get 7-9 hours of quality sleep for muscle recovery and growth hormone release",
                "Focus on compound movements like squats, deadlifts, bench press, and rows"
            ],
            "General Fitness": [
                "Combine cardio, strength training, and flexibility work for balanced fitness",
                "Aim for 150 minutes of moderate cardio plus 2-3 strength sessions weekly",
                "Focus on functional movements that improve daily life activities",
                "Find activities you enjoy to make fitness sustainable long-term"
            ]
        }
        
        self.motivational_messages = [
            "Every workout counts, no matter how small! 💪",
            "Progress isn't always linear - trust the process! 📈",
            "Your body can do it. It's your mind you need to convince! 🧠",
            "You're stronger than you think and capable of amazing things! ⭐"
        ]
    
    def calculate_bmr(self, weight: float, height: float, age: int, sex: str) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor Equation"""
        if sex.lower() in ['male', 'man', 'm']:
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        return bmr
    
    def calculate_tdee(self, bmr: float, activity_level: str) -> float:
        """Calculate Total Daily Energy Expenditure"""
        activity_multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }
        return bmr * activity_multipliers.get(activity_level, 1.2)
    
    def calculate_bmi(self, weight: float, height: float) -> Dict:
        """Calculate BMI and return category with recommendations"""
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        
        if bmi < 18.5:
            category = "Underweight"
            advice = "Consider focusing on healthy weight gain with nutrient-dense foods."
        elif bmi < 25:
            category = "Normal Weight"
            advice = "Great job maintaining a healthy weight! Focus on overall fitness."
        elif bmi < 30:
            category = "Overweight"
            advice = "Consider a moderate weight loss approach with balanced nutrition and exercise."
        else:
            category = "Obese"
            advice = "Consult with healthcare professionals for a comprehensive weight management plan."
        
        return {
            "bmi": round(bmi, 1),
            "category": category,
            "advice": advice
        }
    
    def get_daily_tip(self, goal: str) -> str:
        """Get a daily tip based on user's goal"""
        tips = self.health_tips.get(goal, self.health_tips["General Fitness"])
        import random
        return random.choice(tips)
    
    def get_motivation(self) -> str:
        """Get a motivational message"""
        import random
        return random.choice(self.motivational_messages)

# Initialize the AI assistant
bodybae = BodyBaeAI()

# HTML template for the frontend
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BodyBae.ai - AI Health Chatbot</title>
    <style>
        :root {
            --sage-green: #A4B07E;
            --olive-green: #707C4F;
            --dark-green: #424106;
            --cream: #d4cbbc;
            --mauve: #C6A6B5;
            --brown: #6D4930;
            --white: #ffffff;
            --light-cream: #f9f7f4;
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--light-cream) 0%, var(--cream) 100%);
            min-height: 100vh;
        }
        
        .welcome-screen {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
            color: white;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .welcome-screen::before {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 200px;
            background: var(--light-cream);
            clip-path: ellipse(100% 100% at 50% 100%);
        }
        
        .welcome-content {
            position: relative;
            z-index: 10;
            animation: fadeInUp 1s ease-out;
        }
        
        .logo {
            font-size: 4rem;
            font-weight: 600;
            margin-bottom: 1rem;
            background: linear-gradient(45deg, var(--cream), var(--mauve));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .tagline {
            font-size: 1.8rem;
            margin-bottom: 1rem;
            opacity: 0.95;
        }
        
        .subtitle {
            font-size: 1.2rem;
            margin-bottom: 3rem;
            opacity: 0.85;
        }
        
        .cta-button {
            background: linear-gradient(45deg, var(--mauve), var(--brown));
            color: white;
            border: none;
            padding: 1.2rem 3rem;
            font-size: 1.2rem;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        }
        
        .cta-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.4);
        }
        
        .chat-screen {
            display: none;
            min-height: 100vh;
            padding: 2rem;
        }
        
        .chat-container {
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 2rem;
            height: calc(100vh - 4rem);
        }
        
        .chat-main {
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            border: 1px solid var(--sage-green);
        }
        
        .chat-header {
            background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
            color: white;
            padding: 2rem;
            text-align: center;
            border-radius: 20px 20px 0 0;
        }
        
        .chat-title {
            font-size: 2rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        .chat-subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .chat-messages {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .message {
            max-width: 80%;
            padding: 1rem 1.5rem;
            border-radius: 20px;
            line-height: 1.6;
            animation: slideIn 0.3s ease-out;
        }
        
        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
            color: white;
            border-bottom-right-radius: 8px;
        }
        
        .message.bot {
            align-self: flex-start;
            background: var(--light-cream);
            color: var(--dark-green);
            border: 1px solid var(--cream);
            border-bottom-left-radius: 8px;
        }
        
        .typing-indicator {
            align-self: flex-start;
            background: var(--light-cream);
            padding: 1rem 1.5rem;
            border-radius: 20px;
            border-bottom-left-radius: 8px;
            display: none;
        }
        
        .typing-dots {
            display: flex;
            gap: 6px;
        }
        
        .typing-dot {
            width: 10px;
            height: 10px;
            background: var(--sage-green);
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        .chat-input-area {
            padding: 1.5rem 2rem;
            background: white;
            border-top: 1px solid var(--cream);
        }
        
        .quick-suggestions {
            display: flex;
            gap: 0.8rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        .suggestion-chip {
            background: var(--cream);
            color: var(--dark-green);
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
        }
        
        .suggestion-chip:hover {
            background: var(--sage-green);
            color: white;
        }
        
        .input-wrapper {
            display: flex;
            gap: 1rem;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            border: 2px solid var(--cream);
            border-radius: 25px;
            padding: 1rem 1.5rem;
            font-size: 1rem;
            resize: none;
            max-height: 120px;
            font-family: inherit;
            background: var(--light-cream);
        }
        
        .chat-input:focus {
            outline: none;
            border-color: var(--sage-green);
            background: white;
        }
        
        .send-button {
            background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
            color: white;
            border: none;
            width: 55px;
            height: 55px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.3rem;
            transition: all 0.3s ease;
        }
        
        .send-button:hover {
            transform: scale(1.05);
        }
        
        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        
        .sidebar-card {
            background: white;
            border-radius: 20px;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            border: 1px solid var(--sage-green);
        }
        
        .card-title {
            color: var(--olive-green);
            font-size: 1.4rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            text-align: center;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--dark-green);
            font-weight: 500;
            font-size: 0.9rem;
        }
        
        .form-input {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid var(--cream);
            border-radius: 10px;
            font-size: 0.9rem;
            background: var(--light-cream);
            transition: all 0.3s ease;
        }
        
        .form-input:focus {
            outline: none;
            border-color: var(--sage-green);
            background: white;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.8rem;
        }
        
        .gender-options {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        
        .gender-option {
            padding: 0.6rem;
            border: 2px solid var(--cream);
            border-radius: 8px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: var(--light-cream);
            font-size: 0.8rem;
        }
        
        .gender-option:hover,
        .gender-option.selected {
            border-color: var(--sage-green);
            background: var(--sage-green);
            color: white;
        }
        
        .calculate-btn {
            background: linear-gradient(45deg, var(--mauve), var(--brown));
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 12px;
            font-size: 1rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 1rem;
            width: 100%;
        }
        
        .calculate-btn:hover {
            transform: translateY(-2px);
        }
        
        .bmi-display {
            text-align: center;
            padding: 1.5rem;
            background: linear-gradient(135deg, var(--light-cream), var(--cream));
            border-radius: 15px;
            margin-top: 1rem;
        }
        
        .bmi-number {
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--olive-green);
            margin-bottom: 0.5rem;
        }
        
        .bmi-category {
            font-size: 1.1rem;
            font-weight: 500;
            color: var(--brown);
            margin-bottom: 0.5rem;
        }
        
        .bmi-advice {
            font-size: 0.9rem;
            color: var(--dark-green);
        }
        
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-10px); }
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        @media (max-width: 968px) {
            .chat-container {
                grid-template-columns: 1fr;
                height: auto;
            }
            
            .chat-main {
                height: 70vh;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .gender-options {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <!-- Welcome Screen -->
    <div id="welcome-screen" class="welcome-screen">
        <div class="welcome-content">
            <h1 class="logo">BodyBae.ai</h1>
            <p class="tagline">AI Health & Fitness Chatbot</p>
            <p class="subtitle">Your intelligent companion for a healthier lifestyle</p>
            <button class="cta-button" onclick="startChat()">
                Start Chatting
            </button>
        </div>
    </div>

    <!-- Chat Screen -->
    <div id="chat-screen" class="chat-screen">
        <div class="chat-container">
            <!-- Main Chat Area -->
            <div class="chat-main">
                <div class="chat-header">
                    <h2 class="chat-title">💬 BodyBae AI Assistant</h2>
                    <p class="chat-subtitle">Your personal health & fitness expert</p>
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    <div class="message bot">
                        Hi there! 👋 I'm BodyBae, your AI health and fitness assistant. I'm here to help you with personalized advice, workout plans, nutrition guidance, and motivation. 
                        <br><br>
                        To get started, please fill out your profile on the right, and then we can chat about your health goals!
                    </div>
                </div>

                <div class="typing-indicator" id="typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                </div>

                <div class="chat-input-area">
                    <div class="quick-suggestions">
                        <button class="suggestion-chip" onclick="sendQuickMessage('What should I eat for breakfast?')">Breakfast ideas</button>
                        <button class="suggestion-chip" onclick="sendQuickMessage('Give me a workout plan')">Workout plan</button>
                        <button class="suggestion-chip" onclick="sendQuickMessage('I need motivation')">Motivation</button>
                        <button class="suggestion-chip" onclick="sendQuickMessage('How much water should I drink?')">Hydration tips</button>
                    </div>
                    
                    <div class="input-wrapper">
                        <textarea 
                            class="chat-input" 
                            id="chat-input" 
                            placeholder="Ask me anything about health, fitness, nutrition..."
                            rows="1"
                        ></textarea>
                        <button class="send-button" id="send-button" onclick="sendMessage()">
                            ➤
                        </button>
                    </div>
                </div>
            </div>

            <!-- Sidebar -->
            <div class="sidebar">
                <!-- User Profile Form -->
                <div class="sidebar-card">
                    <h3 class="card-title">👤 Your Profile</h3>
                    
                    <div class="form-group">
                        <label class="form-label">Name</label>
                        <input type="text" class="form-input" id="name" placeholder="Enter your name">
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Age</label>
                            <input type="number" class="form-input" id="age" min="13" max="100" placeholder="25">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Gender</label>
                            <div class="gender-options">
                                <div class="gender-option" data-value="male">M</div>
                                <div class="gender-option" data-value="female">F</div>
                                <div class="gender-option" data-value="other">Other</div>
                            </div>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label class="form-label">Height (cm)</label>
                            <input type="number" class="form-input" id="height" min="100" max="250" placeholder="170">
                        </div>
                        <div class="form-group">
                            <label class="form-label">Weight (kg)</label>
                            <input type="number" class="form-input" id="weight" min="30" max="300" step="0.1" placeholder="70">
                        </div>
                    </div>

                    <div class="form-group">
                        <label class="form-label">Activity Level</label>
                        <select class="form-input" id="activity-level">
                            <option value="">Select activity level</option>
                            <option value="sedentary">Sedentary (Little/no exercise)</option>
                            <option value="lightly_active">Lightly Active (1-3 days/week)</option>
                            <option value="moderately_active">Moderately Active (3-5 days/week)</option>
                            <option value="very_active">Very Active (6-7 days/week)</option>
                            <option value="extremely_active">Extremely Active (2x/day)</option>
                        </select>
                    </div>

                    <button class="calculate-btn" id="calculate-btn" onclick="calculateBMI()">
                        Calculate BMI & Save Profile
                    </button>
                </div>

                <!-- BMI Display -->
                <div class="sidebar-card">
                    <h3 class="card-title">📊 Your BMI</h3>
                    <div class="bmi-display" id="bmi-display">
                        <div style="color: var(--brown); font-size: 1rem;">
                            Fill out your profile above to calculate your BMI and get personalized health insights!
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentUser = null;
        let selectedGender = null;

        // Event listeners
        document.addEventListener('DOMContentLoaded', function() {
            setupEventListeners();
            
            const savedUser = localStorage.getItem('bodybae_user');
            if (savedUser) {
                currentUser = JSON.parse(savedUser);
                if (currentUser.bmi_info) {
                    displayBMI();
                }
            }
        });

        function setupEventListeners() {
            // Gender selection
            document.querySelectorAll('.gender-option').forEach(option => {
                option.addEventListener('click', function() {
                    document.querySelectorAll('.gender-option').forEach(o => o.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedGender = this.dataset.value;
                });
            });

            // Chat input
            const chatInput = document.getElementById('chat-input');
            chatInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            chatInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 120) + 'px';
            });
        }

        function startChat() {
            document.getElementById('welcome-screen').style.display = 'none';
            document.getElementById('chat-screen').style.display = 'block';
        }

        async function calculateBMI() {
            const button = document.getElementById('calculate-btn');
            const originalText = button.textContent;
            button.innerHTML = '<span class="spinner"></span> Calculating...';
            button.disabled = true;

            const formData = {
                name: document.getElementById('name').value.trim(),
                age: parseInt(document.getElementById('age').value),
                height: parseFloat(document.getElementById('height').value),
                weight: parseFloat(document.getElementById('weight').value),
                sex: selectedGender,
                activity_level: document.getElementById('activity-level').value
            };

            // Validate form
            if (!formData.name || !formData.age || !formData.height || !formData.weight || !formData.sex || !formData.activity_level) {
                alert('Please fill in all fields');
                button.textContent = originalText;
                button.disabled = false;
                return;
            }

            try {
                const response = await fetch('/onboard', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.success) {
                    currentUser = {
                        ...formData,
                        user_id: result.user_id,
                        bmr: result.bmr,
                        tdee: result.tdee,
                        bmi_info: result.bmi_info
                    };
                    
                    localStorage.setItem('bodybae_user', JSON.stringify(currentUser));
                    displayBMI();
                    
                    addBotMessage(`✅ Profile saved! Your BMI is ${result.bmi_info.bmi} (${result.bmi_info.category}). I'm now ready to give you personalized advice!`);
                    
                } else {
                    throw new Error(result.error || 'Failed to calculate BMI');
                }
            } catch (error) {
                console.error('BMI calculation error:', error);
                alert('Failed to calculate BMI. Please try again.');
            } finally {
                button.textContent = originalText;
                button.disabled = false;
            }
        }

        function displayBMI() {
            if (!currentUser || !currentUser.bmi_info) return;
            
            const bmiDisplay = document.getElementById('bmi-display');
            const bmiInfo = currentUser.bmi_info;
            
            bmiDisplay.innerHTML = `
                <div class="bmi-number">${bmiInfo.bmi}</div>
                <div class="bmi-category">${bmiInfo.category}</div>
                <div class="bmi-advice">${bmiInfo.advice}</div>
            `;
        }

        function sendQuickMessage(message) {
            document.getElementById('chat-input').value = message;
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value.trim();

            if (!message) return;

            addUserMessage(message);
            input.value = '';
            input.style.height = 'auto';

            const sendButton = document.getElementById('send-button');
            sendButton.disabled = true;
            showTypingIndicator();

            try {
                const requestData = { message };
                
                if (currentUser) {
                    requestData.userProfile = currentUser;
                }

                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });

                const result = await response.json();
                hideTypingIndicator();

                if (result.response) {
                    addBotMessage(result.response);
                } else {
                    throw new Error('No response received');
                }
            } catch (error) {
                console.error('Chat error:', error);
                hideTypingIndicator();
                addBotMessage('Sorry, I\'m having trouble responding right now. Please try again! 😔');
            } finally {
                sendButton.disabled = false;
            }
        }

        function addUserMessage(message) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user';
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        function addBotMessage(message) {
            const messagesContainer = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot';
            messageDiv.textContent = message;
            messagesContainer.appendChild(messageDiv);
            scrollToBottom();
        }

        function showTypingIndicator() {
            document.getElementById('typing-indicator').style.display = 'block';
            scrollToBottom();
        }

        function hideTypingIndicator() {
            document.getElementById('typing-indicator').style.display = 'none';
        }

        function scrollToBottom() {
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/onboard', methods=['POST'])
def onboard_user():
    """Handle user onboarding with BMI calculation"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        # Store user data
        users_db[user_id] = {
            'name': data['name'],
            'age': int(data['age']),
            'height': float(data['height']),
            'weight': float(data['weight']),
            'sex': data['sex'],
            'activity_level': data['activity_level'],
            'created_at': datetime.now().isoformat()
        }
        
        # Calculate BMR, TDEE, and BMI
        user = users_db[user_id]
        bmr = bodybae.calculate_bmr(user['weight'], user['height'], user['age'], user['sex'])
        tdee = bodybae.calculate_tdee(bmr, user['activity_level'])
        bmi_info = bodybae.calculate_bmi(user['weight'], user['height'])
        
        user.update({
            'bmr': bmr,
            'tdee': tdee,
            'bmi': bmi_info['bmi'],
            'bmi_category': bmi_info['category'],
            'bmi_advice': bmi_info['advice']
        })
        
        # Store user_id in session
        session['user_id'] = user_id
        
        # Initialize chat history
        chat_history_db[user_id] = []
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'bmr': bmr,
            'tdee': tdee,
            'bmi_info': bmi_info,
            'message': f"Welcome {data['name']}! Your profile has been created successfully."
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat with RAG system integration"""
    data = request.json
    message = data.get('message', '')
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get user context
        user_profile = users_db.get(user_id, {}) if user_id else {}
        
        # Use RAG system if available
        if rag_system:
            try:
                response = rag_system.get_health_response(
                    question=message,
                    user_profile=user_profile
                )
                
                # Store in chat history
                if user_id:
                    if user_id not in chat_history_db:
                        chat_history_db[user_id] = []
                    chat_history_db[user_id].extend([
                        {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                        {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
                    ])
                
                return jsonify({
                    'response': response,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'rag_system'
                })
                
            except Exception as rag_error:
                print(f"RAG system error: {rag_error}")
                # Fall through to simple responses
        
        # Fallback to simple rule-based responses
        response = get_simple_response(message, user_profile)
        
        # Store in chat history
        if user_id:
            if user_id not in chat_history_db:
                chat_history_db[user_id] = []
            chat_history_db[user_id].extend([
                {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
            ])
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'source': 'fallback'
        })
        
    except Exception as e:
        return jsonify({'error': 'Error processing chat message', 'details': str(e)}), 500

def get_simple_response(message: str, user_profile: Dict) -> str:
    """Fallback response system when RAG is not available"""
    message_lower = message.lower()
    name = user_profile.get('name', 'there') if user_profile else 'there'
    
    if any(word in message_lower for word in ['weight loss', 'lose weight']):
        return f"Hi {name}! For healthy weight loss, focus on creating a moderate caloric deficit of 500-750 calories daily. Combine cardio with strength training, eat plenty of protein, and stay hydrated. Aim for 0.5-1 kg per week. You've got this! 💪"
    
    elif any(word in message_lower for word in ['muscle', 'gain muscle', 'build muscle']):
        return f"Great question, {name}! To build muscle, focus on progressive overload in your workouts and eat 1.6-2.2g protein per kg body weight daily. Get 7-9 hours of sleep for recovery. Compound exercises like squats and deadlifts are your best friends! 🏋️‍♀️"
    
    elif any(word in message_lower for word in ['workout', 'exercise', 'training']):
        return f"Hi {name}! For effective workouts, aim for 150 minutes of moderate cardio per week plus 2-3 strength training sessions. Start with what you can handle and gradually increase intensity. Consistency beats perfection every time! 🌟"
    
    elif any(word in message_lower for word in ['nutrition', 'diet', 'food', 'eat']):
        return f"Nutrition is so important, {name}! Focus on whole foods: lean proteins, vegetables, fruits, whole grains, and healthy fats. Eat balanced meals, stay hydrated, and don't forget that small, sustainable changes lead to big results over time! 🥗"
    
    elif any(word in message_lower for word in ['motivation', 'motivated', 'give up']):
        return f"I believe in you, {name}! 🌟 Remember why you started this journey. Every small step counts, progress isn't always linear, and setbacks are just setups for comebacks. You're stronger than you think and capable of amazing things!"
    
    elif any(word in message_lower for word in ['bmi', 'healthy', 'health']):
        if user_profile and 'bmi' in user_profile:
            bmi = user_profile['bmi']
            category = user_profile.get('bmi_category', 'Unknown')
            return f"Your current BMI is {bmi}, which is in the '{category}' category, {name}. Remember, BMI is just one indicator of health. Focus on how you feel, your energy levels, and building healthy habits! 🌈"
        else:
            return f"Health is about so much more than just weight, {name}! Focus on building sustainable habits: regular movement, balanced nutrition, quality sleep, stress management, and staying hydrated. Small consistent changes lead to big transformations! ✨"
    
    elif 'hello' in message_lower or 'hi' in message_lower:
        return f"Hello {name}! 😊 I'm here to help you on your health and fitness journey. I can assist with workout advice, nutrition guidance, and motivation. What would you like to chat about today?"
    
    else:
        return f"Hi {name}! I'm here to help with your health and fitness journey. I can assist with workout recommendations, nutrition advice, goal setting, and motivation. What specific aspect of your health would you like to focus on today? 😊"

@app.route('/health_check')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'rag_system': 'available' if rag_system else 'fallback'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting BodyBae.ai...")
    print(f"📊 RAG System: {'✅ Available' if rag_system else '⚠️ Fallback'}")
    print(f"🌐 Running on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)