from flask import Flask, request, jsonify, session
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Import RAG system
try:
    from rag_system import HealthRAGSystem
    RAG_AVAILABLE = True
    print("✅ RAG system imported successfully")
except ImportError as e:
    print(f"⚠️ RAG system not available: {e}")
    RAG_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Storage
users_db = {}
chat_history_db = {}
goals_db = {}

# Initialize RAG system
rag_system = None
if RAG_AVAILABLE:
    try:
        rag_system = HealthRAGSystem()
        print("✅ Advanced RAG system initialized")
    except Exception as e:
        print(f"⚠️ RAG initialization failed: {e}")
        rag_system = None

class AdvancedBodyBaeAI:
    def __init__(self):
        self.fitness_goals = [
            "Weight Loss", "Muscle Building", "Strength Training", "Cardiovascular Health",
            "Flexibility & Mobility", "Athletic Performance", "General Wellness", 
            "Weight Gain", "Body Recomposition", "Injury Recovery", "Mental Health",
            "Sleep Optimization", "Nutrition Education", "Habit Building"
        ]
        
        self.specialized_knowledge = {
            "nutrition_science": [
                "Macronutrient timing and cycling", "Micronutrient deficiencies", 
                "Meal prep strategies", "Intermittent fasting protocols",
                "Sports nutrition", "Plant-based nutrition", "Hydration science"
            ],
            "exercise_science": [
                "Progressive overload principles", "Periodization methods",
                "Exercise biomechanics", "Recovery protocols", "HIIT vs LISS",
                "Functional movement patterns", "Injury prevention"
            ],
            "behavioral_psychology": [
                "Habit formation", "Motivation techniques", "Goal setting frameworks",
                "Overcoming plateaus", "Stress management", "Sleep hygiene"
            ]
        }
    
    def calculate_advanced_metrics(self, user_data: Dict) -> Dict:
        """Calculate comprehensive health metrics"""
        weight = user_data['weight']
        height = user_data['height'] / 100
        age = user_data['age']
        gender = user_data['gender']
        activity = user_data['activity']
        
        # BMI and body composition
        bmi = weight / (height ** 2)
        
        # BMR using Mifflin-St Jeor
        if gender.lower() == 'male':
            bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * (height * 100) - 5 * age - 161
        
        # TDEE with activity multipliers
        activity_multipliers = {
            "sedentary": 1.2,
            "lightly_active": 1.375,
            "moderately_active": 1.55,
            "very_active": 1.725,
            "extremely_active": 1.9
        }
        tdee = bmr * activity_multipliers.get(activity, 1.2)
        
        # Health assessments
        bmi_category = self.get_bmi_category(bmi)
        health_risk = self.assess_health_risk(bmi, age)
        
        return {
            'bmi': round(bmi, 1),
            'bmi_category': bmi_category,
            'bmr': round(bmr),
            'tdee': round(tdee),
            'health_risk': health_risk,
            'ideal_weight_range': self.calculate_ideal_weight(height * 100),
            'daily_water_needs': round(weight * 35),  # ml per day
            'protein_needs': {
                'sedentary': round(weight * 0.8, 1),
                'active': round(weight * 1.2, 1),
                'athlete': round(weight * 2.0, 1)
            }
        }
    
    def get_bmi_category(self, bmi: float) -> str:
        if bmi < 16: return "Severely Underweight"
        elif bmi < 18.5: return "Underweight"
        elif bmi < 25: return "Normal Weight"
        elif bmi < 30: return "Overweight"
        elif bmi < 35: return "Moderately Obese"
        elif bmi < 40: return "Severely Obese"
        else: return "Very Severely Obese"
    
    def assess_health_risk(self, bmi: float, age: int) -> str:
        risk_factors = []
        if bmi < 18.5 or bmi > 30: risk_factors.append("BMI")
        if age > 45: risk_factors.append("Age")
        
        if len(risk_factors) == 0: return "Low Risk"
        elif len(risk_factors) == 1: return "Moderate Risk"
        else: return "Higher Risk"
    
    def calculate_ideal_weight(self, height_cm: float) -> Dict:
        # Robinson formula
        if height_cm <= 150:
            ideal_male = 52
            ideal_female = 49
        else:
            ideal_male = 52 + 1.9 * ((height_cm - 152.4) / 2.54)
            ideal_female = 49 + 1.7 * ((height_cm - 152.4) / 2.54)
        
        return {
            'male_range': f"{ideal_male-5:.1f} - {ideal_male+5:.1f} kg",
            'female_range': f"{ideal_female-5:.1f} - {ideal_female+5:.1f} kg"
        }

