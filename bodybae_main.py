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
        'protein_needs': round(weight * 1.6, 1),  # Active person protein needs
        'water_needs': round(weight * 35)  # ml per day
    }

@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>BodyBae.ai - SmolLM3 Health Coach</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: #424106;
            min-height: 100vh;
        }
        
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        
        /* Welcome Screen */
        .welcome {
            text-align: center;
            padding: 60px 20px;
            color: white;
        }
        
        .welcome h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            color: #424106;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .welcome p {
            font-size: 1.2rem;
            margin-bottom: 30px;
            opacity: 0.9;
        }
        
        .btn {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 1.1rem;
            border-radius: 25px;
            cursor: pointer;
            margin: 10px;
            transition: transform 0.3s ease;
        }
        
        .btn:hover { transform: translateY(-2px); }
        .btn-small { padding: 8px 15px; font-size: 0.9rem; }
        
        /* Chat Screen */
        .chat-screen { display: none; background: white; border-radius: 15px; margin-top: 20px; }
        
        .chat-layout {
            display: grid;
            grid-template-columns: 300px 1fr;
            height: 80vh;
        }
        
        /* Sidebar */
        .sidebar {
            background: #f9f7f4;
            padding: 20px;
            border-right: 1px solid #ddd;
            overflow-y: auto;
        }
        
        .form-section {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .form-section h3 {
            color: #707C4F;
            margin-bottom: 15px;
            font-size: 1.1rem;
        }
        
        .form-group { margin-bottom: 10px; }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 0.9rem;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #A4B07E;
        }
        
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        
        /* Goals */
        .goals-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 5px;
            margin-top: 10px;
        }
        
        .goal-chip {
            background: #d4cbbc;
            padding: 8px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 0.8rem;
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .goal-chip:hover, .goal-chip.selected {
            background: #A4B07E;
            color: white;
        }
        
        /* Chat Area */
        .chat-main {
            display: flex;
            flex-direction: column;
            background: white;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: linear-gradient(to bottom, white, #fafafa);
        }
        
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 15px;
            max-width: 85%;
            line-height: 1.5;
        }
        
        .message.user {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .message.bot {
            background: #f0f0f0;
            color: #424106;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        
        .message.system {
            background: linear-gradient(45deg, #C6A6B5, #6D4930);
            color: white;
            margin: 10px auto;
            text-align: center;
            max-width: 90%;
        }
        
        /* Input Area */
        .chat-input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #eee;
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
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
            border: 2px solid #ddd;
            border-radius: 20px;
            padding: 12px 15px;
            resize: none;
            max-height: 100px;
            font-family: inherit;
        }
        
        .chat-input:focus {
            outline: none;
            border-color: #A4B07E;
        }
        
        .send-btn {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            border: none;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
        }
        
        .send-btn:hover { transform: scale(1.05); }
        
        /* Health Metrics */
        .metrics-display {
            background: linear-gradient(135deg, #A4B07E, #707C4F);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-size: 0.9rem;
        }
        
        .metric-item { margin: 5px 0; }
        .metric-number { font-weight: bold; font-size: 1.1rem; }
        
        /* Loading */
        .loading { opacity: 0.7; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .chat-layout { grid-template-columns: 1fr; height: auto; }
            .sidebar { max-height: 300px; }
            .chat-messages { height: 400px; }
            .form-row, .goals-grid { grid-template-columns: 1fr; }
            .quick-actions { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Welcome Screen -->
        <div id="welcome" class="welcome">
            <h1>BodyBae.ai</h1>
            <p>SmolLM3-3B Powered Health Coach</p>
            <p style="font-size: 1rem; margin-bottom: 30px;">
                🤖 Advanced AI with RAG • 🧠 Evidence-based advice • 🎯 Personalized coaching
            </p>
            <button class="btn" onclick="startChat()">Start Health Coaching</button>
            <button class="btn btn-small" onclick="testSystem()">Test AI</button>
            <div id="status" style="margin-top: 20px; font-size: 0.9rem;"></div>
        </div>

        <!-- Chat Screen -->
        <div id="chat" class="chat-screen">
            <div class="chat-layout">
                <!-- Sidebar -->
                <div class="sidebar">
                    <!-- Profile Form -->
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
                                <option value="sedentary">Sedentary</option>
                                <option value="lightly_active">Lightly Active</option>
                                <option value="moderately_active">Moderately Active</option>
                                <option value="very_active">Very Active</option>
                                <option value="extremely_active">Extremely Active</option>
                            </select>
                        </div>
                    </div>

                    <!-- Health Goals -->
                    <div class="form-section">
                        <h3>🎯 Health Goals</h3>
                        <div class="goals-grid" id="goals-grid">
                            <!-- Goals populated by JavaScript -->
                        </div>
                    </div>

                    <!-- Save Profile Button -->
                    <button class="btn" onclick="saveProfile()" style="width: 100%; margin-bottom: 15px;">
                        🔍 Analyze My Health
                    </button>

                    <!-- Health Metrics Display -->
                    <div id="metrics" style="display: none;"></div>
                </div>

                <!-- Main Chat Area -->
                <div class="chat-main">
                    <div class="chat-header">
                        <h2 style="margin: 0;">💬 BodyBae AI Coach</h2>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">
                            Powered by SmolLM3-3B with specialized health knowledge
                        </p>
                    </div>
                    
                    <div id="messages" class="chat-messages">
                        <div class="message bot">
                            👋 Hello! I'm BodyBae, your AI health coach powered by SmolLM3-3B and advanced RAG technology.
                            <br><br>
                            <strong>I specialize in:</strong>
                            <br>• Evidence-based fitness and nutrition advice
                            <br>• Personalized workout and meal planning
                            <br>• Behavioral psychology for lasting change
                            <br>• Recovery and sleep optimization
                            <br><br>
                            📝 <strong>Get started:</strong> Fill out your profile on the left, select your goals, and click "Analyze My Health" for personalized insights!
                        </div>
                    </div>

                    <div class="chat-input-area">
                        <div class="quick-actions">
                            <button class="quick-btn" onclick="askQuestion('Create a personalized workout plan for my goals')">Workout Plan</button>
                            <button class="quick-btn" onclick="askQuestion('Design a nutrition strategy for my body and goals')">Nutrition Plan</button>
                            <button class="quick-btn" onclick="askQuestion('How can I build sustainable healthy habits?')">Habit Building</button>
                            <button class="quick-btn" onclick="askQuestion('I need motivation and accountability strategies')">Motivation</button>
                            <button class="quick-btn" onclick="askQuestion('Explain the science behind my fitness goals')">Science Explained</button>
                            <button class="quick-btn" onclick="askQuestion('What supplements might benefit my goals?')">Supplements</button>
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
        let conversationHistory = [];
        
        const healthGoals = [
            'Weight Loss', 'Muscle Building', 'Strength Training', 'Cardiovascular Health',
            'Flexibility', 'Athletic Performance', 'General Wellness', 'Weight Gain',
            'Body Recomposition', 'Injury Recovery', 'Mental Health', 'Sleep Optimization'
        ];

        function testSystem() {
            document.getElementById('status').innerHTML = '🤖 SmolLM3-3B AI System Ready! ✅';
            console.log('BodyBae.ai system test successful');
        }

        function startChat() {
            console.log('Starting BodyBae chat...');
            document.getElementById('welcome').style.display = 'none';
            document.getElementById('chat').style.display = 'block';
            initializeGoals();
        }

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
                if (selectedGoals.length < 5) {  // Limit to 5 goals
                    selectedGoals.push(goal);
                    element.classList.add('selected');
                } else {
                    addMessage('system', '⚠️ Please select maximum 5 goals for focused coaching');
                }
            }
        }

        async function saveProfile() {
            const name = document.getElementById('name').value.trim();
            const age = document.getElementById('age').value;
            const height = document.getElementById('height').value;
            const weight = document.getElementById('weight').value;
            const gender = document.getElementById('gender').value;
            const activity = document.getElementById('activity').value;

            if (!name || !age || !height || !weight || !gender || !activity) {
                addMessage('system', '⚠️ Please fill in all profile fields');
                return;
            }

            if (selectedGoals.length === 0) {
                addMessage('system', '🎯 Please select at least one health goal');
                return;
            }

            addMessage('system', '🔄 Analyzing your health profile with AI...');

            try {
                const response = await fetch('/analyze_profile', {
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
                    displayMetrics(result.metrics);
                    addMessage('bot', result.ai_analysis);
                    
                    setTimeout(() => {
                        addMessage('system', '🚀 Profile complete! I now have deep insights into your health status. Ask me anything for personalized, evidence-based advice!');
                    }, 2000);
                } else {
                    addMessage('system', '❌ Error analyzing profile: ' + result.error);
                }
            } catch (error) {
                console.error('Profile error:', error);
                addMessage('system', '🔌 Network error. Please try again.');
            }
        }

        function displayMetrics(metrics) {
            const metricsDiv = document.getElementById('metrics');
            metricsDiv.style.display = 'block';
            metricsDiv.innerHTML = `
                <div class="metrics-display">
                    <div class="metric-item">BMI: <span class="metric-number">${metrics.bmi}</span></div>
                    <div class="metric-item">${metrics.bmi_category}</div>
                    <div class="metric-item">Daily Calories: <span class="metric-number">${metrics.tdee}</span></div>
                    <div class="metric-item">Protein: <span class="metric-number">${metrics.protein_needs}g</span></div>
                    <div class="metric-item">Water: <span class="metric-number">${metrics.water_needs}ml</span></div>
                </div>
            `;
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

            // Add to conversation history
            conversationHistory.push({role: 'user', content: message});

            // Show AI thinking
            addMessage('system', '🤖 SmolLM3-3B is analyzing and generating response...');

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message,
                        user_profile: userProfile,
                        conversation_history: conversationHistory.slice(-6)  // Last 3 exchanges
                    })
                });

                const result = await response.json();
                
                // Remove thinking message
                const messages = document.getElementById('messages');
                const lastMessage = messages.lastElementChild;
                if (lastMessage && lastMessage.textContent.includes('analyzing')) {
                    messages.removeChild(lastMessage);
                }
                
                addMessage('bot', result.response);
                
                // Add to conversation history
                conversationHistory.push({role: 'assistant', content: result.response});
                
                // Keep conversation history manageable
                if (conversationHistory.length > 20) {
                    conversationHistory = conversationHistory.slice(-20);
                }
                
            } catch (error) {
                console.error('Chat error:', error);
                // Remove thinking message
                const messages = document.getElementById('messages');
                const lastMessage = messages.lastElementChild;
                if (lastMessage && lastMessage.textContent.includes('analyzing')) {
                    messages.removeChild(lastMessage);
                }
                addMessage('bot', 'I apologize for the technical difficulty. Please try rephrasing your question or check your connection.');
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

        // Auto-resize textarea
        document.addEventListener('DOMContentLoaded', function() {
            const input = document.getElementById('message-input');
            input.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });

            // Enter key support
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        });

        console.log('BodyBae.ai SmolLM3-3B system loaded');
    </script>
