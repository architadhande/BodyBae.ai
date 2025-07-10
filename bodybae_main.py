from flask import Flask, request, jsonify, session
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Import SmolLM RAG system
try:
    from rag_system import SmolLMHealthRAG
    RAG_AVAILABLE = True
    print("✅ SmolLM RAG system imported successfully")
except ImportError as e:
    print(f"⚠️ SmolLM RAG system not available: {e}")
    RAG_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Storage
users_db = {}
chat_history_db = {}

# Initialize SmolLM RAG system
rag_system = None
if RAG_AVAILABLE:
    try:
        print("🔄 Initializing SmolLM3-3B Health RAG system...")
        rag_system = SmolLMHealthRAG()
        print("✅ SmolLM3-3B system ready!")
    except Exception as e:
        print(f"⚠️ SmolLM RAG initialization failed: {e}")
        rag_system = None

def calculate_bmi_and_metrics(user_data):
    """Calculate BMI and health metrics"""
    weight = user_data['weight']
    height = user_data['height'] / 100  # Convert to meters
    age = user_data['age']
    gender = user_data['gender']
    activity = user_data['activity']
    
    # BMI calculation
    bmi = weight / (height ** 2)
    
    # BMI category
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
    
    # BMR calculation (Mifflin-St Jeor)
    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * (height * 100) - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * (height * 100) - 5 * age - 161
    
    # TDEE calculation
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extremely_active": 1.9
    }
    tdee = bmr * activity_multipliers.get(activity, 1.2)
    
    return {
        'bmi': round(bmi, 1),
        'bmi_category': category,
        'bmi_advice': advice,
        'bmr': round(bmr),
        'tdee': round(tdee),
        'protein_needs': round(weight * 1.6, 1),
        'water_needs': round(weight * 35)
    }

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>BodyBae.ai - Your AI Health Coach</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: #424106;
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #424106, #6D4930);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .header p {
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }
        
        /* Chat Container */
        .chat-container {
            background: white;
            border-radius: 0 0 15px 15px;
            flex: 1;
            display: flex;
            flex-direction: column;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        /* Messages Area */
        .messages-area {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: linear-gradient(to bottom, white, #fafafa);
            min-height: 400px;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px 20px;
            border-radius: 20px;
            max-width: 85%;
            line-height: 1.6;
            animation: fadeIn 0.3s ease;
        }
        
        .message.bot {
            background: #f0f0f0;
            color: #424106;
            margin-right: auto;
            border-bottom-left-radius: 8px;
        }
        
        .message.user {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 8px;
        }
        
        .message.system {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            margin: 15px auto;
            text-align: center;
            max-width: 90%;
            font-weight: 500;
        }
        
        /* Profile Form within Chat */
        .profile-form {
            background: #f9f7f4;
            border: 2px solid #A4B07E;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            max-width: 90%;
        }
        
        .form-title {
            color: #424106;
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #424106;
            font-size: 0.9rem;
        }
        
        input, select {
            width: 100%;
            padding: 10px;
            border: 2px solid #d4cbbc;
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.3s ease;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #A4B07E;
        }
        
        /* Goals Selection */
        .goals-section {
            margin: 15px 0;
        }
        
        .goals-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 8px;
            margin-top: 10px;
        }
        
        .goal-chip {
            background: #d4cbbc;
            color: #424106;
            padding: 10px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.85rem;
            text-align: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }
        
        .goal-chip:hover, .goal-chip.selected {
            background: #A4B07E;
            color: white;
            border-color: #707C4F;
            transform: translateY(-2px);
        }
        
        /* Buttons */
        .btn {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 10px 5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-full {
            width: 100%;
            margin: 15px 0;
        }
        
        /* Health Metrics Display */
        .metrics-display {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            padding: 15px;
            border-radius: 12px;
            margin: 15px 0;
            text-align: center;
        }
        
        .metric-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }
        
        .metric-item {
            background: rgba(255,255,255,0.1);
            padding: 8px;
            border-radius: 8px;
            font-size: 0.9rem;
        }
        
        .metric-number {
            font-weight: bold;
            font-size: 1.1rem;
        }
        
        /* Input Area */
        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
        }
        
        .quick-actions {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }
        
        .quick-btn {
            background: #d4cbbc;
            color: #424106;
            border: none;
            padding: 8px 15px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s ease;
        }
        
        .quick-btn:hover {
            background: #A4B07E;
            color: white;
        }
        
        .input-wrapper {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }
        
        .chat-input {
            flex: 1;
            border: 2px solid #d4cbbc;
            border-radius: 25px;
            padding: 12px 18px;
            resize: none;
            max-height: 100px;
            font-family: inherit;
            font-size: 0.95rem;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: #A4B07E;
        }
        
        .send-btn {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.3rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .send-btn:hover {
            transform: scale(1.05);
        }
        
        /* Loading indicator */
        .typing-indicator {
            display: none;
            align-items: center;
            gap: 8px;
            padding: 15px 20px;
            background: #f0f0f0;
            border-radius: 20px;
            margin: 15px 0;
            max-width: 200px;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dot {
            width: 8px;
            height: 8px;
            background: #A4B07E;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-8px); }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .main-container { padding: 10px; height: 100vh; }
            .header h1 { font-size: 2rem; }
            .form-row { grid-template-columns: 1fr; }
            .goals-grid { grid-template-columns: 1fr 1fr; }
            .quick-actions { flex-direction: column; }
            .metric-row { grid-template-columns: 1fr 1fr; }
        }
        
        @media (max-width: 480px) {
            .goals-grid { grid-template-columns: 1fr; }
            .metric-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Header -->
        <div class="header">
            <h1>BodyBae.ai</h1>
            <p>Your ultimate journey to love your body more each day</p>
        </div>

        <!-- Chat Container -->
        <div class="chat-container">
            <!-- Messages Area -->
            <div class="messages-area" id="messages">
                <div class="message bot">
                    👋 Welcome to BodyBae! I'm your AI health coach powered by advanced technology and evidence-based science.
                    <br><br>
                    I'm here to help you with personalized fitness plans, nutrition guidance, habit building, and motivation to love your body more each day! 💖
                    <br><br>
                    <strong>Let's start by getting to know you better...</strong>
                </div>
                
                <!-- Profile Form embedded in chat -->
                <div class="profile-form" id="profile-form">
                    <div class="form-title">📝 Tell me about yourself</div>
                    
                    <div class="form-group">
                        <label>What's your name?</label>
                        <input type="text" id="name" placeholder="Enter your name">
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Age</label>
                            <input type="number" id="age" min="13" max="100" placeholder="25">
                        </div>
                        <div class="form-group">
                            <label>Gender</label>
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
                            <label>Height (cm)</label>
                            <input type="number" id="height" min="100" max="250" placeholder="170">
                        </div>
                        <div class="form-group">
                            <label>Weight (kg)</label>
                            <input type="number" id="weight" min="30" max="300" step="0.1" placeholder="70">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>Activity Level</label>
                        <select id="activity">
                            <option value="">Select your current activity level</option>
                            <option value="sedentary">Sedentary (Office job, little exercise)</option>
                            <option value="lightly_active">Lightly Active (Light exercise 1-3 days/week)</option>
                            <option value="moderately_active">Moderately Active (Moderate exercise 3-5 days/week)</option>
                            <option value="very_active">Very Active (Hard exercise 6-7 days/week)</option>
                            <option value="extremely_active">Extremely Active (Very hard exercise, 2x/day)</option>
                        </select>
                    </div>
                    
                    <div class="goals-section">
                        <label style="font-weight: 600; color: #424106; margin-bottom: 10px; display: block;">
                            🎯 What are your health goals? (Select all that apply)
                        </label>
                        <div class="goals-grid" id="goals-grid">
                            <!-- Goals will be populated by JavaScript -->
                        </div>
                    </div>
                    
                    <button class="btn btn-full" onclick="saveProfile()" id="save-profile-btn">
                        🚀 Let's Start My Health Journey!
                    </button>
                </div>
            </div>

            <!-- Typing Indicator -->
            <div class="typing-indicator" id="typing">
                <span>BodyBae is thinking</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>

            <!-- Input Area -->
            <div class="input-area">
                <div class="quick-actions" id="quick-actions">
                    <button class="quick-btn" onclick="askQuestion('Tell me about healthy breakfast options')">Breakfast Ideas</button>
                    <button class="quick-btn" onclick="askQuestion('Create a workout plan for me')">Workout Plan</button>
                    <button class="quick-btn" onclick="askQuestion('I need motivation today')">Motivation</button>
                    <button class="quick-btn" onclick="askQuestion('How much water should I drink?')">Hydration</button>
                </div>
                <div class="input-wrapper">
                    <textarea 
                        id="message-input" 
                        class="chat-input"
                        placeholder="Ask me anything about health, fitness, nutrition..."
                        rows="1"
                    ></textarea>
                    <button class="send-btn" onclick="sendMessage()">➤</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        let userProfile = null;
        let selectedGoals = [];
        let conversationHistory = [];
        let profileSaved = false;
        
        const healthGoals = [
            'Weight Loss', 'Muscle Building', 'Strength Training', 'Cardiovascular Health',
            'Flexibility & Mobility', 'Athletic Performance', 'General Wellness', 'Weight Gain',
            'Body Recomposition', 'Injury Recovery', 'Mental Health', 'Sleep Optimization',
            'Nutrition Education', 'Habit Building', 'Stress Management', 'Energy Boost'
        ];

        // Initialize goals on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeGoals();
            setupEventListeners();
        });

        function initializeGoals() {
            const goalsGrid = document.getElementById('goals-grid');
            goalsGrid.innerHTML = '';
            
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
                if (selectedGoals.length < 6) {
                    selectedGoals.push(goal);
                    element.classList.add('selected');
                } else {
                    addMessage('system', '⚠️ Please select maximum 6 goals for focused coaching');
                }
            }
        }

        function setupEventListeners() {
            const input = document.getElementById('message-input');
            
            input.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });

            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        }

        async function saveProfile() {
            const name = document.getElementById('name').value.trim();
            const age = document.getElementById('age').value;
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            const gender = document.getElementById('gender').value;
            const activity = document.getElementById('activity').value;

            if (!name || !age || !height || !weight || !gender || !activity) {
                addMessage('system', '⚠️ Please fill in all the fields above so I can personalize your experience!');
                return;
            }

            if (selectedGoals.length === 0) {
                addMessage('system', '🎯 Please select at least one health goal so I know how to help you best!');
                return;
            }

            const saveBtn = document.getElementById('save-profile-btn');
            saveBtn.innerHTML = '🔄 Creating your personalized profile...';
            saveBtn.disabled = true;

            try {
                const response = await fetch('/save_profile', {
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
                    profileSaved = true;
                    
                    // Hide the form
                    document.getElementById('profile-form').style.display = 'none';
                    
                    // Show metrics and AI analysis
                    displayMetrics(result.metrics);
                    addMessage('bot', result.ai_analysis);
                    
                    // Update quick actions for personalized questions
                    updateQuickActions();
                    
                    setTimeout(() => {
                        addMessage('system', '🎉 Perfect! I now have everything I need to give you personalized, evidence-based advice. What would you like to know first?');
                    }, 2000);
                } else {
                    addMessage('system', '❌ Oops! There was an error saving your profile: ' + result.error);
                    saveBtn.innerHTML = '🚀 Let\'s Start My Health Journey!';
                    saveBtn.disabled = false;
                }
            } catch (error) {
                console.error('Profile error:', error);
                addMessage('system', '🔌 Network error. Please check your connection and try again!');
                saveBtn.innerHTML = '🚀 Let\'s Start My Health Journey!';
                saveBtn.disabled = false;
            }
        }

        function displayMetrics(metrics) {
            const metricsHtml = `
                <div class="metrics-display">
                    <div style="font-weight: 600; margin-bottom: 10px;">📊 Your Health Metrics</div>
                    <div class="metric-row">
                        <div class="metric-item">
                            BMI<br><span class="metric-number">${metrics.bmi}</span>
                        </div>
                        <div class="metric-item">
                            Category<br><span class="metric-number">${metrics.bmi_category}</span>
                        </div>
                        <div class="metric-item">
                            Daily Calories<br><span class="metric-number">${metrics.tdee}</span>
                        </div>
                        <div class="metric-item">
                            Protein Needs<br><span class="metric-number">${metrics.protein_needs}g</span>
                        </div>
                        <div class="metric-item">
                            Water Goal<br><span class="metric-number">${Math.round(metrics.water_needs/1000)}L</span>
                        </div>
                    </div>
                </div>
            `;
            addRawMessage(metricsHtml);
        }

        function updateQuickActions() {
            const quickActions = document.getElementById('quick-actions');
            const goals = selectedGoals.slice(0, 4); // Top 4 goals
            
            let newActions = [];
            
            if (goals.includes('Weight Loss')) {
                newActions.push('Create a weight loss meal plan for me');
            }
            if (goals.includes('Muscle Building')) {
                newActions.push('Design a muscle building workout routine');
            }
            if (goals.includes('Cardiovascular Health')) {
                newActions.push('Best cardio exercises for my fitness level');
            }
            
            // Add general actions
            newActions.push('I need motivation and accountability tips');
            newActions.push('How to track my progress effectively');
            newActions.push('What supplements might help my goals');
            
            quickActions.innerHTML = '';
            newActions.slice(0, 6).forEach(action => {
                const btn = document.createElement('button');
                btn.className = 'quick-btn';
                btn.textContent = action;
                btn.onclick = () => askQuestion(action);
                quickActions.appendChild(btn);
            });
        }

        function askQuestion(question) {
            document.getElementById('message-input').value = question;
            sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;

            addMessage('user', message);
            input.value = '';
            input.style.height = 'auto';

            conversationHistory.push({role: 'user', content: message});

            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message,
                        user_profile: userProfile,
                        conversation_history: conversationHistory.slice(-8),
                        profile_saved: profileSaved
                    })
                });

                const result = await response.json();
                
                hideTyping();
                addMessage('bot', result.response);
                
                conversationHistory.push({role: 'assistant', content: result.response});
                
                if (conversationHistory.length > 20) {
                    conversationHistory = conversationHistory.slice(-20);
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                hideTyping();
                addMessage('bot', 'I apologize for the technical difficulty. Please try rephrasing your question or check your connection. I\'m here to help! 💚');
            }
        }

        function addMessage(sender, message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            messageDiv.innerHTML = message.replace(/\n/g, '<br>');
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function addRawMessage(html) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.innerHTML = html;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showTyping() {
            document.getElementById('typing').style.display = 'flex';
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }

        function hideTyping() {
            document.getElementById('typing').style.display = 'none';
        }

        console.log('BodyBae.ai single-page chatbot loaded successfully');
    </script>
</body>
</html>
'''

@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Save user profile and generate AI insights"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
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
        
        # Calculate health metrics
        metrics = calculate_bmi_and_metrics(user_data)
        user_data.update(metrics)
        
        # Store user data
        users_db[user_id] = user_data
        session['user_id'] = user_id
        
        # Generate AI analysis
        if rag_system:
            try:
                analysis_prompt = f"""
                Welcome {data['name']}! I've analyzed your health profile:
                
                Profile: {data['age']} year old {data['gender']}, {data['height']}cm, {data['weight']}kg
                BMI: {metrics['bmi']} ({metrics['bmi_category']})
                Activity: {data['activity']}
                Goals: {', '.join(data['goals'])}
                
                Provide a warm, encouraging welcome message with personalized insights and recommendations.
                """
                
                ai_analysis = rag_system.generate_health_response(
                    analysis_prompt, 
                    user_data, 
                    []
                )
                
            except Exception as e:
                print(f"AI analysis error: {e}")
                ai_analysis = generate_welcome_analysis(user_data, metrics)
        else:
            ai_analysis = generate_welcome_analysis(user_data, metrics)
        
        return jsonify({
            'success': True,
            'profile': user_data,
            'metrics': metrics,
            'ai_analysis': ai_analysis
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_welcome_analysis(user_data, metrics):
    """Generate personalized welcome analysis"""
    name = user_data['name']
    bmi = metrics['bmi']
    category = metrics['bmi_category']
    goals = user_data['goals']
    
    analysis = f"""🎉 **Welcome to your health journey, {name}!**

I'm excited to be your AI health coach! Based on your profile, here's what I see:

**Your Current Status:**
• BMI of {bmi} puts you in the '{category}' range
• Your daily caloric needs are approximately {metrics['tdee']} calories
• You should aim for {metrics['protein_needs']}g of protein daily
• Target water intake: {round(metrics['water_needs']/1000, 1)}L per day

**Your Goals:**
I love that you're focused on: {', '.join(goals[:3])}{'...' if len(goals) > 3 else ''}! This shows you're serious about improving your health.

**What This Means:**
{metrics['bmi_advice']}"""

    # Add goal-specific insights
    if 'Weight Loss' in goals and bmi > 25:
        analysis += f"\n\n**For Weight Loss:** I recommend targeting around {metrics['tdee'] - 500} calories daily (500-calorie deficit) combined with regular exercise."
    
    if 'Muscle Building' in goals:
        analysis += f"\n\n**For Muscle Building:** Focus on strength training 3-4x per week and ensure you're getting that {metrics['protein_needs']}g of protein spread throughout the day."
    
    if 'Cardiovascular Health' in goals:
        analysis += "\n\n**For Heart Health:** Aim for 150+ minutes of moderate cardio or 75+ minutes of vigorous cardio weekly."

    analysis += f"\n\n**Next Steps:**\nI'm here to provide evidence-based, personalized advice for your specific situation. Ask me anything - from meal planning to workout routines to staying motivated!\n\nWhat would you like to tackle first, {name}? 💪"
    
    return analysis

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    data = request.json
    message = data.get('message', '')
    user_profile = data.get('user_profile', {})
    conversation_history = data.get('conversation_history', [])
    profile_saved = data.get('profile_saved', False)
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'})
    
    try:
        # Enhanced user profile from stored data
        if user_id and user_id in users_db:
            stored_profile = users_db[user_id]
            user_profile.update(stored_profile)
        
        # Handle cases where profile isn't saved yet
        if not profile_saved and not user_profile:
            return jsonify({
                'response': "I'd love to help you! But first, please fill out your profile above so I can give you personalized advice tailored to your specific situation. Once you complete your profile, I'll be able to provide much more targeted and effective guidance! 😊"
            })
        
        # Use SmolLM3 RAG system for intelligent responses
        if rag_system:
            try:
                response = rag_system.generate_health_response(
                    message, 
                    user_profile, 
                    conversation_history
                )
                
                # Store conversation
                if user_id:
                    if user_id not in chat_history_db:
                        chat_history_db[user_id] = []
                    chat_history_db[user_id].extend([
                        {'role': 'user', 'content': message, 'timestamp': datetime.now().isoformat()},
                        {'role': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()}
                    ])
                
                return jsonify({
                    'response': response,
                    'source': 'smollm3_rag'
                })
                
            except Exception as rag_error:
                print(f"SmolLM3 RAG error: {rag_error}")
                response = get_intelligent_fallback(message, user_profile)
                
        else:
            response = get_intelligent_fallback(message, user_profile)
        
        return jsonify({
            'response': response,
            'source': 'intelligent_fallback'
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "I'm experiencing some technical difficulties, but I'm still here to help! Could you try rephrasing your question? I'm committed to supporting your health journey! 💚"
        })

def get_intelligent_fallback(message: str, user_profile: Dict) -> str:
    """Intelligent fallback responses with personalization"""
    name = user_profile.get('name', 'there')
    message_lower = message.lower()
    goals = user_profile.get('goals', [])
    bmi = user_profile.get('bmi', 0)
    tdee = user_profile.get('tdee', 0)
    
    # Workout and Exercise
    if any(word in message_lower for word in ['workout', 'exercise', 'training', 'gym', 'routine']):
        response = f"Great question about workouts, {name}! "
        
        if 'Muscle Building' in goals:
            response += "Since muscle building is one of your goals, I recommend:\n\n"
            response += "**Strength Training Focus:**\n"
            response += "• 3-4 sessions per week\n"
            response += "• Compound movements: squats, deadlifts, bench press, rows\n"
            response += "• 3-4 sets of 6-12 reps with progressive overload\n"
            response += "• 48-72 hours rest between training same muscle groups\n\n"
        
        if 'Weight Loss' in goals:
            response += "For your weight loss goal:\n"
            response += "• Combine 3x strength training + 2-3x cardio weekly\n"
            response += "• HIIT sessions 2x per week for efficiency\n"
            response += "• 150+ minutes moderate cardio or 75+ vigorous weekly\n\n"
        
        if 'Cardiovascular Health' in goals:
            response += "For heart health:\n"
            response += "• Start with 20-30 minutes moderate intensity\n"
            response += "• Gradually build to 150+ minutes weekly\n"
            response += "• Mix steady-state and interval training\n\n"
        
        response += "Would you like me to create a specific weekly schedule based on your goals?"
        return response
    
    # Nutrition and Diet
    elif any(word in message_lower for word in ['nutrition', 'diet', 'food', 'calories', 'meal', 'eat']):
        response = f"Excellent question about nutrition, {name}! "
        
        if tdee:
            if 'Weight Loss' in goals and bmi > 25:
                target_calories = int(tdee - 500)
                response += f"For healthy weight loss:\n\n"
                response += f"**Daily Targets:**\n"
                response += f"• Calories: {target_calories} (500-calorie deficit)\n"
                response += f"• Protein: {user_profile.get('protein_needs', 'calculated')}g\n"
                response += f"• Water: {round(user_profile.get('water_needs', 2500)/1000, 1)}L\n\n"
            
            elif 'Muscle Building' in goals:
                target_calories = int(tdee + 250)
                response += f"For muscle building:\n\n"
                response += f"**Daily Targets:**\n"
                response += f"• Calories: {target_calories} (slight surplus)\n"
                response += f"• Protein: {user_profile.get('protein_needs', 'calculated')}g\n"
                response += f"• Protein timing: 20-30g every 3-4 hours\n\n"
            
            else:
                response += f"For maintenance and general health:\n\n"
                response += f"**Daily Targets:**\n"
                response += f"• Calories: {int(tdee)}\n"
                response += f"• Balanced macronutrients\n"
                response += f"• Focus on whole, unprocessed foods\n\n"
        
        response += "**Meal Structure:**\n"
        response += "• Include protein with every meal\n"
        response += "• Fill half your plate with vegetables\n"
        response += "• Choose complex carbohydrates\n"
        response += "• Include healthy fats daily\n\n"
        response += "Would you like specific meal ideas or a sample meal plan?"
        return response
    
    # Motivation and Mental Health
    elif any(word in message_lower for word in ['motivation', 'motivated', 'give up', 'struggling', 'hard', 'difficult', 'help']):
        response = f"I hear you, {name}! 🤗 What you're feeling is completely normal and shows you're pushing yourself out of your comfort zone.\n\n"
        
        response += "**Remember Your Why:**\n"
        if goals:
            response += f"• You chose these goals: {', '.join(goals[:3])}\n"
        response += "• Every small action is building toward your bigger vision\n"
        response += "• Progress isn't linear - there will be ups and downs\n\n"
        
        response += "**Strategies That Work:**\n"
        response += "• Break big goals into tiny daily actions\n"
        response += "• Celebrate small wins along the way\n"
        response += "• Focus on how you FEEL, not just how you look\n"
        response += "• Remember: you're building habits for life, not just quick fixes\n\n"
        
        response += "**Right Now:**\n"
        response += "• Take 3 deep breaths\n"
        response += "• Choose ONE small healthy action for today\n"
        response += "• Be kind to yourself - you're doing better than you think! 💚\n\n"
        
        response += "What specific challenge are you facing? I'm here to help you work through it!"
        return response
    
    # Sleep and Recovery
    elif any(word in message_lower for word in ['sleep', 'tired', 'energy', 'recovery', 'rest']):
        response = f"Sleep is so crucial for your goals, {name}! Let me help you optimize your rest:\n\n"
        
        response += "**Sleep Optimization Protocol:**\n"
        response += "• 7-9 hours nightly (non-negotiable for health)\n"
        response += "• Consistent bedtime and wake time (even on weekends)\n"
        response += "• Cool, dark room (65-68°F / 18-20°C)\n"
        response += "• No screens 1 hour before bed\n\n"
        
        response += "**Natural Sleep Enhancers:**\n"
        response += "• Magnesium supplement (200-400mg before bed)\n"
        response += "• Chamomile tea 30 minutes before sleep\n"
        response += "• Progressive muscle relaxation\n"
        response += "• Morning sunlight exposure (10-15 minutes)\n\n"
        
        if 'Sleep Optimization' in goals:
            response += "**Advanced Strategies for Your Goal:**\n"
            response += "• Track sleep with a device or app\n"
            response += "• Avoid caffeine after 2 PM\n"
            response += "• Consider blue light blocking glasses\n"
            response += "• Create a 30-minute wind-down routine\n\n"
        
        response += "What's your biggest sleep challenge? Falling asleep or staying asleep?"
        return response
    
    # Supplements
    elif any(word in message_lower for word in ['supplement', 'vitamins', 'protein powder', 'creatine']):
        response = f"Smart question about supplements, {name}! Here's evidence-based guidance:\n\n"
        
        response += "**Foundation First:**\n"
        response += "• Whole foods should be your primary source of nutrition\n"
        response += "• Supplements fill specific gaps, not replace good eating\n"
        response += "• Quality matters - look for third-party tested products\n\n"
        
        response += "**Universal Supplements (for most people):**\n"
        response += "• Vitamin D3: 2000-4000 IU daily\n"
        response += "• Omega-3 (EPA/DHA): 1-2g daily\n"
        response += "• Magnesium: 200-400mg daily\n"
        response += "• High-quality multivitamin as insurance\n\n"
        
        if 'Muscle Building' in goals:
            response += "**For Your Muscle Building Goal:**\n"
            response += "• Whey protein powder (if you struggle to hit protein targets)\n"
            response += "• Creatine monohydrate: 3-5g daily (most researched supplement)\n"
            response += "• Consider vitamin D if deficient (affects muscle function)\n\n"
        
        if 'Weight Loss' in goals:
            response += "**For Weight Loss Support:**\n"
            response += "• Green tea extract (EGCG for metabolism)\n"
            response += "• Caffeine (if tolerated, for energy and appetite)\n"
            response += "• Fiber supplement if diet lacks vegetables\n\n"
        
        response += "What specific supplements are you considering? I can give you more targeted advice!"
        return response
    
    # General helpful response
    else:
        response = f"Hi {name}! I'm here to help you achieve your health goals with evidence-based advice.\n\n"
        
        if goals:
            response += f"**Your Goals:** {', '.join(goals[:4])}\n\n"
        
        response += "**I can help you with:**\n"
        response += "• Personalized workout programs\n"
        response += "• Nutrition strategies and meal planning\n"
        response += "• Supplement recommendations\n"
        response += "• Habit formation and motivation\n"
        response += "• Sleep and recovery optimization\n"
        response += "• Progress tracking strategies\n\n"
        
        if user_profile:
            response += f"Based on your profile (BMI: {bmi}, Goals: {len(goals)} selected), I can give you very specific, personalized advice.\n\n"
        
        response += "What would you like to dive deeper into? I'm here to provide detailed, actionable guidance! 😊"
        return response

@app.route('/health_check')
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'SinglePage_SmolLM3_v1.0',
        'ai_system': 'available' if rag_system else 'intelligent_fallback',
        'features': ['Single Page Interface', 'Embedded Profile', 'Personalized Chat', 'Health Metrics']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting BodyBae.ai Single-Page Chatbot...")
    print(f"🤖 AI Model: SmolLM3-3B with RAG")
    print(f"📊 Interface: Single-page with embedded profile")
    print(f"🌐 Port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)