# Initialize advanced AI
advanced_ai = AdvancedBodyBaeAI()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>BodyBae.ai - Advanced AI Health Coach</title>
        <style>
            :root {
                --sage-green: #A4B07E;
                --olive-green: #707C4F;
                --dark-green: #424106;
                --cream: #d4cbbc;
                --mauve: #C6A6B5;
                --brown: #6D4930;
            }
            
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
                color: white;
                margin: 0;
                min-height: 100vh;
                font-weight: 300;
            }
            
            .container { 
                max-width: 1400px; 
                margin: 0 auto; 
                padding: 1rem; 
            }
            
            .welcome { 
                text-align: center; 
                padding: 3rem 1rem;
                display: block;
            }
            
            .welcome h1 {
                font-size: 3.5rem;
                margin-bottom: 0.5rem;
                color: var(--dark-green);
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                font-weight: 600;
            }
            
            .welcome p {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                opacity: 0.9;
            }
            
            .chat { 
                display: none; 
                background: white;
                color: var(--dark-green);
                border-radius: 20px;
                margin-top: 1rem;
                box-shadow: 0 20px 60px rgba(0,0,0,0.2);
                overflow: hidden;
            }
            
            .chat-layout {
                display: grid;
                grid-template-columns: 300px 1fr;
                height: 85vh;
            }
            
            .sidebar {
                background: linear-gradient(180deg, var(--light-cream, #f9f7f4), var(--cream));
                padding: 1.5rem;
                border-right: 1px solid var(--sage-green);
                overflow-y: auto;
            }
            
            .chat-main {
                display: flex;
                flex-direction: column;
                background: white;
            }
            
            .chat-header {
                background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
                color: white;
                padding: 1.5rem;
                text-align: center;
            }
            
            .chat-messages {
                flex: 1;
                padding: 1.5rem;
                overflow-y: auto;
                background: linear-gradient(to bottom, white, #fafafa);
            }
            
            .chat-input-area {
                padding: 1rem 1.5rem;
                background: white;
                border-top: 1px solid #eee;
            }
            
            /* Buttons */
            .btn {
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.3s ease;
                font-family: inherit;
            }
            
            .btn-primary { 
                background: linear-gradient(45deg, var(--mauve), var(--brown));
                color: white; 
                padding: 1rem 2rem;
                font-size: 1.1rem;
                border-radius: 50px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .btn-primary:hover { 
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
            
            .btn-small {
                background: var(--sage-green);
                color: white;
                padding: 0.3rem 0.8rem;
                font-size: 0.8rem;
                margin-left: 1rem;
            }
            
            .btn-small:hover {
                background: var(--olive-green);
            }
            
            /* Forms */
            .form-section {
                margin-bottom: 1.5rem;
                background: white;
                padding: 1rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .form-section h3 {
                color: var(--olive-green);
                margin-bottom: 1rem;
                font-size: 1.1rem;
                font-weight: 600;
            }
            
            .form-group {
                margin-bottom: 0.8rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.3rem;
                font-size: 0.85rem;
                font-weight: 500;
                color: var(--dark-green);
            }
            
            input, select {
                width: 100%;
                padding: 0.6rem;
                border: 2px solid var(--cream);
                border-radius: 8px;
                font-size: 0.9rem;
                transition: border-color 0.3s ease;
                background: #fafafa;
            }
            
            input:focus, select:focus {
                outline: none;
                border-color: var(--sage-green);
                background: white;
            }
            
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.5rem;
            }
            
            /* Goals */
            .goals-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0.3rem;
                margin-top: 0.5rem;
            }
            
            .goal-chip {
                background: var(--cream);
                color: var(--dark-green);
                border: 1px solid transparent;
                padding: 0.4rem 0.6rem;
                border-radius: 15px;
                cursor: pointer;
                font-size: 0.75rem;
                text-align: center;
                transition: all 0.3s ease;
            }
            
            .goal-chip:hover, .goal-chip.selected {
                background: var(--sage-green);
                color: white;
                border-color: var(--olive-green);
            }
            
            /* Messages */
            .message {
                margin: 0.8rem 0;
                padding: 1rem;
                border-radius: 15px;
                max-width: 85%;
                line-height: 1.5;
                animation: fadeIn 0.3s ease;
            }
            
            .message.user {
                background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
                color: white;
                margin-left: auto;
                border-bottom-right-radius: 5px;
            }
            
            .message.bot {
                background: var(--cream);
                color: var(--dark-green);
                margin-right: auto;
                border-bottom-left-radius: 5px;
            }
            
            .message.system {
                background: linear-gradient(45deg, var(--mauve), var(--brown));
                color: white;
                margin: 1rem auto;
                text-align: center;
                font-weight: 500;
                max-width: 90%;
            }
            
            /* Input area */
            .input-wrapper {
                display: flex;
                gap: 0.5rem;
                align-items: flex-end;
                margin-top: 1rem;
            }
            
            .chat-input {
                flex: 1;
                border: 2px solid var(--cream);
                border-radius: 20px;
                padding: 0.8rem 1rem;
                resize: none;
                max-height: 100px;
                background: #fafafa;
            }
            
            .chat-input:focus {
                border-color: var(--sage-green);
                background: white;
            }
            
            .send-btn {
                background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
                color: white;
                border: none;
                width: 45px;
                height: 45px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .send-btn:hover {
                transform: scale(1.05);
            }
            
            /* Quick actions */
            .quick-actions {
                display: flex;
                gap: 0.4rem;
                flex-wrap: wrap;
                margin-bottom: 0.5rem;
            }
            
            .quick-btn {
                background: var(--cream);
                color: var(--dark-green);
                border: none;
                padding: 0.4rem 0.8rem;
                border-radius: 15px;
                cursor: pointer;
                font-size: 0.8rem;
                transition: all 0.3s ease;
            }
            
            .quick-btn:hover {
                background: var(--sage-green);
                color: white;
            }
            
            /* Health metrics */
            .metrics-display {
                background: linear-gradient(135deg, var(--sage-green), var(--olive-green));
                color: white;
                padding: 1rem;
                border-radius: 10px;
                margin-top: 1rem;
                text-align: center;
            }
            
            .metric-item {
                margin: 0.3rem 0;
                font-size: 0.85rem;
            }
            
            .metric-number {
                font-weight: 600;
                font-size: 1.1rem;
            }
            
            /* Animations */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .chat-layout {
                    grid-template-columns: 1fr;
                    height: auto;
                }
                .sidebar {
                    max-height: 40vh;
                }
                .chat-messages {
                    height: 50vh;
                }
                .form-row, .goals-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Welcome Section -->
            <div id="welcome" class="welcome">
                <h1>BodyBae.ai</h1>
                <p>Advanced AI Health & Fitness Coach</p>
                <p style="font-size: 1rem; opacity: 0.8; margin-bottom: 2rem;">
                    Powered by RAG technology for personalized, evidence-based advice
                </p>
                <button class="btn btn-primary" onclick="showChat()">Start Your Health Journey</button>
                <button class="btn btn-small" onclick="testFunction()">Test</button>
                <div id="debug" style="margin-top: 1rem; font-size: 0.9rem;"></div>
            </div>

            <!-- Chat Section -->
            <div id="chat" class="chat">
                <div class="chat-layout">
                    <!-- Sidebar -->
                    <div class="sidebar">
                        <!-- Profile Section -->
                        <div class="form-section">
                            <h3>👤 Your Profile</h3>
                            <div class="form-group">
                                <label>Name:</label>
                                <input type="text" id="name" placeholder="Your name">
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Age:</label>
                                    <input type="number" id="age" min="13" max="100" placeholder="25">
                                </div>
                                <div class="form-group">
                                    <label>Gender:</label>
                                    <select id="gender">
                                        <option value="">Select</option>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Height (cm):</label>
                                    <input type="number" id="height" min="100" max="250" placeholder="170">
                                </div>
                                <div class="form-group">
                                    <label>Weight (kg):</label>
                                    <input type="number" id="weight" min="30" max="300" step="0.1" placeholder="70">
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Activity Level:</label>
                                <select id="activity">
                                    <option value="">Select</option>
                                    <option value="sedentary">Sedentary (Office job, no exercise)</option>
                                    <option value="lightly_active">Lightly Active (1-3 days/week)</option>
                                    <option value="moderately_active">Moderately Active (3-5 days/week)</option>
                                    <option value="very_active">Very Active (6-7 days/week)</option>
                                    <option value="extremely_active">Extremely Active (2x/day)</option>
                                </select>
                            </div>
                        </div>

                        <!-- Goals Section -->
                        <div class="form-section">
                            <h3>🎯 Health Goals</h3>
                            <div class="goals-grid" id="goals-grid">
                                <!-- Goals will be populated by JavaScript -->
                            </div>
                        </div>

                        <!-- Calculate Button -->
                        <button class="btn btn-primary" onclick="calculateAdvancedMetrics()" style="width: 100%; margin-bottom: 1rem;">
                            Analyze My Health Profile
                        </button>

                        <!-- Health Metrics Display -->
                        <div id="metrics-display" style="display: none;"></div>
                    </div>

                    <!-- Main Chat Area -->
                    <div class="chat-main">
                        <div class="chat-header">
                            <h2 style="margin: 0; font-size: 1.5rem;">💬 BodyBae AI Coach</h2>
                            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.95rem;">
                                Advanced AI with specialized health knowledge
                            </p>
                        </div>
                        
                        <div id="messages" class="chat-messages">
                            <div class="message bot">
                                👋 Hi! I'm BodyBae, your advanced AI health coach powered by specialized knowledge in nutrition science, exercise physiology, and behavioral psychology.
                                <br><br>
                                <strong>To get started:</strong>
                                <br>• Fill out your profile on the left
                                <br>• Select your health goals  
                                <br>• Click "Analyze My Health Profile"
                                <br><br>
                                I'll provide evidence-based, personalized recommendations tailored to your unique situation! 🎯
                            </div>
                        </div>

                        <div class="chat-input-area">
                            <div class="quick-actions">
                                <button class="quick-btn" onclick="sendQuickMessage('Create a personalized workout plan for me')">Workout Plan</button>
                                <button class="quick-btn" onclick="sendQuickMessage('Design a nutrition strategy for my goals')">Nutrition Plan</button>
                                <button class="quick-btn" onclick="sendQuickMessage('Help me build sustainable healthy habits')">Habit Building</button>
                                <button class="quick-btn" onclick="sendQuickMessage('I need motivation and accountability')">Motivation</button>
                                <button class="quick-btn" onclick="sendQuickMessage('Explain the science behind fat loss')">Science Explained</button>
                                <button class="quick-btn" onclick="sendQuickMessage('What supplements should I consider?')">Supplements</button>
                            </div>
                            <div class="input-wrapper">
                                <textarea 
                                    id="message-input" 
                                    class="chat-input"
                                    placeholder="Ask me anything about health, fitness, nutrition, psychology..."
                                    rows="1"
                                ></textarea>
                                <button class="send-btn" onclick="sendMessage()">➤</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let userProfile = null;
            let selectedGoals = [];
            
            const healthGoals = [
                'Weight Loss', 'Muscle Building', 'Strength Training', 'Cardiovascular Health',
                'Flexibility & Mobility', 'Athletic Performance', 'General Wellness', 
                'Weight Gain', 'Body Recomposition', 'Injury Recovery', 'Mental Health',
                'Sleep Optimization', 'Nutrition Education', 'Habit Building'
            ];

            // Initialize goals grid
            function initializeGoals() {
                const goalsGrid = document.getElementById('goals-grid');
                healthGoals.forEach(goal => {
                    const chip = document.createElement('div');
                    chip.className = 'goal-chip';
                    chip.textContent = goal;
                    chip.onclick = () => toggleGoal(chip, goal);
                    goalsGrid.appendChild(chip);
                });
            }

            function toggleGoal(element, goal) {
                if (selectedGoals.includes(goal)) {
                    selectedGoals = selectedGoals.filter(g => g !== goal);
                    element.classList.remove('selected');
                } else {
                    selectedGoals.push(goal);
                    element.classList.add('selected');
                }
            }

            function testFunction() {
                document.getElementById('debug').innerHTML = 'Advanced BodyBae.ai is running! ✅';
                console.log('Advanced system test successful');
            }

            function showChat() {
                console.log('Switching to advanced chat interface');
                document.getElementById('welcome').style.display = 'none';
                document.getElementById('chat').style.display = 'block';
                initializeGoals();
            }

            async function calculateAdvancedMetrics() {
                const name = document.getElementById('name').value;
                const age = document.getElementById('age').value;
                const height = document.getElementById('height').value;
                const weight = document.getElementById('weight').value;
                const gender = document.getElementById('gender').value;
                const activity = document.getElementById('activity').value;

                if (!name || !age || !height || !weight || !gender || !activity) {
                    addMessage('system', '⚠️ Please fill in all profile fields to get accurate analysis');
                    return;
                }

                if (selectedGoals.length === 0) {
                    addMessage('system', '🎯 Please select at least one health goal');
                    return;
                }

                addMessage('system', '🔄 Analyzing your health profile with advanced metrics...');

                try {
                    const response = await fetch('/analyze_health', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            name, age: parseInt(age), height: parseFloat(height), 
                            weight: parseFloat(weight), gender, activity,
                            goals: selectedGoals
                        })
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        userProfile = result.profile;
                        displayAdvancedMetrics(result.metrics);
                        addMessage('bot', result.ai_analysis);
                        
                        // Add personalized recommendations
                        setTimeout(() => {
                            addMessage('bot', result.recommendations);
                        }, 2000);
                        
                        // Show next steps
                        setTimeout(() => {
                            addMessage('system', '🚀 Your profile is now set! Ask me specific questions about your health goals, and I\'ll provide evidence-based, personalized advice.');
                        }, 4000);
                    } else {
                        addMessage('system', '❌ Error analyzing profile. Please try again.');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    addMessage('system', '🔌 Network error. Please check your connection and try again.');
                }
            }

            function displayAdvancedMetrics(metrics) {
                const display = document.getElementById('metrics-display');
                display.style.display = 'block';
                display.innerHTML = `
                    <div class="metric-item">BMI: <span class="metric-number">${metrics.bmi}</span> (${metrics.bmi_category})</div>
                    <div class="metric-item">Daily Calories: <span class="metric-number">${metrics.tdee}</span></div>
                    <div class="metric-item">Protein Needs: <span class="metric-number">${metrics.protein_needs.active}g</span></div>
                    <div class="metric-item">Water Needs: <span class="metric-number">${metrics.daily_water_needs}ml</span></div>
                    <div class="metric-item">Health Risk: <span class="metric-number">${metrics.health_risk}</span></div>
                `;
            }

            async function sendMessage() {
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                
                if (!message) return;

                addMessage('user', message);
                input.value = '';
                input.style.height = 'auto';

                // Show typing indicator
                addMessage('system', '🤖 BodyBae is thinking...');

                try {
                    const response = await fetch('/advanced_chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            message,
                            user_profile: userProfile,
                            selected_goals: selectedGoals
                        })
                    });

                    const result = await response.json();
                    
                    // Remove typing indicator
                    const messages = document.getElementById('messages');
                    const lastMessage = messages.lastElementChild;
                    if (lastMessage && lastMessage.textContent.includes('thinking')) {
                        messages.removeChild(lastMessage);
                    }
                    
                    addMessage('bot', result.response);
                    
                    // Add follow-up suggestions if available
                    if (result.follow_up_suggestions) {
                        setTimeout(() => {
                            const suggestions = result.follow_up_suggestions.join(' • ');
                            addMessage('system', `💡 Related topics: ${suggestions}`);
                        }, 1500);
                    }
                    
                } catch (error) {
                    console.error('Error:', error);
                    // Remove typing indicator
                    const messages = document.getElementById('messages');
                    const lastMessage = messages.lastElementChild;
                    if (lastMessage && lastMessage.textContent.includes('thinking')) {
                        messages.removeChild(lastMessage);
                    }
                    addMessage('bot', 'I apologize, but I\'m having trouble processing your request right now. Please try rephrasing your question or check your connection.');
                }
            }

            function sendQuickMessage(message) {
                document.getElementById('message-input').value = message;
                sendMessage();
            }

            function addMessage(sender, message) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}`;
                messageDiv.innerHTML = message.replace(/\\n/g, '<br>');
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }

            // Auto-resize textarea
            document.getElementById('message-input').addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });

            // Enter key support
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            console.log('Advanced BodyBae.ai loaded successfully');
        </script>
    </body>
    </html>
    '''

@app.route('/analyze_health', methods=['POST'])
def analyze_health():
    """Advanced health analysis with comprehensive metrics"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        # Store user data
        user_data = {
            'name': data['name'],
            'age': int(data['age']),
            'height': float(data['height']),
            'weight': float(data['weight']),
            'gender': data['gender'],
            'activity': data['activity'],
            'goals': data['goals'],
            'created_at': datetime.now().isoformat()
        }
        
        users_db[user_id] = user_data
        session['user_id'] = user_id
        
        # Calculate advanced metrics
        metrics = advanced_ai.calculate_advanced_metrics(user_data)
        
        # Store metrics with user data
        users_db[user_id]['metrics'] = metrics
        
        # Generate AI analysis using RAG if available
        if rag_system:
            try:
                # Create comprehensive user profile for RAG
                user_profile = {
                    **user_data,
                    **metrics,
                    'primary_goals': data['goals'][:3]  # Top 3 goals
                }
                
                analysis_prompt = f"""
                Analyze this user's comprehensive health profile and provide detailed insights:
                
                User: {data['name']}, {data['age']} years old, {data['gender']}
                Physical: {data['height']}cm, {data['weight']}kg, BMI {metrics['bmi']} ({metrics['bmi_category']})
                Activity: {data['activity']}
                Goals: {', '.join(data['goals'])}
                
                Provide a detailed health analysis covering their current status, risk factors, and specific recommendations.
                """
                
                ai_analysis = rag_system.get_health_response(analysis_prompt, user_profile)
                
                # Generate specific recommendations
                recommendations_prompt = f"""
                Based on this user's profile and goals ({', '.join(data['goals'])}), provide specific, actionable recommendations for:
                1. Nutrition strategy
                2. Exercise program 
                3. Lifestyle modifications
                4. Progress tracking methods
                """
                
                recommendations = rag_system.get_health_response(recommendations_prompt, user_profile)
                
            except Exception as e:
                print(f"RAG error in analysis: {e}")
                # Fallback analysis
                ai_analysis = generate_fallback_analysis(user_data, metrics)
                recommendations = generate_fallback_recommendations(user_data, metrics)
        else:
            ai_analysis = generate_fallback_analysis(user_data, metrics)
            recommendations = generate_fallback_recommendations(user_data, metrics)
        
        return jsonify({
            'success': True,
            'profile': user_data,
            'metrics': metrics,
            'ai_analysis': ai_analysis,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_fallback_analysis(user_data, metrics):
    """Generate comprehensive analysis when RAG is not available"""
    name = user_data['name']
    bmi = metrics['bmi']
    category = metrics['bmi_category']
    goals = user_data['goals']
    
    analysis = f"""🔍 **Comprehensive Health Analysis for {name}**

**Current Status:**
• Your BMI of {bmi} places you in the '{category}' category
• Daily calorie needs: ~{metrics['tdee']} calories
• Recommended protein intake: {metrics['protein_needs']['active']}g daily
• Health risk assessment: {metrics['health_risk']}

**Key Insights:**
"""
    
    # BMI-specific insights
    if bmi < 18.5:
        analysis += "• Focus on healthy weight gain through nutrient-dense foods and strength training\n"
    elif bmi > 25:
        analysis += "• Gradual weight reduction through moderate caloric deficit recommended\n"
    else:
        analysis += "• Excellent BMI range - focus on body composition and fitness improvements\n"
    
    # Goal-specific insights
    if 'Weight Loss' in goals:
        analysis += "• For weight loss: Create 500-750 calorie daily deficit through diet and exercise\n"
    if 'Muscle Building' in goals:
        analysis += "• For muscle building: Prioritize progressive resistance training and adequate protein\n"
    if 'Cardiovascular Health' in goals:
        analysis += "• For heart health: Include 150+ minutes moderate cardio weekly\n"
    
    analysis += f"\n**Daily Targets:**\n• Water: {metrics['daily_water_needs']}ml\n• Steps: 8,000-10,000\n• Sleep: 7-9 hours"
    
    return analysis

def generate_fallback_recommendations(user_data, metrics):
    """Generate personalized recommendations"""
    goals = user_data['goals']
    activity = user_data['activity']
    
    recommendations = "🎯 **Personalized Action Plan**\n\n"
    
    # Nutrition recommendations
    recommendations += "**🥗 Nutrition Strategy:**\n"
    if 'Weight Loss' in goals:
        target_calories = int(metrics['tdee'] - 600)
        recommendations += f"• Target: {target_calories} calories daily\n• Focus on high-protein, high-fiber foods\n• Eat 4-5 smaller meals throughout the day\n\n"
    elif 'Muscle Building' in goals:
        target_calories = int(metrics['tdee'] + 300)
        recommendations += f"• Target: {target_calories} calories daily\n• Protein timing: 20-30g every 3-4 hours\n• Include complex carbs around workouts\n\n"
    else:
        recommendations += f"• Maintain around {metrics['tdee']} calories daily\n• Focus on balanced, whole foods\n• Stay consistent with meal timing\n\n"
    
    # Exercise recommendations
    recommendations += "**💪 Exercise Program:**\n"
    if 'sedentary' in activity:
        recommendations += "• Start with 20-30 minutes walking daily\n• Add 2 strength training sessions weekly\n• Build gradually to avoid burnout\n\n"
    elif 'very_active' in activity:
        recommendations += "• Continue current activity level\n• Focus on periodization and recovery\n• Consider working with a trainer\n\n"
    else:
        recommendations += "• Aim for 4-5 exercise sessions weekly\n• Mix cardio and strength training\n• Include flexibility work\n\n"
    
    # Goal-specific recommendations
    if 'Sleep Optimization' in goals:
        recommendations += "**😴 Sleep Protocol:**\n• Consistent bedtime routine\n• Dark, cool room (65-68°F)\n• No screens 1 hour before bed\n• Consider magnesium supplementation\n\n"
    
    if 'Mental Health' in goals:
        recommendations += "**🧠 Mental Wellness:**\n• 10-15 minutes daily meditation\n• Regular outdoor exposure\n• Social connection and support\n• Professional help if needed\n\n"
    
    recommendations += "**📊 Progress Tracking:**\n• Weekly body measurements\n• Progress photos\n• Energy and mood levels\n• Workout performance metrics"
    
    return recommendations

@app.route('/advanced_chat', methods=['POST'])
def advanced_chat():
    """Advanced chat with RAG system and context awareness"""
    data = request.json
    message = data.get('message', '')
    user_profile = data.get('user_profile', {})
    selected_goals = data.get('selected_goals', [])
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'})
    
    try:
        # Enhanced context for RAG system
        enhanced_profile = user_profile.copy() if user_profile else {}
        if user_id and user_id in users_db:
            enhanced_profile.update(users_db[user_id])
        
        enhanced_profile['current_goals'] = selected_goals
        enhanced_profile['conversation_context'] = get_recent_conversation(user_id)
        
        # Use RAG system for intelligent responses
        if rag_system and enhanced_profile:
            try:
                response = rag_system.get_health_response(message, enhanced_profile)
                
                # Generate follow-up suggestions based on the response
                follow_up_suggestions = generate_follow_up_suggestions(message, response, selected_goals)
                
                # Store conversation
                store_conversation(user_id, message, response)
                
                return jsonify({
                    'response': response,
                    'follow_up_suggestions': follow_up_suggestions,
                    'source': 'rag_system'
                })
                
            except Exception as rag_error:
                print(f"RAG error in chat: {rag_error}")
                # Fall through to advanced fallback
        
        # Advanced fallback system
        response = get_advanced_fallback_response(message, enhanced_profile, selected_goals)
        follow_up_suggestions = generate_follow_up_suggestions(message, response, selected_goals)
        
        store_conversation(user_id, message, response)
        
        return jsonify({
            'response': response,
            'follow_up_suggestions': follow_up_suggestions,
            'source': 'advanced_fallback'
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "I apologize, but I'm having trouble processing your request. Could you please rephrase your question or try asking about a specific health topic?",
            'follow_up_suggestions': ["What's a good workout routine?", "How many calories should I eat?", "Tips for better sleep"],
            'source': 'error_fallback'
        })

def get_advanced_fallback_response(message: str, user_profile: Dict, selected_goals: List) -> str:
    """Advanced fallback responses with context awareness"""
    message_lower = message.lower()
    name = user_profile.get('name', 'there')
    
    # Context-aware responses based on user profile
    bmi = user_profile.get('bmi', 0)
    age = user_profile.get('age', 0)
    goals = selected_goals or []
    
    # Advanced pattern matching with context
    if any(word in message_lower for word in ['workout', 'exercise', 'training', 'routine']):
        if 'Muscle Building' in goals:
            response = f"Hi {name}! For muscle building, I recommend a structured approach:\n\n"
            response += "**Weekly Structure:**\n• 3-4 strength training days\n• Focus on compound movements\n• Progressive overload principle\n\n"
            response += "**Key Exercises:**\n• Squats, Deadlifts, Bench Press\n• Pull-ups/Rows, Overhead Press\n• 3-4 sets of 6-12 reps\n\n"
            if age > 40:
                response += "**Age Consideration:** Include extra warm-up time and prioritize recovery between sessions."
            response += "\n\nWould you like me to design a specific program for your experience level?"
            
        elif 'Weight Loss' in goals:
            response = f"Perfect question, {name}! For weight loss, combine cardio and strength training:\n\n"
            response += "**Cardio Protocol:**\n• 3-4 sessions weekly\n• Mix HIIT and steady-state\n• 20-45 minutes per session\n\n"
            response += "**Strength Training:**\n• 2-3 full-body sessions\n• Preserves muscle during fat loss\n• Boosts metabolism post-workout\n\n"
            if bmi > 30:
                response += "**Starting Point:** Begin with low-impact activities like walking or swimming to protect joints."
            response += "\n\nShall I create a beginner-friendly schedule for you?"
            
        else:
            response = f"Great question, {name}! For general fitness:\n\n"
            response += "**Balanced Approach:**\n• 3-4 days strength training\n• 2-3 days cardio\n• 1-2 days active recovery\n\n"
            response += "**Weekly Structure:**\n• Monday: Upper body strength\n• Tuesday: Cardio\n• Wednesday: Lower body strength\n• Thursday: Rest or yoga\n• Friday: Full body strength\n• Weekend: Outdoor activity\n\nWhat's your current fitness experience level?"
    
    elif any(word in message_lower for word in ['nutrition', 'diet', 'food', 'eat', 'calories', 'meal']):
        if user_profile.get('tdee'):
            tdee = user_profile['tdee']
            if 'Weight Loss' in goals:
                target = int(tdee - 500)
                response = f"Hi {name}! Based on your profile, here's your nutrition strategy:\n\n"
                response += f"**Daily Targets:**\n• Calories: {target} (deficit for fat loss)\n• Protein: {user_profile.get('protein_needs', {}).get('active', 'calc')}g\n• Water: {user_profile.get('daily_water_needs', 2500)}ml\n\n"
            elif 'Muscle Building' in goals:
                target = int(tdee + 250)
                response = f"Hi {name}! For muscle building nutrition:\n\n"
                response += f"**Daily Targets:**\n• Calories: {target} (slight surplus)\n• Protein: {user_profile.get('protein_needs', {}).get('active', 'calc')}g\n• Carbs around workouts\n\n"
            else:
                response = f"Hi {name}! For maintenance:\n\n"
                response += f"**Daily Targets:**\n• Calories: {int(tdee)}\n• Balanced macronutrients\n• Focus on whole foods\n\n"
                
            response += "**Meal Structure:**\n• 3 main meals + 1-2 snacks\n• Protein with each meal\n• Vegetables with lunch/dinner\n• Complex carbs for sustained energy\n\nWould you like specific meal ideas?"
        else:
            response = f"Hi {name}! Let me help with nutrition fundamentals:\n\n"
            response += "**Key Principles:**\n• Eat protein with every meal\n• Fill half your plate with vegetables\n• Choose complex carbohydrates\n• Include healthy fats daily\n• Stay consistently hydrated\n\nTo give you specific calorie recommendations, I'd need your complete profile. Have you filled that out yet?"
    
    elif any(word in message_lower for word in ['motivation', 'give up', 'struggling', 'hard', 'difficult']):
        response = f"I hear you, {name}! 🌟 Struggling is completely normal and shows you're pushing your boundaries.\n\n"
        response += "**Remember Why You Started:**\n"
        if goals:
            response += f"• Your goals: {', '.join(goals[:3])}\n"
        response += "• Every small step counts\n• Progress isn't always linear\n• Setbacks are temporary\n\n"
        response += "**Strategies to Overcome:**\n• Break big goals into tiny steps\n• Celebrate small wins\n• Find an accountability partner\n• Focus on how you feel, not just results\n\n"
        response += "What specific challenge are you facing right now? I can help you create a plan to push through it! 💪"
    
    elif any(word in message_lower for word in ['sleep', 'tired', 'energy', 'fatigue']):
        response = f"Sleep is crucial for your health goals, {name}! Let me help optimize your rest:\n\n"
        response += "**Sleep Hygiene Protocol:**\n• 7-9 hours nightly\n• Consistent bedtime/wake time\n• Dark, cool room (65-68°F)\n• No screens 1 hour before bed\n\n"
        response += "**Natural Sleep Aids:**\n• Magnesium supplement (200-400mg)\n• Chamomile tea\n• Reading or meditation\n• Progressive muscle relaxation\n\n"
        if 'Sleep Optimization' in goals:
            response += "**Advanced Strategies:**\n• Track sleep with app/device\n• Morning sunlight exposure\n• Avoid caffeine after 2 PM\n• Consider sleep study if persistent issues\n\n"
        response += "What's your biggest sleep challenge? Falling asleep or staying asleep?"
    
    elif any(word in message_lower for word in ['supplement', 'vitamins', 'protein powder']):
        response = f"Great question about supplements, {name}! Here's evidence-based guidance:\n\n"
        response += "**Foundation First:**\n• Whole foods should be primary source\n• Supplements fill specific gaps\n• Quality matters - third-party tested\n\n"
        response += "**Essential Supplements:**\n• Vitamin D3 (2000-4000 IU)\n• Omega-3 (EPA/DHA)\n• Magnesium (200-400mg)\n• Multivitamin (insurance policy)\n\n"
        if 'Muscle Building' in goals:
            response += "**For Muscle Building:**\n• Whey/Casein protein powder\n• Creatine monohydrate (3-5g daily)\n• Consider beta-alanine for performance\n\n"
        if 'Weight Loss' in goals:
            response += "**For Weight Loss:**\n• Green tea extract\n• Caffeine (if tolerated)\n• Fiber supplement if diet lacks\n\n"
        response += "What specific supplement questions do you have? I can provide detailed guidance!"
    
    else:
        # General helpful response with context
        response = f"Hi {name}! I'm here to provide evidence-based health and fitness guidance.\n\n"
        if goals:
            response += f"**Your Goals:** {', '.join(goals[:3])}\n\n"
        response += "**I can help with:**\n• Personalized workout programs\n• Nutrition strategies and meal planning\n• Supplement recommendations\n• Sleep and recovery optimization\n• Habit formation and motivation\n• Exercise form and technique\n• Progress tracking methods\n\n"
        response += "What specific aspect would you like to dive deeper into? I'm here to provide detailed, actionable advice! 😊"
    
    return response

def generate_follow_up_suggestions(message: str, response: str, goals: List) -> List[str]:
    """Generate relevant follow-up questions based on context"""
    message_lower = message.lower()
    suggestions = []
    
    if 'workout' in message_lower:
        suggestions = [
            "How do I track progress in my workouts?",
            "What if I can't access a gym?",
            "How to prevent workout injuries?"
        ]
    elif 'nutrition' in message_lower or 'diet' in message_lower:
        suggestions = [
            "What are good meal prep strategies?",
            "How to handle cravings and hunger?",
            "Best foods for my goals?"
        ]
    elif 'motivation' in message_lower:
        suggestions = [
            "How to build sustainable habits?",
            "What to do when I hit a plateau?",
            "Creating accountability systems"
        ]
    else:
        # Goal-based suggestions
        if 'Weight Loss' in goals:
            suggestions = ["Best cardio for fat loss?", "How to avoid loose skin?", "Dealing with weight plateaus"]
        elif 'Muscle Building' in goals:
            suggestions = ["How much protein is too much?", "Best time to take supplements?", "Muscle building at home"]
        else:
            suggestions = ["Creating a balanced routine", "Tracking health metrics", "Long-term health strategies"]
    
    return suggestions[:3]  # Return top 3 suggestions

def get_recent_conversation(user_id: str) -> List[Dict]:
    """Get recent conversation history for context"""
    if user_id and user_id in chat_history_db:
        return chat_history_db[user_id][-6:]  # Last 3 exchanges
    return []

def store_conversation(user_id: str, message: str, response: str):
    """Store conversation for context"""
    if user_id:
        if user_id not in chat_history_db:
            chat_history_db[user_id] = []
        
        chat_history_db[user_id].extend([
            {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
            {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
        ])
        
        # Keep only last 20 messages to prevent memory issues
        if len(chat_history_db[user_id]) > 20:
            chat_history_db[user_id] = chat_history_db[user_id][-20:]

@app.route('/health_check')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'advanced_v2.0',
        'rag_system': 'available' if rag_system else 'fallback',
        'features': {
            'advanced_metrics': True,
            'goal_based_recommendations': True,
            'context_aware_chat': True,
            'follow_up_suggestions': True
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting Advanced BodyBae.ai...")
    print(f"📊 RAG System: {'✅ Available' if rag_system else '⚠️ Fallback'}")
    print(f"🧠 AI Features: Advanced metrics, Goal-based responses, Context awareness")
    print(f"🌐 Running on port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)