</body>
</html>
'''

@app.route('/analyze_profile', methods=['POST'])
def analyze_profile():
    """Analyze user profile and generate AI insights"""
    data = request.json
    user_id = str(uuid.uuid4())
    
    try:
        # Create user profile
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
        
        # Generate AI analysis using SmolLM3
        if rag_system:
            try:
                analysis_prompt = f"""
                Analyze this comprehensive health profile and provide personalized insights:
                
                Name: {data['name']}, Age: {data['age']}, Gender: {data['gender']}
                Physical: {data['height']}cm, {data['weight']}kg
                BMI: {metrics['bmi']} ({metrics['bmi_category']})
                Activity Level: {data['activity']}
                Health Goals: {', '.join(data['goals'])}
                Daily Needs: {metrics['tdee']} calories, {metrics['protein_needs']}g protein
                
                Provide a comprehensive health analysis with specific recommendations.
                """
                
                ai_analysis = rag_system.generate_health_response(
                    analysis_prompt, 
                    user_data, 
                    []
                )
                
            except Exception as e:
                print(f"AI analysis error: {e}")
                ai_analysis = generate_basic_analysis(user_data, metrics)
        else:
            ai_analysis = generate_basic_analysis(user_data, metrics)
        
        return jsonify({
            'success': True,
            'profile': user_data,
            'metrics': metrics,
            'ai_analysis': ai_analysis
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

def generate_basic_analysis(user_data, metrics):
    """Generate basic analysis when AI is not available"""
    name = user_data['name']
    bmi = metrics['bmi']
    category = metrics['bmi_category']
    goals = user_data['goals']
    
    analysis = f"""🔍 **Health Analysis for {name}**

**Current Status:**
• BMI: {bmi} ({category})
• Daily Caloric Needs: {metrics['tdee']} calories
• Protein Requirements: {metrics['protein_needs']}g daily
• Hydration Target: {metrics['water_needs']}ml daily

**Key Insights:**
{metrics['bmi_advice']}

**Goal-Specific Recommendations:**"""
    
    if 'Weight Loss' in goals:
        target = metrics['tdee'] - 500
        analysis += f"\n• For weight loss: Target {target} calories daily with 500-calorie deficit"
    
    if 'Muscle Building' in goals:
        analysis += f"\n• For muscle building: Focus on {metrics['protein_needs']}g protein daily with resistance training"
    
    if 'Cardiovascular Health' in goals:
        analysis += "\n• For heart health: Include 150+ minutes moderate cardio weekly"
    
    analysis += f"\n\n**Next Steps:**\n• Track your daily intake and exercise\n• Focus on consistency over perfection\n• Ask me specific questions for detailed guidance!"
    
    return analysis

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint using SmolLM3-3B RAG system"""
    data = request.json
    message = data.get('message', '')
    user_profile = data.get('user_profile', {})
    conversation_history = data.get('conversation_history', [])
    user_id = session.get('user_id')
    
    if not message:
        return jsonify({'error': 'Message is required'})
    
    try:
        # Enhanced user profile from stored data
        if user_id and user_id in users_db:
            stored_profile = users_db[user_id]
            user_profile.update(stored_profile)
        
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
                # Fallback to basic response
                response = get_basic_response(message, user_profile)
                
        else:
            response = get_basic_response(message, user_profile)
        
        return jsonify({
            'response': response,
            'source': 'basic_fallback'
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            'response': "I'm experiencing technical difficulties. Please try rephrasing your question or restart the conversation.",
            'source': 'error_fallback'
        })

def get_basic_response(message: str, user_profile: Dict) -> str:
    """Basic fallback response system"""
    name = user_profile.get('name', 'there')
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['workout', 'exercise', 'training']):
        return f"Hi {name}! For effective workouts, I recommend combining strength training with cardiovascular exercise. Based on your goals, focus on progressive overload and consistency. Would you like me to create a specific workout plan for you?"
    
    elif any(word in message_lower for word in ['nutrition', 'diet', 'food', 'calories']):
        if user_profile.get('tdee'):
            return f"Hi {name}! Based on your profile, your daily caloric needs are around {user_profile['tdee']} calories. Focus on whole foods, adequate protein ({user_profile.get('protein_needs', 'calculated')}g daily), and stay hydrated with {user_profile.get('water_needs', 2500)}ml of water daily."
        return f"Hi {name}! For optimal nutrition, focus on balanced meals with lean proteins, complex carbohydrates, healthy fats, and plenty of vegetables. How can I help you with your specific nutrition goals?"
    
    elif any(word in message_lower for word in ['motivation', 'help', 'struggling']):
        return f"I believe in you, {name}! 🌟 Remember, every small step counts toward your health goals. Progress isn't always linear, and that's completely normal. What specific challenge are you facing? I'm here to help you overcome it!"
    
    else:
        goals = user_profile.get('goals', [])
        if goals:
            return f"Hi {name}! I see your goals include {', '.join(goals[:3])}. I'm here to provide evidence-based advice to help you achieve them. What specific aspect would you like to focus on today?"
        return f"Hi {name}! I'm here to help with your health and fitness journey. I can provide advice on workouts, nutrition, motivation, and more. What would you like to know?"

@app.route('/health_check')
def health_check():
    """System health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': 'SmolLM3-3B_v1.0',
        'ai_system': 'available' if rag_system else 'fallback',
        'model': 'HuggingFaceTB/SmolLM3-3B',
        'features': ['RAG', 'Health Knowledge Base', 'Personalized Coaching']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print("🚀 Starting BodyBae.ai with SmolLM3-3B...")
    print(f"🤖 AI Model: HuggingFaceTB/SmolLM3-3B")
    print(f"📊 RAG System: {'✅ Active' if rag_system else '⚠️ Fallback'}")
    print(f"🌐 Port: {port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)